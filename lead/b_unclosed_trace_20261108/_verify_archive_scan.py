# -*- coding: utf-8 -*-
"""_verify_archive_scan.py — 只读复核：全仓扫描归档格式（zip/gz/xz/bz2/tar）
内是否藏有 26f3fb61829756dfeecf 字面或含该串的 SHA256 摘要。
对 .git/objects 松散对象亦做字面扫描（不动 .git 内容）。
只读；运行: python -I -X utf8 <abs>/_verify_archive_scan.py
"""
import hashlib, os, sys, io, tarfile, zipfile, gzip, bz2, lzma, zlib

ROOT = r"D:\Project\ra2-campaign-forge"
TA = b"26f3fb61829756dfeecf"
TB = b"b6f95763794"
SKIP = {".git", "out", "node_modules", ".tmp", "b_unclosed_trace_20261108"}
MAX = 300 * 1024 * 1024

archive_ext = (".zip", ".gz", ".tgz", ".tar", ".xz", ".lzma", ".bz2", ".7z", ".rar")
n_arc = 0
n_git = 0
hits = []

def check(name, data):
    h = hashlib.sha256(data).hexdigest()
    if TA in data:
        hits.append(("LIT_A", name, len(data)))
    if TB in data:
        hits.append(("LIT_B", name, len(data)))
    if TA.decode() in h:
        hits.append(("HASH_A", name, h))
    if TB.decode() in h:
        hits.append(("HASH_B", name, h))

for dp, dns, fns in os.walk(ROOT):
    # .git is NOT pruned here: we scan loose objects; but skip the huge packfiles by size
    dns[:] = [d for d in dns if d not in SKIP and d != ".git"]
    for fn in fns:
        p = os.path.join(dp, fn)
        try:
            sz = os.path.getsize(p)
        except OSError:
            continue
        if sz > MAX:
            continue
        try:
            d = open(p, "rb").read()
        except OSError:
            continue
        if fn.lower().endswith(archive_ext):
            n_arc += 1
            check("MEMBER " + p, d)
            try:
                if zipfile.is_zipfile(p):
                    with zipfile.ZipFile(p) as z:
                        for zi in z.infolist():
                            if zi.file_size > MAX:
                                continue
                            try:
                                b = z.read(zi)
                                check("ZIP " + p + "!" + zi.filename, b)
                            except Exception:
                                pass
            except Exception:
                pass
            try:
                if p.lower().endswith((".tar", ".tgz", ".tar.gz")) or tarfile.is_tarfile(p):
                    with tarfile.open(p, "r:*") as tf:
                        for m in tf:
                            if m.isfile() and m.size <= MAX:
                                try:
                                    b = tf.extractfile(m).read()
                                    check("TAR " + p + "!" + m.name, b)
                                except Exception:
                                    pass
            except Exception:
                pass
            # decompress single-stream
            for dec, tag in ((gzip.decompress, "GZ"), (bz2.decompress, "BZ2"), (lzma.decompress, "XZ")):
                try:
                    b = dec(d)
                    check(tag + " " + p, b)
                except Exception:
                    pass

# .git loose objects (zlib streams) - literal only on decompressed bytes
GIT = os.path.join(ROOT, ".git", "objects")
for dp, dns, fns in os.walk(GIT):
    for fn in fns:
        p = os.path.join(dp, fn)
        try:
            d = open(p, "rb").read()
            b = zlib.decompress(d)
        except Exception:
            continue
        n_git += 1
        if TA in b:
            hits.append(("GIT_LIT_A", p, len(b)))
        if TB in b:
            hits.append(("GIT_LIT_B", p, len(b)))

print(f"archives_scanned={n_arc} git_loose_objects_decompressed={n_git}")
print(f"hits={len(hits)}")
for x in hits[:30]:
    print("HIT\t" + "\t".join(str(i) for i in x))
sys.stdout.flush()
