# B-8 Review — fx-codemode-design.md

**Verdict:** changes-requested
**被审 SHA:** a70c0dd（blog 仓库）
**核对 fx 仓库 commit:** a816eb87f（2026-11-26 20:18，注意：文章编写时基于 c553300ae，当前 HEAD 已前进 4 个 commit，下面列出差异时注明）
**评审日期:** 2026-11-27

---

## 审查维度总览

| 维度 | 结果 |
|------|------|
| 数字抽查（≥10 处） | 全部在源文件中找到对应，数值一致；1 处行号偏移、1 处路径需确认 |
| 实测数据（表 2） | 算术正确；实验数据目录缺失 — **blocker** |
| 失败分布（表 3） | 总数与占比算术正确 |
| JS 示例语法 | 两段均通过 `node --check` |
| 外链 | 三条均返回 200，无断链 |
| 图文路径 | 五个文件全部存在 |
| 技术叙述一致性 | 权限路径、store 兼容决策等核心论述与源码一致 |

---

## Blocker

### B1. 实验数据目录缺失（行 ~180）

**原文引用：** "实验脚本与原始输出存于博客仓库 tmp/fx-exp/，2026-11-26 实测"

**问题：** `/Users/admin/Project/blog/tmp/fx-exp/` 目录不存在。博客仓库 `tmp/` 下仅有 `fx-codemode-outline.md`，无 `fx-exp/` 子目录、无 `results.json`、无实验脚本。

**影响：** 表 2 的四个数字（48561 / 124 / 72932 / 23262）及 392 倍、3.1 倍的结论无法从声称的数据源独立复现。读者按文中指引进 `tmp/fx-exp/` 会扑空。

**建议改法：** 将实验脚本与 results.json 补提交到 `tmp/fx-exp/` 目录，或修改文中措辞，如实说明数据暂未公开。

---

## Major

（无）

---

## Minor

### M1. budget 表 host.zig 行号引用小幅偏移

**原文引用：** 表 1 中 "text/console 捕获缓冲" 行，来源列写 "host.zig:28、36-37"

**问题：** `max_options_output_tokens` 常量在当前 HEAD 位于 host.zig 第 37 行，第 36 行是它的注释。文章编写时基于 c553300ae，当时行号也可能一致。说 "36-37" 不够精确——读者 grep 第 36 行拿到的是注释而非常量。

**建议改法：** 改为 "host.zig:28（缓冲）、37（@options token 帽）" 或保留现状（非关键）。

### M2. "392 倍" 近似值说明缺失

**原文引用：** "中间结果体积差约 392 倍"

**问题：** 48561 / 124 = 391.62，称 "约 392 倍" 可接受，但文中紧邻的 "3.1 倍"（72932 / 23262 = 3.14）有 "只差" 前缀暗示精度。392 和 3.1 的取整策略不一致（一个向上取整，一个四舍五入）。

**建议改法：** 统一为 "约 392 倍" 和 "约 3.1 倍"，或在两处都保持相同近似精度。

### M3. 部分 ISSUE 引用无法独立核验

**原文引用：** ISSUE-12、ISSUE-13、ISSUE-23、ISSUE-27、ISSUE-28、ISSUE-31–36 等多处

**问题：** 这些引用指向 fx 仓库的内部 issue tracker，评审者无访问权限，无法验证文中对 issue 内容描述的准确性（例如 "ISSUE-23：失败体加上耗时回显"）。

**建议：** 非必须修改——技术博客引用内部 issue 是常见做法。若面向外部读者，可考虑在关键处加一句 issue 结论摘要，减少读者对不可访问链接的依赖。

---

## Nit

### N1. context_limits.zig 实际路径与预算表上下文的隐含路径不一致

**原文引用：** 表 1 最后一行 "context_limits.zig:32"

**问题：** `context_limits.zig` 在仓库中的实际路径是 `src/core/config/context_limits.zig`，而预算表前几行引用的 host.zig / shell.zig / store.zig 均在 `src/tools/codemode/` 下。读者按上下文推断可能去错目录。文章并未显式声明路径，不算事实错误，但可加上路径前缀避免踩坑。

**建议改法：** "src/core/config/context_limits.zig:32"（完整路径）。

### N2. 148 条超时中 @options 声明次数的小数点细节

**原文引用：** "148 条超时里只有 3 条在脚本首行声明了 @options"

**问题：** 该数字来自语料分析，无法从源码验证。若来源于 plan.md 的扫描记录，建议注明扫描时间窗口与去重方式（文中部分地方注了，此处未注）。

### N3. "61 次失败里本类 57 次，约 80%" 的精度

**原文引用：** 表 4 ISSUE-31 行 "836 次调用 71 次失败里本类 57 次，约 80%"

**问题：** 57/71 = 80.28%，"约 80%" 合理。但文中 "836 次调用" 与 "71 次失败" 的口径关系未完全交代（是同一窗口？已去重？），而表 3 的 298 条失败来自不同语料窗口。两处数字之间若口径不一致，读者对不上。

---

## 已验证无误的项目

以下各维度均经过核查，未发现问题：

