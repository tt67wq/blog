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

## Poolboy

Elixir没有官方的，甚至没有流行的Worker池库，但是如果你读过我的博客[Just Enough Erlang](https://samuelmullen.com/articles/just_enough_erlang/)，你可以试一试这个炫酷的[Poolboy](https://github.com/devinus/poolboy)库。如果你没听说过它，看看它的描述：“Poolboy是一个Erlang实现的轻量级抽象资源池化库，专注于简洁、高性能和可靠性。”。这个库如它的描述一般名副其实。

Poolboy安装方法如同其他[Hex](https://github.com/devinus/poolboy)库一致，安装完之后，你可以用下面描述的简单的三个步骤来使用Poolboy：

1. 创建一个Worker实例
2. 用监控树配置启动一个Poolboy
3. 使用Worker

我们来看看每一步的细节：

### 创建Worker实例

Poolboy的工作实例是GenServer服务。当Poolboy监控树启动时，它会为每个工作进程创建一个监控进程，当有请求接入时，Poolboy会给这些GenServer分配工作。

我们举个简单的例子，我们创建一个为传入参数算平方的GenServer。

```
defmodule MyApp.SquareWorker do
  use GenServer

  def start_link(_) do
    GenServer.start_link(__MODULE__, nil)
  end

  def init(_) do
    {:ok, nil}
  end

  def handle_call({:square, x}, _from, state) do
    IO.puts("PID: #{inspect(self())} - #{x * x}")
    Process.sleep(1000)

    {:reply, x * x, state}
  end
end
```

这个GenServer非常简单，但是也有几点需要注意。首先，你看到我们并没有在函数`GenServer.start_link/2`中给我们的GenServer命名。因为Poolboy会启动多个实例，如果命名了会引起冲突。

第二个需要注意的是我们并没有存状态。它初始为`nil`且一直不变。当然在一些场合我们需要工作实例维持状态--例如db连接，但这个例子中我们用不到。

最后，调用`:square`接收一个数字然后在一秒钟后返回其平方数。我们也打印了一些辅助信息。这一秒钟的延迟在我们后续的实验中非常重要。

### 启动Poolboy监控树

当我们创建好了工作实例，就可以在应用中配置和启动Poolboy了。大多数情况下我们会在各自的监控树中配置，这里为了简单起见，我们在`application.ex`中声明。

```
defmodule MyApp.Application do
  use Application

  def start(_type, _args) do
    children = [
      :poolboy.child_spec(:square_worker, poolboy_config())
    ]

    opts = [strategy: :one_for_one, name: MyApp.Supervisor]
    Supervisor.start_link(children, opts)
  end

  defp poolboy_config do
    [
      name: {:local, :square_worker},
      worker_module: MyApp.SquareWorker,
      size: 5,
      max_overflow: 0
    ]
  end
end
```

为了将Poolboy加入监控树，我们用了`:poolboy.child_spec/2`函数，传入一个唯一id作为第一个参数，和一系列配置作为第二个参数。在这个例子中，我们用了一个函数来返回配置信息，但是不一定非要这么做。我们看下每个配置参数的说明：

- *name*: 一个2元素的元组，其中包含了`:global`, `:local`或 `:via`的标签和一个池的名字。好像除了`:local`其他的也不太会去用。其余的选项是将进程注册到全局的进程仓库或是某个自定的仓库中。
- *worker_module*: 这是包含工作进程内容的模块名。在我们这个例子中，就是`MyApp.SquareWorker`。
- *size*: 定义了常驻内存的worker数量。
- *max_overflow*: 定义了当常驻进程不够时最多允许超载的进程数量。
- *strategy*: `lifo`或是`fifo`，决定了归还的工作进程被放置在可用队列的队头还是队尾。`lifo`操作起来像个栈，`fifo`像个队列。默认是lifo。

当工作进程和Poolboy配置都搞定了，让我们专注于它们的使用方法。


### 工作进程的使用

有两种使用Poolboy的方法：1) 人为的取出和归还worker；2) 利用Poolboy的事务函数。我们依次看看：

#### 取出再归还worker

取出和归还worker依靠的是poolboy的`checkout/3`和`checkin/2`两个函数。这里有个例子：
```
iex 1> worker_pid = :poolboy.checkout(:square_worker)
#PID<0.187.0>
iex 2> GenServer.call(worker_pid, {:square, 4})
PID: #PID<0.187.0> - 16
16
iex 3> :poolboy.checkin(:square_worker, worker_pid)
:ok
```
这里，我们首先做的就是从池`square_worker`(pid代指GenServer进程)中"取出"一个worker。然后我们调用`GenServer.call/3`函数，传入worker的pid和所需要的参数。一旦调用GenServer完成了，我们就将worker归还至`:square_worker`池。

