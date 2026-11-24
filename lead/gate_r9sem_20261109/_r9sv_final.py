# -*- coding: utf-8 -*-
"""_r9sv_final.py — 收尾核验：46 pin 复跑、R10 三词、绑定行惯例、写域清点。"""
import hashlib
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "gate_r9sem_20261109"
sys.path.insert(0, str(ROOT / "lead" / "gate_fp7_20261108"))
import _g7_predicates as g7

OUT = {}

# --- (1) 撰写人声称的 grep -rl ... | wc -l = 46 精确复跑 ---
print("=== (1) 指纹 pin 计数（撰写人命令：--include='*.py' --include='*.mjs' lead .zcode） ===")
needle = "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120"
files = []
for base in (ROOT / "lead", ROOT / ".zcode"):
    for pat in ("*.py", "*.mjs"):
        for p in base.rglob(pat):
            if not p.is_file():
                continue
            try:
                if needle in p.read_text("utf-8", errors="replace"):
                    files.append(str(p.relative_to(ROOT)).replace("\\", "/"))
            except Exception:
                pass
files = sorted(set(files))
OUT["pin_count_py_mjs"] = len(files)
print("  count =", len(files), "(design claims 46)")
print("  breakdown lead/ =", len([f for f in files if f.startswith("lead/")]),
      " .zcode/ =", len([f for f in files if f.startswith(".zcode/")]))
print("  first 8:", files[:8])

# --- (2) R10 对 matrix_ab_ruling 三词 ---
print("\n=== (2) R10 对 RULING_MATRIX_AB.md 的三条越权断言 ===")
t = (ROOT / "lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md").read_text("utf-8")
banned = ["已改矩阵", "已收紧", "已施行", "已改设计"]
p, w, hits = g7.r10_scan(t, banned)
OUT["r10"] = {"problems": p, "n_warnings": len(w), "hits": hits}
print("  problems =", json.dumps(p, ensure_ascii=False))
for h in hits:
    print("     hit", json.dumps(h, ensure_ascii=False))

# --- (3) 32 域主件指纹 vs 基线（撰写人未做的对账） ---
print("\n=== (3) 32 域主件指纹 vs baseline mainSha256/mainBytes ===")
B = json.loads((ROOT / "lead/gate_rejudge32_20261109/_rj_delivery_baseline.json").read_text("utf-8"))
drift = []
for r in B["rows"]:
    p = ROOT / r["domain"].rstrip("/") / r["main"]
    d = p.read_bytes()
    if hashlib.sha256(d).hexdigest() != r["mainSha256"] or len(d) != r["mainBytes"]:
        drift.append(r["domain"])
OUT["main32"] = {"n": len(B["rows"]), "drift": drift, "n_drift": len(drift)}
print("  n =", len(B["rows"]), " drift =", drift)

# --- (4) 复核员回件绑定行惯例：找最近写域中「复核」类回件，看它绑什么 ---
print("\n=== (4) 复核回件绑定行惯例（有限深度扫描） ===")
BIND = re.compile(r"被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)")
# 先看本仓里有没有「复核回件」文件明确写了「被核对象 = <某件>」
cands = []
for d in sorted((ROOT / "lead").iterdir()):
    if not d.is_dir() or not d.name.endswith("20261109"):
        continue
    for f in d.glob("*.md"):
        try:
            head = f.read_text("utf-8", errors="replace")[:1200]
        except Exception:
            continue
        if "复核" in head and BIND.search(head):
            m = BIND.search(head)
            cands.append((str(f.relative_to(ROOT)).replace("\\", "/"),
                          m.group(1), int(m.group(2)), head[:220].replace("\n", " | ")))
print("  找到 %d 件头部含绑定行且头部含「复核」的件：" % len(cands))
for f, h, b, ctx in cands[:12]:
    print("    %-62s %s/%d" % (f[:62], h[:12], b))
    print("       ", ctx[:180])
OUT["review_binding_samples"] = [{"file": f, "hex": h, "bytes": b} for f, h, b, _ in cands]

# 反查：这些 hex 是否对应盘上某文件
idx = {}
for d in (ROOT / "lead").iterdir():
    if not d.is_dir():
        continue
    for f in d.glob("*.md"):
        try:
            raw = f.read_bytes()
        except Exception:
            continue
        idx.setdefault((hashlib.sha256(raw).hexdigest(), len(raw)), []).append(
            str(f.relative_to(ROOT)).replace("\\", "/"))
res = []
for f, h, b, _ in cands:
    res.append({"hex": h[:12], "bytes": b, "resolves_to": idx.get((h, b), [])})
print("  反查（写域 md 内）：")
for x in res[:12]:
    print("    ", x["hex"], x["bytes"], "->", x["resolves_to"][:2])
OUT["review_binding_resolves"] = res

# --- (5) 写域清点 + git 状态 ---
print("\n=== (5) 本会话写域产物 & git 状态 ===")
mine = sorted([p.name for p in WDIR.glob("_r9sv_*")])
OUT["my_artifacts"] = mine
print("  _r9sv_* =", mine)
r = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                   capture_output=True, text=True)
OUT["git_head"] = r.stdout.strip()
print("  git HEAD =", OUT["git_head"])
r2 = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain=v1", "--",
                     "lead/gate_r9sem_20261109"], capture_output=True, text=True)
OUT["git_status_wdir"] = r2.stdout.strip()
print("  git status (wdir) =", OUT["git_status_wdir"][:200])

# --- (6) 设计回件绑定行格式严格校验 ---
print("\n=== (6) 设计回件绑定行格式严格校验 ===")
dt = (WDIR / "_r9s_DESIGN.md").read_text("utf-8")
strict = re.compile(r"^被核对象 SHA256 = [0-9a-f]{64}，字节数 = \d+$", re.M)
ms = strict.findall(dt)
OUT["design_binding_strict"] = {"n_matching_lines": len(ms), "lines": ms}
print("  strict matches =", len(ms), ms)

(WDIR / "_r9sv_final_out.json").write_text(
    json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("\nwrote _r9sv_final_out.json")
