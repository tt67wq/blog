# 用Elixir写个简单的内网穿透

内网穿透是一个在开发工作中经常需要使用的工具，先看看这个工具的定义：

> 内网穿透即NAT穿透，网络连接时术语，计算机是局域网内时，外网与内网的计算机节点需要连接通信，有时就会出现不支持内网穿透。就是说映射端口, 能让外网的电脑找到处于内网的电脑


简而言之，就是利用一个固定的对外ip来访问内网的机器。
现有的内网穿透的方案有很多，例如[花生壳](https://hsk.oray.com/)，[frp](https://github.com/fatedier/frp)，[ngrok](https://github.com/inconshreveable/ngrok)，[shootback](https://github.com/aploium/shootback)等等，如果你想要稳定高性能的穿透产品，建议还是付费用花生壳这种，如果是用于测试和开发，那么一些开源的产品也可以考虑。


本篇文章就简单介绍下，如何用Elixir语言编写一个简单的内网穿透工具。

-------
## WHY

*问*： 市面上已经有了很多功能强大的穿透工具，为什么还要重复造轮子？

*答*： 1. 因为有趣; 2. 市面上的解决方案大多功能大而全，而这个轮子追求小而美。

*问*： 为什么选择Elixir语言编写

*答*： 1. Elixir号称是socket编程的最佳选择，socket编程体验nice；2. Elixir是erlang虚拟机上的语言，面向并发编程，免去了很多多路复用的实现细节。

------

## PREPARE

理解本篇文章需要以下预备知识:

1. 计算机网络基础；
2. Elixir基础或Erlang基础；

-------
## HOW

### STEP 1: 建立项目骨架

先在脑海中理清软件的物理形态，内网穿透是个典型的CS架构，那么一定有客户端和服务端：

大致的物理形态如图：

![structure](https://raw.githubusercontent.com/tt67wq/blog/master/images/structure.png)


- 客户端部署在内网中，主要工作是连接内网应用，并将内网应用的流量转发至服务端，同时需要承接服务端发来的流量，转发至内网应用；
- 服务端部署在一台可网络直接触达的机器上，既要承接客户端发来的流量也要承接外部访问的流量，将外部流量转发至客户端，同时要将客户端的流量转发给外部连接；
- 客户端与服务端之间维持着tcp连接，如果多个穿透应用想要复用客户端与服务端的连接的话，就需要设计好协议来区分单个连接中的流量归属；


那么先建立两个项目：

```
mix new tunnel_ex --umbrella # 项目顶层，设计成一个umbrella项目，不这样也行，两端都弄成独立app
cd tunnel_ex/apps
mix new client --sup # 客户端
mix new server --sup # 服务端
mix new commmon # 通用组件，utils，helpers之类的东西
```

目前项目看起来是这样：

```
.
├── apps
│   ├── client
│   │   ├── config
│   │   ├── lib
│   │   ├── mix.exs
│   │   ├── mix.lock
│   │   ├── README.md
│   │   └── test
│   ├── common
│   │   ├── lib
│   │   ├── mix.exs
│   │   ├── README.md
│   │   └── test
│   └── server
│       ├── config
│       ├── lib
│       ├── mix.exs
│       ├── mix.lock
│       ├── README.md
│       └── test
├── config
│   └── config.exs
├── LICENSE
├── mix.exs
├── mix.lock
└── README.md
```

当代码编制完毕后，只需要在client和server目录下分别编译打包即可。


### STEP 2: 协议部分
在CS编程的实践中，最最重要的就是协议的设计，好的协议可以节约资源提升性能。当然这个项目的协议设计不用太严谨，毕竟只是个实验性质的项目。
首先我们思考协议的目标：

1. 将外部流量在服务端的行为，在客户端到内部应用上重放。例如：外部与服务端监听的某个端口建立了tcp连接，那么客户端也要马上与内部相应的服务建立tcp连接。外部向服务端端口输送的流量，客户端也要原封不动的输送到内部应用；
2. 由于需要复用客户端与服务端的连接，协议要能区分不同穿透组合的流量。例如上图中，外部8080端口接收的流量只能转发至内部80口，不能转发至81口或82口；


为了完成上述的目标，我设计了一个简单的协议：

#### *1. 客户端与服务端建立连接*

我们设计的穿透可以是一个服务端对应多个客户端，所以客户端在发起连接的时候理应上报自己的相关信息，我们可以如下设计：

在客户端发起连接的时候，发送自己的ip地址(这个ip地址不一定是真实ip，只要不与其他客户端ip地址碰撞即可，其实这里就是一个客户端id的作用，用ip地址还能有点物理意义)给服务端，服务端将存储一个ip地址对应socket的映射关系，格式如下：

```
| 0x09 | 0x01 | ip0 | ip1 | ip2 | ip3 |
```

前面固定2个字节为<<9, 1>>，后面跟着4个字节的ip地址。只要服务端接收到这个格式的包，自然就可以知道这是一个客户端ip地址上报的行为， 此时server会做一个回执给客户端，表示自己已经收到了ip上报，回执格式如下：


```
| 0x09 | 0x02 |
```

固定为<<9, 2>>，如果客户端一段时间内没有收到回执，说明哪里出问题了，应当重试上报，如果多次重试没成功，说明server应该是挂了。这一部分的异常处理情况复杂，第一个版本我就没考虑这些，编程应当先关注主流程。


#### *2. 外部与服务端建立tcp连接*

当外部有流量与服务端监听的某个端口建立了tcp连接，此时服务端应当通知客户端这一事件，我们做如下设计：

```
| 0x09 | 0x03 | key::16 | client_port::16 |
```

前面固定2字节<<9, 3>>，后面会跟上两字节的key和一个2字节的端口号。其中，key用于表示某个外部连接的id，client_port表示这个包要发往内部的哪个端口。当外部与服务端建立了连接，我们会为每个tcp连接，分配一个2字节的key，并存储key到连接的映射关系。再转发至客户端的时候，会带上这个key，此时客户端会根据client_port与内部应用建立连接，并存储key到内部连接的映射关系。这样我们就可以根据key来区分服务端与客户端通信包中的归属。

特别需要注意的是，外部与服务端的交互是没法感知客户端这边的情况，很有可能，外部完成tcp连接后，马上开始发送流量，但是从服务端发往客户端的网络包未必是按照顺序来的，所以在客户端成功与内部应用建立tcp连接之前，服务端最好将外部流量缓存，等待客户端回执一个连接建立成功的信号，再将缓存中的流量按顺序发给客户端。为了简单起见，将回执做如下设计：

```
| 0x09 | 0x03 | key::16 |
```


#### *3. 通信阶段*

当服务端与客户端都建立了tcp连接，接下来就是发送应用层的数据流，我们做如下设计：

```
| key::16 | real packet |  
```

很容易理解，根据key找到对应的内部连接，然后将真正的流量转发过去。

#### *4. 连接关闭*

当外部与服务端的连接关闭，服务端也应该通知客户端关闭内部连接。格式如下：

```
| 0x09 | 0x04 | key :: 16 |
```

前面是固定的<<9, 4>>开头，后面是key标明哪个连接需要被关闭。


### STEP 3: TALK IS CHEAP, SHOW ME THE CODE!

接下来，我们按照协议内容开始编码。

#### *代码骨架*

客户端的部分比较简单，我们先着手写这部分。首先先构思客户端的形态，客户端需要主动连接两方，既要连接内网应用，又要连接服务端，那么客户端应当有两个client组成：

- 对内部应用的client命名为worker，这一进程应该是动态创建的；
- 对服务端的我们命名为selector(叫selector是因为服务端发来的流量是复用tcp连接的，这一层的代码需要做一些选择分发的工作)；

那么client的结构应该如下：

```
├── client
│   ├── application.ex  # 相当于main
│   ├── selector.ex     # 承接server端流量
│   ├── socket_store.ex # 存储端口=>socket的映射关系
│   ├── utils.ex        # 工具函数
│   └── worker.ex       # 承接本地服务流量
```

至于服务端要考虑的东西更多，服务端会承担以下工作：

- 监听客户端连接；
- 监听外部连接；
- 将外部流量转发至客户端；
- 将客户端发来的流量转发回外部。

可见，服务端里面会有两类tcp server，那么结构可以如下设计：

```
├── server
│   ├── application.ex        # 相当于main
│   ├── external_listener.ex  # 外部监听入口
│   ├── external_worker.ex    # 外部socket的代理进程
│   ├── internal_listener.ex  # 客户端的监听进程
│   ├── internal_worker.ex    # 客户端socket的代理进程
│   ├── socket_store.ex       # 存储端口=>socket映射关系以及key=>socket映射关系
│   ├── typespec.ex           # 类型枚举
│   └── utils.ex              # 工具函数
```

这个层级结构设计的相当粗糙，可以更加精细，当然，第一版本先着眼主要矛盾。

#### *客户端服务端建立连接部分*

在Erlang虚拟机上，可以将一个socket的代理权交给一个Erlang的GenServer进程，让GenServer来全权代理socket的一些事件反应(果然，Erlang才是最好的oo模型)，在这个项目中，所有的socket我们都用GenServer进程来代理，有点类似于其他oo语言的class实例。

我们先着眼于客户端selector，首先这是一个客户端进程，会主动连接服务端的端口。那么我们先拉一个GenServer起来。

```
defmodule Client.Selector do
  def start_link(opts) do
    {name, opts} = Keyword.pop(opts, :name, __MODULE__)
    GenServer.start_link(__MODULE__, opts, name: name)
  end

  def init(_opt) do
    send(self(), :connect) # 进程启动后给自己发送一个连接服务端的命令
    {:ok, %{socket: nil}}
  end

  def handle_info(:connect, state) do
    {host, port} = server_cfg() # 读取配置文件中服务端的地址和端口信息
    Logger.info("Connecting to #{host}:#{port}")

    with {:ok, ip} <- host |> to_charlist |> :inet.parse_address(), # 地址解析
         {:ok, sock} <- :gen_tcp.connect(ip, port, [:binary, active: true, packet: 2]), # 建立连接
         localhost <- client_cfg(), # 获取配置本地的ip地址
         {:ok, {ip0, ip1, ip2, ip3}} <- localhost |> to_charlist |> :inet.parse_address() do
      # handshake
      :gen_tcp.send(sock, <<0x09, 0x01, ip0, ip1, ip2, ip3>>) # ip地址上报
      {:noreply, Map.put(state, :socket, sock)}
    else
      {:error, reason} ->
        Logger.warn("reason -> #{inspect(reason)}")
        Process.send_after(self(), :connect, 1000) # 尝试重连
        {:noreply, state}

      _ ->
        {:stop, :normal, state}
    end
  end
end
```

这部分代码主要就是建立服务端连接，同时按协议上报自己的ip地址。

按照协议，服务端会回执一个包，这里需要做一下应答：

```
def handle_info({:tcp, _socket, <<0x09, 0x02>>}, state) do
    # handshake finished
    Logger.info("handshake finished")
    {:noreply, state}
end
```

在socket代理进程中，发给socket的信息会被转成一个发给erlang微进程的msg，简化了我们的编程模型，免去了自己主动recv再去做相应的event handle。

服务端需要监听客户端的连接请求，并且做出相应回应。

对应的服务端部分代码在如下：

```
defmodule Server.InternalListener do
  @moduledoc """
  内部监听
  """
  require Logger
  use GenServer
  alias Server.{InternalWorker}

    def start_link(opts) do
    {name, opts} = Keyword.pop(opts, :name, __MODULE__)
    GenServer.start_link(__MODULE__, opts, name: name)
  end

  def init(_opts) do
    port = server_port()
    {:ok, acceptor} = :gen_tcp.listen(port, [:binary, active: false, reuseaddr: true, packet: 2])
    send(self(), :accept)

    Logger.info("Accepting connection on port #{port}...")
    {:ok, %{acceptor: acceptor}}
  end

  def handle_info(:accept, %{acceptor: acceptor} = state) do
    {:ok, sock} = :gen_tcp.accept(acceptor)

    # 启动一个进程来代理来自客户端的连接
    {:ok, pid} = GenServer.start_link(InternalWorker, socket: sock)

    # 转交给GenServer来处理socket事件
    :gen_tcp.controlling_process(sock, pid)

    send(self(), :accept)
    {:noreply, state}
  end
end


defmodule Server.InternalWorker do
  @moduledoc """
  内部数据交互进程
  """
  use GenServer
  require Logger

  def start_link(opts) do
    {name, opts} = Keyword.pop(opts, :name, __MODULE__)
    GenServer.start_link(__MODULE__, opts, name: name)
  end

  def init(socket: socket) do
    :inet.setopts(socket, active: true)
    {:ok, %{socket: socket}}
  end

  # 接收到<<9， 1>> 开头表示ip地址上报
  def handle_info({:tcp, socket, <<0x09::8, 0x01::8, ip::32>> = data}, state) do
    Logger.info("internal recv => #{inspect(data)}")
    
    IPSocketStore.add_socket(<<ip::32>>, self()) # 存储ip=>socket进程的映射
    # handshake
    :gen_tcp.send(socket, <<0x09, 0x02>>) # 按照协议回执一个 <<9, 2>>
    {:noreply, Map.put(state, :ip, <<ip::32>>)}
  end
end

```

至此，建立连接握手的部分就完成了。


#### *服务端对外部服务的监听*

服务端除了监听客户端的连接，还需要监听外部的映射端口，例如我们的配置文件格式如下：

```
# 转发配置
nat:
  - name: "server0"
    from: localhost:8080
    to: 192.168.10.101:80

  - name: "server1"
    from: localhost:8081
    to: 192.168.10.101:81
```

我们需要监听8080口和8081口，可以根据配置文件动态创建多个监听进程，具体代码如下：

```
defmodule Server.ExternalListener do
  @moduledoc """
  外部监听
  """

  require Logger
  use GenServer
  alias Server.{ExternalWorker, SocketStore, Utils}

  def start_link(opts) do
    {name, opts} = Keyword.pop(opts, :name, __MODULE__)
    GenServer.start_link(__MODULE__, opts, name: name)
  end

  @doc """
  nat 示例
  %{
    "from"=> "localhost:8080"
    "to"=> "192.168.10.101:80"
  }
  """
  def init(nat: nat) do
    [_, port_str] = nat |> Map.get("from") |> String.split(":")
    port = String.to_integer(port_str)

    # 监听
    {:ok, acceptor} = :gen_tcp.listen(port, [:binary, active: false, reuseaddr: true])
    send(self(), :accept)
    Logger.info("Accepting connection on port #{port}...")

    {:ok, %{acceptor: acceptor, nat: nat, port: port}}
  end

  def handle_info(:accept, %{acceptor: acceptor, port: port} = state) do

    # 建立连接
    {:ok, sock} = :gen_tcp.accept(acceptor)
    Logger.info("new connection established from port #{port}")

    sock_key = Utils.generete_socket_key()

    # 创建一个worker 来处理外部数据
    {:ok, pid} = GenServer.start_link(ExternalWorker, socket: sock, nat: state.nat, key: sock_key)
    :gen_tcp.controlling_process(sock, pid)

    # 注册至 key => socket 仓库
    SocketStore.add_socket(sock_key, pid)

    send(self(), :accept)
    {:noreply, state}
  end
end
```

处理外部流量的Worker在创建后需要立即通知客户端，具体细节如下：


```
defmodule Server.ExternalWorker do
  @moduledoc """
  数据处理进程
  """

  use GenServer
  require Logger
  alias Server.{InternalWorker, SocketStore, IPSocketStore, Typespec}

  def start_link(opts) do
    {name, opts} = Keyword.pop(opts, :name, __MODULE__)
    GenServer.start_link(__MODULE__, opts, name: name)
  end

  def send_message(pid, message), do: GenServer.cast(pid, {:message, message})

  @spec init(socket: Typespec.socket(), nat: map(), key: Typespec.sock_key()) :: {:ok, pid()}
  def init(socket: socket, nat: nat, key: key) do

    # 解析配置文件，获取对应的内网端口号和地址
    [client_ip_raw, client_port] =
      nat
      |> Map.get("to")
      |> String.split(":")

    {:ok, {ip0, ip1, ip2, ip3}} = client_ip_raw |> to_charlist() |> :inet.parse_address()

    # 先设置为被动模式，不接收packet
    :inet.setopts(socket, active: false)
    send(self(), :tcp_connection_req)

    {:ok,
     %{
       socket: socket,
       key: key,
       client_ip: <<ip0, ip1, ip2, ip3>>,
       client_port: String.to_integer(client_port),
       status: 0,
       buffer: :queue.new()
     }}
  end

  def handle_info(:tcp_connection_req, state) do
    Logger.info("send tcp connecntion request")

    # 通知客户端，建立tcp连接
    send_msg(state.client_ip, <<0x09, 0x03, state.key::16, state.client_port::16>>)

    # 将socket设置为主动模式，开始接收流量
    :inet.setopts(state.socket, active: true)

    # 将状态置为 握手中
    {:noreply, Map.put(state, :status, 1)}
  end

  ...
end
```