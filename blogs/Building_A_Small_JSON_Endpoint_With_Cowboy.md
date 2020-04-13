# Elixir: 利用Plug，Cowboy和Poison构建小型Json API服务
----
有好几次，我想不用大型的全栈框架去构建一个简单的Json API服务，暴露一个服务或者执行个Webhook事件。现在我们可以试试看，用[Plug](https://hexdocs.pm/plug/readme.html)，Erlang的[Cowboy](https://github.com/ninenines/cowboy)http服务来构建一个可用于生产的服务有多容易。

-----

## Plug Is:
> 1. Web应用之中模块化的组成标准
> 2. Erlang虚拟机中不同Web服务的连接适配器

如果你是`Ruby/Rails`开发者，想想`Rack`，如果你是`Node`开发者，想想`Express`。当然这些库的概念在上层都比较类似，但在他们各自领域又是独一无二的。

## Cowboy Is：
> 一个小型，高性能，现代的Erlang/OTP的HTTP服务

另外说一下，这一个高容错的"现代web服务"，且支持HTTP2，提供了一系列的Websockets处理器和处理长连接的接口。如果不深究细节，我们可以很安全的说，这是一个生产环境可用的选择。查看[文档](https://ninenines.eu/docs/en/cowboy/2.5/guide/)了解更多。

## Poison Is:
> 一个Elixir的JSON库，旨在在不牺牲简洁性，完整性和正确性的基础上追求极致的性能。

换句话来说，这是一个超高性能且可靠的JSON解析库。

-----

### 构建端点

简短介绍了几个定义之后，让我们构建一个端点来处理Webhook事件请求。现在，我们希望这个服务是"生产可用"的，这个对我们的例子来说意味着什么呢？

  1. `高可用`: 总是处于可用状态。永远不会宕机(至少不容易宕机:))
  2. `容易配置`：可以部署到任意的环境
  3. `充分测试`：让我们对所用的工具有充分自信
  
我们确实为这个准备了一个非常简单的例子，在选择工具和投入产出之前充分理解你的需求是一件非常重要的事情。

-----

#### 1. 创建一个新的，被监控树监控的，Elixir应用

```
$ mix new webhook_processor --sup
$ cd webhook_processor
```

`--sup`会创建一个OTP平台的应用。我们的应用会在崩溃后自动重启，但是Erlang虚拟机的崩溃不会被重启。

#### 2. 添加Plug，Cowboy和Poison作为依赖
```
# ./mix.exs
defmodule WebhookProcessor.MixProject do
  use Mix.Project

  def project do
    [
      app: :webhook_processor,
      version: "0.1.0",
      elixir: "~> 1.7",
      start_permanent: Mix.env() == :prod,
      deps: deps()
    ]
  end

  # Run "mix help compile.app" to learn about applications.
  def application do
    [
      # Add :plug_cowboy to extra_applications
      extra_applications: [:logger, :plug_cowboy],
      mod: {WebhookProcessor.Application, []}
    ]
  end

  # Run "mix help deps" to learn about dependencies.
  defp deps do
    [
      {:plug_cowboy, "~> 2.0"}, # This will pull in Plug AND Cowboy
      {:poison, "~> 3.1"} # Latest version as of this writing
    ]
  end
end

```
注意，我们添加了`plug_cowboy`作为Plug和Cowboy单独的依赖。我们也需要在`extra_applications`中添加`:plug_cowboy`。

#### 3. Mix deps.get
```
Mix deps.get
```

#### 4. 补全application.ex
```
# ./lib/webhook_processor/application.ex
defmodule WebhookProcessor.Application do
  @moduledoc "OTP Application specification for WebhookProcessor"

  use Application

  def start(_type, _args) do
    # List all child processes to be supervised
    children = [
      # Use Plug.Cowboy.child_spec/3 to register our endpoint as a plug
      Plug.Cowboy.child_spec(
        scheme: :http,
        plug: WebhookProcessor.Endpoint,
        options: [port: 4001]
      )
    ]

    # See https://hexdocs.pm/elixir/Supervisor.html
    # for other strategies and supported options
    opts = [strategy: :one_for_one, name: WebhookProcessor.Supervisor]
    Supervisor.start_link(children, opts)
  end
end

```

#### 5. 实现WebhookProcessor.Endpoint
```
# ./lib/webhook_processor/endpoint.ex
defmodule WebhookProcessor.Endpoint do
  @moduledoc """
  A Plug responsible for logging request info, parsing request body's as JSON,
  matching routes, and dispatching responses.
  """

  use Plug.Router

  # This module is a Plug, that also implements it's own plug pipeline, below:

  # Using Plug.Logger for logging request information
  plug(Plug.Logger)
  # responsible for matching routes
  plug(:match)
  # Using Poison for JSON decoding
  # Note, order of plugs is important, by placing this _after_ the 'match' plug,
  # we will only parse the request AFTER there is a route match.
  plug(Plug.Parsers, parsers: [:json], json_decoder: Poison)
  # responsible for dispatching responses
  plug(:dispatch)

  # A simple route to test that the server is up
  # Note, all routes must return a connection as per the Plug spec.
  get "/ping" do
    send_resp(conn, 200, "pong!")
  end

  # Handle incoming events, if the payload is the right shape, process the
  # events, otherwise return an error.
  post "/events" do
    {status, body} =
      case conn.body_params do
        %{"events" => events} -> {200, process_events(events)}
        _ -> {422, missing_events()}
      end

    send_resp(conn, status, body)
  end

  defp process_events(events) when is_list(events) do
    # Do some processing on a list of events
    Poison.encode!(%{response: "Received Events!"})
  end

  defp process_events(_) do
    # If we can't process anything, let them know :)
    Poison.encode!(%{response: "Please Send Some Events!"})
  end

  defp missing_events do
    Poison.encode!(%{error: "Expected Payload: { 'events': [...] }"})
  end

  # A catchall route, 'match' will match no matter the request method,
  # so a response is always returned, even if there is no route to match.
  match _ do
    send_resp(conn, 404, "oops... Nothing here :(")
  end
end

```
这些代码看上去很多，但是大部分都是注释。主旨就是利用`Plug.Router`中的`get`和`post`宏来生成路由。这个模块本身就是个Plug，它定义了自身的plug管道。注意，为了解析请求和分发回执，`match`和`dispatch`是必须的。`Pipeline`是个关键概念，plug的排序决定了操作的顺序。注意到match是在我们的parser之前声明的，这就意味着在有路由匹配之前，我们不会做任何解析工作。如果这个顺序被颠倒，就会出现不管有无路由匹配都去做请求解析的情况。点击Plug.Router的[文档](https://hexdocs.pm/plug/Plug.Router.html#content)了解更多。

#### 6. 让端点可配置

```
# ./lib/webhook_processor/application.ex
defmodule WebhookProcessor.Application do
  @moduledoc "OTP Application specification for WebhookProcessor"

  use Application

  def start(_type, _args) do
    # List all child processes to be supervised
    children = [
      # Use Plug.Cowboy.child_spec/3 to register our endpoint as a plug
      Plug.Cowboy.child_spec(
        scheme: :http,
        plug: WebhookProcessor.Endpoint,
        # Set the port per environment, see ./config/MIX_ENV.exs
        options: [port: Application.get_env(:webhook_processor, :port)]
      )
    ]

    # See https://hexdocs.pm/elixir/Supervisor.html
    # for other strategies and supported options
    opts = [strategy: :one_for_one, name: WebhookProcessor.Supervisor]
    Supervisor.start_link(children, opts)
  end
end

```

我们将硬编码的端口号换成了环境变量，这让我们可以在任意环境中运行webhook。最后我们为每个`MIX_ENV`创建一份配置文件：
```
#./config/config.exs

# This file is responsible for configuring your application
# and its dependencies with the aid of the Mix.Config module.
use Mix.Config

import_config "#{Mix.env()}.exs"

-------------------

# ./config/dev.exs

use Mix.Config

config :webhook_processor, port: 4001

-------------------

# ./config/test.exs

use Mix.Config

config :webhook_processor, port: 4002

-------------------

# ./config/prod.exs

use Mix.Config

config :webhook_processor, port: 80

```
#### 7. 测试

```
# ./test/webhook_processor/endpoint_test.exs
defmodule WebhookProcessor.EndpointTest do
  use ExUnit.Case, async: true
  use Plug.Test

  @opts WebhookProcessor.Endpoint.init([])

  test "it returns pong" do
    # Create a test connection
    conn = conn(:get, "/ping")

    # Invoke the plug
    conn = WebhookProcessor.Endpoint.call(conn, @opts)

    # Assert the response and status
    assert conn.state == :sent
    assert conn.status == 200
    assert conn.resp_body == "pong!"
  end

  test "it returns 200 with a valid payload" do
    # Create a test connection
    conn = conn(:post, "/events", %{events: [%{}]})

    # Invoke the plug
    conn = WebhookProcessor.Endpoint.call(conn, @opts)

    # Assert the response
    assert conn.status == 200
  end

  test "it returns 422 with an invalid payload" do
    # Create a test connection
    conn = conn(:post, "/events", %{})

    # Invoke the plug
    conn = WebhookProcessor.Endpoint.call(conn, @opts)

    # Assert the response
    assert conn.status == 422
  end

  test "it returns 404 when no route matches" do
    # Create a test connection
    conn = conn(:get, "/fail")

    # Invoke the plug
    conn = WebhookProcessor.Endpoint.call(conn, @opts)

    # Assert the response
    assert conn.status == 404
  end
end

```

测试代码相当简单，但是它保证了我们的服务是达到预期的。关于这些测试唯一可争论的点就是返回码，而不是事件执行时的副作用。记住，测试代码总是要触达代码的边沿，而不是超过它，除非你是在写集成测试。


### 总结

只用了很少的工作量，我们构建了一个小而强大的后端服务。多谢Cowboy，你能够在单个服务器上处理比你所需多得多的链接，我们只需要为这些优点付出很小的代价。

如往常一样，这些代码都在[仓库](https://github.com/jonlunsford/webhook_processor)中开源。


----
原文链接: [Building a Small JSON Endpoint With Plug, Cowboy and Poison](https://dev.to/jonlunsford/elixir-building-a-small-json-endpoint-with-plug-cowboy-and-poison-1826)