我们的池子被设置成能容纳5个worker。那当我们第6次取出的时候会发生什么事情呢？如果你做个实验，然后等个5秒钟，你会看到下面的报错信息：
```
** (exit) exited in: :gen_server.call(:worker, {:checkout, #Reference<0.797852558.3545497601.41814>, true}, 5000)
    ** (EXIT) time out
    (stdlib) gen_server.erl:223: :gen_server.call/3
    (poolboy) /Users/samullen/sandbox/elixir/my_app/deps/poolboy/src/poolboy.erl:63: :poolboy.checkout/3
```
你也许在期待Poolboy拒绝你的这次请求，但是它并没有。相反，它将其放入队列中等待有worker被释放。由于Poolboy跟所有的GenServer一样有5秒的超时时间，这个进程在超时后崩溃了。这里有几种解决的办法：

1. 提高取出请求的延迟时间限制
2. 当池中没有可用worker时，阻塞请求的进程
3. 在配置中增加池的可用worker数量
4. 在配置文件中加入过载的配置

为了增加超时时间，你仅仅需要在取出worker时加入一个阻塞时间参数：
```
iex 4> worker_pid = :poolboy.checkout(:square_worker, true, 20_000)
```
在某些情况下提升超时时间时有效的，但是这种方法感觉很脏。

除此之外，你可以为`block`参数传入`false`，然后手动的处理。你可以按照这个例程来编写：
```
def squarer(x) do
  case :poolboy.checkout(:square_worker, false) do
    :full ->
      Process.sleep 100
      squarer(x)

    worker_pid ->
      GenServer.call(worker_pid, {:square, x})
      :poolboy.checkin(:square_worker, worker_pid)
  end
end
```

另外两个选项，`:size`和`:max_overflow`，应该就是字面意思了。

就像C语言处理内存请求一般，人为的取出和归还worker有潜在的出错可能。虽然不会造成内存泄漏，但你的代码会迅速的耗尽池资源然后挂掉。谢天谢地，这比在C语言中追踪内存泄漏要容易多了。

如果每次想使用池资源的时候都要`checkout`和`checkin`似乎操作有点多，你可以使用Poolboy的`transaction/2`函数。

#### 事务

