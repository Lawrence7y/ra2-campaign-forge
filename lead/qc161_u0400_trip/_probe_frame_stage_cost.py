import json
import glob
import os
import statistics

BASE = 'out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'

# ★ 核心恒等式：frame 段 = 矩形等待(polls × 0.5s) + 采帧 + 分类
#   ⇒ (capture + classify) = stage_seconds:frame − polls × 0.5
#   这给出**真实产物**里「采帧+分类」的实测开销，无需真机也能算。

rows = []
for f in glob.glob(BASE + '/l*_2026102*/qc151_fields.json') + \
        glob.glob(BASE + '/archive_*/qc151_fields.json'):
    try:
        o = json.load(open(f, encoding='utf-8'))
    except Exception:
        continue
    if not isinstance(o, list):
        continue
    d = {}
    for r in o:
        if isinstance(r, dict) and r.get('group') == 'BUDGET' \
                and str(r.get('key', '')).startswith('stage_seconds:'):
            d[r['key'].split(':', 1)[1]] = r.get('value')
    fr = d.get('frame')
    polls = None
    fs = None
    for r in o:
        if not isinstance(r, dict):
            continue
        if r.get('group') == 'FRAME' and r.get('key') == 'pre_capture_wait_polls':
            polls = r.get('value')
        if r.get('group') == 'META' and r.get('key') == 'fullscreen':
            fs = r.get('value')
    if fr is None or polls is None:
        continue
    est = fr - polls * 0.5
    rows.append((os.path.basename(os.path.dirname(f)), fs is not None,
                 fr, polls, round(est, 3)))

rows.sort(key=lambda r: r[4])
print("frame 段 = 等待 + 采帧 + 分类   ⇒   采帧+分类 = frame − polls×0.5")
print("%-24s %-6s %-10s %-7s %s" % ('trip', '全屏', 'frame_s', 'polls', '采帧+分类'))
for r in rows:
    print("%-24s %-6s %-10s %-7s %s" % r)

vals = [r[4] for r in rows]
print()
if vals:
    print("n=%d  min=%.3f  max=%.3f  median=%.3f  mean=%.3f"
          % (len(vals), min(vals), max(vals),
             statistics.median(vals), statistics.mean(vals)))
    print()
    print("判档器 fullscreen_short 判据: frame_s < 2.0 s")
    print("  在 polls 归零（短路生效）时，frame 段 ≈ 采帧+分类 = %.3f s" % max(vals))
    print("  ⇒ 余量 %.2f s（%.1f 倍）" % (2.0 - max(vals), 2.0 / max(vals) if max(vals) > 0 else 0))
