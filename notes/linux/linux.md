### Linux
----
#### manjaro 配置国内源
```
sudo pacman-mirrors -i -c China -m rank
```

#### ZSH安装脚本
```
https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh
```

#### 获取自己的IP
```
curl https://pv.sohu.com/cityjson
```

#### 批量杀进程
```
ps aux | grep "some process" | awk '{print $2}' | xargs kill -9
```

#### 列出当前目录文件大小并排序
```
du -sh * | sort -nr
```

#### 利用ssh和nc建设临时穿透
```
1. 内网机器执行，ssh隧道，远端8888口映射到本地4000口
ssh -fN -R 8888:localhost:4000 root@xxx.xxx.xxx.xxx -p 22000
或者
autossh -p 22000 -M 8877 -NR 8888:localhost:4000 root@xxx.xxx.xxx.xxx


2. 公网服务器执行，nc监听80口，并转发至8888口
nc -k -l -p 80 -c "nc 127.0.0.1 8888 -i 5" -vv
```

#### 在线剪贴板
```
cmd | curl -F "c=@-" "http://fars.ee/"
```

#### logrotate配置
```
/path/*.log {
    daily
    rotate 5
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}              
```

#### Arch安装字体

1. 字体文件放到~/.local/share/fonts/下
2. 执行fc-cache -vf

#### 生成32位随机串
```
head -c 32 /dev/random | base64
```

#### Linux硬件信息
```
name -a # 查看内核/操作系统/CPU信息
read -n 1 /etc/issue # 查看操作系统版本
cat /proc/cpuinfo # 查看CPU信息
hostname # 查看计算机名
lspci -tv # 列出所有PCI设备
lsusb -tv # 列出所有USB设备
lsmod # 列出加载的内核模块
env # 查看环境变量 资源
free -m # 查看内存使用量和交换区使用量
df -h # 查看各分区使用情况
du -sh # 查看指定目录的大小
grep MemTotal /proc/meminfo # 查看内存总量
grep MemFree /proc/meminfo # 查看空闲内存量
uptime # 查看系统运行时间、用户数、负载
cat /proc/loadavg # 查看系统负载 磁盘和分区
mount | column -t # 查看挂接的分区状态
fdisk -l # 查看所有分区
swapon -s # 查看所有交换分区
hdparm -i /dev/hda # 查看磁盘参数(仅适用于IDE设备)
dmesg | grep IDE # 查看启动时IDE设备检测状况 网络
ifconfig # 查看所有网络接口的属性
iptables -L # 查看防火墙设置
route -n # 查看路由表
netstat -lntp # 查看所有监听端口
netstat -antp # 查看所有已经建立的连接
netstat -s # 查看网络统计信息 进程
ps -ef # 查看所有进程
top # 实时显示进程状态 用户
w # 查看活动用户
id # 查看指定用户信息
last # 查看用户登录日志
```


