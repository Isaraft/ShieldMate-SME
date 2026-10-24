"""Real owned loopback service exercises the bounded HTTP parser, never an external scan."""

import socket
from concurrent.futures import ThreadPoolExecutor

from app.scanner.http_checks import request_headers, response_observation
from app.scanner.policy import Budget


def test_owned_loopback_headers_do_not_follow_redirect_or_consume_body():
    with socket.create_server(("127.0.0.1", 0)) as server:
        server.settimeout(3)

        def serve():
            with server.accept()[0] as connection:
                connection.settimeout(3)
                received = b""
                while not received.endswith(b"\r\n\r\n"):
                    received += connection.recv(1)
                connection.sendall(
                    b"HTTP/1.1 302 Found\r\n"
                    b"Location: http://169.254.169.254/PRIVATE-QA-PATH\r\n"
                    b"Content-Length: 1000000\r\n\r\nPRIVATE-BODY"
                )
                return received

        with ThreadPoolExecutor(1) as pool:
            task = pool.submit(serve)
            with socket.create_connection(server.getsockname(), timeout=3) as connection:
                response = request_headers(connection, "qa-local.example.com", Budget.start(5, 2))
                evidence = response_observation("HTTP_REDIRECT", response, "qa-local.example.com")
                assert response.status == 302
                assert "PRIVATE" not in str(evidence.evidence)
                assert connection.recv(1, socket.MSG_PEEK) == b"P"
            received = task.result(timeout=3)
            assert received.startswith(b"HEAD / HTTP/1.1\r\nHost: qa-local.example.com\r\n")
