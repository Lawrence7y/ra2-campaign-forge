# _shv_fp.py — 复核员指纹自算（只读；hashlib；绝对路径）
import hashlib, os, sys

FILES = [
    r"D:/Project/ra2-campaign-forge/lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md",
    r"D:/Project/ra2-campaign-forge/lead/s604_exclusive_20261109/S604_EXCLUSIVITY.md",
    r"D:/Project/ra2-campaign-forge/lead/s604_attribution_20261108/S604_ATTRIBUTION.md",
    r"D:/Project/ra2-campaign-forge/lead/slowframe_r3_20261108/S604_GAP_RECHECK.md",
    r"D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md",
    r"D:/Project/ra2-campaign-forge/lead/PENDING_DECISIONS.md",
    r"D:/Project/ra2-campaign-forge/lead/s604_script_hunt_20261109/_sh_fp_out.txt",
    r"D:/Project/ra2-campaign-forge/lead/s604_script_hunt_20261109/_sh_generator_512655.txt",
    r"D:/Project/ra2-campaign-forge/lead/s604_script_hunt_20261109/_sh_gen512655_payload.py",
    r"D:/Project/ra2-campaign-forge/lead/s604_script_hunt_20261109/_sh_gen512655_out.txt",
    r"D:/Project/ra2-campaign-forge/lead/s604_script_hunt_20261109/_sh_findings.md",
    r"C:/Users/Administrator/.zcode/cli/db/db.sqlite",
]
for p in FILES:
    try:
        h = hashlib.sha256()
        n = 0
        with open(p, "rb") as f:
            while True:
                b = f.read(1 << 20)
                if not b:
                    break
                h.update(b)
                n += len(b)
        st = os.stat(p)
        print(f"{p}\n  sha256={h.hexdigest()}  bytes={n}  mtime={st.st_mtime:.3f}  size={st.st_size}")
    except Exception as e:
        print(f"{p}\n  ERROR {type(e).__name__}: {e}")
print("PYVER", sys.version)
