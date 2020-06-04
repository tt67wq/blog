## [译] Elixir Telemetry: 采集与汇总 -- Samuel Mullen
--------
> 没有上下文的发言等同废话 -- D. A. Carson


如果给你一个只有一个点的坐标图让你分析信息和趋势，你一定认为我疯了。面对一个只有单个点的图，没人能分析出任何有效信息。话虽如此，我们还是一直在这样做，我们经常在对一个没有上下文的偶发事件强行推断其意义。

![measurement](https://raw.githubusercontent.com/tt67wq/blog/master/images/measurement.png)

在看了朋友发的微博之后，我们是否都在羡慕朋友的生活比自己更加多姿多彩？想想最近的股票市场，在我写这篇文章的时候，市场似乎陷入了衰退，因此，有多少人急切的把钱从股市中取出，担心事情变得更加糟糕？

如果我们回头一步从多个时间点来观察汇总这些信息，我们会更加远视和成熟。毕竟，人们不太会在社交媒体上分享自己的失败和恐惧，至少不是真诚的，至于股市，它总是在衰退，牛市和熊市之间周期循环。

在我的上篇文章[The “How”s, “What”s, and “Why”s of Elixir Telemetry](https://samuelmullen.com/articles/the-hows-whats-and-whys-of-elixir-telemetry/)中，我们讨论了系统监控的价值，怎样使用[Telemetry](https://github.com/beam-telemetry/telemetry)以及采样错误的害处。然而，你可能还在纠结怎样处理采集到的数据。



原文链接: [elixir-telemetry-metrics-and-reporters](https://samuelmullen.com/articles/elixir-telemetry-metrics-and-reporters/)