### 表 1 预算表—数字对照（核对 commit a816eb87f）

| 表项 | 文中值 | 源码位置 | 源码值 | 判定 |
|------|--------|----------|--------|------|
| 脚本墙钟默认 | 30s | host.zig:22 | `30_000` ms | ✅ |
| 可调范围 | 1s–300s | host.zig:31,33 | `1_000`–`300_000` ms | ✅ |
| QuickJS 内存 | 64MB | host.zig:21 | `64 * 1024 * 1024` | ✅ |
| 捕获缓冲 | 1MiB | host.zig:28 | `1024 * 1024` | ✅ |
| max_output_tokens 帽 | 262144 (1MiB/4) | host.zig:37 | `262_144` | ✅ |
| 单条 shell 预算 | 1MiB | shell.zig:7 | `1024 * 1024` | ✅ |
| shell 超限留头尾各半 | — | shell.zig:38-47 | `head_len = budget_bytes/2`, `tail_len = budget_bytes - head_len` | ✅ |
| 模型侧内联阈值 | 16KiB | result_store.zig:15 | `16 * 1024` | ✅ |
| store 单值 | 256KB | store.zig:23 | `256 * 1024` | ✅ |
| store 总量 | 1MB | store.zig:24 | `1024 * 1024` | ✅ |
| 工具目录 | 16KiB | context_limits.zig:32 | `16 * 1024` | ✅ |
| 超时宽限 | 500ms | host.zig:34 | `500` ms | ✅ |
| 1024B 描述帽 | 1024 | model_tool_schema.zig:4 | `1024` | ✅ |

### 其他源文件引用

| 引用 | 出处 | 判定 |
|------|------|------|
| discovery.zig 打分 3/2/1 | discovery.zig:82-84 | ✅ 名字=3，参数=2，描述=1 |
| schema.zig:114 SetKey 封闭枚举 | schema.zig:114 | ✅ 封闭枚举，不含 codemode |
| schema.zig:31 Kind 枚举 codemode_store | schema.zig:31 | ✅ |
| bridge.zig:166 executeToolCallAuthorized | bridge.zig:166 | ✅ 统一入口 |
| bridge.zig deniedResult | bridge.zig:749 | ✅ 返回结果而非异常 |

### 表 2 算术

- 48561 = 16287 + 15987 + 16287 ✅
- 48561 / 124 = 391.62 → "约 392 倍" ✅（见 M2）
- 72932 / 23262 = 3.14 → "只差 3.1 倍" ✅

### 表 3 算术

- 148 + 133 + 12 + 5 = 298 ✅
- 148/298 = 49.66% → 49.7% ✅
- 133/298 = 44.63% → 44.6% ✅
- 12/298 = 4.03% → 4.0% ✅
- 5/298 = 1.68% → 1.7% ✅

### JS 示例语法

- 示例 1（三重 grep + 双层 JSON.parse）：`node --check` 通过 ✅
- 示例 2（store/load + @options）：`node --check` 通过 ✅

### 外链

| 链接 | 状态码 | 判定 |
|------|--------|------|
| https://blog.cloudflare.com/code-mode/ | 200 | ✅ |
| https://www.anthropic.com/research/code-execution-with-mcp | 200 | ✅ |
| https://github.com/tt67wq/fx#codemode-experimental | 200 | ✅ |

### 图文路径

| 文件 | 大小 | 判定 |
|------|------|------|
| static/images/fx-codemode/cover.png | 1.4MB | ✅ |
| static/images/fx-codemode/turns.png | 85KB | ✅ |
| static/images/fx-codemode/architecture.png | 123KB | ✅ |
| static/images/fx-codemode/architecture.mp4 | 582KB | ✅ |
| static/images/fx-codemode/store-compat.png | 159KB | ✅ |

### 核心技术叙述

- **双层 JSON.parse**：run_command 返回 JSON 字符串，其中 `output` 字段是第二层 JSON（shell 快照）。shell.zig 注释证实 "Encodes one completed shell result as the JSON string" ✅
- **权限单一路径**：bridge.zig:166 `executeToolCallAuthorized` 是嵌套调用和直接调用的统一入口 ✅
- **store 兼容决策**：SetKey 是封闭枚举（schema.zig:114），添加键值会破坏老版本解析；Kind 枚举（schema.zig:31）的 codemode_store 变体利用了 "未知 kind 跳过" 的日志格式逃生通道 ✅
- **QuickJS 内存/超时/缓冲三项预算**：host.zig:21-37 全部硬编码为常量 ✅
- **608KB 二进制增量**：622,592B = 608KB ✅

---

## 总结

文章技术质量整体扎实——15 处源码引用中 14 处数字与行号完全匹配，算术全部正确，JS 示例通过语法检查，外链和图片完好。唯一 blocker 是作者声称公开的实验数据目录未实际提交，导致表 2 数字无法独立复现。补齐该目录后建议 approve。

---

*本次评审未检查：ISSUE 编号对应的实际 issue 内容（无访问权限）、TLA+ 模型是否真的通过了 TLC checker、MEMORY.md 中的重开条件是否与文中描述一致、prompter 与终端采集的线程亲和性细节。*