# _verify_d_domain.py — ⑥写域外改动审计 + gamemd.exe 指纹复算 + 写域清点
import hashlib, os, datetime

BASE = r"D:\Project\ra2-campaign-forge"

def sha(p):
    h = hashlib.sha256(); n = 0
    with open(p, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b: break
            h.update(b); n += len(b)
    return h.hexdigest(), n

# 1) gamemd.exe 指纹（复算规格自述 73201cc0…/4825360）
gm = os.path.join(BASE, "ra2youli", "gamemd.exe")
if os.path.isfile(gm):
    d, n = sha(gm)
    print(f"[gamemd.exe] sha256={d} bytes={n}")

# 2) 写域清点 + mtime
wd = os.path.join(BASE, "lead", "n11_protocol_spec_20261108")
print("\n[写域 lead/n11_protocol_spec_20261108/ 内容与 mtime]")
spec_mtime = None
for fn in sorted(os.listdir(wd)):
    p = os.path.join(wd, fn)
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d %H:%M:%S")
    print(f"  {fn}  mtime={mt}")
    if fn.endswith("_ps_N11_MIN_OBS_PROTOCOL_SPEC.md"):
        spec_mtime = os.path.getmtime(p)

# 3) 只读保护区关键件 mtime（应早于规格落盘时刻）
prot = [
    r"lead\GOAL_THREE_TARGETS_20261018.md",
    r"lead\PENDING_DECISIONS.md",
    r"lead\direction_ruling_20261108\RULING_DIRECTION.md",
    r"lead\perf_repair_n11_20261108\PERF_REPAIR_HANDOFF.md",
    r"lead\p11_stations_20261108\P11_STATION_NAMING.md",
    r"lead\spec_static_closure_20261108\STATIC_GAP_CLOSURE.md",
    r"lead\slowwindow_n8_20261108\SLOW_WINDOW_LIMITS.md",
    r"lead\d_o1o4_necessity_20261108\O1_O4_NECESSITY.md",
    r"lead\static_spec_n9_20261107\STATIC_COUNT_SPEC.md",
    r"lead\stall_event_def_20261106\STALL_EVENT_DEFINITION.md",
    r"lead\d13d14_cards_20261108\DECISION_QUESTIONS.md",
    r"lead\nextstep_plan_20261106\NEXT_STEPS_20261106.md",
]
print("\n[保护区件 mtime vs 规格落盘时刻]")
smt = datetime.datetime.fromtimestamp(spec_mtime) if spec_mtime else None
for rel in prot:
    p = os.path.join(BASE, rel)
    if not os.path.isfile(p):
        print(f"  [MISS] {rel}"); continue
    mt = os.path.getmtime(p)
    mts = datetime.datetime.fromtimestamp(mt).strftime("%Y-%m-%d %H:%M:%S")
    rel_txt = ""
    if spec_mtime:
        rel_txt = "AFTER-SPEC!" if mt > spec_mtime else "before-spec"
    print(f"  {mts}  {rel_txt:<12} {rel}")

# 4) ra2youli 与 out/re_work 抽样 mtime（不整树走，抽样 + 顶层）
print("\n[ra2youli 顶层最近修改的 5 件]")
tops = []
rd = os.path.join(BASE, "ra2youli")
for fn in os.listdir(rd):
    p = os.path.join(rd, fn)
    if os.path.isfile(p):
        tops.append((os.path.getmtime(p), fn))
for mt, fn in sorted(tops, reverse=True)[:5]:
    print(f"  {datetime.datetime.fromtimestamp(mt).strftime('%Y-%m-%d %H:%M:%S')}  {fn}")
