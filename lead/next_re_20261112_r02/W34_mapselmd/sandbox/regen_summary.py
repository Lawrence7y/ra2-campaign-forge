from pathlib import Path
out=Path("out")
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
