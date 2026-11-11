# -*- coding: utf-8 -*-
"""patch_capability_audit_20261112 收尾指纹脚本（只读，hashlib 实算）。

对关键既有文件做 SHA-256 实算，用于证明本次审计零改动既有件与 ra2youli/。
用法：python -I -X utf8 fingerprints.py <输出txt>
"""
import hashlib
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")

TARGETS = [
    # ra2youli（游戏目录：铁律零改动对象）
    r"ra2youli\gamemd.exe",
    r"ra2youli\ra2md.exe",
    r"ra2youli\ra2.exe",
    r"ra2youli\RA2MD.INI",
    r"ra2youli\ra2.ini",
    r"ra2youli\ddraw.dll",
    r"ra2youli\ddraw.ini",
    r"ra2youli\BATTLEMD.INI",
    r"ra2youli\BATTLEMD98.INI",
    r"ra2youli\expandmd98.mix",
    r"ra2youli\ra2opt_play.bat",
    r"ra2youli\.ra2opt\manifest.json",
    # 本审计读过/引用的既有件
    r"docs\PROJECT_DIRECTION.md",
    r"REVERSE_ENGINEERING_AND_PATCHES.md",
    r"ra2opt\__init__.py",
    r"ra2opt\cli.py",
    r"ra2opt\optimize.py",
    r"ra2opt\backup.py",
    r"ra2opt\audit.py",
    r"ra2opt\game.py",
    r"ra2opt\pe.py",
    r"ra2opt\safewrite.py",
    r"ra2opt\appcompat.py",
    r"ra2opt\cddraw.py",
    r"ra2opt\launcher.py",
    r"ra2opt\tests.py",
    r"ra2render\blitter_hooks.cpp",
    r"ra2render\ra2render.h",
    r"ra2render\ra2render.ini",
    r"ra2render\ra2loader.cpp",
    r"ra2render\ra2render.dll",
    r"ra2render\ra2loader.exe",
    r"tools\verify_anchors.py",
    r"tools\audit_bytes.py",
    r"tools\verify_hooks.py",
    r"docs\re\anchor_claims.txt",
]


def main() -> int:
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    lines = []
    for rel in TARGETS:
        p = ROOT / rel
        if not p.is_file():
            lines.append(f"ABSENT  {'-' * 64}  {rel}")
            continue
        h = hashlib.sha256()
        with open(p, "rb") as fh:
            for block in iter(lambda: fh.read(1 << 20), b""):
                h.update(block)
        lines.append(f"OK      {h.hexdigest()}  {rel}  ({p.stat().st_size} B)")
    text = "\n".join(lines) + "\n"
    print(text, end="")
    if out_path is not None:
        Path(out_path).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
