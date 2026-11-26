# B-3 评审报告 — fx codemode 博客正文 + 配图

- 被审正文：blog-pi1 drafts/fx-codemode.md @ afe13cd（分支 blog-pi1）
- 被审配图：blog-pi2 static/images/fx-codemode/{architecture,turns,cover,store-compat}.png @ c1dd7c5（分支 blog-pi2）
- 评审人：blog-pi2 worker（B-3）
- 日期：2026-11-26

## Verdict: approve（附 3 条 minor，发布前建议处理但不阻塞）

四张 PNG 已逐张亲眼看；数字抽查 14 处（≥8 达标）；外链 4 条全部实测 200；代码块核对 fx 源码与实测数据。

---

## 一、看图结论（4/4 张亲眼检查）

| 图 | 结论 | 细节 |
|---|---|---|
| architecture.png | ✅ 合格 | 中文渲染正常无豆腐块；组件链 model → fx orchestrator → codemode host(QuickJS 专用线程) → bridge → executeToolCallAuthorized → tools 全部真名正确；计数 2,610 / 2,062 与 plan.md:29 一致，脚注明确标「真实扫描值；动画与速率为示意 (illustrative)」；session log 无溢出 |
| turns.png | ✅ 合格 | 左列 direct 5 回合 vs 右列 codemode 单回合，两列对比清晰；底部标「回合拆分为示意场景 (illustrative)；工具调用次数相同」——与正文第 6 节实测（实际 direct 4 回合 vs codemode 2 回合）不冲突，因为图讲的是概念场景且已标 illustrative；中文正常 |
| cover.png | ✅ 合格 | 16:9（1672×941），深色终端风 + monokai 绿/品红，模型→编排→沙箱→工具流向可读，无文字（适合做封面不与标题打架）；观感与博客代码块配色协调 |
| store-compat.png | ✅ 合格（见 minor #1） | 路线 A Corrupt vs 路线 C 跳过两列对比正确，中文渲染正常；决策逻辑与正文第 5 节叙述一致 |

## 二、数字抽查（14 处）

| # | 正文声明 | 出处核查 | 结果 |
|---|---|---|---|
| 1 | 101 会话 / 2610 tool_call / 2062 codemode 结果 | fx plan.md:29 逐字一致 | ✅ |
| 2 | 失败分布 298 条：Timeout 148 (49.7%) / ScriptError 133 (44.6%) / 缺 script 12 (4.0%) / 越界 5 (1.7%) | plan.md:30 逐字一致，百分比复算正确 | ✅ |
| 3 | 表2 direct 4 回合 / 48,561B (16,287+15,987+16,287) / 72,932B | results.json: modelTurns=4, perCallBytes g1/g2/g3 = 16287/15987/16287, lastRequestBodyBytes=72932 | ✅ |
| 4 | 表2 codemode 2 回合 / 124B / 23,262B | results.json 同上 | ✅ |
| 5 | 392 倍 / 3.1 倍 | 48561/124=391.6≈392 ✅；72932/23262=3.14≈3.1 ✅ | ✅ |
| 6 | QuickJS 增量 622,592B ≈ 608KB，dead_strip 0 收益、-Oz 省 8 字节，450KB 门、548KB 余量 | codemode-plan.md:56、:60、:18 逐字一致 | ✅ |
| 7 | host.zig 预算表：30s 默认、@options 1s–300s、捕获 1MiB、max_output_tokens 帽 262,144、宽限 500ms | src/tools/codemode/host.zig:21-38 全部吻合 | ✅ |
| 8 | shell 单条 1MiB（shell.zig:7）、目录 16KiB（context_limits） | shell.zig:7 ✅；src/core/config/context_limits.zig:32 ✅ | ✅ |
| 9 | discovery 打分 名3/参2/描1（discovery.zig:82-84） | 源码逐行一致 | ✅ |
| 10 | executeToolCallAuthorized 单一权限路径（bridge.zig:166） | bridge.zig:166 正是该调用 | ✅ |
| 11 | 148 条超时仅 3 条声明 @options(全 120000)；5 条越界被拒（180000×2、300000×2） | plan.md:147 逐字一致 | ✅ |
| 12 | 1KiB 摘录槽依据 p50 645B / p90 4211B | plan.md:111 逐字一致；tool_runtime.zig:1319 常量=1024 | ✅ |
| 13 | 结果行集 schema.zig:31 codemode_store；SetKey 封闭枚举 | src/core/session_manager/schema.zig:31 ✅（路径是 session_manager/ 非 session/，正文未写全路径，无碍） | ✅ |
| 14 | 「单条 grep 输出 53,896B，模型侧只拿到 16,384B」+ 出处 commit 4cafddd7 | 16KiB 内联阈值 ✅（result_store.zig:15，conductor 亦核）；但 53,896B 数字与 commit 4cafddd7 在 fx 仓库 git log / plan.md / issues/ 均未找到。outline TODO 本身也标了「复核出处」。数字机制合理（>16384 截断），但这两个出处无法溯源 | ⚠️ minor #2 |

