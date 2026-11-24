"""_sv_net_probe.py — 只读网络能力探针
仅做: (1) TCP connect + close, (2) curl -I (HTTP HEAD).
不发送本仓库任何内容: 无 --data/--upload/POST, 无 TS query, 无文件上传.
用法: python -I -X utf8 <绝对路径>
"""
import socket
import subprocess
import sys

TCP_TARGETS = [
    ("example.com", 443),          # control: generic internet reachability
    ("github.com", 443),           # control: known reachable
    ("freetsa.org", 443),          # free RFC3161 TSA
    ("www.freetsa.org", 443),
    ("timestamp.digicert.com", 80),
    ("timestamp.digicert.com", 443),
    ("timestamp.sectigo.com", 80),
    ("rekor.sigstore.dev", 443),   # transparency log
    ("fulcio.sigstore.dev", 443),  # sigstore CA
]
HEAD_URLS = [
    "https://example.com",
    "https://freetsa.org/",
    "https://freetsa.org/tsr",
    "http://timestamp.digicert.com/",
    "https://timestamp.digicert.com/",
    "https://rekor.sigstore.dev/",
    "https://rekor.sigstore.dev/api/v1/log",
]

print("=== NET PROBE POLICY ===")
print("TCP connect()+close only; curl -I (HEAD) only; NO request body, NO repo bytes, NO TS query.")
print()

print("=== 1. TCP connect (no payload) ===")
for host, port in TCP_TARGETS:
    try:
        s = socket.create_connection((host, port), timeout=8)
        peer = s.getpeername()
        s.close()
        print(f"TCP_OK     {host}:{port}  peer={peer}")
    except Exception as e:
        print(f"TCP_FAIL   {host}:{port}  {type(e).__name__}: {e}")

print()
print("=== 2. curl -I (HTTP HEAD, no body) ===")
for url in HEAD_URLS:
    cmd = ["curl", "-sS", "-I", "--connect-timeout", "8", "--max-time", "18",
           "--no-progress-meter", "-w", "\nCURL_HTTP_CODE=%{http_code}\n", url]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=30)
        out = (r.stdout + r.stderr).decode("utf-8", "replace").strip()
        first = [l for l in out.splitlines() if l.strip()][:14]
        print(f"--- {url}  rc={r.returncode}")
        for l in first:
            print("   ", l[:200])
    except subprocess.TimeoutExpired:
        print(f"--- {url}  TIMEOUT(30s)")
    except Exception as e:
        print(f"--- {url}  {type(e).__name__}: {e}")
print()
print("=== END (no repository content transmitted) ===")
