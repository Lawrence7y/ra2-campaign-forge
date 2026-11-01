import json
import glob
import os

BASE = 'out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'

# ★ deadline 在 window 阶段设置：deadline = monotonic() + STAGE_TIMEOUT_S (30s)
#   nav 发生在 window 之后、frame 之前。
#   ⇒ 若「frame 之前累计耗时」> 30 s，则到 frame 时 deadline 早已过期
#     ⇒ while 谓词第二个条件立即为假 ⇒ 循环空转 ⇒ polls 恒为 0（结构性）。
#   本脚本算「frame 之前累计 stage 秒数」，看它是否恒 > 30。

ORDER_BEFORE_FRAME = ['carrier_ownership', 'target_pin', 'ctrl_pre', 'T0',
                      'backup', 'except_baseline', 'mother_freeze', 'launch',
                      'window', 'nav_start', 'nav_menu', 'nav_setup']

rows = []
for f in glob.glob(BASE + '/archive_*/qc151_fields.json'):
    try:
        o = json.load(open(f, encoding='utf-8'))
    except Exception:
        continue
    if not isinstance(o, list):
        continue
    fs = None
    d = {}
    polls = None
    for r in o:
        if not isinstance(r, dict):
            continue
        if r.get('group') == 'META' and r.get('key') == 'fullscreen':
            fs = r.get('value')
        if r.get('group') == 'BUDGET' and str(r.get('key', '')).startswith('stage_seconds:'):
            d[r['key'].split(':', 1)[1]] = r.get('value')
        if r.get('group') == 'FRAME' and r.get('key') == 'pre_capture_wait_polls':
            polls = r.get('value')
    if fs is not None:
        continue                      # 只看窗口模式
    if 'frame' not in d:
        continue
    pre = sum(v for k, v in d.items()
              if k != 'frame' and isinstance(v, (int, float)))
    rows.append((os.path.basename(os.path.dirname(f)), pre, d.get('frame'), polls))

rows.sort(key=lambda r: -r[1])
print("窗口模式：frame 之前累计耗时（决定 deadline 是否早已过期）")
print("%-24s %-10s %-9s %s" % ('trip', 'pre_frame_s', 'frame_s', 'polls'))
for r in rows[:10]:
    print("%-24s %-10.2f %-9s %s" % r)

pres = [r[1] for r in rows]
polls_all = [r[3] for r in rows if isinstance(r[3], (int, float))]
print()
print("n=%d" % len(rows))
if pres:
    print("pre_frame: min=%.2f  max=%.2f" % (min(pres), max(pres)))
    print("  > 30 s 的占比: %d/%d" % (sum(1 for p in pres if p > 30), len(pres)))
if polls_all:
    print("polls: 取值集合 = %s" % sorted(set(polls_all)))
    print("  ==0 的占比: %d/%d" % (sum(1 for p in polls_all if p == 0), len(polls_all)))
