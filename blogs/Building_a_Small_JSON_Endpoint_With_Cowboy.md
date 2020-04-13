# Elixir: 利用Plug，Cowboy和Poison构建小型Json API服务
----
有好几次，我想不用大型的全栈框架去构建一个简单的Json API服务，暴露一个服务或者执行个Webhook事件。现在我们可以试试看，用[Plug](https://hexdocs.pm/plug/readme.html)，Erlang的[Cowboy](https://github.com/ninenines/cowboy)http服务来构建一个可用于生产的服务有多容易。


## Plug Is:
> 1. Web应用之中模块化的组成标准
> 2. Erlang虚拟机中不同Web服务的连接适配器

如果你是`Ruby/Rails`开发者，想想`Rack`，如果你是`Node`开发者，想想`Express`。当然这些库的概念在上层都比较类似，但在他们各自领域又是独一无二的。

## Cowboy Is：
> 一个小型，高性能，现代的Erlang/OTP的HTTP服务

另外说一下，这个"现代web服务"对HTTP2的支持还比较差，提供了一系列的Websockets处理器和处理长连接的接口。如果不深究细节，我们可以很安全的说，这是一个生产环境可用的选择。查看[文档](https://ninenines.eu/docs/en/cowboy/2.5/guide/)了解更多。

## Poison Is:
> 一个Elixir的JSON库，旨在在不牺牲简洁性，完整性和正确性的基础上追求极致的性能。

换句话来说，这是一个超高性能且可靠的JSON解析库。

----
原文链接: [Building a Small JSON Endpoint With Plug, Cowboy and Poison](https://dev.to/jonlunsford/elixir-building-a-small-json-endpoint-with-plug-cowboy-and-poison-1826)
