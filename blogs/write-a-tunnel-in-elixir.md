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

*答*： Elixir号称是socket编程的最佳选择，socket编程体验nice，而且性能不差。

------

## PREPARE

理解本篇文章需要以下预备知识:

1. 计算机网络基础；
2. Elixir基础或Erlang基础；

-------
## HOW

### STEP 1: 建立项目骨架

先在脑海中理清软件的物理形态，内网穿透是个典型的CS架构，那么一定有客户端和服务端：

- 客户端部署在内网中，主要工作是连接内网应用，并将内网应用的流量转发至服务端，同时需要承接服务端发来的流量，转发至内网应用；
- 服务端部署在一台可网络直接触达的机器上，既要承接客户端发来的流量也要承接外部访问的流量，将外部流量转发至客户端，同时要将客户端的流量转发给外部连接;

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


### STEP 2: 客户端部分

客户端的部分比较简单，我们先着手写这部分。首先先构思客户端的形态，客户端需要主动连接两方，既要连接内网应用，又要连接服务端，那么客户端应当有两个client组成：

- 对内部应用的client命名为worker；
- 对服务端的我们命名为selector(叫selector是因为服务端发来的流量是复用tcp连接的，这一层的代码需要做一些选择分发的工作)；

那么client的结构应该如下：

```
├── client
│   ├── application.ex # 相当于main
│   ├── selector.ex    # 承接server端流量
│   ├── utils.ex       # 工具函数
│   └── worker.ex      # 承接本地服务流量
```

