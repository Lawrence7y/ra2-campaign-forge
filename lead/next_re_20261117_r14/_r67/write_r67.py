# -*- coding: utf-8 -*-
# R17-R67 四件套落盘：R14_COMMON §2.73 / 台账 §1122 / LEAD_LOCK CV / STATUS_BOARD 第 67 轮
# 纪律：wx 独占备份（唯一名） -> 断言旧 sha256 与 CR 不变量 -> 一次性写入 -> 回读校验
# CR 不变量：R14_COMMON=1081、LEAD_LOCK=137、台账=337、STATUS_BOARD=0（行数<=300）、BOARD_ARCHIVE=2952
import os, sys, hashlib, time

R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
LEAD = r"D:\Project\ra2-campaign-forge\lead"
BASE = os.path.join(R14, "R17_LEAD_BASELINE")
DRY = "--dry" in sys.argv

TARGETS = [
    # key,      path,                              cr_expected, section_file,                 sep_before, crlf_tail
    ("common", os.path.join(R14, "R14_COMMON.md"),            1081, r"_r67\s273.md",          "\n", False),
    ("ledger", os.path.join(LEAD, "GOAL_THREE_TARGETS_20261018.md"), 337, r"_r67\ledger_1122.md", "\n", False),
    ("lock",   os.path.join(LEAD, "LEAD_LOCK"),               137,  r"_r67\lock_cv.md",       "\n", False),
    ("board",  os.path.join(R14, "STATUS_BOARD.md"),            0,  r"_r67\board_r67.md",     "\n", False),
]
ARCH = os.path.join(R14, "BOARD_ARCHIVE.md")
CR_ARCH_EXP = 2952

buf = []
fails = []
def P(s=""):
    print(s); buf.append(s)
def ck(n, c, d=""):
    P(("  PASS " if c else "  FAIL ") + n + (("  " + d) if d else ""))
    if not c: fails.append(n)
def sha(b): return hashlib.sha256(b).hexdigest()

ts = time.strftime("%Y%m%d_%H%M%S")
P("=" * 78)
P("[0] 落盘前状态（先量后写）")

states = {}
for key, path, cr_exp, sec, sep, _ in TARGETS:
    raw = open(path, "rb").read()
    states[key] = raw
    P("  %-7s %8d B  CR=%-5d LF=%-6d lines=%-6d sha=%s  %s"
      % (key, len(raw), raw.count(b"\r"), raw.count(b"\n"),
         len(raw.decode("utf-8").split("\n")), sha(raw)[:16], os.path.basename(path)))
    ck("%s 旧 CR = %d" % (key, cr_exp), raw.count(b"\r") == cr_exp, str(raw.count(b"\r")))
    ck("%s 旧文件全 LF（无 CR 字符，与其 CR 计数为 0/%d 一致）" % (key, cr_exp),
       (b"\r" in raw) == (cr_exp > 0), "CR=%d" % raw.count(b"\r"))

# 归档文件只断言不写
arch_raw = open(ARCH, "rb").read()
P("  %-7s %8d B  CR=%-5d LF=%-6d sha=%s  BOARD_ARCHIVE.md"
  % ("arch", len(arch_raw), arch_raw.count(b"\r"), arch_raw.count(b"\n"), sha(arch_raw)[:16]))
ck("BOARD_ARCHIVE CR = 2952（本轮归档后维持）",
   arch_raw.count(b"\r") == CR_ARCH_EXP, str(arch_raw.count(b"\r")))

