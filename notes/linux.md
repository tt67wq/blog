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
du -s * | sort -nr
```