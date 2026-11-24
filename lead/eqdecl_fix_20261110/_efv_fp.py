# _efv_fp.py — 复核员独立指纹核验（before/after 两次调用）
# 只读：对基线十件 + 被核对象 + 修版件自身输出件算 SHA256 与字节数
import hashlib, json, sys, os

ROOT = r"D:\Project\ra2-campaign-forge"
BASELINE = [
    r"lead\PENDING_DECISIONS.md",
    r"lead\GOAL_THREE_TARGETS_20261018.md",
    r"lead\eqdecl_gate_20261109\_eq_detector.py",
    r"lead\eqdecl_gate_20261109\_eq_full_out.json",
    r"lead\eqdecl_gate_20261109\_eq_three_gates_out.json",
    r"lead\eqdecl_gate_20261109\EQDECL_GATE.md",
    r"lead\comparability_20261109\COMPARABILITY_AUDIT.md",
    r"lead\layer_identity_20261109\LAYER_IDENTITY.md",
    r"lead\metric_audit_20261109\METRIC_CONVENTION_AUDIT.md",
    r"lead\tautology_audit_20261109\TAUTOLOGY_AUDIT.md",
]
EXTRA = [  # 无编排方基线的其余只读目录（记录会话起止一致性）
    r"lead\eqdecl_gate_20261109\_eq_DESIGN.md",
    r"lead\eqdecl_gate_20261109\_eq_CONCLUSION.md",
    r"lead\eqdecl_gate_20261109\_eq_three_gates.py",
    r"lead\eqdecl_gate_20261109\_eq_full_run.py",
    r"lead\keff_calc_20261109",
    r"lead\evidence_indep_20261109",
    r"lead\score_decomp_20261109",
    r"lead\chain_vs_single_20261109",
]
SUBJECT = r"lead\eqdecl_fix_20261110\_ef_detector.py"

def fp(rel):
    p = os.path.join(ROOT, rel)
    h = hashlib.sha256()
    n = 0
    if os.path.isdir(p):
        # 目录：对内部所有文件排序后聚合指纹
        agg = hashlib.sha256()
        cnt = 0
        for dirpath, dirnames, filenames in os.walk(p):
            dirnames.sort()
            for fn in sorted(filenames):
                fp2 = os.path.join(dirpath, fn)
                agg.update(fp2.encode("utf-8"))
                with open(fp2, "rb") as f:
                    agg.update(hashlib.sha256(f.read()).digest())
                cnt += 1
        return {"dir": True, "n_files": cnt, "sha256": agg.hexdigest()}
    with open(p, "rb") as f:
        while True:
            data = f.read(1 << 20)
            if not data:
                break
            h.update(data)
            n += len(data)
    return {"sha256": h.hexdigest(), "bytes": n}

out = {}
tag = sys.argv[1] if len(sys.argv) > 1 else "run"
for rel in BASELINE:
    out[rel] = fp(rel)
for rel in EXTRA:
    out["extra:" + rel] = fp(rel)
out["subject:" + SUBJECT] = fp(SUBJECT)
print(json.dumps({"tag": tag, "fps": out}, ensure_ascii=False, indent=1))
