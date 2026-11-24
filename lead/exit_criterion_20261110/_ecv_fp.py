# _ecv_fp.py — 复核员指纹脚本：15 件基线 + 4 件产物 + designer 关键件，全部只读
import hashlib, os, sys, json

ROOT = r"D:\Project\ra2-campaign-forge"

FILES = [
    "lead/PENDING_DECISIONS.md",
    "lead/GOAL_THREE_TARGETS_20261018.md",
    "lead/const_exit_20261109/_ce_final_out.json",
    "lead/const_exit_20261109/CONST_EXIT_CENSUS.md",
    "lead/andk_rerun_20261109/ANDK_RERUN.md",
    "lead/andk_rerun_20261109/_ak_summary.json",
    "lead/d27_ruling_20261106/check_d27.py",
    "lead/d28_ruling_20261106/check_d28.py",
    "lead/d29_ruling_20261106/check_d29.py",
    "lead/d30_ruling_20261106/check_d30.py",
    "lead/re_line_20261105/D21_RULING/_d21_burden5.py",
    "lead/re_line_20261105/V6_V3_REVIEW/_leader_crossframe_check.py",
    "lead/re_line_20261105/_leader/_a7_acf_probe.py",
    "lead/re_line_20261105/_leader/_intra_frame_census.py",
    "lead/goal1_a8_fix_20261022/VERIFY_A8.py",
    # 四件零信息对象产物
    "lead/re_line_20261105/D21_RULING/_d21_burden5_out.txt",
    "lead/re_line_20261105/V6_V3_REVIEW/_leader_crossframe_check_out.txt",
    "lead/re_line_20261105/_leader/_a7_acf_probe_out.txt",
    "lead/re_line_20261105/_leader/_intra_frame_census_out.txt",
    # 设计员关键件（写域内，供绑定与后续比对）
    "lead/exit_criterion_20261110/_ec_criterion.py",
    "lead/exit_criterion_20261110/_ec_report.md",
    "lead/exit_criterion_20261110/_ec_s3_results.json",
    "lead/exit_criterion_20261110/_ec_s4_results.json",
]

def main():
    out = {}
    for rel in FILES:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            out[rel] = {"error": "MISSING"}
            continue
        b = open(p, "rb").read()
        out[rel] = {"sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b),
                    "mtime": os.path.getmtime(p)}
    print(json.dumps(out, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
