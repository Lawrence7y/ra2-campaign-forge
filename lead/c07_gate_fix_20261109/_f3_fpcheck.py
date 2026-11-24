# -*- coding: utf-8 -*-
# _f3_fpcheck.py — 核验编排方给出的只读件指纹（只读，不写任何被核文件）。
# 用法：python -I -X utf8 _f3_fpcheck.py <编排方指纹JSON路径>
import hashlib
import json
import os
import sys

ROOT = r"D:\Project\ra2-campaign-forge"


def fp(rel):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    if not os.path.exists(p):
        return None, None
    with open(p, "rb") as f:
        raw = f.read()
    return hashlib.sha256(raw).hexdigest(), len(raw)


def main(argv):
    if len(argv) < 2:
        print("usage: _f3_fpcheck.py <fingerprint.json>")
        return 2
    with open(argv[1], "rb") as f:
        spec = json.loads(f.read().decode("utf-8"))
    bad = 0
    for rel, want in spec.items():
        got, size = fp(rel)
        if got is None:
            print("MISSING %s" % rel)
            bad += 1
            continue
        ok = (got == want.get("sha256")) and (size == want.get("bytes"))
        print("%s %s bytes=%d sha=%s" % ("OK  " if ok else "BAD ", rel, size, got))
        if not ok:
            bad += 1
    # 36 samples: count + sizes
    sdir = os.path.join(ROOT, "lead", "c07_gate_audit_20261109", "_c7a_samples")
    names = sorted(os.listdir(sdir)) if os.path.isdir(sdir) else []
    print("samples_dir_count=%d" % len(names))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
