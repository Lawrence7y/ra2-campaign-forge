# -*- coding: utf-8 -*-
r"""_n13v_hist_gate_replay.py — 复核⑤：逐字重建 dwfrun-614dbceb GATE_CODE 并实跑

同时只读查 CLI 会话库，找是否真有「四条问题」的门禁输出。
零真机、零采样；只做静态文本 + hashlib + sqlite 只读 + 子进程实跑重建门禁。
"""
import hashlib
import importlib.util
import json
import pathlib
import re
import sqlite3
import subprocess
import sys

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "gate_n13_20261109"
PAYLOAD = ROOT / ".zcode/workflow-runs/dwfrun-614dbceb-b7e1-4dbb-b811-41d148f56a9a.mjs"

# 逐字取自 PAYLOAD 的 GATE_CODE 数组（唯一改动：PRE_* 三行用现盘实算 SHA 代入，
# 与 payload 内 JS 拼接 "PRE_L='" + ledSha + "'" 等价）
GATE_CODE = [
    "import json,pathlib,re,hashlib",
    "root=pathlib.Path('D:/Project/ra2-campaign-forge')",
    "wd=root/'lead/ledger_bound_20261109'",
    "P=[]",
    "expected=wd/'LEDGER_BOUND_VOLUME.md'",
    "if not expected.is_file(): P.append('主交付件未按约定命名 LEDGER_BOUND_VOLUME.md')",
    "else:",
    " t=expected.read_text(encoding='utf-8');NB=expected.stat().st_size",
    " for s in ['## 1','## 2','## 3','## 4','## 5']:",
    "  if s not in t: P.append('缺小节 '+s)",
    " for k in ['待入账','笔3','第五笔','§609','冲突','依赖','编号','逐字照抄','未改台账','未验']:",
    "  if k not in t: P.append('缺要素 '+k)",
    " for bad in ['已入账','已追加','已生效']:",
    "  if bad in t: P.append('含越权断言 '+bad)",
    " B=len(re.findall(r'被核对象 SHA256 = [0-9a-fA-F]{64}',t))",
    " if B<1: P.append('缺规范格式绑定行')",
    "PRE_L='@@LED@@'",
    "PRE_H='@@HEAD@@'",
    "PRE_S='@@S609@@'",
    "for lbl,rel,pre in [('目标台账','lead/GOAL_THREE_TARGETS_20261018.md',PRE_L),('PENDING','lead/PENDING_DECISIONS.md',PRE_H),('§609草案','lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md',PRE_S)]:",
    " p=root/rel",
    " cur=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'MISSING'",
    " if cur!=pre: P.append(lbl+' 被改动 pre='+pre[:12]+' cur='+cur[:12])",
    "print(json.dumps({'ok':not P,'problems':P,'bindings':(B if expected.is_file() else 0)},ensure_ascii=False))",
]


def sha(rel):
    p = ROOT / rel
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "MISSING"


def main():
    print("=" * 78)
    print("⑤ 历史 GATE_CODE 逐字重建 + 现盘实跑")
    print("=" * 78)
    t = PAYLOAD.read_text(encoding="utf-8")
    i = t.find("const GATE_CODE = [")
    j = t.find("].join", i)
    arr = t[i:j + 1]
    for ln in GATE_CODE:
        key = ln.replace("@@LED@@", "").replace("@@HEAD@@", "").replace("@@S609@@", "")
        if key and key not in arr:
            print("  !! 重建行未在 payload 中找到:", repr(ln))
    print("  重建行数 =", len(GATE_CODE), "| payload GATE_CODE 长度 =", len(arr))

    led = sha("lead/GOAL_THREE_TARGETS_20261018.md")
    head = sha("lead/PENDING_DECISIONS.md")
    s609 = sha("lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md")
    print("  三 SHA（现盘实算）:", led[:12], head[:12], s609[:12])
    src = "\n".join(GATE_CODE)
    src = src.replace("@@LED@@", led).replace("@@HEAD@@", head).replace("@@S609@@", s609)
    out = WD / "_n13v_hist_gate_replay_code.py"
    out.write_text(src, encoding="utf-8")
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", str(out)],
                       capture_output=True, text=True, encoding="utf-8")
    print("  子进程命令:", " ".join([sys.executable, "-I", "-X", "utf8", str(out)]))
    print("  exit =", r.returncode, "| stdout =", r.stdout.strip(), "| stderr =", r.stderr.strip()[:300])
    g = json.loads(r.stdout.strip())
    print("  problems 条数 =", len(g["problems"]), "| 逐条:", json.dumps(g["problems"], ensure_ascii=False))
    print("  bindings =", g["bindings"])

    # 谓词化门禁对同一 t
    spec = importlib.util.spec_from_file_location("_n13v_hist_n13", WD / "_n13_predicates.py")
    n13 = importlib.util.module_from_spec(spec); spec.loader.exec_module(n13)
    spec2 = importlib.util.spec_from_file_location("_n13v_hist_g7", ROOT / "lead/gate_fp7_20261108/_g7_predicates.py")
    g7 = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(g7)
    text = (ROOT / "lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md").read_text(encoding="utf-8")
    probs, det = n13.r13_assertions(text, ["已入账", "已追加", "已生效"],
                                     r10_scan=g7.r10_scan, r12_scan=g7.r12_scan)
    print("  谓词化门禁 problems =", json.dumps(probs, ensure_ascii=False),
          "| D 类数 =", sum(1 for d in det if d["kind"] == "D"))
    for p in g["problems"]:
        if p.startswith("含越权断言"):
            tok = p.split()[-1]
            still = any(tok in q for q in probs)
            print("  旧问题", repr(p), "→ 谓词化后", "仍在" if still else "消失")

    print()
    print("=" * 78)
    print("⑤b 只读查 CLI 会话库：是否存在「四条问题」的门禁输出")
    print("=" * 78)
    db = r"C:/Users/Administrator/.zcode/cli/db/db.sqlite"
    con = sqlite3.connect("file:" + db + "?mode=ro", uri=True)
    cur = con.cursor()
    cur.execute("select rowid,data from part where rowid in (613246,613929)")
    for rid, data in cur.fetchall():
        s = data.replace("\\n", "\n")
        idx = s.find("门禁问题")
        if idx < 0:
            idx = s.find("门禁 FAIL")
        print("  rowid", rid, "len", len(data), "| 摘录:",
              repr(s[max(0, idx - 40):idx + 150]))
    pat = re.compile(r'"problems"\s*:\s*\[([^\]]{10,800})\]')
    four = []
    cur.execute("select rowid,data from part where data like ?", ('%含越权断言%',))
    for rid, data in cur.fetchall():
        for m in pat.finditer(data):
            items = re.findall(r'"([^"]{4,80})"', m.group(1))
            if len(items) >= 4 and any("已入账" in x for x in items):
                four.append((rid, items))
    print("  part 表内含 >=4 条 problems 且含「已入账」的 JSON 数组命中 =", len(four))
    for rid, items in four[:8]:
        print("   ", rid, items)
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
