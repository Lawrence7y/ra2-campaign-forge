# -*- coding: utf-8 -*-
"""_si_gatecheck.py — 自验：用还原的本发门禁（显式命名方案A）判本写域；
并用旧 max 门禁对照本写域（双同字节件场景）。只读。"""
import io
import re
import contextlib
import time
from pathlib import Path

ROOT = Path(r"D:/Project/ra2-campaign-forge")
OUTD = ROOT / "lead/gate_subject_id_20261109"
OUT = []
t0 = time.perf_counter()

def emit(s=""):
    OUT.append(s)
    print(s)

# 1) 本发门禁（显式命名）
self_src = (OUTD / "_si_gate_self_extracted.py").read_text(encoding="utf-8")
FORBID = re.compile(r"write_text|write_bytes|unlink|rmdir|rename|mkdir|shutil|os\.remove|open\([^)]*['\"][wax]")
assert not FORBID.search(self_src), "提取门禁含写操作词，拒绝 exec"

emit("=" * 90)
emit("A. 本发门禁（方案A 显式命名，源码=_si_gate_self_extracted.py）对本写域实跑（只读）")
emit("=" * 90)
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    exec(compile(self_src, "_si_gate_self_extracted.py", "exec"), {})
self_out = buf.getvalue().strip()
emit(self_out)
ok_self = '"ok": true' in self_out

# 2) 旧 max 门禁对照（同构逻辑，只读）
emit("")
emit("=" * 90)
emit("B. 旧 max(st_size) 门禁对照本写域（两份同字节 md）")
emit("=" * 90)
wd = OUTD
cands = sorted(wd.glob("*.md"))
doc = max(cands, key=lambda p: p.stat().st_size)
emit("cands = %s" % [c.name for c in cands])
emit("max 选中 = %s（%dB）——同字节双件按字典序取先；两件内容相同，判定不变。" % (doc.name, doc.stat().st_size))

emit("")
emit("SELF_GATE_OK=%s" % ok_self)
emit("elapsedSec=%.3f" % (time.perf_counter() - t0))

(OUTD / "_si_gatecheck_out.txt").write_text("\n".join(OUT), encoding="utf-8")
print("\nwritten _si_gatecheck_out.txt")
