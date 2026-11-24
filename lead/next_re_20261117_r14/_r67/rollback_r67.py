# -*- coding: utf-8 -*-
# R17-R67 回滚：把四件套恢复到 write_r67.py 写前状态。
# 依据 R17_LEAD_BASELINE 里的 SUPERSEDED.before_r67_write_*_20261122_211932.md（wx 独占备份，sha 已断言）。
# 前提：本轮只做「末尾追加」，故恢复 = 用备份整体覆盖；恢复后必须满足写前五项 CR 与字节数。
import os, sys, hashlib

R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
LEAD = r"D:\Project\ra2-campaign-forge\lead"
BASE = os.path.join(R14, "R17_LEAD_BASELINE")
DRY = "--dry" in sys.argv
TS = "20261122_211932"

def sha(b): return hashlib.sha256(b).hexdigest()

# key -> (当前路径, 备份名, 写前字节, 写前 CR, 写前 sha 前 16)
SPEC = {
    "common": (os.path.join(R14, "R14_COMMON.md"), "SUPERSEDED.before_r67_write_common_%s.md" % TS,
               531072, 1081, "a3836c8d5d9d1228"),
    "ledger": (os.path.join(LEAD, "GOAL_THREE_TARGETS_20261018.md"),
               "SUPERSEDED.before_r67_write_ledger_%s.md" % TS, 4668166, 337, "b11641baf8ea3548"),
    "lock":   (os.path.join(LEAD, "LEAD_LOCK"),
               "SUPERSEDED.before_r67_write_lock_%s.md" % TS, 348908, 137, "771a5d023f8fac6f"),
    "board":  (os.path.join(R14, "STATUS_BOARD.md"),
               "SUPERSEDED.before_r67_write_board_%s.md" % TS, 51888, 0, "e5ef5347f645acb2"),
}

buf = []
fails = []
def P(s=""):
    print(s); buf.append(s)
def ck(n, c, d=""):
    P(("  PASS " if c else "  FAIL ") + n + (("  " + d) if d else ""))
    if not c: fails.append(n)

P("=" * 78)
P("[1] 校验备份完整且与写前声明一致")
rec = {}
for k, (path, bn, nbytes, cr, sh16) in SPEC.items():
    bp = os.path.join(BASE, bn)
    ck("%s 备份存在" % k, os.path.exists(bp), bn)
    raw = open(bp, "rb").read()
    rec[k] = raw
    ck("%s 备份字节 = %d" % (k, nbytes), len(raw) == nbytes, str(len(raw)))
    ck("%s 备份 CR = %d" % (k, cr), raw.count(b"\r") == cr, str(raw.count(b"\r")))
    ck("%s 备份 sha[:16] = %s" % (k, sh16), sha(raw)[:16] == sh16, sha(raw)[:16])

P("")
P("[2] 当前文件必须是「备份 + 本轮追加」（即备份是当前文件的前缀）")
cur = {}
for k, (path, bn, nbytes, cr, sh16) in SPEC.items():
    c = open(path, "rb").read()
    cur[k] = c
    P("  %-7s 当前 %8d B / 写前 %8d B（增量 %+d）" % (k, len(c), len(rec[k]), len(c) - len(rec[k])))
    ck("%s 当前 > 写前（确有追加）" % k, len(c) > len(rec[k]))
    ck("%s 写前内容为当前文件前缀（追加型改动，可无损回滚）" % k,
       c[:len(rec[k])] == rec[k])

P("")
P("[3] 回滚（用备份整体覆盖）" + ("  [DRY]" if DRY else ""))
if not DRY:
    for k, (path, bn, nbytes, cr, sh16) in SPEC.items():
        open(path, "wb").write(rec[k])
        got = open(path, "rb").read()
        ck("%s 回滚后字节 = %d" % (k, nbytes), len(got) == nbytes, str(len(got)))
        ck("%s 回滚后 CR = %d" % (k, cr), got.count(b"\r") == cr, str(got.count(b"\r")))
        ck("%s 回滚后 sha 与备份相同" % k, sha(got) == sha(rec[k]), sha(got)[:16])
        ck("%s 本轮追加内容已移除" % k, got == rec[k])
else:
    P("    (DRY：未写入)")

P("")
P("[4] 五项 CR 不变量（回滚后）")
arch = os.path.join(R14, "BOARD_ARCHIVE.md")
a = open(arch, "rb").read()
cur_cr = {k: (open(SPEC[k][0], "rb").read() if not DRY else rec[k]).count(b"\r") for k in SPEC}
exp = {"common": 1081, "ledger": 337, "lock": 137, "board": 0}
ok = True
for k, e in exp.items():
    good = cur_cr[k] == e
    ok &= good
    P("  %-8s CR=%-5d 期望=%-5d %s" % (k, cur_cr[k], e, "PASS" if good else "FAIL"))
P("  %-8s CR=%-5d 期望=%-5d %s" % ("arch", a.count(b"\r"), 2952,
                                  "PASS" if a.count(b"\r") == 2952 else "FAIL"))
ok &= a.count(b"\r") == 2952
ck("五项 CR 不变量 1081/137/337/0/2952（回滚后）", ok)

P("")
P("RESULT " + ("ALL-PASS" if not fails else "FAIL: " + ",".join(fails)))
open(os.path.join(R14, r"_r67\rollback_r67.log"), "w", encoding="utf-8",
     newline="\n").write("\n".join(buf) + "\n")
sys.exit(0 if not fails else 1)
