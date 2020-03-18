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
在Erlang/Elixir中，tcp连接是用`:gen_tcp`模块来处理的。这篇文章中我们只编写客户端部分来与Redis服务交互，实际上`:gen_tcp`也可以用来编写TCP服务端。

所有的发向Server的消息都用`:gen_tcp.send/2`函数来发送。而从服务端发送至客户端的消息我们总是倾向于把它们当作Erlang Message来处理，因为这样处理起来比较直观。后面我们会看到，我们将通过设置TCP socket的`:active` option选项来控制发送至客户端的消息。

我们通过传递host、port等参数至`:gen_tcp.connect/3`来建立与服务端的连接。默认情况下，调用connect函数的进程会被认为是这个tcp连接的“controlling process”，意思就是这个进程将会处理所有发到这个socket的tcp消息。

以上是我们对tcp连接所需要了解的知识，我们继续。

### 第一个版本
我们将使用`GenServer`作为我们TCP连接的接口。我们需要一个GenServer以便于我们在state中保持socket的状态和在所有消息通信中复用这个socket。

#### 建立连接
因为我们使用GenServer作为TCP连接的接口，所以我们一次只能在state的socket中维护单个连接的状态，我们希望它总是和Server保持连接的状态。最优的策略实在GenServer启动的时候来做连接的工作，具体是在init的回调函数中实现。`init/1`是在`GenServer.start_link/2`被调用的时候触发的函数，GenServer在init被调用前不会做多余的工作，所有是我们建立连接的最佳场所。
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
我们给`:gen_tcp.connect/3`设定的参数非常直观。`:binary`要求socket从TCP server中接收的消息以binary的格式接收而不是Erlang默认的charlist格式：在Elixir中这可能是我们想要的，而且可能是最高效的选择。`active: false`告诉socket永远不要把TCP message转换成发送给GenServer的Erlang message；我们将用`:gen_tcp.recv/2`函数来显式的接收tcp消息。我们这样做是为了我们的GenServer不被汹涌而来的tcp消息淹没：我们只在我们想要的时候去接收并处理它们。

#### 发送消息
现在我们已经有了一个连接上Redis服务的GenServer了，现在让我们给Redis发送一些指令。

