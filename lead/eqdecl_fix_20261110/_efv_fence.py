# _efv_fence.py — 复核员独立实现围栏状态机 v2（修正：开栏允许信息串，如 ```python）
# 语义：开行 ^\s*(`{3,}|~{3,})（信息串允许）；闭行=同字符、仅围栏字符、个数>=开行；
#       未闭合兜底到文件尾。栏内=开行+1..闭行-1（未闭合则到文件尾）。
import io
import json
import re

FENCE_OPEN = re.compile(r"^\s*(`{3,}|~{3,})")
FENCE_CLOSE = re.compile(r"^\s*(`{3,}|~{3,})\s*$")


def fence_state(path):
    with io.open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    segs = []
    cur = None
    for i, l in enumerate(lines, 1):
        if cur is None:
            m = FENCE_OPEN.match(l)
            if m:
                cur = (i, m.group(1)[0], len(m.group(1)))
        else:
            m = FENCE_CLOSE.match(l)
            if m and m.group(1)[0] == cur[1] and len(m.group(1)) >= cur[2]:
                segs.append((cur[0], i))
                cur = None
    if cur:
        segs.append((cur[0], None))
    ins = set()
    for o, c in segs:
        e = (c - 1) if c else len(lines)
        ins.update(range(o + 1, e + 1))
    return len(lines), segs, ins


FILES = {
    "COMPARABILITY_AUDIT.md": (r"D:\Project\ra2-campaign-forge\lead\comparability_20261109\COMPARABILITY_AUDIT.md",
                               [158]),
    "LAYER_IDENTITY.md": (r"D:\Project\ra2-campaign-forge\lead\layer_identity_20261109\LAYER_IDENTITY.md",
                          [13, 223, 242, 338]),
    "TAUTOLOGY_AUDIT.md": (r"D:\Project\ra2-campaign-forge\lead\tautology_audit_20261109\TAUTOLOGY_AUDIT.md",
                           [158, 289, 328]),
    "_ta_TAUTOLOGY_AUDIT_20261109.md": (r"D:\Project\ra2-campaign-forge\lead\tautology_audit_20261109\_ta_TAUTOLOGY_AUDIT_20261109.md",
                                        [203, 244]),
}

out = {}
for name, (path, checks) in FILES.items():
    n_lines, segs, ins = fence_state(path)
    out[name] = {
        "n_lines_split": n_lines,
        "n_inside_excl_markers": len(ins),
        "n_inside_incl_markers": len(ins) + 2 * sum(1 for s in segs if s[1] is not None),
        "n_segments": len(segs),
        "unclosed": [s for s in segs if s[1] is None],
        "checks": {str(n): (n in ins) for n in checks},
    }
    if name == "TAUTOLOGY_AUDIT.md":
        out[name]["segments"] = segs
print(json.dumps(out, ensure_ascii=False, indent=1))
