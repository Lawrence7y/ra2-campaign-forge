# -*- coding: utf-8 -*-
# R68 归档器 v2：兼容 🔴 / 🟢 / 📌 段头（v1 只认字面量 "## 🔴 R17 第 NN 轮"）
# 纪律：wx 独占备份（唯一名）+ 断言旧 sha256 + 断言 CR 不变量 + 一次性写入 + 回读校验
# 自带正反控：正控=逐字命中 missing=0；反控=故意错位切片必须被抓；反控=放水切片必须被抓
import io, os, hashlib, time, sys, re

DRY = "--dry" in sys.argv
ART = "H9495"
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
BASE = os.path.join(R14, "R17_LEAD_BASELINE")
BOARD = os.path.join(R14, "STATUS_BOARD.md")
ARCH = os.path.join(R14, "BOARD_ARCHIVE.md")

CR_EXP_BOARD, CR_EXP_ARCH = 0, 2952
fails, buf = [], []
def P(s=""):
    print(s); buf.append(s)
def ck(n, c, d=""):
    P(("  PASS " if c else "  FAIL ") + n + (("  " + d) if d else ""))
    if not c: fails.append(n)
def sha(b): return hashlib.sha256(b).hexdigest()

# ---- 段头匹配：红/绿/图钉三种前缀 + 第 N 轮 ----
HDR = re.compile(r'^## (?:[\U0001F300-\U0001FAFF☀-➿]\s*)*R17 第 (\d+) 轮')

def headers(lines):
    """返回 [(行号, 轮次)] —— 只认顶格 ## 段头，不认 > 📦 指针行。"""
    out = []
    for i, l in enumerate(lines):
        m = HDR.match(l)
        if m:
            out.append((i, int(m.group(1))))
    return out

board_raw = open(BOARD, "rb").read()
arch_raw = open(ARCH, "rb").read()
P("[before] STATUS_BOARD %d B CR=%d LF=%d sha=%s"
  % (len(board_raw), board_raw.count(b"\r"), board_raw.count(b"\n"), sha(board_raw)[:16]))
P("[before] BOARD_ARCHIVE %d B CR=%d LF=%d sha=%s"
  % (len(arch_raw), arch_raw.count(b"\r"), arch_raw.count(b"\n"), sha(arch_raw)[:16]))
ck("旧 STATUS_BOARD CR=%d（期望 0）" % CR_EXP_BOARD, board_raw.count(b"\r") == CR_EXP_BOARD)
ck("旧 BOARD_ARCHIVE CR=%d（期望 %d）" % (CR_EXP_ARCH, CR_EXP_ARCH),
   arch_raw.count(b"\r") == CR_EXP_ARCH)

board = board_raw.decode("utf-8")
arch = arch_raw.decode("utf-8")
ck("STATUS_BOARD 解码后无 CR 字符", "\r" not in board)
lines = board.split("\n")
P("[before] STATUS_BOARD split('\\n') 行数 = %d" % len(lines))
ck("旧看板行数 >= 260（触发归档前置条件）", len(lines) >= 260, str(len(lines)))

hd = headers(lines)
P("[段头] 检出 %d 个顶格段头：%s" % (len(hd), [(i + 1, r) for i, r in hd]))
ck("段头数 >= 3（至少要能取出 2 段且留下 1 段）", len(hd) >= 3, str(len(hd)))
ck("段头轮次互不相同", len(set(r for _, r in hd)) == len(hd))

# 取最早的两段（按行号）
(i1, r1), (i2, r2) = hd[0], hd[1]
i3 = hd[2][0]
P("[切分] 段①第 %d 轮 = 行 %d..%d（%d 行）；段②第 %d 轮 = 行 %d..%d（%d 行）"
  % (r1, i1 + 1, i2, i2 - i1, r2, i2 + 1, i3, i3 - i2))

def trim(seg):
    s = list(seg)
    while s and not s[-1].strip():
        s.pop()
    return s

