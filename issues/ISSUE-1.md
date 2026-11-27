# ISSUE-1 — 文章声称的实验数据目录 tmp/fx-exp/ 不存在

- status: closed
- resolution: B-9 改措辞如实化(e8fdcab), B-10 approve; 重跑实验补数据留作可选升级
- 来源: B-8 评审 blocker B1（blog-pi5, review commit 710de47）；conductor 已独立证实
- 位置: content/posts/fx-codemode-design.md L129「实验脚本与原始输出存于博客仓库 tmp/fx-exp/，2026-11-26 实测」

## 事实
- 主 worktree tmp/ 下只有 fx-codemode-outline.md，无 fx-exp/。
- git ls-files 与 git log --all 均无 tmp/fx-exp 任何记录（从未提交过）。
- blog-pi1 worktree 已清理，mdfind/find 全盘无 fx-exp 目录。B-1 manifest 曾记「实测数据 tmp/fx-exp/results.json」，推测随 worktree 清理丢失。

## 影响
表 2 的 48561/124/72932/23262 与 392 倍、3.1 倍无法按文中指引复现；「所有数字都有出处」的卖点被这一处打脸。

## 修法（二选一）
1. 重跑对照实验，把脚本与 results.json 补进 tmp/fx-exp/ 并提交（fx 二进制 c553300ae 口径）。
2. 改文中措辞，如实说明数据暂未公开/仅存档于会话记录。
