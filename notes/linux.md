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
    if (dnsDomainIs(host, "intranet.domain.com") ||
        shExpMatch(host, "(*.abcdomain.com|abcdomain.com)"))
        return "DIRECT";

    if (dnsDomainIs(host, "google.com") ||
        shExpMatch(host, "(*.google.com|google.com)"))
	return "SOCKS5 127.0.0.1:1080; SOCKS 127.0.0.1:1080";

    
    if (dnsDomainIs(host, "github.com") ||
        shExpMatch(host, "(*.github.com|github.com)"))
	return "SOCKS5 127.0.0.1:1080; SOCKS 127.0.0.1:1080";
    
    return "DIRECT";
}
```
