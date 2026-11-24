# -*- coding: utf-8 -*-
# _wlv_guard.py — 用复核轮 _r9sv_extra.py:39-41 的同一 guard_words 词表独立复算 13/24
import sys
from pathlib import Path
ROOT = Path(r"D:\Project\ra2-campaign-forge")
sys.path.insert(0, str(ROOT/"lead/gate_r9sem_20261109"))
import _r9s_samples as S
guard_words = ["待指定", "尚未", "无需批准", "待验", "输出未采集", "PROBE_DONE", "详见",
               "索引", "TBD", "待定", "略。", "不可重建", "待补", "未验", "无输出",
               "待确认", "见附件", "需进一步"]
with_ids, without = [], []
for s in S.NEG:
    hits = [w for w in guard_words if w in s["text"]]
    (with_ids if hits else without).append((s["id"], hits))
print(f"含现成守卫词/占位词 = {len(with_ids)}/{len(S.NEG)}；不含 = {len(without)}")
for i,h in with_ids: print(f"  WITH {i}: {h}")
print("不含 ids =", [i for i,_ in without])