学习Poolboy事务的最好方法就是类比[数据库的事务](https://en.wikipedia.org/wiki/Database_transaction)。它们"使工作具有了原子性，...，它们会独立可靠的运行，不依赖其他的事务。"，取出和归还的动作已经帮你处理好了。你只需要负责事务部分的逻辑。

这就是事务的模样：

```
:poolboy.transaction(:square_worker, fn pid ->
  GenServer.call(pid, {:square, 4})
end)
```

有了这些知识，我们可以用Poolboy在5个实例的工作池中做平方计算。

```
defmodule MyApp.Tester do
  def run do
    1..25
    |> Enum.map(&spawn_workers/1)
    |> Enum.map(&Task.await/1)
  end

  def spawn_workers(i) do
    Task.async(fn ->
      :poolboy.transaction(:square_worker, fn pid ->
        GenServer.call(pid, {:square, i})
      end)
    end)
  end
end
```

在上面的代码中，我们用`Task`模块去加载新的进程，每个进程都使用`:poolboy.transaction/2`函数来计算输入值的平方。尽管提供了5个工作GenServer，如果我们想实现并发，我们还是需要用`Task.async/1`(甚至`spawn/1`)。

一旦我们对参数Map调用了`Task.async/1`，我们就必须用`Task.await/1`等待所有的任务完成。

运行这段代码，我们会看到以下的结果输出，一次输出5行：
```
iex [19:18 :: 1] > MyApp.Tester.run
PID: #PID<0.190.0> - 1
PID: #PID<0.189.0> - 4
PID: #PID<0.187.0> - 16
PID: #PID<0.188.0> - 9
PID: #PID<0.186.0> - 25
PID: #PID<0.187.0> - 36
PID: #PID<0.188.0> - 49
PID: #PID<0.189.0> - 100
PID: #PID<0.190.0> - 64
PID: #PID<0.186.0> - 81
PID: #PID<0.186.0> - 144
PID: #PID<0.188.0> - 169
PID: #PID<0.190.0> - 225
PID: #PID<0.189.0> - 196
PID: #PID<0.187.0> - 121
PID: #PID<0.186.0> - 289
PID: #PID<0.187.0> - 256
PID: #PID<0.188.0> - 361
PID: #PID<0.189.0> - 324
PID: #PID<0.190.0> - 400
PID: #PID<0.186.0> - 441
PID: #PID<0.187.0> - 484
PID: #PID<0.188.0> - 529
PID: #PID<0.190.0> - 625
PID: #PID<0.189.0> - 576
[1, 4, 9, 16, 25, 36, 49, 64, 81, 100, 121, 144, 169, 196, 225, 256, 289,
 324, 361, 400, 441, 484, 529, 576, 625]
iex [19:18 :: 2] >

```

注意到GenServer的默认超时时间，如果我们把`1..25`换成`1..26`会发生什么？如果你回答："服务会宕掉，邮箱里的消息都会丢失"，那么恭喜你答对了。

怎样处理这个问题呢？不像Poolboy的`checkin/checkout`函数，`transaction/2`函数并没有提供一个`:full`信号的回调。我们只能提高进程数量。但是提高到多少呢？

## 利特尔法则

想要算出究竟需要多少个进程，我们需要两个信息：数据的到达率和平均的消费时间。这个公式由John Little提出，"在一个静止系统中，平均消费者的数量等于平均到达率乘以每个消费者在耗费的平均系统时间。"([利特尔法则](https://en.wikipedia.org/wiki/Little%27s_law))。公式如下：

```
L = λW
```

- L: 静止系统中消费者数量。即队列中元素数量。
- λ: 到达率或单位时间吞吐量。
- W: 队列中的平均等待时间。

在我们的例子中，我们知道`W`是1秒钟，因为那是我们传给`Process.sleep/1`函数的值。不幸的是，`λ`值目前还是个未知数，因为传一个范围值给`Enum.map/2`函数的速度接近无穷大。考虑到在现实世界中我们不需要处理无限的吞吐量，所以我们对我们的测试代码做一下微调，让它变的有意义。

```
defmodule MyApp.Tester do
  def run do
    1..100
    |> Stream.map(fn i ->
      Process.sleep(100)
      spawn_workers(i)
    end)
    |> Enum.to_list()
    |> Enum.map(&Task.await/1)
  end

  def spawn_workers(i) do
    Task.async(fn ->
      :poolboy.transaction(:worker, fn pid ->
        GenServer.call(pid, {:square, i})
      end)
    end)
  end
end
```

在通过往流水线中加入`Stream.map/2`函数和`Enum.to_list/1`函数，我们把到达率降低到了10(每100ms到达一个)。由于我们给到达率加上了一个延迟，我们把请求数量从25上调到100也就说的通了。现在对单个进程来说公式是这样的：
```
10 = 10 * 1
```

由于我们池中有5个worker，我们需要修改下`W`参数，即把平均等待时间改成0.2(1/5=0.2)。
```
2 = 10 * 0.2
```
现在我们在请求队列中始终有两个元素。问题在于，这个是否足够限制我们在5秒的超时范围内？我们可以通过把`L`和`W`相乘得到，即2 * 0.2。结果为0.4，是元素在队列中等待时间的两倍，所以说队列会持续增长直到超时时间到达。如果你在新代码中运行`Tester.run/0`，你会发现在第56个请求的时候挂掉。

我们现在有3个选择：如果我们对我们能建立的链接数量不做约束，我们可以把池规模拓展到10，保持队列中等待时间(`W`)和到达率(`λ`)不变。或者，如果我们对链接数量做了限制，我们可以专注于提高元素在队列中等待的时间(`W`)，最后也是通常我们不想去做的，降低我们接受请求的速度。

当我们把池的规模扩展到10然后再运行`Tester.run/0`，我们达到了平衡，能够成功输出100个数的平方。

## 过载
我们创建的系统在大多数情况下是不变的。每0.1秒来一个请求，然后每1秒处理一个请求。没有变化和意外。在这个练习系统之外你很难遇到一个这样的系统。相反，我们几乎每天都在处理流量的起伏。网页，API还有我们的后端请求数量都会有堵车体验；有些时候会像日常一样正常，有些就会弄个大意外。

为了处理这些拥堵，Poolboy的`:max_overflow`选项才被设计出来。如果你已经用利特尔法则算出了你想要的进程数量，而且你也知道你经历过的常规的流量上涨幅度。想计算出过载数量就不是一件难事。

就我们的例子来说，如果你的吞吐量在一天的某个时间中从10/s涨到了15/s，你会看出这里有一个50%幅度的流量涨幅。基于这个值，我们知道`:max_overflow`值得是我们池`:size`的50％，即5。

再提一下，这个方案只在你有多余可用链接的情况下才可行。如果你没有达到这个要求，你可能需要优化你的算法效率了。


-----

原文链接: [Elixir, Poolboy, and Little's Law](https://samuelmullen.com/articles/elixir-poolboy-and-littles-law/?utm_campaign=elixir_radar_230&utm_medium=email&utm_source=RD+Station)
