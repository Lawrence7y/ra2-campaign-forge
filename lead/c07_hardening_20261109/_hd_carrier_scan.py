# -*- coding: utf-8 -*-
# _hd_carrier_scan.py — 只读侦察：lead/ 树内「机器运行态载体」存量盘点。
# 定义：*.json 可解析且顶层含 recordedAt(ISO8601 字符串) + sessionId(非空字符串) 两字段。
# 用途：为 C07 五项加固设计（①在先性 ③对照集扩容 ⑤载体分类）提供实测基数。
# 纪律：绝对只读——os.walk + open(rb) + os.stat，不写、不改、不删任何仓库文件；零真机、零采样。
import json
import os
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WALK = os.path.join(ROOT, "lead")
SKIP = {".git", "__pycache__", "node_modules", ".zcode"}
MAXB = 1024 * 1024


def dom(rel):
    parts = rel.replace("\\", "/").split("/")
    return parts[1] if len(parts) > 2 and parts[0] == "lead" else (parts[1] if len(parts) > 1 else rel)


carriers = []  # (rel, sid, recordedAt, mtime_local_iso)
njson = 0
for dp, dn, fn in os.walk(WALK):
    dn[:] = [d for d in dn if d not in SKIP]
    for f in fn:
        if not f.lower().endswith(".json"):
            continue
        p = os.path.join(dp, f)
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        try:
            if os.path.getsize(p) > MAXB:
                continue
            with open(p, "rb") as fh:
                obj = json.loads(fh.read().decode("utf-8"))
        except (OSError, ValueError, UnicodeDecodeError):
            continue
        njson += 1
        if (isinstance(obj, dict)
                and isinstance(obj.get("recordedAt"), str) and obj["recordedAt"].strip()
                and isinstance(obj.get("sessionId"), str) and obj["sessionId"].strip()):
            st = os.stat(p)
            carriers.append((rel, obj["sessionId"], obj["recordedAt"],
                             datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")))

sids = {}
for rel, sid, ra, mt in carriers:
    sids.setdefault(sid, []).append(rel)
forms = {"dwf": [], "session_hex": [], "other": []}
for s in sids:
    if s.startswith("sess_dwf-dwfrun-"):
        forms["dwf"].append(s)
    elif s.startswith("session_"):
        forms["session_hex"].append(s)
    else:
        forms["other"].append(s)

doms = {}
for rel, sid, ra, mt in carriers:
    doms.setdefault(dom(rel), set()).add(sid)

print("json parsed=%d ; machine carriers(files)=%d ; distinct sessionId=%d" % (njson, len(carriers), len(sids)))
print("form counts: " + ", ".join("%s=%d" % (k, len(v)) for k, v in sorted(forms.items())))
print("carrier write domains=%d" % len(doms))
for d in sorted(doms):
    nf = sum(1 for c in carriers if dom(c[0]) == d)
    print("  %-36s carrier_files=%-3d distinct_sid=%d" % (d, nf, len(doms[d])))

# 物理不可能信号：本地 mtime 日期 < recordedAt 折算本地日期（真载体不应出现；出现=伪造/回填/恢复嫌疑）
sus = 0
for rel, sid, ra, mt in carriers:
    try:
        rdt = datetime.fromisoformat(ra.replace("Z", "+00:00")).astimezone().date()
        mdt = datetime.fromisoformat(mt).date()
    except ValueError:
        sus += 1
        print("  UNPARSEABLE %s recordedAt=%r mtime=%s" % (rel, ra, mt))
        continue
    if mdt < rdt:
        sus += 1
        print("  SUSPECT mtime<recordedAt %s recordedAt=%s mtime=%s sid=%s" % (rel, ra, mt, sid[:52]))
print("mtime<recordedAt 嫌疑件=%d（0=全树自洽；>0 需逐件人工看）" % sus)
