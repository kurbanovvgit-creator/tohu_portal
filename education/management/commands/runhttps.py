import socket
import ssl

from django.conf import settings
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.management.base import BaseCommand
from django.core.servers.basehttp import ThreadedWSGIServer, WSGIRequestHandler
from django.core.wsgi import get_wsgi_application

from education.devcert import ensure_cert, local_ips


class Handler(WSGIRequestHandler):
    def get_environ(self):
        env = super().get_environ()
        if isinstance(self.connection, ssl.SSLSocket):
            env["HTTPS"] = "on"
            env["wsgi.url_scheme"] = "https"
        return env


class DualServer(ThreadedWSGIServer):
    ssl_context = None

    def get_request(self):
        conn, addr = super().get_request()
        conn.settimeout(3)
        first = b""
        try:
            while not first:
                first = conn.recv(1, socket.MSG_PEEK)
        except (OSError, socket.timeout):
            first = b""
        conn.settimeout(None)
        if first == b"\x16" and self.ssl_context is not None:
            conn = self.ssl_context.wrap_socket(conn, server_side=True)
        return conn, addr


class Command(BaseCommand):
    help = "Запуск сайта по HTTPS, чтобы телефон не упирался в SSL."

    def add_arguments(self, parser):
        parser.add_argument("--port", default="8000")

    def handle(self, *args, **options):
        port = int(options["port"])
        cert, key = ensure_cert()
        origins = [f"https://localhost:{port}", f"https://127.0.0.1:{port}"]
        origins += [f"https://{ip}:{port}" for ip in local_ips()]
        settings.CSRF_TRUSTED_ORIGINS = list(getattr(settings, "CSRF_TRUSTED_ORIGINS", [])) + origins
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=str(cert), keyfile=str(key))
        DualServer.ssl_context = context
        server = DualServer(("0.0.0.0", port), Handler)
        server.set_app(StaticFilesHandler(get_wsgi_application()))
        self.stdout.write(self.style.SUCCESS(f"PK: http://127.0.0.1:{port}/"))
        self.stdout.write(self.style.SUCCESS(f"HTTPS: https://127.0.0.1:{port}/"))
        for ip in local_ips():
            if ip != "127.0.0.1":
                self.stdout.write(self.style.SUCCESS(f"Telefon: https://{ip}:{port}/"))
        server.serve_forever()
