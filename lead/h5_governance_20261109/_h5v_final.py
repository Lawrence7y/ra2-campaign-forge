# -*- coding: utf-8 -*-
r"""_h5v_final.py — 收尾复核：NEW 九条逐项、26 处 H5 来源明细、越界 git/文件核对。"""
import sys, json, importlib.util, hashlib, subprocess, time, re
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:\Project\ra2-campaign-forge")
HERE = ROOT / "lead" / "h5_governance_20261109"
RULE = ROOT / "lead" / "gate_v1v2_20261109" / "_v12_rule.py"


def _import(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


OLD = _import("_h5v_old4", RULE)
NEW = _import("_h5v_new4", HERE / "_h5v_patched.py")


def run(mod, text, tok, pos=None):
    p = text.find(tok) if pos is None else pos
    r = mod.classify_v12(text, p, p + len(tok), tok)
    return {"verdict": r["verdict"], "hard": r["hard"], "override": r["override"],
            "review": r["review_flag"], "weak": r["weak"]}


NINE = [
 ("REGRESS1", "本笔已入账 0 命中不得写成未入账", "已入账", "CATCH"),
 ("REGRESS2", "审阅不得不承认本候选已生效。", "已生效", "CATCH"),
 ("CTRL_OK", "本件已生效，可应用母本", "已生效", "CATCH"),
 ("TRUE_NEG", "本节登记不宣告 N-4 正式绑定已生效", "已生效", "PASS"),
 ("TRAIL_NEG", "已入账不得重复登记", "已入账", "CATCH"),
 ("LEAD_NEG", "不得写成已入账", "已入账", "PASS"),
 ("DOUBLE_1", "并非不宣告已生效", "已生效", "CATCH"),
 ("DOUBLE_2", "不能不说本笔已入账", "已入账", "CATCH"),
 ("DOUBLE_3", "无不认为本件已生效", "已生效", "CATCH"),
]
print("=== NEW 修后副本跑九条（宣称：9/9） ===")
nine = []
for cid, text, tok, exp in NINE:
    o, n = run(OLD, text, tok), run(NEW, text, tok)
    d = "PASS" if n["verdict"] == "V1" else "CATCH"
    od = "PASS" if o["verdict"] == "V1" else "CATCH"
    print("%-10s exp=%-5s old=%-5s new=%-5s newOK=%-5s hard=%r ov=%r" %
          (cid, exp, od, d, d == exp, n["hard"], n["override"]))
    nine.append(dict(id=cid, expect=exp, old=od, new=d, ok=d == exp,
                     hard=n["hard"], override=n["override"]))
print("NEW nine = %d/9" % sum(x["ok"] for x in nine))

# ---- 26 处 H5 来源明细 ----
bl = json.loads((ROOT / "lead" / "gate_rejudge32_20261109" / "_rj_delivery_baseline.json").read_text(encoding="utf-8"))
sh = json.loads((ROOT / "lead" / "v12_impact_20261109" / "_vi_shadow_out.json").read_text(encoding="utf-8"))
by = {d["domain"]: d for d in sh["rows"]}
print("\n=== 26 处现盘命中：哪些靠 H5、是否仍是旧口径误豁免 ===")
detail = []
h5cnt = 0
for r in bl["rows"]:
    text = (ROOT / r["domain"] / r["main"]).read_bytes().decode("utf-8")
    rec = by.get(r["domain"])
    for h in (rec["hits"] if rec else []):
        pos, tok = h["pos"], h["token"]
        o, n = run(OLD, text, tok, pos), run(NEW, text, tok, pos)
        h5_old = any("H5" in x for x in o["hard"])
        h5_new = any("H5" in x for x in n["hard"])
        h5cnt += h5_old
        detail.append(dict(domain=r["domain"], pos=pos, token=tok,
                           old=o["verdict"], new=n["verdict"],
                           h5_old=h5_old, h5_new=h5_new,
                           old_hard=o["hard"], new_hard=n["hard"],
                           gateProblems=r["gateProblems"],
                           r10_problems=(rec or {}).get("r10_problems")))
        if h5_old != h5_new or o["verdict"] != n["verdict"]:
            print("  DIFF %s pos=%d tok=%s H5 %s->%s verdict %s->%s" %
                  (r["domain"], pos, tok, h5_old, h5_new, o["verdict"], n["verdict"]))
print("  26 处中 old 靠 H5 豁免 = %d；new 靠 H5 豁免 = %d；DIFF 数 = %d" %
      (h5cnt, sum(x["h5_new"] for x in detail),
       sum(1 for x in detail if x["h5_old"] != x["h5_new"] or x["old"] != x["new"])))
print("  注：26/26 全为 V1（old 与 new 皆同），changed=0 只说明『没引入判定变化』，")
print("      不等于『本来对的仍对』——本脚本额外给出 gateProblems / r10_problems 作旁证：")
print("  gateProblems 非空处数 =", sum(1 for x in detail if x["gateProblems"]),
      " r10_problems>0 处数 =", sum(1 for x in detail if (x["r10_problems"] or 0) > 0))

# ---- 越界 git 状态 ----
print("\n=== ⑧ git status（只读件路径 + 写域） ===")
cmd = ["git", "-C", str(ROOT), "status", "--porcelain", "--",
       "lead/gate_v1v2_20261109", "lead/v12_impact_20261109",
       "lead/gate_n13_20261109", "lead/gate_fp7_20261108",
       "lead/gate_pipeline_20261109", "lead/PENDING_DECISIONS.md",
       "lead/GOAL_THREE_TARGETS_20261018.md", "lead/h5_governance_20261109"]
r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
print("  cmd = git -C <ROOT> status --porcelain -- <8 read-only paths + write domain>")
print("  rc =", r.returncode)
for l in (r.stdout or "").splitlines()[:40]:
    print("   ", l)
print("  (stderr) ", (r.stderr or "").strip()[:200])

# ---- 只读目录内是否有本次会话新写入（按 mtime 粗筛，阈值 14:35） ----
print("\n=== ⑧ 只读域 mtime > 2026-11-09 14:35 的文件（粗筛） ===")
import datetime
cut = datetime.datetime(2026, 11, 9, 14, 35).timestamp()
readdirs = ["lead/gate_v1v2_20261109", "lead/v12_impact_20261109",
            "lead/gate_n13_20261109", "lead/gate_fp7_20261108",
            "lead/gate_pipeline_20261109"]
new = []
for d in readdirs:
    for p in (ROOT / d).rglob("*"):
        if p.is_file() and p.stat().st_mtime > cut:
            new.append((str(p.relative_to(ROOT)).replace("\\", "/"),
                        time.strftime("%H:%M:%S", time.localtime(p.stat().st_mtime))))
print("  count =", len(new))
for x in new[:20]:
    print("   ", x)
print("  两本台账 mtime =",
      [(f, time.strftime("%H:%M:%S", time.localtime((ROOT / f).stat().st_mtime)))
       for f in ["lead/PENDING_DECISIONS.md", "lead/GOAL_THREE_TARGETS_20261018.md"]])

# ---- 写域最终清单 ----
wf = sorted(p.name for p in HERE.iterdir() if p.is_file())
print("\n=== ⑧ 写域最终文件清单 (n=%d) ===" % len(wf))
for f in wf:
    print("   ", f)

(HERE / "_h5v_final_out.json").write_text(
    json.dumps({"nine_new": nine, "detail26": detail}, ensure_ascii=False, indent=1),
    encoding="utf-8")
print("\nwritten: _h5v_final_out.json")
