## [译] Elixir中TCP连接处理技巧 -- Andrea Leopardi

鉴于Erlang的设计风格和Erlang虚拟机的特性，Elixir作为一门Erlang虚拟机上的语言，在网络编程中大展身手。在这个大前提下，我们总有这样的需求---在网络世界中处理外部链接。
举个例子：一个典型的Web应用需要连接一个关系型数据库和一个kvdb，或者一个嵌入式的系统需要连接其他的node。

大多数情况下，归功于一些已经封装好的网络驱动(例如数据库驱动)，这些网络连接对程序员来说是无需关心的，但是我认为了解这些连接如何手动处理是一件很有趣的事情。如果某些特殊的网络服务没有外部的驱动代码可用，又或者你想了解这些驱动是怎样工作的，这些知识就会很有用。

这篇文章中我们只会讨论TCP协议的连接，因为TCP协议可能是网络世界中最基础和使用最多的协议了。但是我们所使用的方法和原理，在其他协议面前也是通用的，例如UDP协议。

### 一个很现实的例子
作为这篇文章的目标，我们想编写一个差不多能work的redis驱动。Redis服务是能够收发message的TCP服务。Redis在TCP之上使用了一个自定义的应用层协议，并没有使用通用的HTTP协议。而我们并不关心这些，我们只关心怎样处理我们的Elixir应用和Redis Server之间的TCP连接。

一点题外话：显然，社区里已经有很多的Erlang和Elixir的Redis驱动，不过，懒惰的我懒得再去想一个聪明的名字，我们就叫他Redis好了。

这就开始吧。

### Erlang/Elixir中TCP简述
在Erlang/Elixir中，tcp连接是用:gen_tcp模块来处理的。这篇文章中我们只编写客户端部分来与Redis服务交互，实际上:gen_tcp也可以用来编写TCP服务端。

所有的发向Server的消息都用:gen_tcp.send/2函数来发送。而从服务端发送至客户端的消息我们总是倾向于把它们当作Erlang Message来处理，因为这样处理起来比较直观。后面我们会看到，我们将通过设置TCP socket的:active option选项来控制发送至客户端的消息。

我们通过传递host、port等参数至:gen_tcp.connect/3来建立与服务端的连接。默认情况下，调用connect函数的进程会被认为是这个tcp连接的“controlling process”，意思就是这个进程将会处理所有发到这个socket的tcp消息。

以上是我们对tcp连接所需要了解的知识，我们继续。

### 第一个版本
我们将使用GenServer作为我们TCP连接的接口。我们需要一个GenServer以便于我们在state中保持socket的状态和在所有消息通信中复用这个socket。

#### 建立连接
因为我们使用GenServer作为TCP连接的接口，所以我们一次只能在state的socket中维护单个连接的状态，我们希望它总是和Server保持连接的状态。最优的策略实在GenServer启动的时候来做连接的工作，具体是在init的回调函数中实现。init/1是在GenServer.start_link/2被调用的时候触发的函数，GenServer在init被调用前不会做多余的工作，所有是我们建立连接的最佳场所。
```
defmodule Redis do
  use GenServer

  @initial_state %{socket: nil}

  def start_link do
    GenServer.start_link(__MODULE__, @initial_state)
  end

  def init(state) do
    opts = [:binary, active: false]
    {:ok, socket} = :gen_tcp.connect('localhost', 6379, opts)
    {:ok, %{state | socket: socket}}
  end
end
```
我们给:gen_tcp.connect/3设定的参数非常直观。:binary要求socket从TCP server中接收的消息以binary的格式接收而不是Erlang默认的charlist格式：在Elixir中这可能是我们想要的，而且可能是最高效的选择。active: false告诉socket永远不要把TCP message转换成发送给GenServer的Erlang message；我们将用:gen_tcp.recv/2函数来显式的接收tcp消息。我们这样做是为了我们的GenServer不被汹涌而来的tcp消息淹没：我们只在我们想要的时候去接收并处理它们。

#### 发送消息
现在我们已经有了一个连接上Redis服务的GenServer了，现在让我们给Redis发送一些指令。

##### RESP PROTOCL
这里需要简单提一下Redis的二进制协议，RESP：这是Redis用于编解码它的Requst/Reply的协议，[协议的细节](https://redis.io/topics/protocol)简单明了，如果你想了解更多，我建议你看看。为了这篇文章的中心目标，我们假设我们有了RESP的完全实现：它提供了encode/decode两个函数：
- Redis.RESP.encode/1: 将list编码成redis command，例如:
```
Redis.RESP.encode(["GET", "mykey"])
#=> <<...>>
```
- Redis.RESP.decode/1: 将一个binary解码成一个Elixir对象，例如:
```
resp_to_get_command = <<...>>
Redis.RESP.decode(resp_to_get_command)
#=> 1
```

##### :gen_tcp.send/2
我们在文章开头提到过，我们利用:gen_tcp.send/2来向tcp连接发送消息。我们的Redis模块将提供单独一个函数来向Redis Server发送命令：Redis.command/2。具体实现也很直观：
```
defmodule Redis do
  # ...as before...

  def command(pid, cmd) do
    GenServer.call(pid, {:command, cmd})
  end

  def handle_call({:command, cmd}, from, %{socket: socket} = state) do
    :ok = :gen_tcp.send(socket, Redis.RESP.encode(cmd))

    # `0` means receive all available bytes on the socket.
    {:ok, msg} = :gen_tcp.recv(socket, 0)
    {:reply, Redis.RESP.decode(msg), state}
  end
end
```
这段代码能顺利工作
```
{:ok, pid} = Redis.start_link()
Redis.command(pid, ["SET", "mykey", 1])
Redis.command(pid, ["GET", "mykey"])
#=> 1
```
... 但这里有个大问题
#### 哪里有问题呢？
长话短说：:gen_tcp.recv/2函数是阻塞的。

这段代码能顺利工作的前提是这个GenServer只被单个Elixir进程调用。当一个进程想发送命令给Redis Server的时候会发生如下事件：
1. Elixir进程调用GenServer的command/2命令，然后进程阻塞的等待结果
2. GenServer向Redis Server发送指令然后阻塞在:gen_tcp.recv/2上
3. Redis Server回复结果
4. GenServer回应调用进程

你能看出问题出在哪里了吗？GenServer在等待Redis Server回复的过程中是阻塞的。当然在单个进程的情况下这样是没问题的，但当多个进程同时想通过GenServer跟Redis Server做交互的时候情况就会变得很糟糕。幸好，我们可以做一个更好的实现。


----
原文链接: [Handling TCP connections in Elixir](https://andrealeopardi.com/posts/handling-tcp-connections-in-elixir/)
