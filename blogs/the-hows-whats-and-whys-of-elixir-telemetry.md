## [译] Elixir Telemetry: 采集与汇总 -- Samuel Mullen
-----
"得监控者得管理"引用自[wrongly attributed to Peter Drucker ](http://billhennessy.com/simple-strategies/2015/09/09/i-wish-drucker-never-said-it)--这个故事告诉我们，一旦我们对某件事务进行监控，我们就可以针对被监控对象作出决策以及判断接下来的发展方向。注意，这只是一个部分引述，完整的引述是："得监控者得管理 -- 即使监控对象毫无意义，即使它对目前组织目的相违背。"某种意义上来说，如果你监控到错误的数据，你就会做出错误决定。

直到最近，Erlang和Elixir的开发者一谈到对自己应用和进程进行监控采集，基本都是自己造轮子。在2018年，[arkgil](https://github.com/arkgil)发布了[Telemetry](https://github.com/beam-telemetry/telemetry)，给了开发者一个用于指标和设备的动态分发库。它为从监控上采集到的指标提供了一套标准的接口。

我们将详细的介绍如何将其用于一个实时的小容器中，你会将它作为一个被监控进程贴在你的项目中，设置一些命名事件用于匹配，然后执行这些事件。首先，我们先讨论下为何需要监控我们的进程。

### 监控的价值

在项目的初始阶段，任何小的细节都应该被监控，随着项目体积膨胀，在你审视项目的时候不难发现有很多"这里到底TMD发生了什么"的场合是需要监控的，监控的必要性还有多个理由。

第一个理由就是能够让我们这些系统的开发者快速的发现和评估系统的瓶颈和问题。这些问题包罗万象，从网络延迟到数据库慢查询，也可以简单用于计算GenServer或者某个单独函数的执行效率。

当然如果你发现了某个问题，想要知道你作出的修改是否真的有所提升。抓取系统的运行数据可以让你对比原有逻辑和修改后的性能差距。如果你不知道靶子在哪，那你怎么可能知道是否击中它了？

牢记这一点，第三个做运行时数据采样的理由是它能让你抢在客户之前发现问题。这一点可以让客户更满意，也能避免和老板多余的尬聊。

最后一点，我们已经讨论过了，对系统进行采样可以帮助你做下一步的决策。如果你在[gigalixir](https://www.gigalixir.com/)上看到你的应用内存占用率达到了85%，那么现在就是时候做系统升级了。相似的，如果你发现系统中某些功能的使用情况明显高于其他，那么你就知道了后续努力的方向，甚至可以裁剪掉某些功能。

既然我们在讨论如何正确决策...

### 谎言，该死的谎言，错误的数据！

如果你从事Web开发很久，你一定听人们说过网页浏览数的概念。网页浏览数指的是你的网站被浏览的数量，这意味着什么呢？是否说明公司将挣了多的钱？还是说明了市场工作颇有成效？如果是的话，是哪方面的成效呢？它与几天、几周、几个月之前比较如何？这其中的转化关系是怎样的？简单的说，就是这些数据告诉你哪些信息？

打点数据本身只是数字而已。它需要与其他数据进行关联比较以获得用于决策的信息。例如网页访问量、内存使用率、错误统计、甚至是这些信息的自身排序都被称作"垃圾埋点"。"垃圾埋点看上去挺好，但是它不会改变你的行为模式。而有效埋点将改变你的行为，帮助你选择行动的方向。"([Lean Analytics](https://www.goodreads.com/book/show/16033602-lean-analytics))

监控数字要比仅仅记录数字更重要；我们需要一个目标。"每当你看着打点数据的时候，问问自己：「基于这些信息我该做些什么？」"，如果你答不出来，那么你或许没必要太在意这些打点数据。

### Telemetry入门

先无视警告和劝退，我们来安装设置Telemetry。在项目中设置Telemetry分四步：1) 安装库；2) 将Telemetry的监控树"贴"进你的项目中；3) 定义好需要抓取的事件；4) "执行"这些事件。

#### 第一步：安装Telemetry

第一步当然是安装Telemetry库。我知道你懂怎么安装Elixir包，但是为了文章的完整性，将以下内容加入到`mix.exs`文件中的`deps/0`函数中。

```
defp deps() do
  [
    {:telemetry, "~> 0.4.0"}
  ]
end
```
*注意： [当前版本](https://hex.pm/packages/telemetry)可能跟你读这篇文章的时候有不一样了*

#### 第二步：贴上Telemetry监控树

一旦安装完成，下一步就是要启动Telemetry好让它开始干活。至少有两种方法去做这件事：1) 将Telemetry的裸代码加入`application.ex`文件中；2) 将逻辑包装进函数，在`application.ex`中调用它。

##### 基础的Telemetry侵入

这是在项目中启动Telemetry的最简单方法。在`application.ex`文件中，在启动函数之前加入这段代码：

```
defmodule MyApp.Application do
  use Application

  def start(_type, _args) do
    children = [
      ...
    ]

    # Start the Telemetry supervisor
    :telemetry.attach("handler-id", [:event_name], &handle_event/4, nil)

    opts = [strategy: :one_for_one, name: MyApp.Supervisor]
    Supervisor.start_link(children, opts)
  end

  ...
end
```
这里要注意几点：

- `attach/4`函数只允许你抓取某一个事件。如果想抓取更多，请用`attach_many/4`函数
- "handler-id"是一个唯一标识，"handler-id"必须唯一，如果有一个同名的handler存在，那么会返回一个`{error, already_exists}`元组
- `[:event_name]`是一个用于匹配事件和启动回调函数的原子列表
- `handle_event/4`就是回调函数
- 最后一个参数是"配置"参数

##### 包装骇入逻辑

