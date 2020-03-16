### [译] Elixir中TCP连接处理技巧 -- Andrea Leopardi

鉴于Erlang的设计风格和Erlang虚拟机的特性，Elixir作为一门Erlang虚拟机上的语言，在网络编程中大展身手。在这个大前提下，我们总有这样的需求---在网络世界中处理外部链接。
举个例子：一个典型的Web应用需要连接一个关系型数据库和一个kvdb，或者一个嵌入式的系统需要连接其他的node。

大多数情况下，归功于一些已经封装好的网络驱动(例如数据库驱动)，这些网络连接对程序员来说是无需关心的，但是我认为了解这些连接如何手动处理是一件很有趣的事情。如果某些特殊的网络服务没有外部的驱动代码可用，又或者你想了解这些驱动是怎样工作的，这些知识就会很有用。

这篇文章中我们只会讨论TCP协议的连接，因为TCP协议可能是网络世界中最基础和使用最多的协议了。但是我们所使用的方法和原理，在其他协议面前也是通用的，例如UDP协议。

#### 一个很现实的例子
作为这篇文章的目标，我们想编写一个差不多能work的redis驱动。Redis服务是能够收发message的TCP服务。Redis在TCP之上使用了一个自定义的应用层协议，并没有使用通用的HTTP协议。而我们并不关心这些，我们只关心怎样处理我们的Elixir应用和Redis Server之间的TCP连接。

一点题外话：显然，社区里已经有很多的Erlang和Elixir的Redis驱动，不过，懒惰的我懒得再去想一个聪明的名字，我们就叫他Redis好了。

这就开始吧。



----
原文链接: [Handling TCP connections in Elixir](https://andrealeopardi.com/posts/handling-tcp-connections-in-elixir/)
