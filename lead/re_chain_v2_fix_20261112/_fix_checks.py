# -*- coding: utf-8 -*-
"""C1-C6 独立复核 + 收尾指纹。用法:
  python -I -X utf8 <abs>/_fix_checks.py          -> 首次: 输出复核结果并生成 _fix_baseline.json
  python -I -X utf8 <abs>/_fix_checks.py verify   -> 收尾: 重算并与基线比对, 报零改动
零真机；只读既有件；只在本新建写域内落盘输出/基线。
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
LEAD = os.path.join(REPO, "lead")
SYNTH = os.path.join(LEAD, "re_chain_synth_v2_20261111")
XVER = os.path.join(LEAD, "re_chain_v2_xverify_20261112")
BENCH = os.path.join(REPO, "ra2bench", "gamemd.exe")
BASE = os.path.join(HERE, "_fix_baseline.json")
OUT = os.path.join(HERE, "_fix_checks_out.txt")

WATCHED = [
    "re_chain_synthesis_20261111", "playerctrl_semantics_20261111",
    "slot2_fullscan_20261111", "re_crashwriter_static_20261110",
    "re_orphan_owners_20261110", "re_map_preset_decode_20261110",
    "re_loadbench_diff_20261110", "stale_pass_20261109", "re_dispatch_20261111",
]
KEY = [
    "ra2bench/gamemd.exe",
    "lead/re_chain_synthesis_20261111/CHAIN_SYNTHESIS.md",
    "lead/re_chain_synthesis_20261111/LEDGER_SECTION_DRAFT.md",
    "lead/re_chain_synthesis_20261111/_repro_ps_disasm.txt",
    "lead/playerctrl_semantics_20261111/_ps_disasm.py",
]

_buf = []


def P(s=""):
    _buf.append(str(s))
    print(s)


def fp(p):
    if not os.path.isfile(p):
        return ("MISSING", -1)
    h = hashlib.sha256()
    n = 0
    with open(p, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            n += len(b)
            h.update(b)
    return (h.hexdigest(), n)


def lines(p):
    with open(p, "r", encoding="utf-8") as f:
        return f.read().splitlines()


def collect():
    out = {}
    for d in WATCHED:
        full = os.path.join(LEAD, d)
        if not os.path.isdir(full):
            continue
        for root, _dirs, files in os.walk(full):
            for name in files:
                p = os.path.join(root, name)
                rel = os.path.relpath(p, REPO).replace("\\", "/")
                out[rel] = fp(p)
    for rel in KEY + ["lead/re_chain_v2_xverify_20261112/XVERIFY.md",
                      "lead/re_chain_v2_xverify_20261112/_x.py",
                      "lead/re_chain_v2_xverify_20261112/_x_stdout.txt",
                      "lead/re_chain_v2_xverify_20261112/_x_pwsh_stdout.txt"]:
        p = os.path.join(REPO, rel.replace("/", os.sep))
        out[rel] = fp(p)
    for name in sorted(os.listdir(SYNTH)):
        p = os.path.join(SYNTH, name)
        if os.path.isfile(p):
            out["lead/re_chain_synth_v2_20261111/" + name] = fp(p)
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "checks"
    P("== FIX_CHECKS mode=%s ==" % mode)
    P("REPO = %s" % REPO)
    now = collect()

    # ---------- 基线 / 零改动 ----------
    if mode == "verify":
        with open(BASE, "r", encoding="utf-8") as f:
            base = {k: (tuple(v) if isinstance(v, list) else v)
                    for k, v in json.load(f).items()}
        drift = [k for k in base if k not in now or now[k] != base[k]]
        new = [k for k in now if k not in base]
        missing = [k for k in base if k not in now]
        P("VERIFY baseline=%d now=%d drift=%d missing=%d new=%d" %
          (len(base), len(now), len(drift), len(missing), len(new)))
        for k in drift:
            P("  DRIFT  %s  before=%s after=%s" % (k, base[k], now[k]))
        for k in new:
            P("  NEW    %s" % k)
        for k in missing:
            P("  MISSING %s" % k)
        P("  说明: 允许的改动仅限 RE_GRADING.md / LEDGER_SECTION_DRAFT_v2.md 两份被修正件；")
        P("        其余既有件（含 XVERIFY.md、全部证据件、写域内原有脚本/产物）应 0 漂移。")
    else:
        with open(BASE, "w", encoding="utf-8", newline="\n") as f:
            json.dump(now, f, ensure_ascii=False, indent=1, sort_keys=True)
        P("SNAPSHOT files=%d -> %s" % (len(now), BASE))

    # ---------- C1 ----------
    P("")
    P("== C1: _pssim_rerun_out.txt 是否存在 ==")
    ghost = os.path.join(SYNTH, "_pssim_rerun_out.txt")
    P("  os.path.isfile(_pssim_rerun_out.txt) = %s" % os.path.isfile(ghost))
    for n in ("_pssim_rerun_stdout.txt", "_pssim_rerun_stderr.txt", "_ps_disasm_out.txt", "_ps_disasm_out.json"):
        P("  %-28s sha=%s %d B" % (n, fp(os.path.join(SYNTH, n))[0], fp(os.path.join(SYNTH, n))[1]))
    P("  RE_GRADING L73 原文含 '全文落盘' = %s" % ("全文落盘" in lines(os.path.join(SYNTH, "RE_GRADING.md"))[72]))
    P("  RE_GRADING L91 原文含 '_pssim_rerun_out.txt' = %s" % ("_pssim_rerun_out.txt" in lines(os.path.join(SYNTH, "RE_GRADING.md"))[90]))

    # ---------- C2 ----------
    P("")
    P("== C2: 24 条引用 / 2 条键引用 / 首行 / REF18 ==")
    scan = lines(os.path.join(SYNTH, "_regrade_scan_out.txt"))
    refs = [l for l in scan if " -> " in l and ("[OK]" in l or "[OK*]" in l)]
    ok_line = [l for l in refs if "[OK]" in l]
    ok_key = [l for l in refs if "[OK*]" in l]
    P("  引用总数=%d ; 文件:行[OK]=%d ; 文件:键[OK*]=%d" % (len(refs), len(ok_line), len(ok_key)))
    for l in ok_key:
        P("  KEYREF %s" % l.strip())
    j = json.load(open(os.path.join(SYNTH, "_ps_disasm_out.json"), "r", encoding="utf-8"))
    P("  json:verdict 实际键值 = %s" % json.dumps(j["verdict"], ensure_ascii=False))
    P("  json:percent_built 实际键值 = %s" % json.dumps(j["percent_built"], ensure_ascii=False))
    ld = lines(os.path.join(LEAD, "re_loadbench_diff_20261110", "_ld_diff_out.txt"))
    P("  ld:L88 首行 = %s" % ld[87])
    P("  '0add791d' 在 _ld_diff_out.txt 全文命中数 = %d" %
      sum(l.count("0add791d") for l in ld))
    P("  '311,822' 命中行 = %s" % [i + 1 for i, l in enumerate(ld) if "311,822" in l])
    P("  '222,799' 命中行 = %s" % [i + 1 for i, l in enumerate(ld) if "222,799" in l])
    P("  '93c2974b' 命中行 = %s" % [i + 1 for i, l in enumerate(ld) if "93c2974b" in l])
    P("  '11ec8ff6' 命中行 = %s" % [i + 1 for i, l in enumerate(ld) if "11ec8ff6" in l])
    P("  [OK] 首行为小节标题的样例:")
    for l in ok_line:
        first = l.split("首行:")[-1].strip()
        if first.startswith(("[", "◆", "全局对象")) or "标题" in first:
            P("    %s" % l.strip()[:150])

    # ---------- C3 ----------
    P("")
    P("== C3: 无别名逃逸 vs R2 尾注 ==")
    sf = lines(os.path.join(LEAD, "slot2_fullscan_20261111", "_sf_scan_out.txt"))
    for n in (20, 28, 29, 40):
        P("  sf:L%d  %s" % (n, sf[n - 1].strip()))
    cs = lines(os.path.join(LEAD, "re_chain_synthesis_20261111", "CHAIN_SYNTHESIS.md"))
    P("  CHAIN_SYNTHESIS.md L67 边界列 = %s" % cs[66].split("|")[-2].strip())
    P("  CHAIN_SYNTHESIS.md L69 边界列 = %s" % cs[68].split("|")[-2].strip())

    # ---------- C4 ----------
    P("")
    P("== C4: §2 理由列自认推断 ==")
    P("  ld:L91 实文 = %s" % ld[90].strip())
    ps = lines(os.path.join(SYNTH, "_ps_disasm_out.txt"))
    for n in (899, 900):
        P("  ps:L%d 实文 = %s" % (n, ps[n - 1].strip()))
    rg = lines(os.path.join(SYNTH, "RE_GRADING.md"))
    for n in (40, 42, 43, 45):
        P("  RE_GRADING L%d = %s" % (n, rg[n - 1][:240]))

    # ---------- C5 ----------
    P("")
    P("== C5: 0x5012ED 既有证据 ==")
    P("  ps:L34 = %s" % ps[33].strip())
    P("  json:L55 = %s" % lines(os.path.join(SYNTH, "_ps_disasm_out.json"))[54].strip())
    P("  (静态反汇编见 _disasm_5012ed.py / _disasm_5012ed_out.txt)")

    # ---------- C6 ----------
    P("")
    P("== C6: LEDGER A 节 L26 ==")
    lg = lines(os.path.join(SYNTH, "LEDGER_SECTION_DRAFT_v2.md"))
    P("  LEDGER_SECTION_DRAFT_v2.md L26 = %s" % lg[25])
    P("  含 '后者性质未核实' = %s" % ("后者性质未核实" in lg[25]))

    # ---------- 关键件指纹 ----------
    P("")
    P("== 关键件收尾指纹（hashlib 实算） ==")
    for rel in KEY:
        p = os.path.join(REPO, rel.replace("/", os.sep))
        P("  %s  %s  %d B" % (rel, fp(p)[0], fp(p)[1]))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(_buf) + "\n")
    print("[out] %s (%d B)" % (OUT, fp(OUT)[1]))


if __name__ == "__main__":
    main()
