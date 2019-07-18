### Linux
----
#### manjaro 配置国内源
```
sudo pacman-mirrors -i -c China -m rank
```

#### 获取自己的IP
```
dig @resolver1.opendns.com ANY myip.opendns.com +short
curl http://ip111.cn/
```

#### 科学上网代理Pac script
```
function FindProxyForURL(url, host) {

    var hosts = [ "google.com", "github.com" ];
    var i;

    for (i = 0; i < hosts.length; i++) {
        if (dnsDomainIs(host, hosts[i]) || shExpMatch(host, "*." + hosts[i] + "|" + hosts[i]))
            return "SOCKS5 127.0.0.1:1080; SOCKS 127.0.0.1:1080";
    }

    return "DIRECT";
}

```
