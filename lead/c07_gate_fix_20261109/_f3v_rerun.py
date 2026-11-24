# _f3v_rerun.py -- independent double-runner (reviewer's own, not the author's)
# usage: python -I -X utf8 _f3v_rerun.py <checker_abs_path> <out_transcript> <out_summary>
# targets: 36 samples in _c7a_samples + the unfilled template (37 total)
import subprocess, sys, os, json
BASE = r"D:\Project\ra2-campaign-forge"
checker = os.path.abspath(sys.argv[1])
out_tx = os.path.abspath(sys.argv[2])
out_sum = os.path.abspath(sys.argv[3])
sd = os.path.join(BASE, "lead", "c07_gate_audit_20261109", "_c7a_samples")
targets = [os.path.join(sd, n) for n in sorted(os.listdir(sd)) if n.endswith(".json")]
targets.append(os.path.join(BASE, "lead", "c07_slot_20261109", "_c7_record_template.json"))
py = sys.executable
results = {}
with open(out_tx, "w", encoding="utf-8", newline="\n") as tx:
    for t in targets:
        name = os.path.basename(t)
        proc = subprocess.run([py, "-I", "-X", "utf8", checker, t],
                              capture_output=True, cwd=BASE)
        so = proc.stdout.decode("utf-8", "replace")
        se = proc.stderr.decode("utf-8", "replace")
        results[name] = proc.returncode
        tx.write("===== %s exit=%d =====\n" % (name, proc.returncode))
        tx.write(so)
        if se:
            tx.write("--- STDERR ---\n" + se)
        tx.write("\n")
blocked = sorted(k for k, v in results.items() if v == 1)
passed = sorted(k for k, v in results.items() if v == 0)
other = sorted(k for k, v in results.items() if v not in (0, 1))
with open(out_sum, "w", encoding="utf-8", newline="\n") as f:
    json.dump({"checker": checker, "n_targets": len(targets), "results": results,
               "blocked": blocked, "passed": passed, "other": other},
              f, ensure_ascii=False, indent=1)
print("checker:", checker)
print("targets:", len(targets), "blocked:", len(blocked), "passed:", len(passed), "other:", len(other))
print("blocked:", ", ".join(blocked))
print("passed:", ", ".join(passed))
print("other:", ", ".join(other))
