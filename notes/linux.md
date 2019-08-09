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

#### 科学上网代理Pac script
```
function FindProxyForURL(url, host) {

    var hosts = [ "v2ex.com",  "stackoverflow.com", "google.com", "github.com" ];
    var i;

    for (i = 0; i < hosts.length; i++) {
        if (dnsDomainIs(host, hosts[i]) || shExpMatch(host, "*." + hosts[i] + "|" + hosts[i]))
            return "SOCKS5 127.0.0.1:1080; SOCKS 127.0.0.1:1080";
    }

    return "DIRECT";
}
```

#### 列出当前目录文件大小并排序
```
du -sh * | sort -nr
```