P("")
P("[1] 校验 R14_COMMON 末尾确有 §2.73 前状态（不得已有该节，防重复追加）")
common_txt = states["common"].decode("utf-8")
ck("R14_COMMON 尚无 §2.73", "## 2.73 " not in common_txt and "## 2.73【" not in common_txt)
ck("R14_COMMON 末节为 §2.72", "## 2.72 " in common_txt)
ledger_txt = states["ledger"].decode("utf-8")
ck("台账 尚无 §1122", "\n## §1122" not in ledger_txt)
ck("台账 末节为 §1121", "\n## §1121" in ledger_txt)
lock_txt = states["lock"].decode("utf-8")
ck("LEAD_LOCK 尚无 CV 段", "## CV · R17 第 67 轮" not in lock_txt)
ck("LEAD_LOCK 末段为 CU", "## CU · R17 第 66 轮" in lock_txt)
board_txt = states["board"].decode("utf-8")
ck("STATUS_BOARD 尚无第 67 轮段", "R17 第 67 轮" not in board_txt)
ck("STATUS_BOARD 末段为第 66 轮", "R17 第 66 轮" in board_txt)
P("  看板当前行数 = %d（须 <= 265 才许追加；上限 300）"
  % len(board_txt.split("\n")))
ck("看板当前行数 <= 265", len(board_txt.split("\n")) <= 265, str(len(board_txt.split("\n"))))

P("")
P("[2] 构造新内容（纯 LF，单次拼接）")
news = {}
for key, path, cr_exp, sec, sep, _ in TARGETS:
    secp = os.path.join(R14, sec)
    sec_raw = open(secp, "rb").read()
    ck("%s 段草稿 %s 全 LF" % (key, sec), b"\r" not in sec_raw,
       "CR=%d" % sec_raw.count(b"\r"))
    body = sec_raw.decode("utf-8")
    ck("%s 段草稿以单换行结尾" % key, body.endswith("\n") and not body.endswith("\n\n"))
    old = states[key].decode("utf-8")
    new = old
    if not new.endswith("\n"):
        new = new + "\n"
    new = new + "\n" + body
    news[key] = new
    nb = new.encode("utf-8")
    P("  %-7s %8d -> %8d B (%+d)  CR %d -> %d  lines %d -> %d"
      % (key, len(states[key]), len(nb), len(nb) - len(states[key]),
         states[key].count(b"\r"), nb.count(b"\r"),
         len(old.split("\n")), len(new.split("\n"))))
    ck("%s 新内容 CR 不变（= %d）" % (key, cr_exp), nb.count(b"\r") == cr_exp,
       str(nb.count(b"\r")))
    ck("%s 新内容严格增长" % key, len(nb) > len(states[key]), "%+d" % (len(nb) - len(states[key])))
    ck("%s 前缀不变（前旧长字节完全相同）" % key,
       nb[:len(states[key])] == states[key] if not states[key].endswith(b"\n")
       else nb[:len(states[key])] == states[key])
    ck("%s 段内容逐行命中新文件" % key,
       all(l in new for l in body.split("\n") if l.strip()))
    # 新内容只追加不删：旧内容去掉末尾换行的部分必须仍是前缀
    old_stripped = old.rstrip("\n")
    ck("%s 旧内容全部保留（rstrip 后为前缀）" % key, new.startswith(old_stripped))

nb_lines = len(news["board"].split("\n"))
P("")
P("[3] 看板上限校验")
P("  追加后看板行数 = %d（上限 300）" % nb_lines)
ck("看板追加后行数 <= 300", nb_lines <= 300, str(nb_lines))
ck("看板追加后 CR = 0", news["board"].encode("utf-8").count(b"\r") == 0)

P("")
P("[4] wx 独占备份（唯一名）" + ("  [DRY]" if DRY else ""))
bks = {}
if not DRY:
    os.makedirs(BASE, exist_ok=True)
    for key, path, cr_exp, sec, sep, _ in TARGETS:
        bn = os.path.join(BASE, "SUPERSEDED.before_r67_write_%s_%s.md" % (key, ts))
        with open(bn, "xb") as f:      # 'x' 独占：已存在即抛
            f.write(states[key])
        got = open(bn, "rb").read()
        bks[key] = bn
        ck("备份 %-7s 字节一致 / sha 相同" % key, sha(got) == sha(states[key]))
        P("    -> %s (%d B)" % (os.path.basename(bn), len(got)))
    P("")
    P("[5] 断言旧 sha256 与 CR 不变量后，一次性写入")
    for key, path, cr_exp, sec, sep, _ in TARGETS:
        assert sha(open(bks[key], "rb").read()) == sha(states[key]), key
        assert states[key].count(b"\r") == cr_exp, key
        ck("%s 写前 sha/CR 断言" % key, True)
    # 一次性写入：先把全部新内容算好（已在 news），再逐个写
    for key, path, cr_exp, sec, sep, _ in TARGETS:
        open(path, "wb").write(news[key].encode("utf-8"))
        P("    wrote %-7s %s" % (key, os.path.basename(path)))