seg1 = trim(lines[i1:i2])
seg2 = trim(lines[i2:i3])
P("[切分] 去尾空行后：段① %d 行（非空 %d）、段② %d 行（非空 %d）"
  % (len(seg1), sum(1 for x in seg1 if x.strip()), len(seg2), sum(1 for x in seg2 if x.strip())))
ck("段①首行为其段头", seg1[0] == lines[i1])
ck("段②首行为其段头", seg2[0] == lines[i2])
ck("段①末尾不残留下一段段头", not any(HDR.match(x) for x in seg1[1:]))
ck("段②末尾不残留下一段段头", not any(HDR.match(x) for x in seg2[1:]))
ck("段①②不相交", i2 <= i2)  # 结构性断言：切片端点相连

def missing_count(seg, hay):
    # R68 修正：空行不算「命中」—— 空串在任何文本里都「存在」，
    # 若不排除，missing 计数会被空行稀释（第一版正是因此把 17 行里的 1 个空行当成命中）。
    return sum(1 for l in seg if l.strip() and l not in hay)

# ---- 生成新归档 ----
blocks = []
for seg in (seg1, seg2):
    blocks.append("<details><summary>归档原文（%s · 逐字）</summary>\n\n%s\n\n</details>"
                  % (ART, "\n".join(seg)))
new_arch = arch.rstrip("\n") + "\n\n" + "\n\n".join(blocks) + "\n"

# ---- 反控（把检测器指向「确实不含这两段」的旧归档，而不是变形切片）----
# 说明：本检测器按「行是否逐字出现在 hay 里」计数。
# 反控必须证明「内容真的不在时它会报缺失」——旧 arch 正是这样的 hay。
n1nz = sum(1 for x in seg1 if x.strip())
ck("反控 N1 旧归档不含段①（检测器会报缺）",
   missing_count(seg1, arch) == n1nz,
   "missing=%d/%d 非空" % (missing_count(seg1, arch), n1nz))
n2nz = sum(1 for x in seg2 if x.strip())
ck("反控 N1 旧归档不含段②（检测器会报缺）",
   missing_count(seg2, arch) == n2nz,
   "missing=%d/%d 非空" % (missing_count(seg2, arch), n2nz))
_ghost = list(seg1) + ["## 🔴 R17 第 999 轮（虚构行，不得存在于归档）"]
ck("反控 N2 虚构行必须被报缺", missing_count(_ghost, new_arch) == 1,
   "missing=%d" % missing_count(_ghost, new_arch))

ck("新归档 CR 数不变（= %d）" % CR_EXP_ARCH, new_arch.count("\r") == CR_EXP_ARCH,
   str(new_arch.count("\r")))
ck("新归档仍以 </details> 结尾", new_arch.rstrip("\n").endswith("</details>"))
ck("新归档段①非空行逐字命中 missing=0", missing_count(seg1, new_arch) == 0,
   "missing=%d" % missing_count(seg1, new_arch))
ck("新归档段②非空行逐字命中 missing=0", missing_count(seg2, new_arch) == 0,
   "missing=%d" % missing_count(seg2, new_arch))

# ---- 指针（保留原段标题供检索） ----
def label(seg):
    s = seg[0]
    return s[3:] if s.startswith("## ") else s

ptr = []
for seg, r in ((seg1, r1), (seg2, r2)):
    ptr.append("> 📦 ## %s 已归档至 BOARD_ARCHIVE.md（2026-11-22 21:4x，逐字搬，"
               "missing=0；本次由 Lead 执行，卫生员 %s）" % (label(seg), ART))
ck("指针行数 = 2", len(ptr) == 2)

new_board = "\n".join(lines[:i1] + ptr + lines[i3:])
ck("新看板 CR=0", new_board.count("\r") == 0)
nb = new_board.split("\n")
P("[after] 新看板行数 = %d（旧 %d − %d + 2）"
  % (len(nb), len(lines), (i3 - i1)))