用不相干的逻辑污染你的Application模块不是一个好主意。相反，通用做法是将"贴入"函数提取到一个"插装器"模块中，然后在appliction模块中调用它。插装器模块会包含相干的事件句柄。

```
defmodule MyApp.Instrumenter do
  def setup do
    events = [
      [:web, :request, :start],
      [:web, :request, :success],
      [:web, :request, :failure],
    ]

    :telemetry.attach_many("myapp-instrumenter", events, &handle_event/4, nil)
  end

  def handle_event([:web, :request, :start], measurements, metadata, _config) do
    ...
  end

  def handle_event([:web, :request, :success], measurements, metadata, _config) do
    ...
  end

  def handle_event([:web, :request, :failure], measurements, metadata, _config) do
    ...
  end
end
```

然后，在你的`Application`模块中，使用`MyApp.Instrumenter.setup()`替代`:telemetry.attach/4`函数。

```
defmodule MyApp.Application do
  use Application

  def start(_type, _args) do
    children = [
      ...
    ]

    MyApp.Instrumenter.setup()

    opts = [strategy: :one_for_one, name: MyApp.Supervisor]
    Supervisor.start_link(children, opts)
  end

  ...
end
```

#### 第三步：定义事件

在第二步中，我们看到了基本的事件定义方法。我们没必要去命名函数为`handle_event/4`，但是这好像是约定做法。这个函数也接收四个参数：

- 事件名称：用于匹配事件的原子列表。例如：

```
events = [
  [:my_app, :repo_name, :query],     # to capture DB queries
  [:my_app, :web_request, :success], # to capture HTTP 200s
  [:my_app, :web_request, :failure], # to capture web errors
]
```

- 度量：一些你感兴趣的度量用的数据结构。例如：

```
%{
  decode_time: 6000,
  query_time: 673000,
  queue_time: 39000,
  total_time: 718000
}
```

- 元数据：具体某个Telemetry事件的信息。它可能是个`%Plug.Conn{}`对象，可能是个Ecto请求，一个栈追踪，或任何其他有用的信息。

抓取数据是简单的，困难的部分在于怎样处理你抓来的数据。一个简单的选择是打印到日志中。

```
def handle_event([:web, :request, :start], measurements, metadata, _config) do
    Logger.info inspect(measurements)
    Logger.info inspect(metadata)
end
```

另外一个选择就是存在ETS表中。这个在你需要处理大量数据又不用长期持久化的情况下尤其有用。一个相似的选择就是使用[telemetry_metrics](https://github.com/beam-telemetry/telemetry_metrics)库。最后，如果将数据存在第三方存储中会更有意义。例如[DataDog](https://www.datadoghq.com/), [NewRelic](https://newrelic.com/), [Scout](https://scoutapm.com)。


#### 第四步：事件执行

最后，在你的项目已经做好准备之后，剩下的事情就只剩发送打点数据了。你可以使用`execute/2`或`execute/3`函数来做到这一点。

```
:telemetry.execute(
  [:my_app, :request, :success],
  %{time_in_milliseconds: 42},
  %{
    request_path: conn.request_path,
    status_code: conn.status
  }
)
```

当上述函数被执行的时候，匹配到`[:my_app, :request, :success]`的事件句柄会接收第二个参数作为打点，接收第三个参数作为元数据。你可以忽略元数据，如果你认为它不重要的话。


#### 不用重复发明轮子

现在似乎是一个很诱人的时间点去花时间构建你的事件打点，在你的代码中到处加上`execute`函数，但是，你要先确定你没有在重复劳动。多个Elixir库已经支持了Telemetry，可以减轻你的负担。让我们来看看两个常用的。

##### Plug.Telemetry

[Plug](https://github.com/elixir-plug/plug)的v1.8版本已经有了Telemetry的支持，只要在项目依赖中加入Telemtry，你将自动的载入它预设的事件。

当Telemetry安装好之后，你需要将`Plug.Telemetry`的插头加入相关的流水线中让其开始发送事件。举个例子：

```
defmodule MyApp.Router do
  use MyAppWeb, :router

  pipeline :browser do
    ...
    plug Plug.Telemetry, event_prefix: [:my_app, :plug]
    ...
  end

  ...
end
```

通过流水线中的这是行代码，所有使用了这个流水线的plug或controller都将触发两个事件：`:start`和`:stop`。为了收集这两个事件，你需要将它们加入到你的"插装器"模块中。

```
events = [
  ...
  [:my_app, :plug, :start], # Captures the time the request began
  [:my_app, :plug, :stop],  # Captures the duration the request took
  ...
]
```

`:start`事件在事件发生瞬间抓取了一个度量：`:time`。`:stop`事件却抓取了stop和start事件发生的时间差。在任何场景下-至少是在Mac下-，时间的单位是纳秒。你可以利用`System.convert_time_unit/3`函数将其转换成更容易管理的单位。你该注意到，这两个事件的`metadata`值都是请求的`%Plug.Conn{}`值。

```
System.convert_time_unit(duration, :nano_seconds, :milli_seconds)
```

最后一件事就是定义你的事件句柄。这就是你想干的事情：

```
def handle_event([:my_app, :plug, :start], %{time: time}, metadata, _config) do
  time = System.convert_time_unit(time, :nano_seconds, :milli_seconds)

  # Logic to handle :start event
end

def handle_event([:my_app, :plug, :stop], %{duration: duration}, metadata, _config) do
  duration = System.convert_time_unit(duration, :nano_seconds, :milli_seconds)

  # Logic to handle :stop event
end
```


原文链接：[The “How”s, “What”s, and “Why”s of Elixir Telemetry](https://samuelmullen.com/articles/the-hows-whats-and-whys-of-elixir-telemetry/)
