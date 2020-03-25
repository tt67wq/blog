## [译] Elixir, Poolboy, 和利特尔法则

------

Elixir由于其简洁的语法和出色的表现力，它常常被拿来和[Ruby](http://www.ruby-lang.org/zh_cn/)语言做比较。这也很容易理解：函数定义，`do/end`块，感叹词和疑问词的命名，甚至函数命名的风格都来自Ruby或是收到其风格的影响。但是仅凭语法类似就说Elixir跟Ruby很相似就如同说我跟Steve Jobs很像差不多（我也喜欢穿黑领毛衣）。实际上我并不像，而且我也不想像他。

事实上来说，与Ruby相比，Elixir和[Erlang](https://erlang.org/)有更多的相似性。尽管它们的语法相差甚远，和大多数事物一样，都是表面之下的东西更为关键。在这个例子中，说的就是[Beam虚拟机](https://en.wikipedia.org/wiki/BEAM_(Erlang_virtual_machine))，也就是说Elixir跟Erlang一样，是一门并发编程语言。

因为运行在Beam虚拟机上的原因，Elixir可以同时处理成千上万，甚至百万个进程。不幸的是，并不是每个与其交互的系统都能做到这一点。数据库、云服务、以及一些内部和外部的API通常都限制了我们访问它们的次数和频率。所以，即使Elixir应用能够很好的处理海量并发，我们有时也必须给应用加上限制以适应周遭环境。

## Worker池

一个简单的限制连接数的办法就是上worker池或[线程池](https://en.wikipedia.org/wiki/Thread_pool)。简言之，一个worker池就是为了限制完成某项特定任务的进程或者线程数量。在大多数编程语言中，使用worker池能*有效降低频繁创建销毁线程带来的性能损失*，但是对Beam虚拟机来说这并不是个问题。Elixir或Erlang程序员倾向于用池来实现资源限制，降低效能。


把线程池想像成一个需要20个人一起的草坪修理工作。这里有10台割草机。当一个人要执行割草任务的时候，他需要去“领取”一台割草机。当割完草之后他需要还回这台割草机，把它留给其余排队要割草的人。当割草机被领完的时候，剩余的人要么做做其他事情，要么等着有割草机被还回来。在这个场景中，人们也行在某个地方等着没事干，但优点在于保证了所有的割草机不会闲着。

worker池也是这个原理。你创建一个完成特定任务的worker池。当进程需要一个worker时，它从池中拿出一个，使用它，然后用完还回去。当所有的worker都在服役的时候，再有需求worker的进程只能排队等候。

检验自己是否需要worker池最简单的方法就是测试输出。如同上面提到的，数据库、云服务和API常常要限制可用连接数。这些都是需要用到worker池的场合。*本质上来说，这项技术让并发数量可控，而且它最适合工作在无法应对大量并发请求的场合。*([Elixir in Action](https://www.goodreads.com/book/show/38732242-elixir-in-action))

如果碰到以下三场景，即可考虑使用worker池:

- 请求有限制条件
- 有清晰的资源约束
- 有内部施加的限制

如果没有输出的限制，worker池或许不是最佳选择。


原文链接: [Elixir, Poolboy, and Little's Law](https://samuelmullen.com/articles/elixir-poolboy-and-littles-law/?utm_campaign=elixir_radar_230&utm_medium=email&utm_source=RD+Station)