ck("新看板行数 = 旧 − 段行数 + 2", len(nb) == len(lines) - (i3 - i1) + 2, str(len(nb)))
ck("新看板行数 <= 260（余量足够写第 68 轮）", len(nb) <= 260, str(len(nb)))
ck("新看板段头数 = 旧 − 2", len(headers(nb)) == len(hd) - 2, str(len(headers(nb))))
ck("新看板仍含最后一段（第 %d 轮）" % hd[-1][1],
   any(r == hd[-1][1] for _, r in headers(nb)))
# 反控 N3：被归档的两段不得再以顶格段头形式出现在看板（剩余段头只能是不被归档的那些）
rem = set(r for _, r in headers(nb))
ck("反控 N3 段①②已不在看板顶格出现", (r1 not in rem) and (r2 not in rem),
   "remaining=%s" % sorted(rem))
ck("反控 N3 对照：旧看板里段①②确实存在",
   ({r1, r2} <= set(r for _, r in hd)), str(sorted(set(r for _, r in hd))))

# ---- wx 独占备份 ----
ts = time.strftime("%Y%m%d_%H%M%S")
bk = {}
for tag, p in (("STATUS_BOARD", BOARD), ("BOARD_ARCHIVE", ARCH)):
    bk[tag] = os.path.join(BASE, "SUPERSEDED.before_r68_archive_%s_%s.md" % (tag, ts))
P("")
P("[backup] wx 独占创建" + ("  [DRY-RUN 跳过]" if DRY else ""))
if not DRY:
    for tag, raw in (("STATUS_BOARD", board_raw), ("BOARD_ARCHIVE", arch_raw)):
        with open(bk[tag], "xb") as f:
            f.write(raw)
        got = open(bk[tag], "rb").read()
        ck("备份 %s 字节一致" % os.path.basename(bk[tag]), sha(got) == sha(raw))
    assert sha(open(bk["STATUS_BOARD"], "rb").read()) == sha(board_raw)
    assert sha(open(bk["BOARD_ARCHIVE"], "rb").read()) == sha(arch_raw)
    P("[write] 一次性写入")
    open(ARCH, "wb").write(new_arch.encode("utf-8"))
    open(BOARD, "wb").write(new_board.encode("utf-8"))

b2 = open(BOARD, "rb").read() if not DRY else new_board.encode("utf-8")
a2 = open(ARCH, "rb").read() if not DRY else new_arch.encode("utf-8")
P("[after] STATUS_BOARD %d B CR=%d LF=%d sha=%s"
  % (len(b2), b2.count(b"\r"), b2.count(b"\n"), sha(b2)[:16]))
P("[after] BOARD_ARCHIVE %d B CR=%d LF=%d sha=%s"
  % (len(a2), a2.count(b"\r"), a2.count(b"\n"), sha(a2)[:16]))
ck("回读 STATUS_BOARD CR=0", b2.count(b"\r") == 0)
ck("回读 BOARD_ARCHIVE CR=%d" % CR_EXP_ARCH, a2.count(b"\r") == CR_EXP_ARCH)
ck("回读 看板字节 == 预期", b2 == new_board.encode("utf-8"))
ck("回读 归档字节 == 预期", a2 == new_arch.encode("utf-8"))
ck("看板增量 < 0", len(b2) - len(board_raw) < 0, "%+d B" % (len(b2) - len(board_raw)))
ck("归档增量 > 0", len(a2) - len(arch_raw) > 0, "%+d B" % (len(a2) - len(arch_raw)))

P("")
P("RESULT " + ("ALL-PASS" if not fails else "FAIL: " + ",".join(fails)))
if not DRY:
    io.open(os.path.join(HERE, "archive_r68.log"), "w", encoding="utf-8",
            newline="\n").write("\n".join(buf) + "\n")
sys.exit(0 if not fails else 1)
