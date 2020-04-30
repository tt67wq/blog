# 利用yecc和leex在Elixir语言中做词法分析和语法分析
------
词法分析和语法分析是编程和计算机科学中十分重要的概念。在这背后有许许多多的理论，受篇幅限制，我不打算在这里讨论它们。而且，用一种"科学系统"的方法来进入这个话题让它显得有些可怕；而在具体实践中则会显得非常直观易懂。如果你想了解更多理论知识，可以看看维基百科([词法分析](https://en.wikipedia.org/wiki/Lexical_analysis)和[语法分析](https://en.wikipedia.org/wiki/Parsing))或者[龙书](https://en.wikipedia.org/wiki/Compilers:_Principles,_Techniques,_and_Tools)。

## Why

首先，词法分析和语法分析通常在一起使用，但是并不一定要这样。你可以使用词法分析器将一个字符串解析为一系列展开的词法单元，你也可以用语法分析器来帮你理解语法或者其他东西。

开始之前的一些题外话。人们常常用常规的表达式去理解文本。对简单的解析任务是没啥问题，通常情况下，这会返回一些支离破碎的代码。同时，常规表达式能解析的范围受限于固定的语法规则，所以这一次我们需要一些更强有力的工具。

## 走近`leex`和`yecc`

Erlang为了简化词法分析和语法分析的编写，提供了俩强有力的模块：[leex](https://erlang.org/doc/man/leex.html)和[yecc](https://erlang.org/doc/man/yecc.html)。`leex`是一个词法生成器。它读入一个语法规则文件后会吐出一个Erlang模块，你可以编译使用这个模块来做一些真正的词法分析。`yecc`功能类似，除了做的是语法分析的工作。

由于这些模块是Erlang标准库中的，所以使用这些模块基本没有太多后顾之忧，如果遇到啥问题，他们也能帮忙解决。


## 一个不切实际的小例子

每个想阐述类似理论的文章都需要这样一个例子，所以我们也要弄一个：我们将对一个Elixir原子和整型变量打包的字符串做词法分析和语法分析。最终目标是能够读入一个字符串表示的Elixir列表也能将其转换回一个Elixir的字符串，如下：
```
iex> ListParser.parse("[1, 2, [:foo, [:bar]]]")
[1, 2, [:foo, [:bar]]]
```
可见这个例子小巧做作且不切实际，我们应该准备好去做。


------
原文链接：[tokenizing-and-parsing-in-elixir-using-leex-and-yecc](https://andrealeopardi.com/posts/tokenizing-and-parsing-in-elixir-using-leex-and-yecc/)
