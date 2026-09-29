---
title: "About Me"
date: 2026-09-29T14:00:00+08:00
slug: about-me
summary: 关于我：一个写中间件、也拆存储引擎的人。
ShowToc: false
ShowReadingTime: false
comments: false
---

<div class="about">

<style>
.about { --org: #ea6a1e; --org-deep: #c2540f; --org-soft: rgba(234,106,30,.1);
  --org-line: rgba(234,106,30,.35); }
.about .hero { background: linear-gradient(135deg, var(--org-soft), rgba(234,106,30,.02));
  border: 1px solid var(--org-line); border-radius: 14px; padding: 28px 26px; margin: 8px 0 28px; }
.about .hero .name { font-size: 1.6em; font-weight: 700; color: var(--org-deep); }
.about .hero .tag { color: var(--ink-light); margin-top: 6px; }
.about section h2 { display: flex; align-items: center; gap: 10px;
  border-bottom: none; margin-top: 34px; }
.about section h2::before { content: ""; width: 6px; height: 22px; border-radius: 3px;
  background: var(--org); }
.about .card { background: var(--card); border: 1px solid var(--line); border-left: 4px solid var(--org);
  border-radius: 10px; padding: 14px 18px; margin: 12px 0;
  box-shadow: 0 1px 3px rgba(61,55,51,.06); }
.about .card b:first-child { color: var(--org-deep); }
.about ul.work { list-style: none; padding-left: 0; }
.about ul.work li { padding: 10px 0 10px 26px; position: relative; border-bottom: 1px dashed var(--line); }
.about ul.work li:last-child { border-bottom: none; }
.about ul.work li::before { content: "▸"; position: absolute; left: 4px; color: var(--org); }
.about .contact { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }
.about .contact a { border: 1px solid var(--org-line); border-radius: 999px; padding: 6px 16px;
  text-decoration: none; border-bottom: 1px solid var(--org-line); color: var(--org-deep); font-size: .92em; }
.about .contact a:hover { background: var(--org); color: #fff; border-color: var(--org); }
.about .posts a { color: var(--org-deep); border-bottom-color: var(--org-line); }
.about .posts a:hover { color: #fff; background: var(--org); border-bottom-color: var(--org); }
@media (prefers-color-scheme: dark) { .about { --org: #f5843c; --org-deep: #f9a86b;
  --org-soft: rgba(245,132,60,.12); --org-line: rgba(245,132,60,.35); } }
</style>

<div class="hero">
  <div class="name">你好，我是 SaveMe 👋</div>
  <div class="tag">资深中间件工程师 · 分布式系统 / 分布式存储 · 坐标杭州<br>
  信奉「从零实现一遍才算真的懂」</div>
</div>

<section>
<h2>在得物</h2>
<ul class="work">
  <li>主导自研分布式注册中心，从设计到落地全程负责，替换掉社区版 Nacos，如今承载着全公司 50 万节点的服务注册与发现</li>
  <li>参与 IM 平台建设，负责私信模块与 IM 网关</li>
  <li>维护配置中心 / 注册中心 / MQ 等中间件 SDK，并自研了一版，把业务方的接入成本降到几乎可以忽略</li>
</ul>
</section>

<section>
<h2>业余在拆的东西</h2>
<p>工作之外喜欢造轮子，理由很简单：只有亲手实现，才知道黑盒里到底发生了什么。</p>
<div class="card"><b>cube_db</b> —— 用 Zig 从零写的嵌入式 KV 存储引擎，LMDB 式纯 COW B-tree，无 WAL 崩溃安全，O(1) 恢复和 compact，有序写路径性能优于 LMDB</div>
<div class="card"><b>ESP32</b> —— 正在啃 ESP32 生态，从固件到配网、OTA，把嵌入式这条线补齐</div>
</section>

<section>
<h2>写作</h2>
<p>得物技术公众号作者，写过三篇从零实现系列长文，拿过年度「金笔杆」技术写作第一名。这个博客会延续同样的路子：把一个系统从零拆开，顺手记下踩过的坑。</p>
<ul class="posts">
  <li><a href="https://mp.weixin.qq.com/s/Ghx9emnAnrAhkkcUrqzHjg" target="_blank" rel="noopener">《LSM-TREE 从入门到入魔：从零开始实现一个高性能键值存储》</a></li>
  <li><a href="https://mp.weixin.qq.com/s/R2XXYFoR67VsiGwT6XM96A" target="_blank" rel="noopener">《实战从零开始实现 Raft》</a></li>
  <li><a href="https://mp.weixin.qq.com/s/yFHRoAi6fe2dduXXlM8Tzw" target="_blank" rel="noopener">《实战从零开始构建一个 Coding Agent：Violin》</a></li>
</ul>
</section>

<div class="contact">
  <a href="https://github.com/tt67wq" target="_blank" rel="noopener">GitHub: tt67wq</a>
  <a href="mailto:807643203@qq.com">807643203@qq.com</a>
</div>

</div>
