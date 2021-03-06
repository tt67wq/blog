# 利用yecc和leex在Elixir语言中做词法分析和语法分析
------
词法分析和语法分析是编程和计算机科学中十分重要的概念。在这背后有许许多多的理论，受篇幅限制，我不打算在这里讨论它们。而且，用一种"科学系统"的方法来进入这个话题让它显得有些可怕；而在具体实践中则会显得非常直观易懂。如果你想了解更多理论知识，可以看看维基百科([词法分析](https://en.wikipedia.org/wiki/Lexical_analysis)和[语法分析](https://en.wikipedia.org/wiki/Parsing))或者[龙书](https://en.wikipedia.org/wiki/Compilers:_Principles,_Techniques,_and_Tools)。

## Why

首先，词法分析和语法分析通常在一起使用，但是并不一定要这样。你可以使用词法分析器将一个字符串解析为一系列展开的词法单元，你也可以用语法分析器来帮你理解语法或者其他东西。

开始之前的一些题外话。人们常常用常规的表达式去理解文本。对简单的解析任务是没啥问题，通常情况下，这会返回一些支离破碎的代码。同时，常规表达式能解析的范围受限于固定的语法规则，所以这一次我们需要一些更强有力的工具。

## 走近`leex`和`yecc`

Erlang为了简化词法分析和语法分析的编写，提供了俩强有力的模块：[leex](https://erlang.org/doc/man/leex.html)和[yecc](https://erlang.org/doc/man/yecc.html)。`leex`是一个词法生成器。它读入一个语法规则文件后会吐出一个Erlang模块，你可以编译使用这个模块来做一些真正的词法分析。`yecc`功能类似，但做的是语法分析的工作。

由于这些模块是Erlang标准库中的，所以使用这些模块基本不会有太多后顾之忧，如果遇到啥问题，他们也能帮忙解决。


## 一个不切实际的小例子

每个想阐述类似理论的文章都需要这样一个例子，所以我们也要弄一个：我们将对一个Elixir原子和整型变量打包的字符串做词法分析和语法分析。最终目标是能够读入一个字符串表示的Elixir列表也能将其转换回一个Elixir的字符串，如下：
```
iex> ListParser.parse("[1, 2, [:foo, [:bar]]]")
[1, 2, [:foo, [:bar]]]
```

这个例子小巧做作且不切实际，应该不难实现。

## 词法部分

首先要做的是标记化这些字符：标记化指的是将字符串转变为一个比一堆字符更加结构化的Token列表。

举个例子来说，一个单独的词法单元可能为一个整数例如`4917`：整数`4917`就比字符列表`[?4, ?9, ?1, ?7]`更加结构化，因为它们是被当作一个整体来对待的。

标记化一个列表相当容易：只需要标记括号，逗号，整数和原子。我们先去标记简单的原子，例如`foo`和`foo_bar`，先不管用单引号或双引号引起来的原子类型，例如`:'foo bar'`和`:"hello world!"`。

根据这些基本语法来制作词法分析器不算复杂，但是`leex`大大简化了我们的工作，我们只需要编写十分简洁的语法就能写出我们的词法分析器。我们根据常规表达式来识别词法单元，我们可以将一个常规表达式与Erlang表达式关联来做到这一点。我曾提起过常规表达式并不能完全覆盖这个工作：由于语法分析有递归的属性，所以常规表达式并不适合，但是它们很适合做一个平坦结构的分离工作。

`lexx`的语法规则如下：
```
Regular expression : Erlang code.
```
在"Erlang code"部分中，如果我们想词法分析器解析出这个Token，我们需要返回一个`{:token, value}`的元组。

我们的词法分析器很简单：

```
Rules.

[0-9]+   : {token, {int,  TokenLine, TokenChars}}.
:[a-z_]+ : {token, {atom, TokenLine, TokenChars}}.
\[       : {token, {'[',  TokenLine}}.
\]       : {token, {']',  TokenLine}}.
,        : {token, {',',  TokenLine}}.
```

我们返回`{:token, value}`来告诉`leex`我们对匹配上的Token感兴趣而且我们希望在词法分析的输出结果中看到这个Token。

`TokenLine`和`TokenChars`是`leex`在Erlang表达式后面正则中维护的对象。这些变量存储了匹配到的Token的行号和内容。

我们总是使用二元或三元的元组作为Token，因为这是`yecc`的格式要求。如你所见，有时候我们对Token感兴趣所以我们返回三元组，然而有时候Token本身就是Token值(比如逗号)，所以二元组就足够了。`TokenLine`是强制要求的，为了`yecc`能够准确分离错误信息。

我们没必要把所有找到的Token都记下来：我们可以通过返回`:skip_token`来忽略掉它们。一个常用的例子就是忽略空格：
```
[\s\t\n\r]+ : skip_token.
```

常规表达式很快就会变得庞杂难以维护，不过我们可以利用`ALIAS = REGEX`语法来给这些表达式加上定义值。我们把定义放置在文件头部，在规则列表之前。为了在语法中使用这些定义值，我们需要在定义两边加上花括号。
```
Definitions.

INT        = [0-9]+
ATOM       = :[a-z_]+
WHITESPACE = [\s\t\n\r]

Rules.

{INT}         : {token, {int,  TokenLine, TokenChars}}.
{ATOM}        : {token, {atom, TokenLine, TokenChars}}.
\[            : {token, {'[',  TokenLine}}.
\]            : {token, {']',  TokenLine}}.
,             : {token, {',',  TokenLine}}.
{WHITESPACE}+ : skip_token.
```

现在我们可以尝试下我们编写的词法分析器。首先我们要把这些写进一个`.xrl`结尾的文件。然后我们可以利用`:leex.file/1`函数将`.xrl`文件转换成`.erl`文件。最后我们可以编译下新生成的Erlang模块。记住，大部分Erlang模块接受charlist而不是binary。所以我们要用单引号将它们引起来。

```
iex> :leex.file('list_lexer.xrl')
iex> c("list_lexer.erl")
iex> {:ok, tokens, _} = :list_lexer.string('[1, [:foo]]')
iex> tokens
{:"[", 1}, {:int, 1, '1'}, {:",", 1}, {:"[", 1}, {:atom, 1, ':foo'}, {:"]", 1}, {:"]", 1}]
```

Nice！`leex`也支持添加一些Erlang代码在其中：这部分写在`.xrl`文件尾部的`Erlang code.`部分中。我们可以利用这个功能把原子类型token转成原子变量：

```
...

{INT}  : {token, {int,  TokenLine, list_to_integer(TokenChars)}}.
{ATOM} : {token, {atom, TokenLine, to_atom(TokenChars)}}.

...

Erlang code.

to_atom([$:|Chars]) ->
  list_to_atom(Chars).
```

`to_atom/1`函数拿掉原子token的首字母，然后将其余部分转换成原子变量。我们也可以用`list_to_integer/1`函数将整数token转成整数变量。

我们的词法分析器现在是这个模样：

```
Definitions.

INT        = [0-9]+
ATOM       = :[a-z_]+
WHITESPACE = [\s\t\n\r]

Rules.

{INT}         : {token, {int,  TokenLine, list_to_integer(TokenChars)}}.
{ATOM}        : {token, {atom, TokenLine, to_atom(TokenChars)}}.
\[            : {token, {'[',  TokenLine}}.
\]            : {token, {']',  TokenLine}}.
,             : {token, {',',  TokenLine}}.
{WHITESPACE}+ : skip_token.

Erlang code.

to_atom([$:|Chars]) ->
    list_to_atom(Chars).
```

分析器如我们预期一般可用：

```
iex> {:ok, tokens, _} = :list_lexer.string('[1, :foo]')
iex> tokens
[{:"[", 1}, {:int, 1, 1}, {:",", 1}, {:atom, 1, :foo}, {:"]", 1}]
```

## 语法分析

我们现在有了一系列平铺开的token列表。我们想要给这些token赋予结构将其转换成Elixir中的列表对象就需要做语法分析。语法分析器依赖语法规则，而语法就是一系列确定这些token怎样被组织起来的规则。

我们也可以手写一个语法分析器(要比手写一个词法分析要困难一点)，如果使用`yecc`就很简单，它让你可以编写一些声明式的语法，而且就像`leex`一样容易使用。

一点点题外话：到现在为止，你可能认为这些名字没太大意义。事实上是有的。它们都是受到了两个著名的词法和语法分析器(`lex`和`yacc`)的影响。说明了这些搞Erlang的人也不是完全疯了，是吧？

言归正传，`yecc`的核心语法就是规则，如以下形式：

```
Left-hand side -> Right-hand side : Erlang expressions.
```

左手边是一类token的符号集，右手边是一个符号集或多个符号集。token的符号集有两类：终结符和非终结符。终结符就是不会再展开为其他符号集的token；非终结符就是可以递归的展开为其他符号集的token。

举个例子， `:"["`或者`{atom, Atom}`就是终结符，而一个列表可以被`list`非终结符表示。

```
list -> '[' ']'.
% or...
list -> '[' elems ']'.

% By the way, '%' is used for comments just like in Erlang.
```
如你所见，我们可以为每个符号集定义多个语法条款：而符号集可以采用这些条款中的任意一个。

`elems`本身也是一个非终结符。我们可以定义其为一个元素、一个标点或是一个元素列表：

```
elems -> elem.
elems -> elem ',' elems.
```

`elems`符号可以是`elem`，`elem, elem`以此类推。

`elem`本身也是个非终结符：它可以表示一个整数、一个原子、或一个列表。感慨下这里列表的元素本身也可以是一个列表这一逻辑的实现十分的优雅。

```
lem -> int.
elem -> atom.
elem -> list.
```
Beautiful！

所有的非终结符都要在某个时间点上被翻译成终结符：你不能让某个非终结符一直不被展开。`yecc`要求你在文件头部声明哪些类是终结符，哪些类是非终结符。

```
Terminals '[' ']' ',' int atom.
Nonterminals list elems elem.
```

你也需要声明一个*根符号*，这是一个初始点非终结符，用于生成所有的语法。在我们的例子中，就是`list`：

```
Rootsymbol list.
```

我们几乎要完成了，我们只需要将解析出的list转换成Elixir的list。我们可以在每个解析规则后面跟着的Erlang代码中做到这一点。在这些Erlang的代码中，我们有一些特殊的原子变量：`'$1'`, `'$2'`, `'$3'`这些。`yecc`会将这些变量替换成Erlang代码的返回值，并放置在类规则右手边的相同位置。我刚刚听到你说："What?!"；你是对的，这个在实践中更容易理解：

```
list ->
  '[' ']' : []. % an empty list translate to, well, an empty list
list ->
  '[' elems ']' : '$2'. % the list is formed by its elements

elems ->
  elem : ['$1']. % single-element list (and base case for the recursion)
elems ->
  elem ',' elems : ['$1'|'$3']. % '$3' will be replaced recursively

elem -> int  : extract_token('$1').
elem -> atom : extract_token('$1').
elem -> list : '$1'.

% Yep, we can use Erlang code here as well.
Erlang code.

extract_token({_Token, _Line, Value}) -> Value.
```

完成了，我们的语法分析器长这样：

```
Nonterminals list elems elem.
Terminals '[' ']' ',' int atom.
Rootsymbol list.

list -> '[' ']'       : [].
list -> '[' elems ']' : '$2'.

elems -> elem           : ['$1'].
elems -> elem ',' elems : ['$1'|'$3'].

elem -> int  : extract_token('$1').
elem -> atom : extract_token('$1').
elem -> list : '$1'.

Erlang code.

extract_token({_Token, _Line, Value}) -> Value.
```

我们现在可以从`yecc`文件生成一个Erlang文件，就像`lexx`一样：

```
iex> :yecc.file('list_parser.yrl')
iex> c("list_parser.erl")
iex> :list_parser.parse([{:"[", 1}, {:atom, 1, :foo}, {:"]", 1}])
{:ok, [:foo]}
```
生效了！

## 一起运行

我们现在可以将词法分析器的输出直接输入给语法分析器：
```
iex> source = "[:foo, [1], [:bar, [2, 3]]]"
iex> {:ok, tokens, _} = source |> String.to_charlist() |> :list_lexer.string
iex> :list_parser.parse(tokens)
{:ok, [:foo, [1], [:bar, [2, 3]]]}1
```
Awesome！

## Elixir集成

手动从`.xrl`和`.yrl`文件中生成Erlang文件，然后再编译这些Erlang文件，这一系列的工作很快就变得枯燥无味。幸运的是，Mix工具可以帮你！

Mix有"compiler"这么一个概念：对，它们就是你想的东西——编译器。Mix提供了一个Erlang编译器，同时也提供了`:leex`和`:yecc`编译器。它们是默认启用的，你可以在Mix项目中调用`Mix.compilers\0`函数来看到它们：

```
iex> Mix.compilers()
[:yecc, :leex, :erlang, :elixir, :app]
```

你只需要把`.xrl`和`.yrl`文件放在`src/`目录下，当项目被编译时，这些Erlang模块也会被编译出来。

```
mix new list_parser
mkdir list_parser/src
mv ./list_parser.yrl ./list_lexer.xrl ./list_parser/src/
```

现在，在目录`list_parser/lib/list_parser.ex`中：

```
defmodule ListParser do
  @spec parse(binary) :: list
  def parse(str) do
    {:ok, tokens, _} = str |> to_charlist() |> :list_lexer.string()
    {:ok, list} = :list_parser.parse(tokens)
    list0
  end
end
```

## 还不确信?

所有这些可能听上去比较抽象，不过我保证`leex`和`yecc`有许许多多的使用场景。举个例子，最近我在为[GNU gettext](https://www.gnu.org/software/gettext/)写Elixir实现的时候需要一个[PO files](https://www.gnu.org/software/gettext/manual/html_node/PO-Files.html)的解析器。我用了`yecc`编写了一个解释器：结果生成了一个声明式，简洁易懂的语法，我超喜欢这个。单元最后我们没有直接使用`leex`而是决定自己写一个解析器，因为我需要的token标记相当简单，而用`leex`有点杀鸡用牛刀的感觉。

## 简单总结
我们写了一个简单的词法和语法分析器，用于将表示Elixir列表的字符串转换成真正的Elixir列表。我们使用了`leex`生成了词法分析器，用`yecc`生成了语法分析器。我们只展示了这两个工具的基本用法，实际上它们还能做更复杂的事情(`yecc`还能生成LALR语法分析器)，这一部分，如往常一样，还是去看[文档](https://www.erlang.org/doc/apps/parsetools/)吧。


------
原文链接：[tokenizing-and-parsing-in-elixir-using-leex-and-yecc](https://andrealeopardi.com/posts/tokenizing-and-parsing-in-elixir-using-leex-and-yecc/)
