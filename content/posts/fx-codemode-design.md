---
title: "2610 次工具调用教会我的事：把 agent 的工具编排搬进 JS 沙箱"
date: 2026-11-26T11:30:00+08:00
slug: fx-codemode-design
summary: 我的 coding agent 近 30 天跑了 2610 次工具调用，其中 2062 条结果来自同一个工具：codemode。让模型写一段 JS 在 QuickJS 沙箱里编排工具，N 个回合压成 1 个，中间结果不进上下文。这篇讲它的设计、踩坑和账本。
tags: ["AI", "agent", "fx", "QuickJS", "工具编排"]
description: "以 fx fork 的 codemode 为例，讲清 code execution 式工具编排：嵌套权限、预算与失败语义、store 的前向兼容决策，附真机实测的回合与体积对照。"
ShowToc: true
comments: false
cover:
  image: "/images/fx-codemode/cover.png"
  alt: "终端里的 JS 沙箱编排工具流"
---

近 30 天，我的 coding agent 在 101 个会话里发起了 2610 次工具调用，其中 **2062 条**结果来自同一个工具：codemode。它做的事情一句话能说清：模型不再一次调一个工具，而是写一段 JavaScript，在 QuickJS 沙箱里把一串工具调用编排完，N 个模型回合压成 1 个，只有最终输出进上下文。
<span class="src-note">来源：fx 仓库 plan.md「数据基线」节，扫描时刻 2026-11-18 19:22</span>

这篇记录这个功能怎么设计、我怎么被真实使用打脸、以及最后算出来的账。所有数字都有出处，所有示例脚本都在真机跑通过。

## 工具调用的隐性账单

先说问题。你让 agent「grep 一下，再读三个文件，然后跑测试」，传统做法是 5 次以上的模型回合：每次工具调用都要等模型看完上一次的结果、再决定下一步。每个回合是一次完整的模型请求，延迟叠加不说，grep 出来的几百行、文件的全文，这些中间结果全部灌进上下文，后面的每一轮请求都要重新带上它们。

这笔账的坏处在于重复计费。上下文是累积的，第一回合 grep 出来的几百行，第二、第三、第四回合的请求都要原样再带一遍，中间结果**要付 N 次钱**。我每周扫一遍会话日志统计调用分布，2610 这个数字就是这么来的，扫的时候我最在意每条结果有多少字节最终进了模型上下文。

