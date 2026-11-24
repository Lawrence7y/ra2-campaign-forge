# -*- coding: utf-8 -*-
# R17-R67 归档：把 STATUS_BOARD 最早的 2 段（第 59、60 轮）逐字搬入 BOARD_ARCHIVE
# 纪律：wx 独占备份（唯一名） + 断言旧 sha256 + 断言 CR 不变量 + 一次性写入 + 回读校验
import io, os, hashlib, time, sys

DRY = "--dry" in sys.argv

R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
BASE = os.path.join(R14, "R17_LEAD_BASELINE")
BOARD = os.path.join(R14, "STATUS_BOARD.md")
ARCH = os.path.join(R14, "BOARD_ARCHIVE.md")

CR_EXP = {"board": 0, "arch": 2952}
fails = []
buf = []
def P(s=""):
    print(s); buf.append(s)
def ck(n, c, d=""):
    P(("  PASS " if c else "  FAIL ") + n + (("  " + d) if d else ""))
    if not c: fails.append(n)
def sha(b): return hashlib.sha256(b).hexdigest()

board_raw = open(BOARD, "rb").read()
arch_raw = open(ARCH, "rb").read()
P("[before] STATUS_BOARD %d B CR=%d LF=%d sha=%s"
  % (len(board_raw), board_raw.count(b"\r"), board_raw.count(b"\n"), sha(board_raw)[:16]))
P("[before] BOARD_ARCHIVE %d B CR=%d LF=%d sha=%s"
  % (len(arch_raw), arch_raw.count(b"\r"), arch_raw.count(b"\n"), sha(arch_raw)[:16]))
ck("旧 STATUS_BOARD CR=0", board_raw.count(b"\r") == 0)
ck("旧 BOARD_ARCHIVE CR=2952", arch_raw.count(b"\r") == 2952)

board = board_raw.decode("utf-8")
arch = arch_raw.decode("utf-8")
ck("STATUS_BOARD 全 LF（无 CR 字符）", "\r" not in board)
ck("BOARD_ARCHIVE 解码无异常", True)

lines = board.split("\n")
P("[before] STATUS_BOARD 行数（split '\\n'）= %d" % len(lines))
ck("旧看板行数 = 280", len(lines) == 280, str(len(lines)))

# ---- 定位最早两段 ----
i59 = next(i for i, l in enumerate(lines) if l.startswith("## 🔴 R17 第 59 轮"))
i61 = next(i for i, l in enumerate(lines) if l.startswith("## 🔴 R17 第 61 轮"))
P("  第 59 轮起于 0-based 行 %d；第 61 轮起于 %d" % (i59, i61))

segA = lines[i59:i61]              # 第 59 轮段 + 第 60 轮段（连续 2 段）
# 拆分确认段界
i60 = next(i for i, l in enumerate(lines[i59:i61], i59) if l.startswith("## 🟢 R17 第 60 轮"))
seg59 = lines[i59:i60]
seg60 = lines[i60:i61]
P("  段 59 = %d 行（非空 %d）；段 60 = %d 行（非空 %d）"
  % (len(seg59), sum(1 for x in seg59 if x.strip()),
     len(seg60), sum(1 for x in seg60 if x.strip())))
ck("两段合计行数 = 段59 + 段60", len(segA) == len(seg59) + len(seg60))

# 尾部空行归并：每段末尾的空行不搬（跟随 <details> 结构）
def trim(seg):
    s = list(seg)
    while s and not s[-1].strip():
        s.pop()
    return s
seg59t, seg60t = trim(seg59), trim(seg60)
P("  去尾空行后 段59 = %d 行 / 段60 = %d 行" % (len(seg59t), len(seg60t)))
dropped = (len(seg59) - len(seg59t)) + (len(seg60) - len(seg60t))
P("  丢弃的尾部空行 = %d（不计入 missing；原文内容行全搬）" % dropped)

ART = "H9293"
blocks = []
for title, seg in (("第 59 轮", seg59t), ("第 60 轮", seg60t)):
    blocks.append("<details><summary>归档原文（%s · 逐字）</summary>\n\n%s\n\n</details>"
                  % (ART, "\n".join(seg)))

# ---- 生成新内容（纯 LF，一次写入） ----
new_arch = arch.rstrip("\n") + "\n\n" + "\n\n".join(blocks) + "\n"

ptr = []
for title, seg in (("第 59 轮", seg59t), ("第 60 轮", seg60t)):
    head = seg[0].split("·")
    label = seg[0][3:] if seg[0].startswith("## ") else seg[0]
    ptr.append("> 📦 ## %s 已归档至 BOARD_ARCHIVE.md（2026-11-22 22:0x，逐字搬，"
               "missing=0；本次由 Lead 执行，卫生员 %s）" % (label, ART))
