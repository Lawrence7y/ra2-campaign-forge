# -*- coding: utf-8 -*-
"""Q5 independent reviewer clean-room probe (READ-ONLY, zero真机/zero采样).

Does NOT import or call _w9_q5.py. Independently:
  [1] hashlib SHA256 of exe + EXCEPT (both hashes)
  [2] Engine() real run: coverage / IB / fo / rd(VA,32) vs EXCEPT L17 bytes
  [3] by()[VA] + disasm(VA,0x30) + disasm(0x7CFC98,0x10)
  [4] func_rets(0x7CFB13,0x7CFE1C)
  [5] RC-1 AV file L18 bytes vs EXCEPT L17 bytes (byte-string equality)
Outputs to reviews/_Q5_review_probe_out.txt (script's own write, inside allowed write域).
"""
import sys, hashlib
from pathlib import Path

ROOT = r"D:\Project\ra2-campaign-forge"
SWARM = ROOT + r"\lead\goal3t_nightwatch_20261102\swarm_20261104"
EXE = ROOT + r"\ra2youli\gamemd.exe"
EXCEPT = ROOT + r"\out\re_work\work_chain\CONTINUE_20261003\lead\boot_hang_triage_20261018\EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt"
AV = ROOT + r"\out\re_work\zcode_live\zc11\evidence\closeout\except.txt.final_isolated"
OUT = ROOT + r"\lead\re_line_20261105\W9_SINGLESTEP_7CFC9F\reviews\_Q5_review_probe_out.txt"
VA = 0x7CFC9F

sys.path.insert(0, SWARM)
from ra2tool import Engine

L = []
def p(s): L.append(str(s))

raw_exe = Path(EXE).read_bytes()
raw_exc = Path(EXCEPT).read_bytes()
raw_av = Path(AV).read_bytes()
p("[1] hashlib SHA256 (independent read)")
p("  exe sha    = %s" % hashlib.sha256(raw_exe).hexdigest())
p("  exe bytes  = %d" % len(raw_exe))
p("  EXC sha    = %s" % hashlib.sha256(raw_exc).hexdigest())
p("  EXC bytes  = %d" % len(raw_exc))
p("  AV  sha    = %s" % hashlib.sha256(raw_av).hexdigest())
p("  AV  bytes  = %d" % len(raw_av))

e = Engine()
cov, nins, fails = e.coverage
p("[2] Engine() real run")
p("  e.sha == self-computed exe sha : %s" % (e.sha == hashlib.sha256(raw_exe).hexdigest()))
p("  IB = 0x%X" % e.IB)
p("  COVERAGE = %.12f%% / %d insns / %d resync-fails" % (cov, nins, fails))
p("  fo(VA)=0x%X ; VA-IB=0x%X" % (e.fo(VA), VA - e.IB))
b = e.rd(VA, 32)
p("  e.rd(VA,32) = %s" % " ".join("%02X" % x for x in b))
txt = raw_exc.decode("latin-1")
l17 = [ln for ln in txt.splitlines() if "Bytes at CS:EIP" in ln][0]
expect = bytes(int(x, 16) for x in l17.rsplit(":", 1)[1].strip().split()[:32])
p("  EXCEPT L17 = %s" % " ".join("%02X" % x for x in expect))
p("  rd==L17 : %s ; diff idx=%s" % (b == expect, [i for i in range(32) if b[i] != expect[i]]))

p("[3] instruction start / disasm")
p("  VA in e.by() = %s" % (VA in e.by()))
bi = e.by().get(VA)
if bi: p("  by()[VA] bytes=%s size=%d %s %s" % (bi.bytes.hex(), bi.size, bi.mnemonic, bi.op_str))
ins = e.disasm(VA, 0x30)
p("  disasm(VA,0x30) count = %d" % len(ins))
for i, (a, by, mn, op) in enumerate(ins[:8]):
    p("    #%d 0x%X %-10s %s %s" % (i+1, a, by, mn, op))
p("  --- predecessor window 0x7CFC98 ---")
for a, by, mn, op in e.disasm(0x7CFC98, 0x10):
    p("    0x%X %-10s %s %s" % (a, by, mn, op))

p("[4] function boundary")
p("  e.rd(0x7CFB13,5) = %s" % e.rd(0x7CFB13,5).hex())
p("  e.rd(0x7CFB12,1) = %s" % e.rd(0x7CFB12,1).hex())
rl, _ = e.func_rets(0x7CFB13, 0x7CFE1C)
p("  func_rets count=%d addrs=%s" % (len(rl), ["0x%X" % r.address for r in rl]))
p("  e.rd(0x7CFE1B,1) = %s" % e.rd(0x7CFE1B,1).hex())
p("  length incl ret = 0x%X / excl = 0x%X" % (0x7CFE1C-0x7CFB13, 0x7CFE1B-0x7CFB13))

p("[5] RC-1 AV bytes line vs EXCEPT L17 (independent read)")
txt_av = raw_av.decode("latin-1")
av_lines = txt_av.splitlines()
p("  AV total lines = %d" % len(av_lines))
hits = [(i+1, ln) for i, ln in enumerate(av_lines) if "Bytes at CS:EIP" in ln]
p("  AV 'Bytes at CS:EIP' line numbers = %s" % [i for i, _ in hits])
for i, ln in hits:
    av_b = bytes(int(x, 16) for x in ln.rsplit(":", 1)[1].strip().split()[:32])
    p("  AV L%d bytes == EXCEPT L17 bytes : %s" % (i, av_b == expect))
    p("  AV L%d bytes = %s" % (i, " ".join("%02X" % x for x in av_b)))
p("  AV L1 = %s" % av_lines[0].strip())
p("  AV L3 = %s" % av_lines[2].strip())
p("  AV L14 = %s" % av_lines[13].strip())
p("PROBE DONE")
Path(OUT).write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
print("PROBE DONE -- exit 0 -> " + OUT)
