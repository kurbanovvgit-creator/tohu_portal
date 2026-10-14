import datetime
import ipaddress
import socket
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from education.context import lan_ip


def cert_dir():
    from django.conf import settings
    folder = Path(settings.BASE_DIR) / "certs"
    folder.mkdir(exist_ok=True)
    return folder


def local_ips():
    found = {"127.0.0.1", lan_ip()}
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            found.add(info[4][0])
    except OSError:
        pass
    return sorted(found)


def ensure_cert():
    folder = cert_dir()
    cert_path = folder / "dev.crt"
    key_path = folder / "dev.key"
    ips = local_ips()
    stamp = folder / "dev.ips"
    wanted = "\n".join(ips)
    if cert_path.exists() and key_path.exists() and stamp.exists() and stamp.read_text(encoding="utf-8") == wanted:
        return cert_path, key_path
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "TOHU BILIM")])
    alt = [x509.DNSName("localhost")]
    for ip in ips:
        alt.append(x509.IPAddress(ipaddress.ip_address(ip)))
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=365))
        .add_extension(x509.SubjectAlternativeName(alt), critical=False)
        .sign(key, hashes.SHA256())
    )
    key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    stamp.write_text(wanted, encoding="utf-8")
    return cert_path, key_path