##### RESP PROTOCL
这里需要简单提一下Redis的二进制协议，RESP：这是Redis用于编解码它的Requst/Reply的协议，[协议的细节](https://redis.io/topics/protocol)简单明了，如果你想了解更多，我建议你看看。为了这篇文章的中心目标，我们假设我们有了RESP的完全实现：它提供了encode/decode两个函数：
- `Redis.RESP.encode/1`: 将list编码成redis command，例如:
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

##### `:gen_tcp.send/2`
我们在文章开头提到过，我们利用`:gen_tcp.send/2`来向tcp连接发送消息。我们的Redis模块将提供单独一个函数来向Redis Server发送命令：`Redis.command/2`。具体实现也很直观：
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
长话短说：`:gen_tcp.recv/2`函数是阻塞的。

这段代码能顺利工作的前提是这个GenServer只被单个Elixir进程调用。当一个进程想发送命令给Redis Server的时候会发生如下事件：
1. Elixir进程调用GenServer的`command/2`命令，然后进程阻塞的等待结果
2. GenServer向Redis Server发送指令然后阻塞在`:gen_tcp.recv/2`上
3. Redis Server回复结果
4. GenServer回应调用进程

你能看出问题出在哪里了吗？GenServer在等待Redis Server回复的过程中是阻塞的。当然在单个进程的情况下这样是没问题的，但当多个进程同时想通过GenServer跟Redis Server做交互的时候情况就会变得很糟糕。幸好，我们可以做一个更好的实现。

#### 使用队列
你可能知道这样一个事实，GenServer的handle_call/3函数可以不用立即返回结果，它可以先返回一个`{:noreply, state}`作为结果，然后通过`GenServer.reply/2`函数返回真实的结果给请求进程。

在客户端请求然后阻塞的等待结果的同时GenServer继续工作直到它有了对这个客户端的回复， 这样一种方法正式我们所需要的。

为了执行我们这一策略，我们需要摆脱`:gen_tcp.recv/2`函数，转而用Erlang Message的形式来接收TCP message。我们可以在连接Redis服务的时候将socket参数中的`active: false`转换成`active: true`，当active被设置为true的时候，所有tcp socket接收的消息都会转换成`{:tcp, socket, message}`形式的Erlang Message发送给GenServer。

这些事情将会发生：

1. Elixir进程在GenServer中调用`command/2`，然后阻塞自己等待结果
2. GenServer将命令发向Redis Server然后返回`{:noreply, state}`，所以它自身不会被阻塞
3. Redis Server回复一条tcp message给GenServer，GenServer以`{:tcp, socket, message}`的形式接收到
4. GenServer在`handle_info/2`函数中处理这条消息，并回应调用的Elixir进程

不难看出，从GenServer发出命令给Redis Server到它接收到Redis Server的回应这段时间内，GenServer是非阻塞的，它还能继续发送其他的命令给GenServer，这很棒！

剩下需要解决的问题就是，GenServer怎样回执给正确的调用进程：当GenServer接收到一条`{:tcp, ....}`的消息时，它怎么知道`GenServer.reply/2`函数该发给谁呢？ 我们知道Redis是严格按照fifo的顺序来应答的，我们可以利用一个简单的队列来把请求的进程存储起来。我们将在GenServer的state中维护一个队列，当进程请求的时候入队，当有应答到来的时候出队。

```
defmodule Redis do
  @initial_state %{socket: nil, queue: :queue.new()}
  # ...as before...

  def handle_call({:command, cmd}, from, %{queue: queue} = state) do
    # We send the command...
    :ok = :gen_tcp.send(state.socket, Redis.RESP.encode(cmd))

    # ...enqueue the client...
    state = %{state | queue: :queue.in(from, queue)}

    # ...and we don't reply right away.
    {:noreply, state}
  end

  def handle_info({:tcp, socket, msg}, %{socket: socket} = state) do
    # We dequeue the next client:
    {{:value, client}, new_queue} = :queue.out(state.queue)

    # We can finally reply to the right client.
    GenServer.reply(client, Redis.RESP.decode(msg))

    {:noreply, %{state | queue: new_queue}}}
  end
end
```

#### 按需求收取消息
在上面的篇幅中，为了能够以Erlang Message的形式接收TCP消息，我们从一个`active: false`的socket转移到了`active: true`的socket。它能正常运行，但在一种情况下会出现问题：当TCP服务发送大量数据给GenServer的时候，因为Erlang本身并没有对消息接收的队列大小做限制，这样很容易造成GenServer的消息雪崩；这也是我们最开始选择`active: false`的原因。为了解决这个问题，我们可以将`active: true`改成更保守的`active: once`：这样每次只会有一个tcp消息被转换成Erlang Message，然后socket又回到了`active: false`的状态。我们可以重新设置`active: once`来接收下一条消息，如此循环。我们每次只转换一条TCP消息为Erlang Message，这样可以保证我们能够处理它们。

我们只要记得在接收一条`{:tcp, ...}`的消息的时候重新激活Socket即可，我们可以利用`:inet:setopt/2`函数来实现。
```
defmodule Redis do
  # ...as before...

  def handle_info({:tcp, socket, msg}, %{socket: socket} = state) do
    # Allow the socket to send us the next message.
    :inet.setopts(socket, active: :once)

    # exactly as before
  end
end
```

### 剧情转折
上文描述的模式并不是我想出来的，很令人震惊对吧？我所形容的模式在一票Erlang和Elixir应用中非常常见。这个模式在任何需要连接tcp服务的场合(或者类似的场合)都表现的十分良好，它经常被用在数据库驱动，这也是我为啥选Redis来做例子的理由。

很多现实世界中的库都使用着我所描述的模式：举个例子，[eredis](https://github.com/wooga/eredis)(Erlang最常用的Redis驱动)就跟我们的例子很类似：看看这部分[代码注释](https://github.com/wooga/eredis/blob/770f828918db710d0c0958c6df63e90a4d341ed7/src/eredis_client.erl#L1-L21)，基本上就是这篇文章的总结。另外一个跟我们的模式大致相似的例子就是[PostgreSQL](https://github.com/ericmj/postgrex)和[MongoDB](https://github.com/ankhers/mongodb)的Elixir驱动。目前我正在为[OrientDB](https://orientdb.com/orientdb/)编写Elixir驱动，也使用的是这个模式。所以这个肯定是可行的。


### TCP连接处理的更优解
上文中我们愉快的忽略了一个令人烦躁的问题 -- 错误处理！

我们将继续愉快的忽略一系列可能发生的错误，例如，消息到来的时候遇到空队列(它会报一个`{{:value, val}, new_queue}`的模式匹配错误)，或是接收到不完整的TCP消息。但是在TCP连接中可能发生的一系列问题例如断线和超时这些我们是可以尝试解决的。

我们可以自己手动的来处理这些异常，幸运的是，Elixir的核心开发者*James Fish*已经在他的类库[connection](https://github.com/fishcakez/connection)中做完了大部分工作。这个类库十分年轻，它已经被用在上文提到的[MongoDB驱动](https://github.com/ankhers/mongodb)和[OrientDB驱动](https://orientdb.com/orientdb/)之中了。

#### 使用Connection来处理连接
这个库协议定义了一个名为`connection`的协议：这个协议所规定的API是GenServer协议的一个超集，所以它易于理解也容易整合进现有的项目。

这篇[文档](https://hexdocs.pm/connection/Connection.html)详细的解释了`Connection`协议，这个库的主旨是实现一个连接着另一端且能做断线处理的进程。为了实现这一目标，`Connection`协议定义了两个附加函数并且修改了部分GenServer的返回值。

我们这里只研究部分`Connection`的函数，如果你想了解更多细节，请阅读文档。

#### 初始化连接
我们的`Redis.init/1`回调函数实现了连接Redis服务的行为，阻塞了调用`Redis.start_link/0`函数的进程直到回调函数返回。如果我们不希望GenServer在连接上Redis服务之前做其他事情的话是没太大问题的。但是我们的`start_link/0`函数可能是被监控树所调用，或者是被专门来启动GenServer的进程所调用：在这种情况下，我们希望`start_link/0`函数尽快的返回`{:ok, pid}`的结果，然后在后台来完成连接的动作。我们也希望GenServer能用队列缓存住建立连接期间的请求。这个协议能够使进程非阻塞的启动GenServer，但是会阻塞后续的请求直到GenServer连接上Redis。
	
有了`Connection`我们可以完全做到这一点。`init/1`回调函数返回`{:connect, info, state}`而非`{:ok, state}`迫使`start_link/0`立即返回`{:ok, pid}`，同时调用了`connect/2`的GenServer回调阻塞GenServer接收其他的请求直到连接完成。`{:connect, info, state}`中的`info`应该包含我们建立连接的所有信息，这些信息我们并不想放在GenServer的state中保存。

我们把代码做点改进：
```
defmodule Redis do
  use Connection
  @initial_state %{socket: nil}

  def start_link do
    # We need Connection.start_link/2 now,
    # not GenServer.start_link/2
    Connection.start_link(__MODULE__, @initial_state)
  end

  def init(state) do
    # We use `nil` as we don't need any additional info
    # to connect
    {:connect, nil, state}
  end

  def connect(_info, state) do
    opts = [:binary, active: :once]
    {:ok, socket} = :gen_tcp.connect('localhost', 6379, opts)
    {:ok, %{state | socket: socket}}
  end
end
```

这对我们之前的实现来说是个巨大改进，但是`Connection`库还可以做的更好。



----
原文链接: [Handling TCP connections in Elixir](https://andrealeopardi.com/posts/handling-tcp-connections-in-elixir/)
