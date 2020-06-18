## [译] Elixir Telemetry: 采集与汇总 -- Samuel Mullen

--------
> 没有上下文的发言等同废话 -- D. A. Carson


如果给你一个只有一个点的坐标图让你分析信息和趋势，你一定认为我疯了。面对一个只有单个点的图，没人能分析出任何有效信息。话虽如此，我们还是一直在这样做，我们经常在对一个没有上下文的偶发事件强行推断其意义。

![measurement](https://raw.githubusercontent.com/tt67wq/blog/master/images/measurement.png)

在看了朋友发的微博之后，我们是否都在羡慕朋友的生活比自己更加多姿多彩？想想最近的股票市场，在我写这篇文章的时候，市场似乎陷入了衰退，因此，有多少人急切的把钱从股市中取出，担心事情变得更加糟糕？

如果我们回头一步从多个时间点来观察汇总这些信息，我们会更加远视和成熟。毕竟，人们不太会在社交媒体上分享自己的失败和恐惧，至少不是真诚的，至于股市，它总是在衰退，牛市和熊市之间周期循环。

在我的上篇文章[The “How”s, “What”s, and “Why”s of Elixir Telemetry](https://samuelmullen.com/articles/the-hows-whats-and-whys-of-elixir-telemetry/)中，我们讨论了系统监控的价值，怎样使用[Telemetry](https://github.com/beam-telemetry/telemetry)以及度量错误的害处。然而，你可能还在纠结怎样处理采集到的数据。

监控抓取数据只是这个方程式的一半。这篇文章中，我们将看看measurement和metrics的区别，怎样定一个好的度量，度量时需要注意的东西以及如何使用Elixir的库[Telemetry](https://github.com/beam-telemetry/telemetry_metrics)来度量。


### 啥是Metric？

"Metric"是一个很难定义的词语，而且经常会跟"measurement"搞混，然而Measurement是一些事物的特定单位值(例如长度，时长，体积等)，metric是用来跟踪和评测这些测量值（例如总和，平均值，分布之类）。

就像书[Lean Analytics](https://www.goodreads.com/book/show/16033602-lean-analytics)中解释的那样，有四条准则来评价何为好的度量：

#### 好的度量是有对照的
可能这一点很明显，度量本身就有做参照的意思，但是经常会错误的把两个不相关的度量拿来比较。Benchmarks就是一个绝佳的对照例子，因为你是在对比相似的事物例如对比不同的库或者是对比库的不同版本。而一个糟糕的对比例子就是比较两个程序员的代码行数：谁写的多不代表谁写的有价值。

#### 好的度量是易于理解的
程序员能够理解一些专业术语例如"代码复杂度"、"技术债务"或是"重构"，但是大部分人不懂。复杂度是可量化的，但是像技术债务这种就比较难量化，它必须和某种理想版本的软件做比较才能得出。当选择要追踪的测量时，尽量选择那些容易理解的。"如果人们不能记住和讨论这些度量，那么就很难从数据的变化转变成文化的变化。"

#### 好的度量应该是比例和速率
除非你在追踪的测量是按某种标准分组的，你所做的不过是收集数字。除此之外，我们需要收集与时间或是系统资源相关的度量。常用的几个比例的例子有吞吐(每秒的事务数量)和带宽(比特数与资源的比值)。"比例往往是最好的度量"有如下三个理由：

- 比例更容易起作用；
- 比例有内在的对照属性；
- 比例擅长比较两个有对立或者有内在矛盾的因素。

#### 好的度量能改变你的行为

### Telemetry.Metrics
当我开始探索`Telemetry.Metrics`这个库时，我错误的以为它会帮我堆度量数据。我错误的解读了README文件的第一句话："Telemetry.Metrics基于:telemetry事件提供了定义度量的标准接口"。"Telemetry.Metrics"并没有在提供不同的度量类型和提供时序测量的单元转换之外做更多的事情。这也说通了我的疑问："Telemetry怎么会知道我们要怎样处理这些数据？"。

`Telemetry.Metrics`目前提供了四种度量类型：

- `Telemetry.Metrics.Counter`：用于某个事件的持续计数。
- `Telemetry.Metrics.Sum`: 用于计算某个测量值的总和。
- `Telemetry.Metrics.LastValue`: 用这个值来维护最后一次事件发生的度量。
- `Telemetry.Metrics.Summary`: 用于计算测量的统计值例如，最大值/最小值，平均值，百分比之类。
- `Telemetry.Metrics.Distribution`: 用于将测量值分组到不同的分片中。

为了追踪一个或多个度量，你需要一个汇报者。重申一下，防止你跟我一样粗心：

```
度量本身是不够的，它们只提供了我们希望得到的规范的最终结果。订阅事件和构建度量是汇报者的工作。这是这个库至关重要的设计理念 -- 库本身不帮你收集数据，你需要依赖第三方的汇报者来完成这个操作，某种意义上来说，它才是参与构建监控系统中最有意义的一步。
```



原文链接: [elixir-telemetry-metrics-and-reporters](https://samuelmullen.com/articles/elixir-telemetry-metrics-and-reporters/)
