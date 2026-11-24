# -*- coding: utf-8 -*-
"""_integ_make_rollback.py — D-25 第 6 步「保存差异与回退材料」。

产出 _integ_isolated_vs_mother.diff（母本 → 隔离副本 unified diff，difflib n=3），
并与只读域既有件 CANDIDATE_LF.diff 逐字节对照（预期仅 +++ b/ 头行不同——b 路径不同）。
母本全程零接触 ⇒ 真回退动作 = 丢弃本写域（lead/b2b_isolated_20261107/），母本无需任何回退。
"""
import difflib
import hashlib
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge")
MOTHER = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py"
ISOL = ROOT / "lead/b2b_isolated_20261107/qc151_trip.isolated.py"
CANDIFF = ROOT / "lead/b2b_candidate_lf_20261107/CANDIDATE_LF.diff"
OUT = ROOT / "lead/b2b_isolated_20261107/_integ_isolated_vs_mother.diff"

mt = MOTHER.read_bytes().decode("utf-8")
it = ISOL.read_bytes().decode("utf-8")
dl = list(difflib.unified_diff(mt.split("\n"), it.split("\n"),
                               fromfile="a/out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py",
                               tofile="b/lead/b2b_isolated_20261107/qc151_trip.isolated.py",
                               n=3, lineterm=""))
text = "\n".join(dl) + "\n"
OUT.write_text(text, encoding="utf-8", newline="\n")
h = hashlib.sha256(text.encode("utf-8")).hexdigest()
print(f"_integ_isolated_vs_mother.diff: bytes={len(text.encode('utf-8'))} sha256={h} LF={text.count(chr(10))} @@头数={sum(1 for l in dl if l.startswith('@@ '))}")

cd = CANDIFF.read_bytes().decode("utf-8")
cl = cd.split("\n")
print(f"CANDIDATE_LF.diff（只读原件）: bytes={len(cd.encode('utf-8'))}")
same = text == cd
print("与 CANDIDATE_LF.diff 逐字节相同 =", same)
if not same:
    pairs = [(i + 1, a[:80], b[:80]) for i, (a, b) in enumerate(zip(dl, cl)) if a != b]
    print(f"行级差异 {len(pairs)} 处（应仅为 tofile 头行）:")
    for n, a, b in pairs[:10]:
        print(f"  L{n} 重建: {a!r}")
        print(f"  L{n} 原件 : {b!r}")
    print(f"行数: 重建={len(dl)} 原件={len(cl)}")
