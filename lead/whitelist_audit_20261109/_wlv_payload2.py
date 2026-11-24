# -*- coding: utf-8 -*-
# _wlv_payload2.py — 追查 matrix_reach 第二步原文实跑输出措辞 + s604 歧义句 + R9SEM 第一步要求
import json, re
from pathlib import Path
ROOT = Path(r"D:\Project\ra2-campaign-forge\.zcode\workflow-runs")
def lowered(fn):
    t = (ROOT/fn).read_text(encoding="utf-8", errors="replace")
    i = t.find("export const payload = ")
    low,_ = json.JSONDecoder().raw_decode(t[i+len("export const payload = "):])
    return low.get("lowered","")

mr = lowered("dwfrun-c482b235-41c5-431b-b9d9-2617c362b1cc.mjs")
print("=== matrix_reach lowered 中 实跑 / 输出 / 第二步 出现处 ===")
for kw in ["实跑输出","实跑","第二步","不许写","理论上可以","构造的输入字典","实际返回","落入矩阵哪一行","与矩阵声称是否一致","附实跑输出"]:
    idxs = [m.start() for m in re.finditer(re.escape(kw), mr)]
    print(f"  {kw!r}: {len(idxs)} hits at {idxs[:8]}")
print("\n=== 第二步整段（『第二步』前后 900 字符逐字）===")
i = mr.find("第二步")
print(repr(mr[max(0,i-100): i+900]))
print("\n=== 含『实跑输出』的整行（逐字）===")
for m in re.finditer("实跑输出", mr):
    s = mr.rfind("\n",0,m.start())+1; e=mr.find("\n",m.end())
    print(repr(mr[s:(e if e>=0 else len(mr))]))

s604 = lowered("dwfrun-bc9d8b8e-9faa-4226-8022-ccd881335683.mjs")
print("\n=== s604: 『若脚本确实不在盘且无法重建』歧义句 ===")
for kw in ["若脚本确实不在盘且无法重建","如实说无法重建","不许为了给出答案而编造脚本内容或推测算法细节充数","只查脚本存在性与可重建性"]:
    idxs=[m.start() for m in re.finditer(re.escape(kw), s604)]
    print(f"  {kw!r}: {len(idxs)} hits {idxs[:5]}")
    for j in idxs[:2]:
        s=s604.rfind("\n",0,j)+1; e=s604.find("\n",j+len(kw))
        print("    ",repr(s604[s:(e if e>=0 else len(s604))]))

r9 = lowered("dwfrun-8156bb52-3202-457d-bbde-6774ee112fb8.mjs")
print("\n=== R9SEM: 第一步『独立复核 5 处』整段 + 白名单相关措辞 ===")
i=r9.find("第一步 独立复核 5 处")
print(repr(r9[max(0,i-50): i+1400]))
for kw in ["白名单","预先指定的例外","自证","语义真值","第三方"]:
    idxs=[m.start() for m in re.finditer(re.escape(kw), r9)]
    print(f"  {kw!r}: {len(idxs)} hits {idxs[:6]}")
