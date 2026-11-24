# _verify_a_fingerprint.py — 复核员独立实算指纹（不复用规格员脚本）
# 只读：hashlib 实算 SHA256 + 字节数
import hashlib, os

BASE = r"D:\Project\ra2-campaign-forge"

TARGETS = {
    # 被核对象
    "TARGET lead/n11_protocol_spec_20261108/_ps_N11_MIN_OBS_PROTOCOL_SPEC.md":
        r"lead\n11_protocol_spec_20261108\_ps_N11_MIN_OBS_PROTOCOL_SPEC.md",
    # 编排方指纹表 7 件
    "RULING lead/direction_ruling_20261108/RULING_DIRECTION.md":
        r"lead\direction_ruling_20261108\RULING_DIRECTION.md",
    "PERF lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md":
        r"lead\perf_repair_n11_20261108\PERF_REPAIR_HANDOFF.md",
    "P11 lead/p11_stations_20261108/P11_STATION_NAMING.md":
        r"lead\p11_stations_20261108\P11_STATION_NAMING.md",
    "SGC lead/spec_static_closure_20261108/STATIC_GAP_CLOSURE.md":
        r"lead\spec_static_closure_20261108\STATIC_GAP_CLOSURE.md",
    "N8 lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md":
        r"lead\slowwindow_n8_20261108\SLOW_WINDOW_LIMITS.md",
    "O14 lead/d_o1o4_necessity_20261108/O1_O4_NECESSITY.md":
        r"lead\d_o1o4_necessity_20261108\O1_O4_NECESSITY.md",
    "NEXT lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md":
        r"lead\nextstep_plan_20261106\NEXT_STEPS_20261106.md",
    # 回件 evidence 自述另算的件
    "N-9 lead/GOAL_THREE_TARGETS_20261018.md": None,  # N-9 具体路径待定，先占位
    "PEND lead/PENDING_DECISIONS.md":
        r"lead\PENDING_DECISIONS.md",
    "DQ lead/DECISION_QUESTIONS.md": None,  # 路径待查
}

def sha(p):
    h = hashlib.sha256()
    n = 0
    with open(p, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
            n += len(b)
    return h.hexdigest(), n

for label, rel in TARGETS.items():
    if rel is None:
        print(f"[SKIP] {label} (路径待定)")
        continue
    p = os.path.join(BASE, rel)
    if not os.path.isfile(p):
        print(f"[MISS] {label} -> {rel}")
        continue
    d, n = sha(p)
    print(f"[OK] {label}\n     sha256={d}\n     bytes={n}")

# 找 DECISION_QUESTIONS.md 与 N-9 的实际位置
for root, dirs, files in os.walk(os.path.join(BASE, "lead")):
    dirs[:] = [d for d in dirs if d not in (".git",)]
    for fn in files:
        if fn.upper() in ("DECISION_QUESTIONS.MD",):
            print("[FOUND] DECISION_QUESTIONS: " + os.path.join(root, fn))
