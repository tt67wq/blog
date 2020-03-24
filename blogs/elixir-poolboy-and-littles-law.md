## [译] Elixir, Poolboy, 和利特尔法则

------

Elixir由于其简洁的语法和出色的表现力，它常常被拿来和[Ruby](http://www.ruby-lang.org/zh_cn/)语言做比较。这也很容易理解：函数定义，`do/end`块，感叹词和疑问词的命名，甚至函数命名的风格都来自Ruby或是收到其风格的影响。但是仅凭语法类似就说Elixir跟Ruby很相似就如同说我跟Steve Jobs很像差不多（我也喜欢穿黑领毛衣）。实际上我并不像，而且我也不想像他。

事实上来说，与Ruby相比，Elixir和[Erlang](https://erlang.org/)有更多的相似性。尽管它们的语法相差甚远，和大多数事物一样，都是表面之下的东西更为关键。在这个例子中，说的就是[Beam虚拟机](https://en.wikipedia.org/wiki/BEAM_(Erlang_virtual_machine))，也就是说Elixir跟Erlang一样，是一门并发编程语言。

因为运行在Beam虚拟机上的原因，Elixir可以同时处理成千上万，甚至百万个进程。不幸的是，并不是每个与其交互的系统都能做到这一点。数据库、云服务、以及一些内部和外部的API通常都限制了我们访问它们的次数和频率。所以，即使Elixir应用能够很好的处理海量并发，我们有时也必须给应用加上限制以适应周遭环境。


原文链接: [Elixir, Poolboy, and Little's Law](https://samuelmullen.com/articles/elixir-poolboy-and-littles-law/?utm_campaign=elixir_radar_230&utm_medium=email&utm_source=RD+Station)
