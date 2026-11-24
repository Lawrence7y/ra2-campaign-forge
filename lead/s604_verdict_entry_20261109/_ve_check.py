# -*- coding: utf-8 -*-
"""_ve_check.py — 一次性独立复验 (b)(c)(d)。只读：DB 以 ro+immutable 打开；只 print，stdout 由 shell 重定向。"""
import io, json, sqlite3, hashlib, datetime

LEDGER = "D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md"
RERUN = "D:/Project/ra2-campaign-forge/lead/s604_script_hunt_20261109/_sph_gen512655_rerun_out.txt"
PRIOR = "D:/Project/ra2-campaign-forge/lead/s604_script_hunt_20261109/_sh_gen512655_out.txt"
DB = "C:/Users/Administrator/.zcode/cli/db/db.sqlite"

print("== A. 台账 §604 尾块原文（行 9687..9757 + 末换行，与 _sph_ledger_cmp.py 同口径） ==")
with open(LEDGER, "rb") as f:
    b = f.read()
lines = b.split(b"\n")
print("ledger_total_lines(split by LF) =", len(lines))
tail71 = b"\n".join(lines[9686:9757]).replace(b"\r", b"") + b"\n"
s_blk = tail71.decode("utf-8")
print("block lines=9687..9757(+final NL) chars=", len(s_blk), "sha256=", hashlib.sha256(s_blk.encode()).hexdigest())
blk72 = b"\n".join(lines[9685:9757]).replace(b"\r", b"")
s_blk72 = blk72.decode("utf-8")
print("variant lines=9686..9757(no final NL) chars=", len(s_blk72), "sha256=", hashlib.sha256(s_blk72.encode()).hexdigest())

print("")
print("== B. (b) 复跑输出 vs 台账 §604 表 15 行逐位机械比对 ==")
def fnum(tok):
    tok = tok.replace("\u2212", "-").replace("−", "-").replace("**", "").replace("`", "").replace("ms", "").replace("|", " ").strip()
    return float(tok)

rerun_rows = []
with io.open(RERUN, encoding="utf-8") as f:
    for ln in f:
        parts = ln.split()
        if len(parts) == 6 and parts[0] != "window":
            rerun_rows.append((parts[0], [fnum(x) for x in parts[1:6]]))
print("rerun data rows parsed:", len(rerun_rows))

NUMCH = set("0123456789+-.\u2212")
ledger_rows = []
for ln in lines[9705:9720]:
    s = ln.decode("utf-8")
    toks = [t for t in s.replace("|", " ").replace("**", "").replace("`", "").replace("ms", "").split() if t != "-"]
    toks = [t for t in toks if t and set(t) <= NUMCH]
    ledger_rows.append([fnum(t) for t in toks])
print("ledger table rows parsed:", len(ledger_rows))

mismatch = 0
for i, (w, nums) in enumerate(rerun_rows):
    L = ledger_rows[i]
    ok = all(abs(a - b2) < 1e-9 for a, b2 in zip(nums, L)) and len(nums) == len(L)
    if not ok:
        mismatch += 1
    print("row%02d %s rerun=%s ledger=%s equal=%s" % (i + 1, w, nums, L, ok))
print("15/15 rows equal =", (mismatch == 0 and len(rerun_rows) == 15 and len(ledger_rows) == 15))

neg = [(w, nums[4]) for w, nums in rerun_rows if nums[4] < 0]
print("strictly negative gapdiff cells in rerun:", neg)
raw15 = [l for l in io.open(RERUN, encoding="utf-8").read().splitlines() if l[:1] in ("l", "t")]
print("minus-signed cells in rerun raw text:", [l.split()[-1] for l in raw15 if "-" in l.split()[-1]])

sum_line = io.open(RERUN, encoding="utf-8").read()
print("rerun has -114.820 :", "-114.820" in sum_line, "| rerun has 2.19 :", "2.19 倍" in sum_line)
l9754 = lines[9753].decode("utf-8")
print("ledger line9754 =", l9754.strip())
print("ledger 9754 mentions 114.8 (U+2212 or ASCII) :", ("114.8" in l9754))
print("ledger 9723 mentions 2.19 :", "2.19" in lines[9722].decode("utf-8"))

with open(PRIOR, "rb") as f:
    prior_b = f.read()
with open(RERUN, "rb") as f:
    rerun_b = f.read()
print("hunt-round prior bytes=", len(prior_b), "sha256=", hashlib.sha256(prior_b).hexdigest())
print("hunt-round prior == sph rerun bytes_equal =", prior_b == rerun_b)

print("")
print("== C. (c) DB 512667 sec 文本 vs 台账尾块 一次性直连比对 ==")
con = sqlite3.connect("file:" + DB + "?mode=ro&immutable=1", uri=True)
row = con.execute("SELECT data FROM part WHERE rowid=512667").fetchone()
con.close()
d = json.loads(row[0])
cmd = d["state"]["input"]["command"]
i0 = cmd.index("sec = '''") + len("sec = '''")
i1 = cmd.index("'''", i0)
sec = cmd[i0:i1]
print("sec as-is chars=", len(sec), "sha256=", hashlib.sha256(sec.encode()).hexdigest())
s1 = sec[1:]
print("sec[1:] chars=", len(s1), "sha256=", hashlib.sha256(s1.encode()).hexdigest())
print("sec[1:-1] chars=", len(sec[1:-1]), "sha256=", hashlib.sha256(sec[1:-1].encode()).hexdigest())
print("sec[1:] == ledger block(9687..9757+final NL, CR stripped) bytes_equal =", s1 == s_blk)
print("sec[1:-1] == ledger block(9687..9757 no final NL) bytes_equal =", sec[1:-1] == s_blk.rstrip("\n"))

print("")
print("== D. (d) 时间线 rowid 存在性+时刻（DB 只读点查） ==")
con = sqlite3.connect("file:" + DB + "?mode=ro&immutable=1", uri=True)
for rid in (512550, 512645, 512650, 512655, 512660, 512664, 512667, 512670):
    r = con.execute("SELECT session_id, time_created FROM part WHERE rowid=?", (rid,)).fetchone()
    if r is None:
        print("rowid=%d NOT FOUND" % rid)
        continue
    sid, tc = r
    ts = datetime.datetime.fromtimestamp(tc / 1000.0).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print("rowid=%d exists time_created=%d -> %s session=%s" % (rid, tc, ts, sid))
con.close()
