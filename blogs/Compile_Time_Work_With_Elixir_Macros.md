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


---
原文链接：[compile-time-work-with-elixir-macros](https://andrealeopardi.com/posts/compile-time-work-with-elixir-macros/)
