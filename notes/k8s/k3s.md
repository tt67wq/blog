## K3S笔记

---------

### 安装 
```
// 需要科学上网
// 下载脚本
curl -sfL https://get.k3s.io > install.sh
// 运行脚本
INSTALL_K3S_SKIP_START=true ./install.sh
```

### 加入K3S
```
K3S_TOKEN=xxx K3S_URL=https://server-url:6443 INSTALL_K3S_SKIP_START=true ./install.sh 
```