这类方案现在有个通用名字：code execution 或者 tool orchestration，让模型写代码来编排工具，而不是逐个发起工具调用。Cloudflare 在 [Code Mode](https://blog.cloudflare.com/code-mode/) 里给 agent 一个写 TypeScript 调 MCP 工具的沙箱，Anthropic 在 [Code execution with MCP](https://www.anthropic.com/research/code-execution-with-mcp) 里把工具变成代码 API，思路一致：中间结果留在执行环境里，模型只看摘要。我在自己的 fx fork（[tt67wq/fx](https://github.com/tt67wq/fx)，一个 Zig 写的终端 coding agent）里做了同样的事，下面按读者的疑问顺序讲，不按开发时间线。

![图1（示意）：direct 多回合 vs codemode 单回合](/images/fx-codemode/turns.png)

## 总体设计：一段 JS 能干什么

codemode 是一个内置工具，参数就是一段脚本。沙箱里只开几扇门：调工具、交最终输出、存跨脚本的状态、搜索更多工具，没有任何文件、网络之类的宿主能力。默认只暴露只读四件套——找文件、搜内容、读文件、跑命令；写工具要再开一个开关才加上。

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

三次 grep 的完整输出（每个文件约 16KB）只在脚本里流动，模型收到的是 `TODO total: 900` 加一份嵌套调用清单，一共 **124 字节**。这个双层 JSON.parse 不是笔误，是当前二进制的真实返回形状，我先在沙箱里打印了 `typeof` 和字段名才敢这么写。
<span class="src-note">返回形状出处：当前二进制 commit c553300ae</span>

工具多了之后，「让模型知道有哪些工具」本身也是预算。默认四件套的说明直接写进工具描述；开了写工具之后，工具目录受 16KiB 帽约束，排序是核心四件套永远在列，然后写工具，然后其余，装不下就丢后面的条目并附一份省略清单。

目录之外的工具靠搜索找：名字命中得分最高，其次参数，再次描述，几行打分逻辑，没有引入任何检索库。名字不认识时给相近名字建议。

脚本里的失败语义也定死了：

- 参数错误、执行失败：脚本拿到一个能自己 catch 的错误。
- 权限被拒：不是异常，是一份带理由的结果，脚本能直接分支。
- 脚本结束时还没回来的调用：直接取消。

<span class="src-note">来源：bridge.zig deniedResult 注释；.agents/codemode-plan.md §4</span>

调用也可以并行发起（Promise.allSettled）。README 里还有一句我特意保留的警告：只包一个工具调用的脚本比直接调工具更慢，codemode 不是所有调用的默认包装纸。

设计上有四条硬约束，写在方案第一页：

1. 权限优先：脚本内每次工具调用独立过既有审查，没有免审通道。
2. 单文件交付不变，沙箱引擎直接编进 fx。
3. 启动预算 2ms，沙箱必须用到才初始化，不用不付费。
4. 依赖纪律：沙箱引擎是全方案唯一新依赖。

![图2：架构图 model → orchestrator → codemode host → bridge → 授权执行入口 → tools](/images/fx-codemode/architecture.png)

[看动画版架构（mp4）](/images/fx-codemode/architecture.mp4)

<details class="impl-note"><summary>实现细节</summary>

沙箱里注册的全局只有白名单：`tools.*` 调工具、`text()` 交最终输出、`store()/load()` 存跨调用状态、`searchTools/describeTool` 发现工具，没有任何 std/os 宿主能力。默认只暴露只读四件套 `glob_files`、`grep_files`、`read_file`、`run_command`；打开 `experimental.codemode_derived_surface` 才加上 write_file、edit_file 等写工具。
<span class="src-note">来源：.agents/codemode-plan.md §3；README.md codemode 节</span>

默认四件套的声明直接内联进工具描述；derived surface 的工具目录受 16KiB 预算约束（context_limits.codemode_catalog_bytes），排序是核心四件套永远在列，然后写工具，然后其余，触发预算就丢后面的条目并给一份省略清单。
<span class="src-note">来源：README.md codemode 节</span>

目录之外的工具靠 searchTools 找，实现是自实现的加权 token 打分：名字命中 3 分、参数命中 2 分、描述命中 1 分（discovery.zig:82-84），没有引入任何检索库；describeTool 返回单个工具的完整 schema，名字不认识时给相近名字建议。

四条硬约束原文：1. permission-first：脚本内每次工具调用独立过既有准入，没有免审通道。2. 单二进制交付不变，QuickJS 直接编进 fx。3. 启动预算 2ms，沙箱必须惰性初始化，不用不付费。4. 依赖纪律：QuickJS 是全方案唯一新依赖。
<span class="src-note">来源：.agents/codemode-plan.md §0</span>

</details>

## 最难的一关：嵌套调用怎么过权限

动手前我最怕一个问题：**脚本里发起的工具调用，会不会绕过权限弹窗？**模型直接调工具要过审，换成脚本调就免审的话，是安全倒退，这功能宁可不做。所以我先做了个最小验证，只回答这一个问题。

答案是好消息。权限弹窗要的现场信息（谁在调、调什么、评审看什么），工具执行期间本来就齐全。MCP 工具早就走通过同样的路。不用改造主流程，也不用开第二条执行通道。验证通过，方案继续。

剩下三个设计决策，都只为同一件事：**脚本里的调用和直接调用待遇完全一样**。

- 弹窗照常弹，还能看出调用是脚本第几行发起的。评审的上下文证据一样不少。
- 脚本周围的文本按不受信内容处理，不能因为「是脚本调的」就放松审查。
- 用户按取消时行为和直接调用一致：进行中的等它做完、结果丢弃，不假装成功。

<mark>权限路径只有一条</mark>。脚本调用和模型直接调用走同一个入口。端到端测试验证过：两条路径送到权限弹窗的内容，除归因标记和调用编号外**逐字节一致**。这是整个项目里我盯得最紧的一条测试。

<details class="impl-note"><summary>实现细节</summary>

动手前的 spike 本来要回答一个吓人的问题：工具执行到一半回调 Zig 再走一轮权限准入，准入需要的 Input 得借用 orchestrator 的运行时状态（worker、评审上下文、prompter、调用身份），这条路径当时不存在。如果答案是「要重排 orchestrator 状态机」，方案就地终止。

结果 spike 把原问题推翻了：执行帧本来就持有完整的 tool_runtime.Context，`ctx.admissionInput()`（tool_runtime.zig:267）现场就能造出合法 Input，16 个字段里执行期唯一缺的 permission_review_turn 有现成先例，MCP bridge 早就在工具执行期构造过完整评审上下文。判定 GO，而且不用引入第二条执行路径。
<span class="src-note">来源：.agents/codemode-plan.md §0.1，T-6，2026-11-06</span>

线程模型也在这一步核实了。沙箱在专用线程跑，QuickJS runtime 单线程使用；担心过的 prompter 与终端采集跨线程问题，spike 逐个调用链核实：prompter 挂 worker_mutex 加条件变量，终端采集是 2ms 轮询，都没有线程亲和性，沙箱线程可以直接阻塞调用。单 pending 权限槽也天然满足：脚本执行期间 worker 线程必然阻塞在外层调用里，不会同时冒出两个权限请求。
<span class="src-note">来源：.agents/codemode-plan.md §0.1</span>

剩下的设计决策三个：

- 归因：ReviewOrigin 是封闭枚举，加一个 `.codemode` 变体，评审视图走 contextual（评审弹窗按调用现场展示上下文证据）。脚本周围的文本是不受信证据，和 dynamic tools、subagent 同一侧，不能因为「是脚本调的」就降级评审。
- 行号：脚本行号编码进嵌套调用的 ToolCall.id（`<parent>:cm<seq>:L<line>`）。id 全链路是不透明字符串，零契约改动，权限弹窗和日志里能直接看到脚本第几行发起的调用。
- 取消：接 worker_cancel_requested 同一个原子位。取消发生时进行中的子调用等待完成、结果丢弃，不放大副作用也不假装成功，这和直接调用的既有契约一致。

脚本里的调用和模型直接调用走的是同一个入口 `executeToolCallAuthorized`（bridge.zig:166），e2e 断言两条路径的评审载荷除了归因和调用 id 逐字节一致。我做这个功能最怕的就是「脚本拿到免审通道」，那是安全倒退，所以这条一致性测试是整个项目里我盯得最紧的。

</details>

## 预算与失败语义：数字全部上桌

沙箱是个资源黑洞的潜在入口，预算必须事先钉死。表 1 是当前实现的全部硬数字：

| 项 | 默认值 | 可调范围 | 来源 |
|---|---|---|---|
| 脚本墙钟预算 | 30s | @options（脚本首行预算声明）timeout_ms 1s–300s | host.zig:22、31-33 |
| QuickJS 内存 | 64MB | 宿主配置 | host.zig:21 |
| text/console 捕获缓冲 | 1MiB | @options max_output_tokens（4B/token，帽 262144） | host.zig:28、37 |
| 单条 shell 结果脚本内预算 | 1MiB | 超限留头尾各半 | src/tools/codemode/shell.zig:7 |
| 模型侧内联阈值 | 16KiB | 超限头尾保留 + read_tool_result 回读 | result_store.zig:15、ISSUE-12 |
| store 单值 / 总量 | 256KB / 1MB | 宿主层强制 | store.zig:23-24 |
| 工具目录（derived surface） | 16KiB | context_limits.codemode_catalog_bytes | src/core/config/context_limits.zig:32 |
| 超时后宽限排空 | 500ms | 常量 | host.zig:34 |

表 1：codemode 预算表。表里的回读工具是落盘句柄机制：超限输出全文落盘，模型拿句柄按字节区间回读。

预算定下来只是开始，真实使用教会我的是失败语义。超时占了我全部 codemode 失败的 **49.7%**（第 6 节有分布），而最初的超时失败体只有一行标题：脚本死了，不知道死在哪、跑了多久、已经干成了什么。修这个问题花了三轮：

- 第一轮，把死讯扩成完整现场。失败体加上耗时、预算来源（默认还是脚本自己声明的）、脚本已产出的部分输出和已执行调用清单。模型至少能知道「grep 已经跑完了，卡在第二条命令」。
- 第二轮，两个计时器打架，修成超时说了算。长命令有个「到点先返回句柄、脚本结束、下一轮再查结果」的机制；脚本又能给嵌套命令声明更短的超时。两个计时器一旦接近，谁先触发原先看线程竞争脸色，同一份脚本两次跑可能两种结局。修法：声明的超时不大于句柄返回时间时，就老实等超时来杀，不再做聪明钳制。
- 第三轮，两处收口。命令实际已完成仍被判超时失败；脚本可声明的预算上限与提示文案自相矛盾。一起修掉。

今天一条超时失败体长这样：首行报耗时与预算来源，接着是脚本自己的部分输出，最后是已执行调用清单，每条带名字、结局、耗时，32 条封顶。模型拿到这些才谈得上自救：加大预算、换命令、或者干脆放弃这条路径。<mark>失败体不是日志，是给模型的下一轮输入</mark>。
<span class="src-note">来源：codemode_tool.zig:115-148、tool_runtime.zig:1297-1307</span>

部分输出也有自己的预算决策。每个脚本调用给一个 1KiB 固定摘录槽，存最近一次已返回调用的输出摘录。定 1KiB 的依据是语料：命令落盘输出中位数 645B、九成分位 4211B，1KiB 保住中位全量，定位是「认出卡在哪一步」，全文靠句柄回读。逐条 400B 的方案被否决：32 条封顶乘 400B 会把宿主状态撑大 12.5KiB，摘录槽只留一份。

还有两个容易忽略的语义。一，沙箱超时只在 JS 指令之间生效，永远不会跳过在飞的工具调用，所以被杀的命令也有快照。二，输出超限保留头尾，全文落盘，模型按字节区间回读。我自己就撞过 16KiB 内联阈值：语料加大后单条 grep 输出远超 16KiB，模型侧只拿到 16,384B 加一个省略标记，全文在落盘句柄里。

<details class="impl-note"><summary>实现细节</summary>

三轮修复原文：

- ISSUE-23：失败体加上耗时回显、预算来源（默认还是 @options）、部分输出和已执行嵌套调用清单。模型至少能知道「grep 已经跑完了，卡在第二条命令」。
- ISSUE-28：嵌套命令的超时阈值一旦严格小于 yield_time，managed execution 的 yield/timeout 双线程竞争会让结局非确定。修法是 yield_waits_for_timeout 标志，timeout 小于等于 yield 时等待超时杀，不用 min 钳制。yield 说白了就是：长命令到点先返回句柄、脚本结束、下一轮再查结果。
  <span class="src-note">来源：MEMORY.md 2026-11-20</span>
- ISSUE-33：命令实际已完成仍被判超时失败，以及 @options 上限与提示文案自相矛盾，两处收口。

部分输出也有自己的预算决策。T-23b 方案给每个脚本调用一个 1KiB 固定摘录槽，存最近一次已返回嵌套调用的输出摘录。定 1KiB 的依据是语料：命令落盘输出 p50 645B、p90 4211B，1KiB 保住中位全量，定位是「认出卡在哪一步」，全文靠句柄回读。逐条 400B 的方案被否决，32 条封顶乘 400B 会把宿主状态撑大 12.5KiB，摘录槽只留一份。
<span class="src-note">来源：fx 仓库 plan.md，帽常量 max_nested_output_excerpt_bytes = 1024B</span>

还有两个容易忽略的语义：QuickJS 的 deadline 只在 JS 指令之间触发，永远不会跳过在飞的嵌套调用，所以被杀的命令也有快照；输出超限走头尾保留，全文落盘，模型拿 read_tool_result 按字节区间回读（ISSUE-12）。我自己就撞过 16KiB 内联阈值：语料加大后单条 grep 输出远超 16KiB，模型侧只拿到 16,384B 加一个省略标记，全文在落盘句柄里（阈值出处：result_store.zig:15）。

</details>

## 跨调用状态：store/load 为什么是新事件 kind

脚本之间要传点状态：游标、ID、上一次的摘要。最顺手的路是塞进既有的宿主状态事件，加个新键就行。方案最初就是这么定的，然后被测试钉死了。

问题出在老版本对新键的态度。打个比方：给旧抽屉加一个新标签，结果整个柜子锁死；新开一个抽屉，老版本不认识就跳过，柜子照常打开。既有状态事件用的是封闭键表，遇到不认识的键直接判「存档损坏」——老版本 fx 打开含新键的会话，整个会话打不开，不是丢一个键，是锁死整个柜子。我的 dev 和 stable 双通道共用 profile，这是必踩的雷。

顺带一提，更早还否决过一条暗路：把状态藏进模型可见的会话内容件。那等于造一条压缩、分叉、回放都不认的暗渠，而且内容件必须挂对话回合，没有回合外写入的保证。宿主状态通道才是设计好的正路：任何时刻可写、新值覆盖旧值。store/load 要的正是回合外可写。

重拍板走第三条路：给脚本状态新增一个专用事件类型。老版本对新类型的态度是「不认识就跳过」，前向兼容全路径成立：

- 事件行：老版本直接跳过不认识的类型，会话恢复不受影响。
- 快照：老版本只按名取它认识的字段，新字段被静默忽略。
- 老版本丢 store 值是合理降级，它本来就不认识 codemode。

新事件复用既有写入管线：校验和、序号、新值覆盖旧值全走老规矩，不加第二写入路径。改动面和「加个键」方案相当，形式化模型也同步更新、检查器过一遍。「加个枚举值」看起来是最小改动，**实际上把降级兼容变成了数据损坏**。「不认识就跳过」是日志格式早就设计好的逃生通道，新状态走新类型，才是顺着纹理切。

![图3：store 兼容决策，加旧键的损坏路径 vs 新类型的跳过路径](/images/fx-codemode/store-compat.png)

<details class="impl-note"><summary>实现细节</summary>

脚本之间要传点状态：游标、ID、上一次的摘要。最顺手的路是扩展现有的 set 事件，给 SetKey 枚举加一个 codemode_store 键。方案最初就是这么定的（路线 A），然后被测试钉死了。

SetKey 是封闭枚举（schema.zig:114），set 事件的 key 解析失败直接 error.Corrupt。这意味着老版本 fx 打开含新键的会话，整个会话报 InvalidSessionFormat 打不开，没有丢键自愈的降级路径（session.zig，T-6 的 14/14 测试逐条验证了这条路径）。我的 dev 和 stable 双通道共用 profile，这是必踩的雷。

顺带一提，更早还否决过把状态藏进 item 的路线 B：item 的语义是模型可见的会话内容件，藏状态进去等于造一条压缩、分叉、回放都不认的暗渠，而且 item 必须挂回合，没有回合外写入的保证。set 才是设计好的宿主状态通道，任何时刻可写、新值覆盖旧值。store/load 要的正是回合外可写。
<span class="src-note">来源：.agents/codemode-plan.md §6</span>

重拍板走路线 C：新增专用事件 kind `codemode_store`（schema.zig:31）。前向兼容全路径成立：

- 事件行：老 fx 对未知 kind 直接跳过，只标记 clean_exit=false，resume 不受影响。
- 快照：fold.decodeState 只按名取已知字段，新快照里的新字段被老 fx 静默忽略。
- 老 fx 丢 store 值是合理降级，它本来就不认识 codemode。

<span class="src-note">来源：.agents/codemode-plan.md §6，G4 决策，2026-11-06</span>

事件 body 形态是 {scope, value}，scope 预留命名空间，newest-wins 语义与 set 一致，事件行带 CRC 与 seq 走既有 frame，不加第二写入路径。改动面和路线 A 相当：Kind 枚举、parseBody、fold 状态、TLA+ 模型同步，TLC checker 过一遍。「加个枚举值」看起来是最小改动，实际上把降级兼容变成了数据损坏。未知 kind 跳过是日志格式早就设计好的逃生通道，新状态走新 kind，才是顺着纹理切。

</details>

## 收益账本：实测、规模与成本

先给实测。我设计了一个最小可复现对照：同一个任务（统计三个文件里含 TODO 的行数，每文件 600 行、其中 300 行含 TODO），真二进制加固定模型响应做对照。一边让模型逐次调工具，另一边给模型第 2 节那段脚本。回合数数网关收到的请求数，体积数请求体里工具结果的字节数（实验脚本与原始输出未随仓库公开，存档于作者会话记录，2026-11-26 实测）：

| 指标 | direct 逐调用 | codemode 单脚本 |
|---|---|---|
| 模型回合数 | 4（3 次 shell + 1 次总结） | 2（1 次脚本 + 1 次总结） |
| 工具结果进上下文 | 48,561 B（16,287 + 15,987 + 16,287） | 124 B |
| 最后一轮请求体 | 72,932 B | 23,262 B |
| 任务结果 | 正确（900） | 正确（900） |

表 2：同一任务的 direct vs codemode 实测对照。

对照的公平性我检查过：direct 模式三条结果都低于 16KiB 内联阈值，没有触发截断，两边拿到的是同样完整的 grep 输出，差别只在输出进不进上下文。

中间结果体积差**约 392 倍**，回合数从 N+1 压到 2（N 是工具调用次数，文件再多也一样）。最后一轮请求体只差约 3.1 倍，因为两边都背着约 23KB 的系统提示加工具声明，这是固定开销，也提醒我 codemode 自己的描述和工具目录同样在吃 token，不是免费午餐。诚实声明：假网关意味着模型响应是脚本化的，这个实验测的是机制收益，模型行为收益没测；单任务样本，外推到真实工作负载要靠下面的语料。

固定开销那 23KB 里也有 codemode 自己的一份：工具描述共享约 3000 tokens 预算，MCP 工具默认不进描述，搜到才出现。编排层省下的中间结果，要拿声明预算去换，这笔交换在工具少的时候不一定划算，工具多、中间结果大的时候才稳赚。

真实使用规模：101 个会话、2610 条工具调用、2062 条 codemode 结果。也就是说我日常的工具调用绝大多数已经走脚本编排，这不是演示功能。
<span class="src-note">来源：fx 仓库 plan.md「数据基线」节，扫描 2026-11-18，记录级去重</span>

尺寸成本也要算一笔。沙箱引擎按最小尺寸口径编译，实测增量 622,592B，**约 608KB**。裁剪实验全无效：链接器死代码剥离零收益，换更激进的尺寸优化省 8 字节。

原方案定的尺寸门是 450KB，上游发布余量约 548KB，608KB 两个都顶破了。处置：自用 fork 不受发布管线约束，尺寸门降级为记录项，Bellard/Duktape 替代轨取消。这意味着 codemode 短期内是 fork 先行功能，上游化要先解决 608KB 的账。

失败分布同样来自语料（298 条 codemode 失败）：

| 失败类别 | 条数 | 占比 |
|---|---|---|
| Timeout | 148 | 49.7% |
| ScriptError | 133 | 44.6% |
| 缺 script 字段 | 12 | 4.0% |
| @options 越界拒绝 | 5 | 1.7% |

表 3：codemode 失败类别分布（plan.md 语料，扫描 2026-11-18）。

语料里还有两个细节值得记：148 条超时里只有 3 条在脚本首行声明了 @options（全是 120000），另有 5 条因为声明越界被直接拒绝（180000 两次、300000 两次等），脚本一行没跑。模型会用预算，只是大多数时候根本想不起来用，这直接决定了第 7 节的治理方向。
<span class="src-note">来源：plan.md</span>

一句诚实声明：「今天的行为」只能看修复合入后的 25 条超时样本，全窗 148 条只用于分布趋势；时长统计含审查与人工权限等待，是上界，不是命令纯运行时长。

<details class="impl-note"><summary>实现细节</summary>

实测环境原文：用假网关喂固定的模型响应，真 fx 二进制（commit c553300ae）执行，隔离 HOME 加 `experimental.codemode: true`，跑 `fx ask --quiet --json`。direct 模式让模型逐次调 shell 工具，codemode 模式给模型第 2 节那段脚本。

固定开销那 23KB 里也有 codemode 自己的一份：工具描述内联的声明共享约 3000 tokens 预算，MCP 工具默认 deferred 不进描述。
<span class="src-note">来源：.agents/codemode-plan.md §5</span>

尺寸成本原文：QuickJS 以 ReleaseSmall 同口径实测增量 622,592B，约 608KB（commit 4cafddd7，.agents/codemode-plan.md §0.2）。裁剪实验全无效：dead_strip 零收益，-Oz 省 8 字节。

两个口径警告我照抄方案原文：plan.md 的嵌套摘要节 11-13（ISSUE-23 的已执行调用清单）才合入，「今天的行为」只能看之后的 25 条超时样本，全窗 148 条只用于分布趋势；duration_ms 含准入与人工权限等待，时长分位数是上界，不是命令运行时长。

</details>

## 上线后被真实使用打脸的五轮治理

功能合入后我定期扫会话记录，下面五轮治理全部来自真实失败样本，表 4 是问题到修法的对照：

| 轮次 | 真实失败 | 修法 |
|---|---|---|
| 1 | 模型把参数里的 JSON 转义带进脚本源码，836 次调用 71 次失败里本类 57 次，约 80% | 报错提示定向改写，直接点出转义泄漏进源码 |
| 2 | 猜工具名、用 require、顶层 return，报错提示合入后仍复发 9 次 | 三则坑前置进工具描述，让模型踩坑前就看到 |
| 3 | 描述 1172B 超模型侧 1024B 帽被截断，真相句和收尾规则到不了模型 | 压缩描述，再加双平台逐字节比对测试钉死 |
| 4 | 调命令工具传字符串不传对象 | 字符串参数自动包装为对象 |
| 5 | Python 脚本的解释器路径硬编码，虚拟环境用户没法用 | 解释器路径开放为个人配置，不进仓库文件 |

表 4：五轮治理对照。

第 3 轮还有个测试教训：帽测试只测一条路径等于没测。描述在另一条出网路径上照样被截，评审才发现。

第 2 轮和第 3 轮要连起来看。报错侧的提示治不住误用，因为模型不先踩坑就看不到提示，所以要前置到工具描述；而描述本身是稀缺预算，模型侧有 **1024 字节的硬帽**，多写一句就有另一句被截掉。我最后给描述上了双平台逐字节比对测试，改一个字节测试就红。<mark>工具描述不是文档，是受预算约束的接口</mark>。

<details class="impl-note"><summary>实现细节</summary>

治理表原文（含来源编号）：

| 轮次 | 真实失败 | 修法 | 来源 |
|---|---|---|---|
| 1 | 模型把 arguments_json 的 JSON 转义带进脚本源码，836 次调用 71 次失败里本类 57 次，约 80% | SyntaxError 定向改写提示，指出转义泄漏 | ISSUE-31 |
| 2 | 猜工具名、require、顶层 return，报错提示合入后仍复发 9 次 | 三则坑前置进 codemode 工具描述 | ISSUE-34 |
| 3 | 描述 1172B 超模型侧 1024B 帽被截断，真相句和收尾规则到不了模型 | 压缩描述 + darwin/linux 双平台 byte-exact 哈希钉 | ISSUE-36 |
| 4 | tools.run_command("ls") 传字符串不传对象 | 字符串参数自动包装为对象 | ISSUE-32 |
| 5 | run_script 的 python3 解释器硬编码，venv/conda 用户没法用 | experimental.codemode_python 可配置，仅 profile 不进仓库文件 | ISSUE-35 |

第 3 轮还有个测试教训：1024 字节帽的测试原本漏检了 gated_all 出网路径，评审才发现描述在另一条路上照样被截（ISSUE-36 F-2）。帽测试只测一条路径等于没测，这和「测试必须证明真的进入新代码路径」是同一条纪律。

模型侧有 1024 字节的硬帽（model_tool_schema.zig:4）。我最后给描述上了双平台哈希钉测试，改一个字节都要重钉。

</details>

## 已知局限与没选的路

没选的路，逐条给理由：

- 逐条 400B 部分输出、扩大宿主捕获缓冲：否决，账见第 4 节。
- Bellard 原版 QuickJS / Duktape：前者更新停滞，后者省不下够用的尺寸，替代轨在 608KB 实测后取消。
- 沙箱内模型 API、多线程脚本、用户自定义脚本生态：方案第一页的非目标，fx 没有分类器目录，沙箱引擎单线程使用，脚本面越小心越安全。

尺寸账再补一句：608KB 约占当前候选二进制（5.98MiB）的一成，启动 2ms 预算靠惰性初始化守住，模型不真正调 codemode，沙箱一个字节都不分配。

已知局限：沙箱单线程，脚本里 await 再多的工具也是串行过审查；默认 30s 对长命令偏短，但语料里 148 条超时只有 3 条声明了预算，数据不支持改默认，支持的是把预算声明的用法写进失败提示；模型自主压缩的范围语法永久出局，最小形只留无参数 compress()，和 codemode 脚本面同属最小化决策：暴露面收得越小越安全。

沙箱逃逸也要说清楚：审查守的是正常脚本面，一旦发生内存安全逃逸，**等于在 fx 进程内以用户身份任意执行代码**。压这个面靠三件事：最小绑定面、沙箱引擎版本锁定、快速跟进上游安全补丁。
<span class="src-note">来源：.agents/codemode-plan.md §8 风险 3</span>

<details class="impl-note"><summary>实现细节</summary>

没选的路原文：逐条 400B 部分输出、扩大宿主捕获缓冲：T-23b 否决，账见第 4 节。沙箱内模型 API、多线程脚本、用户自定义脚本生态：方案第一页的非目标，fx 没有分类器目录，QuickJS runtime 单线程使用，脚本面越小心越安全。

</details>

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

需要写工具时再开那个写工具开关，它额外提供一个「跑脚本」原语：语言选 shell 或 python，给源码或大文件路径，还能附一句只进转录、不执行的意图说明；python 解释器路径可在个人配置里指定。命令行场景用 fx 的 ask 入口，第 6 节的实测就是拿它跑的。

这段也是真机跑过的：预算声明被接受，store/load 往返正确。跨会话的持久化走第 5 节的专用事件。工具实现和更多细节在 fork 仓库的 [README codemode 节](https://github.com/tt67wq/fx#codemode-experimental)。

什么时候该用，我的经验是**两条都占才用**：步骤在三步以上，且中间结果比最终答案大得多。只调一个工具、或者中间结果本来就要给模型看，直接调工具更快也更透明。

回到开头的账单：2610 条工具调用记录里 2062 条是 codemode 结果，我的上下文里少了几百份 grep 全文和文件快照，多了几百行「TODO total: 900」这样的摘要。把编排搬进沙箱不是为了让 agent 更聪明，是为了让它<mark>别把草稿纸当成品交上来</mark>。

<details class="impl-note"><summary>实现细节</summary>

需要写工具时再开 derived surface，它额外提供 run_script 原语：language 选 shell 或 python，code 给源码、file 给大文件、intent 只进转录不执行，python 解释器用 experimental.codemode_python 指定。headless 场景用 fx ask 入口，第 6 节的实测就是拿它跑的。
<span class="src-note">来源：ISSUE-35、bridge.zig canonicalRunScript</span>

跨会话的持久化走第 5 节的 codemode_store 事件（ISSUE-13 已落地）。

</details>

## FAQ

**codemode 和 MCP 是什么关系？** 不冲突。MCP 工具默认不进工具描述，脚本可以搜索发现它们，调用照样过审查。codemode 是编排层，MCP 是工具来源之一。

**会绕过权限吗？** 不会。脚本内每次调用独立过审查，和直接调用同一个入口，脚本周围文本按不受信内容处理。测试验证过两条路径送到权限弹窗的内容逐字节一致。

**为什么选 QuickJS，不是 Lua 或 Duktape？** 选型理由是 quickjs-ng 维护活跃、内存 API 完整、JS 是模型最熟的语言。代价是 608KB 二进制增量，Bellard 原版更新停滞，替代轨在尺寸实测后取消。
<span class="src-note">来源：.agents/codemode-plan.md §3</span>

**超时了怎么办？** 失败体带耗时、预算来源、1KiB 部分输出摘录和已执行调用清单，模型据此换打法。长任务在脚本首行声明预算（上限 300s）；更长的命令让它到点先返回句柄、脚本结束、下一轮再查结果，别在脚本里空转轮询。

<details class="impl-note"><summary>实现细节</summary>

MCP 工具默认 deferred 不进描述，脚本可以用 searchTools 发现它们，嵌套调用照样走准入。

脚本内每次调用独立过既有准入，和直接调用同一个入口（bridge.zig:166），评审视图走 contextual，脚本周围文本按不受信证据处理。e2e 断言两条路径的评审载荷逐字节一致。

长任务用 @options 声明 timeout_ms（上限 300s），更长的命令让 shell 先 yield、脚本结束、下一轮再查，别在脚本里空转轮询。

</details>
