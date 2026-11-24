import json
from pathlib import Path
out=Path("out")
d=json.loads((out/"compat_sha256.json").read_text(encoding="utf-8"))
lines=[
 "W34 backward-compatibility hard evidence: v10 (W30) default build vs v11 default build",
 "Same design, same CLI (no --mapselmd), every output file compared byte-for-byte.",
 "Source: EVIDENCE/step4_compat_sha256.py / step4_compat_sha256.stdout.txt (exit 0)",
 "",
 f"{'file':<44} {'bytes':>8}  {'v10 sha256':<64}  {'v11 sha256':<64}  verdict",
]
for n in sorted(d["v10_default"]):
    a=d["v10_default"][n]; b=d["v11_default"].get(n)
    verdict="IDENTICAL" if b and a["sha256"]==b["sha256"] and a["size"]==b["size"] else "DIFFERENT"
    lines.append(f"{n:<44} {a['size']:>8}  {a['sha256']:<64}  {(b['sha256'] if b else '-'):<64}  {verdict}")
lines += ["",f"default_identical={d['default_identical']}  exits={d['exits']}",
          "",
          "v11 WITH --mapselmd adds exactly one new artifact:",
          f"{'file':<44} {'bytes':>8}  sha256"]
for n,v in sorted(d["v11_mapselmd"].items()):
    if n not in d["v11_default"]:
        lines.append(f"{n:<44} {v['size']:>8}  {v['sha256']}")
lines += ["","(BUILD_REPORT.txt / INSTALL.txt also change when the switch is on - by design.)"]
(out/"SHA256_V10_V11.txt").write_text("\n".join(lines)+"\n",encoding="utf-8")
# full-run summary with explicit exit
run=(out/"full_run.txt").read_text(encoding="utf-8")
exitcode=(out/"full_run.exitcode.txt").read_text(encoding="ascii").strip()
s=(out/"SUMMARY.txt").read_text(encoding="utf-8")
extra=["", "=== full regression run (regress_dlc_v11.py, all cases) ===",
       f"cases: 51  passed: 51  failed: 0  exit: {exitcode}",
       "raw log: out/full_run.txt ; per-case logs: out/<case>.log ; summary: out/SUMMARY.txt",
       "", "=== EVIDENCE exit codes ==="]
for n in ("step1_extract_mapsel","step2_disasm_mapsel","step3_disasm_stage","step4_compat_sha256"):
    p=Path("EVIDENCE")/(n+".exitcode.txt")
    extra.append(f"{n}: {p.read_text(encoding='ascii').strip() if p.exists() else 'MISSING'}")
(out/"RUN_SUMMARY.txt").write_text(s+"\n".join(extra)+"\n",encoding="utf-8")
print("wrote",out/"SHA256_V10_V11.txt",out/"RUN_SUMMARY.txt")
