# -*- coding: utf-8 -*-
"""收尾指纹复核（只读 + hashlib 实算），写域内脚本。

用法：python -I -X utf8 final_check.py
输出：两个 gamemd.exe 的 sha256 / 体积，以及 fingerprints_pre 与 post 是否逐字节一致。
"""
import hashlib
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
HERE = ROOT / "lead" / "patch_capability_audit_20261112"


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    for rel in (r"ra2youli\gamemd.exe", r"ra2youli\.ra2opt\orig\gamemd.exe"):
        p = ROOT / rel
        if not p.is_file():
            print("ABSENT  " + rel)
            continue
        print("OK      %s  %s  (%d B)" % (sha256_of(p), rel, p.stat().st_size))

    pre = HERE / "fingerprints_pre.txt"
    post = HERE / "fingerprints_post.txt"
    if pre.is_file() and post.is_file():
        same = pre.read_bytes() == post.read_bytes()
        print("PRE_POST_IDENTICAL  %s" % same)
        print("PRE_SHA256  %s" % hashlib.sha256(pre.read_bytes()).hexdigest())
        print("POST_SHA256 %s" % hashlib.sha256(post.read_bytes()).hexdigest())
    else:
        print("PRE_POST_IDENTICAL  UNVERIFIED (pre or post missing)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
