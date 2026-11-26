---
title: "2610 次工具调用教会我的事：把 agent 的工具编排搬进 JS 沙箱"
date: 2026-11-26T12:00:00+08:00
slug: fx-codemode-design
summary: 我的 coding agent 近 30 天跑了 2610 次工具调用，其中 2062 条结果来自同一个工具：codemode。让模型写一段 JS 在 QuickJS 沙箱里编排工具，N 个回合压成 1 个，中间结果不进上下文。这篇讲它的设计、踩坑和账本。
tags: ["AI", "agent", "fx", "QuickJS", "工具编排"]
description: "以 fx fork 的 codemode 为例，讲清 code execution 式工具编排：嵌套权限、预算与失败语义、store 的前向兼容决策，附真机实测的回合与体积对照。"
ShowToc: true
comments: false
---

近 30 天，我的 coding agent 在 101 个会话里发起了 2610 次工具调用，其中 2062 条结果来自同一个工具：codemode（来源：fx 仓库 plan.md「数据基线」节，扫描时刻 2026-11-18 19:22）。它做的事情一句话能说清：模型不再一次调一个工具，而是写一段 JavaScript，在 QuickJS 沙箱里把一串工具调用编排完，N 个模型回合压成 1 个，只有最终输出进上下文。

这篇记录这个功能怎么设计、我怎么被真实使用打脸、以及最后算出来的账。所有数字都有出处，所有示例脚本都在真机跑通过。

## 工具调用的隐性账单

先说问题。你让 agent「grep 一下，再读三个文件，然后跑测试」，传统做法是 5 次以上的模型回合：每次工具调用都要等模型看完上一次的结果、再决定下一步。每个回合是一次完整的模型请求，延迟叠加不说，grep 出来的几百行、文件的全文，这些中间结果全部灌进上下文，后面的每一轮请求都要重新带上它们。

这笔账的坏处在于重复计费。上下文是累积的，第一回合 grep 出来的几百行，第二、第三、第四回合的请求都要原样再带一遍，中间结果不是付一次钱，是付 N 次。我每周扫一遍会话日志统计调用分布，2610 这个数字就是这么来的，扫的时候我最在意的不是调用次数，是每条结果有多少字节最终进了模型上下文。