另：正文说 fx 二进制 commit c553300ae —— git log 存在（"Add memory"）✅。

## 三、外链（4/4 实测）

| 链接 | 状态 |
|---|---|
| https://github.com/tt67wq/fx | 200 |
| https://github.com/tt67wq/fx#codemode-experimental | 200，README.md:7 标题 "## Codemode (experimental)"，GitHub 锚点 id 为 codemode-experimental，锚点有效 |
| https://blog.cloudflare.com/code-mode/ | 200 |
| https://www.anthropic.com/research/code-execution-with-mcp | 200 |

## 四、硬门逐条

| 门 | 判定 | 说明 |
|---|---|---|
| 开头直给问题/结论 | ✅ | 首段直接给 2610/2062 数字与一句话定义，无背景铺垫、无 hype |
| 结构按读者疑问 | ✅ | 小节顺序（账单→设计→权限→预算→store→收益→治理→局限→怎么用→FAQ）是读者疑问链，且作者明说不按时间线 |
| 取舍与失败尝试 | ✅ | 路线 A/B/C 决策故事、spike 推翻原问题、裁剪实验全无效、五轮治理打脸——这是全文最强的部分 |
| 性能声明带数字可溯源 | ✅(12/14) | 见第二节；两处出处缺失为 minor |
| 代码能跑 | ✅ | 第 2 节示例脚本与 results.json 实测输入一致（同构 TODO 统计），B-4 独立验收报告（blog-pi1 c55556d）亦确认真机通过；@options/store/load 片段与 ISSUE-35、codemode_store 语义一致 |
| 禁 AI 腔/hype 词 | ✅ | grep 赋能/不仅仅/值得一提/总而言之/深入探讨/seamless/delve/revolution 全零命中；无 Sentry 口吻残留；无排比堆砌 |
| 标题钩子 | ✅ | 数字钩子 + 痛点承诺，已定不改 |
| 诚实声明 | ✅ | 假网关=机制收益非模型行为收益、单任务样本、direct 无截断公平性检查、codemode 描述预算成本——反向声明齐全 |

## 五、文风

个人视角"我"贯穿，无术语堆砌（每个术语首次出现即给一句话解释：derived surface、摘录槽、头尾保留）。重复句式检查："这笔账"出现 2 次（隔 3 段，可接受）。句子长度节奏好，无三连排比。

## 六、图文一致性

正文 3 个图片占位路径 /images/fx-codemode/{turns,architecture,store-compat}.png 与 blog-pi2 static/images/fx-codemode/ 实际文件名逐一对应 ✅。cover.png 不在正文占位中（封面走 Hugo 配置/列表图，正文无引用，不算失配）。图 2 alt 文字里的组件链与图中实际组件一致。

## 七、Minor（不阻塞 approve，建议作者顺手改）

1. **store-compat.png 行号漂移 2 处**：图中 "SetKey 是封闭枚举 schema.zig:111" 实际在 session_manager/schema.zig:114；"fold.zig:398-413" 的 decodeState 实际在 420-456 行。语义都正确，纯行号过期。低优先级——博客里行号引用本就是快照，但如果在意可由 conductor 重渲 mermaid（源在 assets/fx-codemode/store-compat.mmd 一带）。
2. **一处数字出处无法溯源（正文第 4 节末）**：「单条 grep 输出 53,896B，模型侧只拿到 16,384B」及「commit 4cafddd7」。16KiB 阈值本身 ✅（result_store.zig:15），622,592B 主数字另有人证（codemode-plan.md:60），但 53,896B 这个单例和 4cafddd7 这个 hash 在 fx 仓库（git log --all、plan.md、issues/）找不到。要么补出处，要么删 hash 留数字改口"实测"。大纲 TODO 里本来就有"复核出处 commit 4cafddd7"一条，B-1 没闭环。
3. **turns.png 与正文实测数字的表面张力**：图写 direct 5 回合，正文表 2 实测 4 回合。图已标 illustrative 且正文未声称图=实测，不构成错误；若想零歧义，把图 alt 里加半句"示意"即可（可不动图）。

## 结论

approve。正文质量高于博客平均线：数字全部可溯源（除 1 处标注）、反向声明诚实、治理故事真实。配图四张亲眼看过全部合格。minor 三条发布前顺手处理即可。
