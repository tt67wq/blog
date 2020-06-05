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


原文链接：[The “How”s, “What”s, and “Why”s of Elixir Telemetry](https://samuelmullen.com/articles/the-hows-whats-and-whys-of-elixir-telemetry/)