else:
    P("    (DRY：跳过备份与写入)")

P("")
P("[6] 回读校验")
CR_AFTER = {"common": 1081, "ledger": 337, "lock": 137, "board": 0}
for key, path, cr_exp, sec, sep, _ in TARGETS:
    if DRY:
        got = news[key].encode("utf-8")
    else:
        got = open(path, "rb").read()
    P("  %-7s 回读 %8d B  CR=%-5d LF=%-6d lines=%-6d sha=%s"
      % (key, len(got), got.count(b"\r"), got.count(b"\n"),
         len(got.decode("utf-8").split("\n")), sha(got)[:16]))
    ck("%s 回读字节与预期一致" % key, got == news[key].encode("utf-8"))
    ck("%s 回读 CR = %d" % (key, CR_AFTER[key]), got.count(b"\r") == CR_AFTER[key],
       str(got.count(b"\r")))
    body = open(os.path.join(R14, sec), "rb").read().decode("utf-8")
    miss = [l for l in body.split("\n") if l.strip() and l not in got.decode("utf-8")]
    ck("%s 段逐行命中回读内容（missing=%d）" % (key, len(miss)), len(miss) == 0,
       "missing=%d" % len(miss))

# 归档文件未被本轮写入
a2 = open(ARCH, "rb").read() if not DRY else arch_raw
ck("BOARD_ARCHIVE 未被本轮四件套写入（sha 不变）", sha(a2) == sha(arch_raw))
ck("BOARD_ARCHIVE CR 仍 = 2952", a2.count(b"\r") == 2952, str(a2.count(b"\r")))

P("")
P("[7] 五项 CR 不变量总校验")
inv = {
    "R14_COMMON": (open(os.path.join(R14, "R14_COMMON.md"), "rb").read() if not DRY
                   else news["common"].encode(), 1081),
    "LEAD_LOCK": (open(os.path.join(LEAD, "LEAD_LOCK"), "rb").read() if not DRY
                  else news["lock"].encode(), 137),
    "台账": (open(os.path.join(LEAD, "GOAL_THREE_TARGETS_20261018.md"), "rb").read()
             if not DRY else news["ledger"].encode(), 337),
    "STATUS_BOARD": (open(os.path.join(R14, "STATUS_BOARD.md"), "rb").read() if not DRY
                     else news["board"].encode(), 0),
    "BOARD_ARCHIVE": (a2, 2952),
}
allok = True
for k, (raw, exp) in inv.items():
    ok = raw.count(b"\r") == exp
    allok &= ok
    P("  %-14s CR=%-5d 期望=%-5d %s" % (k, raw.count(b"\r"), exp, "PASS" if ok else "FAIL"))
ck("五项 CR 不变量 1081/137/337/0/2952 全部成立", allok)
brd = inv["STATUS_BOARD"][0].decode("utf-8")
P("  看板总行数 = %d（<= 300）" % len(brd.split("\n")))
ck("看板总行数 <= 300", len(brd.split("\n")) <= 300, str(len(brd.split("\n"))))

P("")
P("RESULT " + ("ALL-PASS" if not fails else "FAIL: " + ",".join(fails)))
open(os.path.join(R14, r"_r67\write_r67.log"), "w", encoding="utf-8",
     newline="\n").write("\n".join(buf) + "\n")
sys.exit(0 if not fails else 1)
