function FindProxyForURL(url, host) {

    var hosts = [ "v2ex.com",  "stackoverflow.com", "google.com", "github.com" ];
    var i;

    for (i = 0; i < hosts.length; i++) {
        if (dnsDomainIs(host, hosts[i]) || shExpMatch(host, "*." + hosts[i] + "|" + hosts[i]))
            return "SOCKS5 127.0.0.1:1080; SOCKS 127.0.0.1:1080";
    }

    return "DIRECT";
}
