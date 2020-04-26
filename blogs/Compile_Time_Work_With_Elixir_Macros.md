# Elixir宏与编译时
---

宏是Elixir中元编程常用手段。网上有非常多的资料会解释什么是宏，以及怎样使用他们：有Elixir官网"Getting Start"中关于[宏](https://elixir-lang.org/getting-started/meta/macros.html)的部分，由Saša Jurić遍写的一系列很不错的[文章](https://www.theerlangelist.com/2014/06/understanding-elixir-macros-part-1.html)，甚至是McCord写的[一本书](https://pragprog.com/book/cmelixir/metaprogramming-elixir)。这篇文章中，我假设你已经很熟练的使用宏编程而且c知道其原理，这里我着重讲一下宏的另外一种很少见的使用场景：在宏中做编译时工作。

## 宏展开

宏经常被用来操作抽象语法树，然后生成一个新的抽象语法树。举个例子，`if`的宏看起来像这样:

```
defmacro if(condition, do: do_block, else: else_block) do
  quote do
    case unquote(condition) do
      x when x in [false, nil] -> unquote(else_block)
      _                        -> unquote(do_block)
    end
  end
end
```

`if`展开后是一个`case`的表达式，检查`condition`是否为真，然后执行相应的代码。

这里的核心概念是*展开*：一个宏会被转换成其他的代码。用函数`Macro.expand/2`或`Macro.expand_once/2`很容易就能看到这一过程。让我们用一个简单的宏试试看：
```
defmodule SimpleMacro do
  defmacro plus(x, y) do
    quote do: unquote(x) + unquote(y)
  end
end
```

展开的过程比较琐碎：
```
iex> import SimpleMacro
iex> ast = quote do: plus(x, 23)
iex> ast |> Macro.expand(__ENV__) |> Macro.to_string
"x + 23"
```

展开一个宏的意思是指执行宏内的代码，将宏的调用替换为它返回的抽象语法树。展开的过程发生在编译阶段：一个宏是在编译阶段被执行，然后返回它递归生成的代码，这些代码在只在运行时被执行。我们刚好可以利用这一点！我们可以写一个宏，它在不会翻译它接收的抽象语法树，而是在编译阶段利用抽象语法树来执行某些操作。


## 编译时操作

通常来说，宏被描述为接收代码返回代码的函数；在这个描述中，我们把宏看成一种函数。但是，我们也可以将函数函数定义为一种宏：每个函数只是在编译时啥都不做的宏而已。

比如我们有以下代码：

```
defmodule MacroPhilosophy do
  def hello(name) do
    "Hello #{name}!"
  end
end
```

```
iex> hello "Elixir"
"Hello Elixir!"
```

我们可以将`hello/1`函数改写成一个宏，除了需要`require`一下`MacroPhilosophy`这个模块以外，不用修改所有依赖它的代码。我们只需要将`hello/1`修改为代码引用而非代码执行：幸好`quote`函数有`:bind_quoted`选项，我们可以利用这一点。

```
defmodule MacroPhilosophy do
  defmacro hello(name) do
    quote bind_quoted: binding() do
      "Hello #{name}!"
    end
  end
end
```

```
iex> require MacroPhilosophy
iex> hello "Elixir"
"Hello Elixir"
```

如你所见，函数体部分在函数实现和宏实现中是一致的。

这让我们可以用另外一个视角来看待函数，同时也强调了宏的重要特点：它们可被用来做编译时工作。我们可以在编译时的宏内部执行任何代码，只要我们能返回合法的代码。同时，在我们返回代码之前的所有工作都会在运行时消失不见。Poof!


### 一个没用的表达式记数宏

为了保持例子和现实世界毫无关联的优良传统，我们编写一个宏来日志打印Elixir的表达式数量：
```
defmodule UselessExamplesAreFun do
  defmacro log_number_of_expressions(code) do
    {_, counter} = Macro.prewalk code, 0, fn(expr, counter) ->
      {expr, counter + 1}
    end

    IO.puts "You passed me #{counter} expressions/sub-expressions"

    code
  end
end
```

让我们简单看一下这个宏，我们用`Macro.walk/3`函数来统计表达式数量。然后我们打印出这个数字：这就是我们编译时工作。最后我们返回参数中的代码(抽象语法树)。这个宏在运行时实际上啥也不干：它甚至不会在编译好的代码中留下痕迹。这是个性能友好的特性，因为编译时的日志代码消失不见了。

### 一个现实世界的例子

当我们在编写[gettext for elixir](https://github.com/elixir-gettext/gettext)的时候，José Valim建议我们使用这项技术，在那之后我意识到宏可以用来做编译时的工作。Gettext提供了名叫`mix gettext.extract`的任务用于提取源文件中的翻译写入到`。po`文件中。翻译动作就变成了带上字符串作为参数调用gettext宏。

```
# in lib/greetings.ex
import MyApp.Gettext
gettext "Hello people of Gotham!", "fr"
```

执行`mix gettext.extract`的结果会写入一个`.po`的文件中：
```
#: lib/greetings.ex:2
msgid "Hello people of Gotham!"
msgstr ""
```

大部分其他语言(例如Python)的gettext实现是解析代码然后寻找`gettext()`函数调用。而在Elixir中，我们只需要在宏中注入这个字符串，然后重新编译展开这个宏来完成翻译工作。Awesome！

这就是`gettext`函数定义的大致模样:
```
defmacro gettext(msgid, locale) do
  extract(msgid)

  quote do
    translate(unquote(msgid), unquote(locale))
  end
end
```

当我们调用`extract/2`函数时，我们在重新编译之前将`msgid`注入到一个代理中。当编译工作完成后，我们将代理的状态导出即可。这一切在运行时不会有任何副作用：调用`gettext/2`就如同调用`translate/2`一样。

## 总结

深入了解宏和其工作机制是元编程，优化和理解Elixir代码的基础。在这篇文章中，我们实践了用宏来完成编译时工作。我们看到了一个非现实世界的例子和一个gettext项目中真实的例子。


---
原文链接：[compile-time-work-with-elixir-macros](https://andrealeopardi.com/posts/compile-time-work-with-elixir-macros/)
