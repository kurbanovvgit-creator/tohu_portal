import ipaddress
import socket


def private_ips():
    found = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            try:
                addr = ipaddress.ip_address(ip)
            except ValueError:
                continue
            if addr.is_private and not addr.is_loopback and not addr.is_link_local:
                found.add(ip)
    except OSError:
        pass
    return sorted(found)


def _score(ip):
    parts = [int(p) for p in ip.split(".")]
    score = 0
    # Prefer common classroom / home Wi-Fi ranges.
    if parts[0] == 192 and parts[1] == 168:
        score += 40
    if parts[0] == 10 and parts[1] >= 200:
        score += 35
    if parts[0] == 172 and 16 <= parts[1] <= 31:
        score += 20
    # Hyper-V / Docker / VPN hosts often end with .1 on small virtual nets.
    if parts[3] == 1:
        score -= 25
    if parts[0] == 10 and parts[1] == 0:
        score -= 30
    return score


def lan_ip(preferred=None):
    ips = private_ips()
    if preferred and preferred in ips:
        return preferred
    if not ips:
        return "127.0.0.1"
    return max(ips, key=_score)


def public_base(request, preferred=None):
    host = (request.get_host() or "").split(":")[0]
    port = request.get_port()
    ips = private_ips()
    if preferred and preferred in ips:
        ip = preferred
    elif host in ips:
        ip = host
    else:
        ip = lan_ip(preferred)
    return f"https://{ip}:{port}"


def platform(request):
    preferred = request.GET.get("ip") or request.session.get("join_ip")
    origin = public_base(request, preferred)
    return {
        "lan_ip": origin.split("://", 1)[1].split(":")[0],
        "lan_port": request.get_port(),
        "lan_origin": origin,
        "lan_ips": private_ips(),
    }
