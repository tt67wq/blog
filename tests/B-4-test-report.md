# B-4 独立验收报告 — fx codemode 草稿复跑验证

- **结论：PASS**（1 条非阻塞 NOTE，见验收项 5）
-  tester 身份独立复跑，未修改任何被测物（drafts/ 与 fx 仓库零改动，实验副本在 tmp/B-4/）。
- 验收时间：2026-11-26 10:55–10:58 (+08:00)

## 被测物与环境指纹

| 项 | 值 |
|---|---|
| 草稿 | blog-pi1 @ afe13cd（drafts/fx-codemode.md） |
| 配图源 | blog-pi2 @ c1dd7c5（static/images/fx-codemode/） |
| fx 二进制 | /Users/admin/Project/Zig/fx/zig-out/bin/fx，`fx --version` = 0.0.16，fx 仓库 HEAD c553300ae，二进制 mtime 2026-11-25 14:41 |
| bun | 1.4.2 |
| hugo | v0.170.1+withdeploy darwin/arm64（Homebrew，已安装，无需 brew install） |
| 平台 | macOS arm64 |

## 验收项 1 — B-1 acceptance（blog-pi1 目录，原样执行）

命令：`test -f drafts/fx-codemode.md && python3 -c "..."`（任务契约原文）。
**退出码 0**。标题串、≥4000 汉字（实测 5108）、≥3 图占位（实测 3）、store/QuickJS 均在。

## 验收项 2 — B-2 acceptance（blog-pi2 目录，原样执行）

命令：四个 `test -f`（architecture.png / turns.png / cover.png / architecture.config.json）。
**退出码 0**，四文件齐全。另核实草稿引用的第三张图 store-compat.png 也在 blog-pi2 成品目录。

## 验收项 3 — 收益实验复跑

方法：`cp tmp/fx-exp/run.ts tmp/B-4/run.ts` 后 `bun run.ts`（原脚本只读未动）。假网关 + 真 fx 二进制 + 隔离 HOME（experimental.codemode:true），`fx ask --quiet --json`。
**退出码 0**。关键数字对照：

| 指标 | 草稿声称 | 本次复跑 | 判定 |
|---|---|---|---|
| direct 回合数 | 4 | 4 | 一致 |
| direct 工具结果进上下文 | 48,561 B | 48,561 B（16,287+15,987+16,287） | 一致，零漂移 |
| codemode 回合数 | 2 | 2 | 一致 |
| codemode 结果体积 | 124 B | 124 B | 一致，零漂移 |
| direct 最后一轮请求体 | 72,932 B | 72,932 B | 一致 |
| codemode 最后一轮请求体 | 23,262 B | 23,262 B | 一致 |
| 两边任务结果 | 900 | 900（direct stdout 与 codemode 结果均含 TODO total: 900，codemode status=success） | 一致 |

漂移记录：字节数零漂移；仅嵌套调用耗时（48/23/25ms vs 原 48/25/24ms）、session_id 与落盘句柄名随机变化，不影响任何声称数字。

## 验收项 4 — 文中两段示例脚本复跑

方法：用正则从草稿**原文**抽出两个 javascript 代码块（tmp/B-4/example1.js、example2.js），自写 tester harness（tmp/B-4/examples.ts，隔离方式与 run.ts 相同）真机执行。
**退出码 0**，两段均 tool status=success：

- 第 2 节 TODO 统计脚本：结果含 `TODO total: 900`，与文中声称一致（语料按 run.ts 同法生成：3 文件 × 600 行 × 300 TODO 行）。
- 第 9 节 @options+store/load 脚本：`// @options: {"timeout_ms": 120000}` 被接受，结果 `cursor={"file":"alpha.txt","line":42}`，往返正确，与文中声称一致。

## 验收项 5 — hugo build

方法：草稿临时复制到 content/posts/fx-codemode-design.md，blog-pi2 的 static/images/fx-codemode/*.png 复制到本 worktree，跑 hugo。

- `hugo --quiet`：**退出码 0，输出零字节**（无 error 无 warning）。
- **NOTE（非阻塞）**：默认构建不产出该文章页，因 frontmatter date 为 2026-11-26T12:00:00+08:00，晚于构建时刻（10:57），Hugo 默认不发布未来日期内容。加 `--buildFuture` 后退出码 0、输出零字节，public/posts/fx-codemode-design/index.html 正常渲染，页面引用的三张图（turns/architecture/store-compat）全部存在于构建树。发布时注意：12:00 后构建或调整 date。
- 三个图片引用逐一核对文件存在：EXISTS × 3。
- 验证后已删除临时副本（content/posts/fx-codemode-design.md、static/images/fx-codemode/、public/），未 commit，git status 干净。

## 总结论

**PASS**。B-1/B-2 acceptance 均过；收益实验关键数字零漂移复现；两段示例脚本从草稿原文抽出真机跑通且输出与声称一致；hugo 构建零 error。唯一 NOTE 是 frontmatter 发布日期晚于验收时刻导致默认构建跳过该页，属发布时间设置问题，不阻塞草稿验收。

## 产物清单（tmp/B-4/，不入库）

run.ts（副本）、rerun.json、example1.js、example2.js、examples.ts、examples.json、hugo*.out。
