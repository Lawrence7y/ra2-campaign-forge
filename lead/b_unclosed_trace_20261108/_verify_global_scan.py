# -*- coding: utf-8 -*-
r"""_verify_global_scan.py — 只读复核：全局 ~/.zcode 会话产物里
(1) 是否有任何文件 SHA256 含/尾接两尾串；
(2) 是否有 \uXXXX 转义形式的 26f3fb；
(3) 是否藏有「调查 B 回件 evidence 原文」的措辞；
(4) 列出 26f3fb 字面命中的最小 mtime（判断首次落盘时间）。
只读，不写域外任何文件。
"""
import os, hashlib, datetime
R = r"C:\Users\Administrator\.zcode"
TA = "26f3fb61829756dfeecf"
TB = "b6f95763794"
bs = "\\" + "u"
esc = "".join(bs + ("%04x" % ord(c)) for c in TA)
esc_bytes = esc.encode("ascii")
phrases = [
    "脚本 hash 尾".encode("utf-8"),
    b"ev_script_tail",
    "回件 evidence".encode("utf-8"),
]
n = 0
digest_hits = []
esc_hits = []
lit = []
phrase_hits = {p: [] for p in phrases}
for dp, dns, fns in os.walk(R):
    for fn in fns:
        p = os.path.join(dp, fn)
        try:
            if os.path.getsize(p) > 80 * 1024 * 1024:
                continue
            d = open(p, "rb").read()
        except OSError:
            continue
        n += 1
        h = hashlib.sha256(d).hexdigest()
        rel = os.path.relpath(p, R)
        if TA in h or TB in h:
            digest_hits.append((rel, h))
        if esc_bytes in d or esc_bytes.upper() in d:
            esc_hits.append(rel)
        if TA.encode() in d:
            lit.append((rel, datetime.datetime.fromtimestamp(os.path.getmtime(p))))
        for ph in phrases:
            if ph in d:
                phrase_hits[ph].append(rel)
print("global_scanned_files =", n)
print("digest_hits =", len(digest_hits), digest_hits[:3])
print("escaped_unicode_hits =", len(esc_hits), esc_hits[:3])
print("literal_26f3fb_files =", len(lit))
if lit:
    print("earliest_literal_mtime =", min(lit, key=lambda x: x[1]))
for ph, v in phrase_hits.items():
    print("phrase", repr(ph[:40]), "files =", len(v), v[:3])
