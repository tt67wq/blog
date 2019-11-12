### Linux
----
#### manjaro 配置国内源
```
sudo pacman-mirrors -i -c China -m rank
```

#### 获取自己的IP
```
curl https://pv.sohu.com/cityjson
```

#### 测试网络带宽
```
curl -s https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py | python -
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

#### 查看硬件信息
```
sudo lshw -short
```