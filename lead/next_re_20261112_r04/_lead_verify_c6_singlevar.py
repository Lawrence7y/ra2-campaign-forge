#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lead 核验：C6 与 CTRL_C6 的输入是否真的「只差敌人 mission」。

做法：
1) 对 out/inputs/<arm>/ 下每个文件算 sha256，列表对比。
2) 对两个 design JSON 做结构 diff（忽略 mission 字段后应完全相同）。
3) 对两个 .MAP 做字节 diff，定位差异偏移。
"""
import hashlib
import json
from pathlib import Path

BASE = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r04\W88_envelope\out\inputs")


def sha(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def list_arm(arm: str):
    d = BASE / arm
    if not d.exists():
        print(f"  !! 缺 {d}")
        return {}
    return {p.name: (p.stat().st_size, sha(p), p) for p in sorted(d.iterdir()) if p.is_file()}


for arm in ("C6", "CTRL_C6"):
    print(f"=== {arm} ===")
    for name, (sz, h, _) in list_arm(arm).items():
        print(f"  {name:26s} {sz:>8d}  {h[:32]}")

a = list_arm("C6")
b = list_arm("CTRL_C6")
print("\n=== 文件级对比 ===")
for name in sorted(set(a) | set(b)):
    ia, ib = a.get(name), b.get(name)
    if not ia or not ib:
        print(f"  {name}: 仅存在于一臂 ({'C6' if ia else 'CTRL_C6'})")
        continue
    same = ia[1] == ib[1]
    print(f"  {name:26s} {'SAME' if same else 'DIFF'}   sizes {ia[0]} vs {ib[0]}")

# design json 结构 diff
dja = next((p for n, (_, _, p) in a.items() if n.endswith('.json') and 'design' in n), None)
djb = next((p for n, (_, _, p) in b.items() if n.endswith('.json') and 'design' in n), None)
if dja and djb:
    ja = json.loads(dja.read_text(encoding="utf-8"))
    jb = json.loads(djb.read_text(encoding="utf-8"))
    print(f"\n=== design diff（{dja.name} vs {djb.name}）===")

    def flatten(o, path=""):
        out = {}
        if isinstance(o, dict):
            for k, v in o.items():
                out.update(flatten(v, f"{path}.{k}" if path else k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                out.update(flatten(v, f"{path}[{i}]"))
        else:
            out[path] = o
        return out

    fa, fb = flatten(ja), flatten(jb)
    diffs = []
    for k in sorted(set(fa) | set(fb)):
        va, vb = fa.get(k, "<absent>"), fb.get(k, "<absent>")
        if va != vb:
            diffs.append((k, va, vb))
    print(f"  扁平字段数 {len(fa)} vs {len(fb)}；差异字段 {len(diffs)} 个")
    nonmission = [d for d in diffs if "mission" not in d[0].lower()]
    print(f"  其中『非 mission』差异 = {len(nonmission)} 个")
    for k, va, vb in diffs[:8]:
        print(f"    {k}: {va!r} -> {vb!r}")
    if len(diffs) > 8:
        print(f"    ... 共 {len(diffs)} 处")
    # 若把 mission 全归一后是否完全相同
    def norm(o):
        if isinstance(o, dict):
            return {k: ("<M>" if k.lower() == "mission" else norm(v)) for k, v in o.items()}
        if isinstance(o, list):
            return [norm(v) for v in o]
        return o
    print(f"  ⇒ mission 归一后两设计{'完全相同' if norm(ja) == norm(jb) else '仍有差异'}")

# .MAP 字节 diff
ma = next((p for n, (_, _, p) in a.items() if n.upper().endswith('.MAP')), None)
mb = next((p for n, (_, _, p) in b.items() if n.upper().endswith('.MAP')), None)
if ma and mb:
    da, db = ma.read_bytes(), mb.read_bytes()
    print(f"\n=== .MAP 字节 diff（{len(da)} vs {len(db)} B）===")
    n = min(len(da), len(db))
    offs = [i for i in range(n) if da[i] != db[i]]
    print(f"  不同字节数 = {len(offs)}" + (f"，首个偏移 0x{offs[0]:X}" if offs else ""))
