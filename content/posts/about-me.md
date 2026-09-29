title: "About Me"
date: 2026-09-29T14:00:00+08:00
slug: about-me
summary: 关于我：一个写中间件、也拆存储引擎的人。
ShowToc: false
---

你好，我是 **SaveMe**，资深中间件工程师，坐标杭州，主攻分布式系统与分布式存储，信奉“从零实现一遍才算真的懂”。

## 在得物

我在得物做资深中间件工程师，这几年主要干了三件事：

- 主导自研分布式注册中心，从设计到落地全程负责，替换掉社区版 Nacos，如今承载着全公司 50 万节点的服务注册与发现
- 参与 IM 平台建设，负责私信模块与 IM 网关
- 维护配置中心 / 注册中心 / MQ 等中间件 SDK，并自研了一版，把业务方的接入成本降到几乎可以忽略

## 业余在拆的东西

工作之外喜欢造轮子，理由很简单：只有亲手实现，才知道黑盒里到底发生了什么。

- **cube_db** —— 用 Zig 从零写的嵌入式 KV 存储引擎，LMDB 式纯 COW B-tree，无 WAL 崩溃安全，O(1) 恢复和 compact，有序写路径性能优于 LMDB
- **ESP32** —— 正在啃 ESP32 生态，从固件到配网、OTA，把嵌入式这条线补齐

## 写作

得物技术公众号作者，写过三篇从零实现系列长文：

- [《LSM-TREE 从入门到入魔：从零开始实现一个高性能键值存储》](https://mp.weixin.qq.com/s/Ghx9emnAnrAhkkcUrqzHjg)
- [《实战从零开始实现 Raft》](https://mp.weixin.qq.com/s/R2XXYFoR67VsiGwT6XM96A)
- [《实战从零开始构建一个 Coding Agent：Violin》](https://mp.weixin.qq.com/s/yFHRoAi6fe2dduXXlM8Tzw)

拿过年度「金笔杆」技术写作第一名。这个博客会延续同样的路子：把一个系统从零拆开，顺手记下踩过的坑。

---

- GitHub: [tt67wq](https://github.com/tt67wq)
- 邮箱： 807643203@qq.com