这类方案现在有个通用名字：code execution 或者 tool orchestration，让模型写代码来编排工具，而不是逐个发起工具调用。Cloudflare 在 [Code Mode](https://blog.cloudflare.com/code-mode/) 里给 agent 一个写 TypeScript 调 MCP 工具的沙箱，Anthropic 在 [Code execution with MCP](https://www.anthropic.com/research/code-execution-with-mcp) 里把工具变成代码 API，思路一致：中间结果留在执行环境里，模型只看摘要。我在自己的 fx fork（[tt67wq/fx](https://github.com/tt67wq/fx)，一个 Zig 写的终端 coding agent）里做了同样的事，下面按读者的疑问顺序讲，不按开发时间线。

![图1：传统逐调用 vs codemode 单回合对比](/images/fx-codemode/turns.png)

## 总体设计：一段 JS 能干什么

codemode 是一个内置工具，参数就是一段脚本。沙箱里注册的全局只有白名单：`tools.*` 调工具、`text()` 交最终输出、`store()/load()` 存跨调用状态、`searchTools/describeTool` 发现工具，没有任何 std/os 宿主能力（来源：.agents/codemode-plan.md §3）。默认只暴露只读四件套 `glob_files`、`grep_files`、`read_file`、`run_command`；打开 `experimental.codemode_derived_surface` 才加上 write_file、edit_file 等写工具（来源：README.md codemode 节）。

下面这段脚本是我真机跑过的，任务是统计三个文件里含 TODO 的行数。它也是第 6 节实测对照用的脚本：

```javascript
const files = ["alpha.txt", "beta.txt", "gamma.txt"];
let total = 0;
for (const f of files) {
  const raw = await tools.run_command({ command: "grep -n TODO " + f });
  // run_command 返回 JSON 字符串，output 字段里还有一层 shell 快照 JSON
  const snap = JSON.parse(JSON.parse(raw).output);
  total += snap.output_delta.split("\n").filter((l) => l.includes("TODO")).length;
}
text("TODO total: " + total);
```

三次 grep 的完整输出（每个文件约 16KB）只在脚本里流动，模型收到的是 `TODO total: 900` 加一份嵌套调用清单，一共 124 字节。这个双层 JSON.parse 不是笔误，是当前二进制（commit c553300ae）的真实返回形状，我先在沙箱里打印了 `typeof` 和字段名才敢这么写。

工具多了之后，发现本身也是预算。默认四件套的声明直接内联进工具描述；derived surface 的工具目录受 16KiB 预算约束（context_limits.codemode_catalog_bytes），排序是核心四件套永远在列，然后写工具，然后其余，触发预算就丢后面的条目并给一份省略清单（来源：README.md codemode 节）。目录之外的工具靠 searchTools 找，实现是自实现的加权 token 打分：名字命中 3 分、参数命中 2 分、描述命中 1 分（discovery.zig:82-84），没有引入任何检索库；describeTool 返回单个工具的完整 schema，名字不认识时给相近名字建议。

脚本里的失败语义也定死了：参数错误和执行失败 reject 成 Error，脚本可以 catch；权限被拒则返回带 reason 的结果而不是异常，脚本能直接分支（来源：bridge.zig deniedResult 注释）；Promise.allSettled 可以并行发起调用；脚本结束时还没 await 的调用直接取消（来源：.agents/codemode-plan.md §4）。README 里还有一句我特意保留的警告：只包一个工具调用的脚本比直接调工具更慢，codemode 不是所有调用的默认包装纸。

设计上有四条硬约束，写在方案第一页（来源：.agents/codemode-plan.md §0）：

1. permission-first：脚本内每次工具调用独立过既有准入，没有免审通道。
2. 单二进制交付不变，QuickJS 直接编进 fx。
3. 启动预算 2ms，沙箱必须惰性初始化，不用不付费。
4. 依赖纪律：QuickJS 是全方案唯一新依赖。

![图2：架构图 model → orchestrator → codemode host → bridge → executeToolCallAuthorized → tools](/images/fx-codemode/architecture.png)

## 最难的一关：嵌套调用怎么过权限

动手前的 spike 本来要回答一个吓人的问题：工具执行到一半回调 Zig 再走一轮权限准入，准入需要的 Input 得借用 orchestrator 的运行时状态（worker、评审上下文、prompter、调用身份），这条路径当时不存在。如果答案是「要重排 orchestrator 状态机」，方案就地终止。

结果 spike 把原问题推翻了（来源：.agents/codemode-plan.md §0.1，T-6，2026-11-06）：执行帧本来就持有完整的 tool_runtime.Context，`ctx.admissionInput()`（tool_runtime.zig:267）现场就能造出合法 Input，16 个字段里执行期唯一缺的 permission_review_turn 有现成先例，MCP bridge 早就在工具执行期构造过完整评审上下文。判定 GO，而且不用引入第二条执行路径。

线程模型也在这一步核实了。沙箱在专用线程跑，QuickJS runtime 单线程使用；担心过的 prompter 与终端采集跨线程问题，spike 逐个调用链核实：prompter 挂 worker_mutex 加条件变量，终端采集是 2ms 轮询，都没有线程亲和性，沙箱线程可以直接阻塞调用。单 pending 权限槽也天然满足：脚本执行期间 worker 线程必然阻塞在外层调用里，不会同时冒出两个权限请求（来源：.agents/codemode-plan.md §0.1）。

剩下的设计决策三个：

- **归因**：ReviewOrigin 是封闭枚举，加一个 `.codemode` 变体，评审视图走 contextual。脚本周围的文本是不受信证据，和 dynamic tools、subagent 同一侧，不能因为「是脚本调的」就降级评审。
- **行号**：脚本行号编码进嵌套调用的 ToolCall.id（`<parent>:cm<seq>:L<line>`）。id 全链路是不透明字符串，零契约改动，权限弹窗和日志里能直接看到脚本第几行发起的调用。
- **取消**：接 worker_cancel_requested 同一个原子位。取消发生时进行中的子调用等待完成、结果丢弃，不放大副作用也不假装成功，这和直接调用的既有契约一致。

这一节最值钱的一句话：权限路径只有一条。脚本里的调用和模型直接调用走的是同一个入口 `executeToolCallAuthorized`（bridge.zig:166），e2e 断言两条路径的评审载荷除了归因和调用 id 逐字节一致。我做这个功能最怕的就是「脚本拿到免审通道」，那是安全倒退，所以这条一致性测试是整个项目里我盯得最紧的。

## 预算与失败语义：数字全部上桌

沙箱是个资源黑洞的潜在入口，预算必须事先钉死。表 1 是当前实现的全部硬数字：

| 项 | 默认值 | 可调范围 | 来源 |
|---|---|---|---|
| 脚本墙钟预算 | 30s | @options timeout_ms 1s–300s | host.zig:22、31-33 |
| QuickJS 内存 | 64MB | 宿主配置 | host.zig:21 |
| text/console 捕获缓冲 | 1MiB | @options max_output_tokens（4B/token，帽 262144） | host.zig:28、36-37 |
| 单条 shell 结果脚本内预算 | 1MiB | 超限留头尾各半 | src/tools/codemode/shell.zig:7 |
| 模型侧内联阈值 | 16KiB | 超限头尾保留 + read_tool_result 回读 | result_store.zig:15、ISSUE-12 |
| store 单值 / 总量 | 256KB / 1MB | 宿主层强制 | store.zig:23-24 |
| 工具目录（derived surface） | 16KiB | context_limits.codemode_catalog_bytes | context_limits.zig:32 |
| 超时后宽限排空 | 500ms | 常量 | host.zig:34 |

表 1：codemode 预算表。

预算定下来只是开始，真实使用教会我的是失败语义。超时占了我全部 codemode 失败的 49.7%（下一节有分布），而最初的超时失败体只有一行 headline：脚本死了，不知道死在哪、跑了多久、已经干成了什么。修这个问题花了三轮：

- **ISSUE-23**：失败体加上耗时回显、预算来源（默认还是 @options）、部分输出和已执行嵌套调用清单。模型至少能知道「grep 已经跑完了，卡在第二条命令」。
- **ISSUE-28**：嵌套命令的超时阈值一旦严格小于 yield_time，managed execution 的 yield/timeout 双线程竞争会让结局非确定。修法是 yield_waits_for_timeout 标志，timeout 小于等于 yield 时等待超时杀，不用 min 钳制（来源：MEMORY.md 2026-11-20）。
- **ISSUE-33**：命令实际已完成仍被判超时失败，以及 @options 上限与提示文案自相矛盾，两处收口。

今天一条超时失败体长这样：headline 报耗时与预算来源，接着是脚本自己的 text/console 部分输出，最后是已执行嵌套调用清单，每条带名字、结局、耗时，32 条封顶（来源：codemode_tool.zig:115-148、tool_runtime.zig:1297-1307）。模型拿到这些才谈得上自救：换 @options、换命令、或者干脆放弃这条路径。失败体不是日志，是给模型的下一轮输入。

部分输出也有自己的预算决策。T-23b 方案给每个脚本调用一个 1KiB 固定摘录槽，存最近一次已返回嵌套调用的输出摘录（来源：fx 仓库 plan.md，帽常量 max_nested_output_excerpt_bytes = 1024B）。定 1KiB 的依据是语料：命令落盘输出 p50 645B、p90 4211B，1KiB 保住中位全量，定位是「认出卡在哪一步」，全文靠句柄回读。逐条 400B 的方案被否决，32 条封顶乘 400B 会把宿主状态撑大 12.8KiB，摘录槽只留一份。

还有两个容易忽略的语义：QuickJS 的 deadline 只在 JS 指令之间触发，永远不会跳过在飞的嵌套调用，所以被杀的命令也有快照；输出超限走头尾保留，全文落盘，模型拿 read_tool_result 按字节区间回读（ISSUE-12）。我自己就撞过 16KiB 内联阈值：语料加到每文件 2000 行时，单条 grep 输出 53,896B，模型侧只拿到 16,384B 加一个省略标记，全文在落盘句柄里。

## 跨调用状态：store/load 为什么是新事件 kind

脚本之间要传点状态：游标、ID、上一次的摘要。最顺手的路是扩展现有的 set 事件，给 SetKey 枚举加一个 codemode_store 键。方案最初就是这么定的（路线 A），然后被测试钉死了。

SetKey 是封闭枚举（schema.zig:114），set 事件的 key 解析失败直接 error.Corrupt。这意味着老版本 fx 打开含新键的会话，不是丢掉不认识的状态自愈，而是整个会话报 InvalidSessionFormat 打不开（session.zig，T-6 的 14/14 测试逐条验证了这条路径）。我的 dev 和 stable 双通道共用 profile，这不是理论风险，是必踩的雷。

顺带一提，更早还否决过把状态藏进 item 的路线 B：item 的语义是模型可见的会话内容件，藏状态进去等于造一条压缩、分叉、回放都不认的暗渠，而且 item 必须挂回合，没有回合外写入的保证。set 才是设计好的宿主状态通道，任何时刻可写、新值覆盖旧值（来源：.agents/codemode-plan.md §6）。store/load 要的正是回合外可写。

重拍板走路线 C：新增专用事件 kind `codemode_store`（schema.zig:31）。前向兼容全路径成立（来源：.agents/codemode-plan.md §6，G4 决策，2026-11-06）：

- 事件行：老 fx 对未知 kind 直接跳过，只标记 clean_exit=false，resume 不受影响。
- 快照：fold.decodeState 只按名取已知字段，新快照里的新字段被老 fx 静默忽略。
- 老 fx 丢 store 值是合理降级，它本来就不认识 codemode。

事件 body 形态是 {scope, value}，scope 预留命名空间，newest-wins 语义与 set 一致，事件行带 CRC 与 seq 走既有 frame，不加第二写入路径。改动面和路线 A 相当：Kind 枚举、parseBody、fold 状态、TLA+ 模型同步，TLC checker 过一遍。这一节是我全文最想分享的决策故事：「加个枚举值」看起来是最小改动，实际上把降级兼容变成了数据损坏。未知 kind 跳过是日志格式早就设计好的逃生通道，新状态走新 kind，才是顺着纹理切。

![图3：store 兼容决策，路线 A 的 Corrupt 路径 vs 路线 C 的跳过路径](/images/fx-codemode/store-compat.png)

## 收益账本：实测、规模与成本

先给实测。我设计了一个最小可复现对照：同一个任务（统计三个文件里含 TODO 的行数，每文件 600 行、其中 300 行含 TODO），用假网关喂固定的模型响应，真 fx 二进制（commit c553300ae）执行，隔离 HOME 加 `experimental.codemode: true`，跑 `fx ask --quiet --json`。direct 模式让模型逐次调 shell 工具，codemode 模式给模型第 2 节那段脚本。回合数数网关收到的请求数，体积数请求体里 tool-result 的字节数（实验脚本与原始输出存于博客仓库 tmp/fx-exp/，2026-11-26 实测）：

| 指标 | direct 逐调用 | codemode 单脚本 |
|---|---|---|
| 模型回合数 | 4（3 次 shell + 1 次总结） | 2（1 次脚本 + 1 次总结） |
| 工具结果进上下文 | 48,561 B（16,287 + 15,987 + 16,287） | 124 B |
| 最后一轮请求体 | 72,932 B | 23,262 B |
| 任务结果 | 正确（900） | 正确（900） |

表 2：同一任务的 direct vs codemode 实测对照。

对照的公平性我检查过：direct 模式三条结果都低于 16KiB 内联阈值，没有触发截断，两边拿到的是同样完整的 grep 输出，差别只在输出进不进上下文。

中间结果体积差约 392 倍，回合数从 N+1 压到 2（N 是工具调用次数，文件再多也一样）。最后一轮请求体只差 3.1 倍，因为两边都背着约 23KB 的系统提示加工具声明，这是固定开销，也提醒我 codemode 自己的描述和工具目录同样在吃 token，不是免费午餐。诚实声明：假网关意味着模型响应是脚本化的，这个实验测的是机制收益，不是模型行为收益；单任务样本，外推到真实工作负载要靠下面的语料。

固定开销那 23KB 里也有 codemode 自己的一份：工具描述内联的声明共享约 3000 tokens 预算，MCP 工具默认 deferred 不进描述（来源：.agents/codemode-plan.md §5）。编排层省下的中间结果，要拿声明预算去换，这笔交换在工具少的时候不一定划算，工具多、中间结果大的时候才稳赚。

真实使用规模（来源：fx 仓库 plan.md「数据基线」节，扫描 2026-11-18，记录级去重）：101 个会话、2610 条 tool_call、2062 条 codemode 结果。也就是说我日常的工具调用绝大多数已经走脚本编排，这不是演示功能。

成本也要上桌。QuickJS 以 ReleaseSmall 同口径实测增量 622,592B，约 608KB（commit 4cafddd7，.agents/codemode-plan.md §0.2）。裁剪实验全无效：dead_strip 零收益，-Oz 省 8 字节。原方案定的尺寸门是 450KB，上游发布余量约 548KB，608KB 两个都顶破了。处置：自用 fork 不受发布管线约束，尺寸门降级为记录项，Bellard/Duktape 替代轨取消。这意味着 codemode 短期内是 fork 先行功能，上游化要先解决 608KB 的账。

失败分布同样来自语料（298 条 codemode failure）：

| 失败类别 | 条数 | 占比 |
|---|---|---|
| Timeout | 148 | 49.7% |
| ScriptError | 133 | 44.6% |
| 缺 script 字段 | 12 | 4.0% |
| @options 越界拒绝 | 5 | 1.7% |

表 3：codemode 失败类别分布（plan.md 语料，扫描 2026-11-18）。

语料里还有两个细节值得记：148 条超时里只有 3 条在脚本首行声明了 @options（全是 120000），另有 5 条因为声明越界被直接拒绝（180000 两次、300000 两次等），脚本一行没跑（来源：plan.md）。模型不是不会用预算，是大多数时候根本想不起来用，这直接决定了第 7 节的治理方向。

两个口径警告我照抄方案原文：嵌套摘要节 11-13 才合入，「今天的行为」只能看之后的 25 条超时样本，全窗 148 条只用于分布趋势；duration_ms 含准入与人工权限等待，时长分位数是上界，不是命令运行时长。

## 上线后被真实使用打脸的五轮治理

功能合入只是开始。我定期扫会话记录，下面五轮治理全部来自真实失败样本，表 4 是问题到修法的对照：

| 轮次 | 真实失败 | 修法 | 来源 |
|---|---|---|---|
| 1 | 模型把 arguments_json 的 JSON 转义带进脚本源码，836 次调用 71 次失败里本类 57 次，约 80% | SyntaxError 定向改写提示，指出转义泄漏 | ISSUE-31 |
| 2 | 猜工具名、require、顶层 return，报错提示合入后仍复发 9 次 | 三则坑前置进 codemode 工具描述 | ISSUE-34 |
| 3 | 描述 1172B 超模型侧 1024B 帽被截断，真相句和收尾规则到不了模型 | 压缩描述 + darwin/linux 双平台 byte-exact 哈希钉 | ISSUE-36 |
| 4 | tools.run_command("ls") 传字符串不传对象 | 字符串参数自动包装为对象 | ISSUE-32 |
| 5 | run_script 的 python3 解释器硬编码，venv/conda 用户没法用 | experimental.codemode_python 可配置，仅 profile 不进仓库文件 | ISSUE-35 |

表 4：五轮治理对照。

第 3 轮还有个测试教训：1024 字节帽的测试原本漏检了 gated_all 出网路径，评审才发现描述在另一条路上照样被截（ISSUE-36 F-2）。帽测试只测一条路径等于没测，这和「测试必须证明真的进入新代码路径」是同一条纪律。

第 2 轮和第 3 轮连起来看最有意思。报错侧的提示治不住误用，因为模型不先踩坑就看不到提示，所以要前置到工具描述；而描述本身是稀缺预算，模型侧有 1024 字节的硬帽（model_tool_schema.zig:4），多写一句就有另一句被截掉。我最后给描述上了双平台哈希钉测试，改一个字节都要重钉。工具描述不是文档，是受预算约束的接口。

## 已知局限与没选的路

没选的路，逐条给理由：

- **逐条 400B 部分输出、扩大宿主捕获缓冲**：T-23b 否决，32 条乘 400B 撑大宿主状态，1KiB 单摘录槽够用，全文有落盘句柄。
- **Bellard 原版 QuickJS / Duktape**：前者更新停滞，后者省不下够用的尺寸，替代轨在 608KB 实测后取消。
- **沙箱内模型 API、多线程脚本、用户自定义脚本生态**：方案第一页的非目标，fx 没有分类器目录，QuickJS runtime 单线程使用，脚本面越小心越安全。

尺寸账再补一句：608KB 约占当前候选二进制（5.98MiB）的一成，启动 2ms 预算靠惰性初始化守住，模型不真正调 codemode，沙箱一个字节都不分配。

已知局限：单线程 QuickJS，脚本里 await 再多的工具也是串行过准入；默认 30s 对长命令偏短，但语料里 148 条超时只有 3 条声明了 @options，数据不支持改默认，支持的是把 @options 的用法写进失败提示；模型自主压缩的范围语法永久出局，最小形只留无参数 compress()，这是 ISSUE-27 P2 双 worker 论证后的裁决，重开条件写死在 MEMORY.md（manual 压缩 ≥5 session、overflow ≥1、search 使用率 ≥1%）。

沙箱逃逸也要说清楚：准入守的是正常脚本面，一旦发生内存安全逃逸，等于在 fx 进程内以用户身份任意执行代码。压这个面靠三件事：最小绑定面、vendor 版本锁定、快速跟进上游安全补丁（来源：.agents/codemode-plan.md §8 风险 3）。

## 怎么用

在 `~/.fx/settings.json` 里开 profile 专属开关（默认关）：

```json
{
  "experimental": {
    "codemode": true
  }
}
```

然后给模型一段脚本任务。第 2 节那段「三次 grep 合成一段脚本」就是可抄的模式：循环里调工具、中间结果留在脚本变量里、`text()` 只交摘要。长任务在第一行声明预算：

```javascript
// @options: {"timeout_ms": 120000}
store("cursor", { file: "alpha.txt", line: 42 });
const c = load("cursor");
text("cursor=" + JSON.stringify(c));
```

需要写工具时再开 derived surface，它额外提供 run_script 原语：language 选 shell 或 python，code 给源码、file 给大文件、intent 只进转录不执行，python 解释器用 experimental.codemode_python 指定（来源：ISSUE-35、bridge.zig canonicalRunScript）。headless 场景用 fx ask 入口，第 6 节的实测就是拿它跑的。

这段也是真机跑过的：@options 被接受，store/load 往返正确。跨会话的持久化走第 5 节的 codemode_store 事件（ISSUE-13 已落地）。工具实现和更多细节在 fork 仓库的 [README codemode 节](https://github.com/tt67wq/fx#codemode-experimental)。

什么时候该用，我的经验是两条都占才用：步骤在三步以上，且中间结果比最终答案大得多。只调一个工具、或者中间结果本来就要给模型看，直接调工具更快也更透明。

回到开头的账单：2610 次工具调用里 2062 次走了脚本，我的上下文里少了几百份 grep 全文和文件快照，多了几百行「TODO total: 900」这样的摘要。把编排搬进沙箱不是为了让 agent 更聪明，是为了让它别把草稿纸当成品交上来。

## FAQ

**codemode 和 MCP 是什么关系？** 不冲突。MCP 工具默认 deferred 不进描述，脚本可以用 searchTools 发现它们，嵌套调用照样走准入。codemode 是编排层，MCP 是工具来源之一。

**会绕过权限吗？** 不会。脚本内每次调用独立过既有准入，和直接调用同一个入口（bridge.zig:166），评审视图走 contextual，脚本周围文本按不受信证据处理。e2e 断言两条路径的评审载荷逐字节一致。

**为什么选 QuickJS，不是 Lua 或 Duktape？** 选型理由是 quickjs-ng 维护活跃、内存 API 完整、JS 是模型最熟的语言（来源：.agents/codemode-plan.md §3）。代价是 608KB 二进制增量，Bellard 原版更新停滞，替代轨在尺寸实测后取消。

**超时了怎么办？** 失败体带耗时、预算来源、1KiB 部分输出摘录和已执行调用清单。长任务用 @options 声明 timeout_ms（上限 300s），更长的命令让 shell 先 yield、脚本结束、下一轮再查，别在脚本里空转轮询。