new_board = "\n".join(lines[:i59] + ptr + lines[i61:])

ck("新看板无 CR", "\r" not in new_board)
ck("新归档无新增 CR（原 CR 数不变）",
   new_arch.count("\r") == 2952, str(new_arch.count("\r")))
nb = new_board.split("\n")
P("[after] 新看板行数 = %d（280 − %d + 2）" % (len(nb), len(segA)))
ck("新看板行数 <= 265", len(nb) <= 265, str(len(nb)))
ck("新看板行数 = 280 - 段行数 + 2", len(nb) == 280 - len(segA) + 2, str(len(nb)))

# ---- 归档内容回读断言（逐字命中） ----
for title, seg in (("第59轮", seg59t), ("第60轮", seg60t)):
    miss = [l for l in seg if l not in new_arch]
    ck("归档逐字命中 %s（missing=0）" % title, len(miss) == 0, "missing=%d" % len(miss))

# ---- wx 独占备份 ----
ts = time.strftime("%Y%m%d_%H%M%S")
bk_board = os.path.join(BASE, "SUPERSEDED.before_r67_archive_STATUS_BOARD_%s.md" % ts)
bk_arch = os.path.join(BASE, "SUPERSEDED.before_r67_archive_BOARD_ARCHIVE_%s.md" % ts)
P("")
P("[backup] wx 独占写入（唯一名）" + ("  [DRY-RUN 跳过]" if DRY else ""))
d = os.path.dirname(bk_board)
if not os.path.isdir(d):
    os.makedirs(d)
if not DRY:
    for p, raw in ((bk_board, board_raw), (bk_arch, arch_raw)):
        with open(p, "xb") as f:      # 'x' = 独占创建，已存在则异常
            f.write(raw)
        got = open(p, "rb").read()
        ck("备份 %s 字节一致" % os.path.basename(p), sha(got) == sha(raw))
        P("    -> %s (%d B)" % (os.path.basename(p), len(got)))
    # ---- 断言备份 sha 与内存旧值一致，再一次性写入 ----
    assert sha(open(bk_board, "rb").read()) == sha(board_raw)
    assert sha(open(bk_arch, "rb").read()) == sha(arch_raw)
    P("")
    P("[write] 一次性写入（先写新内容，再回读校验）")
    open(ARCH, "wb").write(new_arch.encode("utf-8"))
    open(BOARD, "wb").write(new_board.encode("utf-8"))
else:
    P("    (跳过备份与写入)")

b2 = open(BOARD, "rb").read() if not DRY else new_board.encode("utf-8")
a2 = open(ARCH, "rb").read() if not DRY else new_arch.encode("utf-8")
P("[after] STATUS_BOARD %d B CR=%d LF=%d sha=%s"
  % (len(b2), b2.count(b"\r"), b2.count(b"\n"), sha(b2)[:16]))
P("[after] BOARD_ARCHIVE %d B CR=%d LF=%d sha=%s"
  % (len(a2), a2.count(b"\r"), a2.count(b"\n"), sha(a2)[:16]))
ck("回读 STATUS_BOARD CR=0", b2.count(b"\r") == 0)
ck("回读 BOARD_ARCHIVE CR=2952", a2.count(b"\r") == 2952)
ck("回读 STATUS_BOARD 行数 <= 265", len(b2.decode("utf-8").split("\n")) <= 265,
   str(len(b2.decode("utf-8").split("\n"))))
ck("回读 看板字节与预期一致", b2 == new_board.encode("utf-8"))
ck("回读 归档字节与预期一致", a2 == new_arch.encode("utf-8"))
ck("看板增量 = 新 − 旧", len(b2) - len(board_raw) == len(new_board.encode()) - len(board_raw),
   "%+d B" % (len(b2) - len(board_raw)))
ck("归档增量", len(a2) - len(arch_raw) > 0, "%+d B" % (len(a2) - len(arch_raw)))
# 归档尾部保留
ck("归档仍以 </details> 结尾", a2.decode("utf-8").rstrip("\n").endswith("</details>"))

open(os.path.join(R14, r"_r67\archive_r67.log"), "w", encoding="utf-8",
     newline="\n").write("\n".join(buf) + "\n")
P("")
P("RESULT " + ("ALL-PASS" if not fails else "FAIL: " + ",".join(fails)))
sys.exit(0 if not fails else 1)
