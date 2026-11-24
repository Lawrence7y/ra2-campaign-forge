# -*- coding: utf-8 -*-
"""R73 归档器：看板 273 行 >= 260 ⇒ 先把「最早的 2 段」逐字搬进 BOARD_ARCHIVE。

与 R68 归档器的差别（以及为什么改）：
  * R68 只认 `## <emoji> R17 第 N 轮` 形态的段头。本看板**最早的两段**不是轮次段，
    而是 `## 🔴🔴 Lead 自认错误` 与 `## 🔴 本段第二个系统性发现`（第 19-21 轮时期的常设结论）。
    按「最早的 2 段」字面执行，就得认任意顶格 `## ` 段头，排除 `> 📦` 指针行。
  * 被切掉的 slab 里夹着**别的**指针行（第 33 行「第 62–90 段已归档」）。
    若只把两个段搬走、slab 里的指针行不搬，那行就会**凭空消失**。
    ⇒ 本器把 slab **整块**逐字搬进归档（missing 断言对整个 slab 的非空行做），
      看板上只留 2 条新指针。

纪律（与 R72 事故教训一致：断言只记录不中止 = 没有断言）：
  wx 独占备份 -> 断言旧 sha256 与 CR -> 断言新内容自洽 -> 一次性写入 -> 回读校验。
  任何断言 FAIL 立即 exit 3，**不写任何 live 文件**。
  「已含本轮归档段则拒绝」前置守卫：重跑不会二次追加。
"""
import io, os, re, sys, hashlib, time

DRY = "--dry" in sys.argv
ART = "R73"
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
BASE = os.path.join(R14, "R17_LEAD_BASELINE")
BOARD = os.path.join(R14, "STATUS_BOARD.md")
ARCH = os.path.join(R14, "BOARD_ARCHIVE.md")

CR_EXP_BOARD, CR_EXP_ARCH = 0, 2952
FAILS = []


def P(s=""):
    print(s)


def ck(name, cond, detail=""):
    P(("  PASS " if cond else "  FAIL ") + name + (("  " + detail) if detail else ""))
    if not cond:
        FAILS.append(name)
    return cond


def abort_if_fails(where):
    if FAILS:
        P("")
        P("[ABORT] %s 断言失败 %d 条：%s —— 不写任何 live 文件" % (where, len(FAILS), FAILS))
        sys.exit(3)


def sha(b):
    return hashlib.sha256(b).hexdigest()


board_raw = io.open(BOARD, "rb").read()
arch_raw = io.open(ARCH, "rb").read()
P("[before] STATUS_BOARD   %d B  CR=%d  LF=%d  sha=%s"
  % (len(board_raw), board_raw.count(b"\r"), board_raw.count(b"\n"), sha(board_raw)[:16]))
P("[before] BOARD_ARCHIVE  %d B  CR=%d  LF=%d  sha=%s"
  % (len(arch_raw), arch_raw.count(b"\r"), arch_raw.count(b"\n"), sha(arch_raw)[:16]))

ck("旧 STATUS_BOARD CR=0", board_raw.count(b"\r") == CR_EXP_BOARD, str(board_raw.count(b"\r")))
ck("旧 BOARD_ARCHIVE CR=%d" % CR_EXP_ARCH, arch_raw.count(b"\r") == CR_EXP_ARCH,
   str(arch_raw.count(b"\r")))

board = board_raw.decode("utf-8")
arch = arch_raw.decode("utf-8")
ck("STATUS_BOARD 解码后无 CR", "\r" not in board)

# 前置守卫：本轮段不得已存在（防重跑二次追加 —— R72 事故的直接教训）
ck("前置守卫：归档里尚未含本轮标记 %s" % ART, ("归档原文（%s · 逐字）" % ART) not in arch)
abort_if_fails("前置守卫")

lines = board.split("\n")
P("[before] 看板 split('\\n') 行数 = %d" % len(lines))
ck("旧看板行数 >= 260（归档触发条件）", len(lines) >= 260, str(len(lines)))

# ---- 段头：任意顶格 '## '，排除 '> 📦' 指针行（它们以 '>' 开头，本就不会 match）----
HDR = re.compile(r"^## ")
idx = [i for i, l in enumerate(lines) if HDR.match(l)]
P("[段头] 顶格 ## 段头 %d 个，行号(1-based)=%s" % (len(idx), [i + 1 for i in idx]))
ck("段头数 >= 3", len(idx) >= 3, str(len(idx)))

i0, i1, i2 = idx[0], idx[1], idx[2]
P("[切分] 段①=行 %d..%d  段②=行 %d..%d  下一段起于行 %d"
  % (i0 + 1, i1, i1 + 1, i2, i2 + 1))
P("       段①标题: %s" % lines[i0][:60])
P("       段②标题: %s" % lines[i1][:60])

slab = lines[i0:i2]
ck("slab 非空", len(slab) > 0, "%d 行" % len(slab))
ck("slab 首行是段①标题", slab[0] == lines[i0])
ck("slab 末行是段②的末行（下一段标题不在 slab 内）", not HDR.match(slab[-1]),
   "末行=%r" % slab[-1][:40])
ck("slab 内恰好含 2 个顶格段头", sum(1 for x in slab if HDR.match(x)) == 2,
   str(sum(1 for x in slab if HDR.match(x))))
ck("slab 内不含第 3 段标题", lines[i2] not in slab)


# ---- 判据修正（R73 实测暴露，非推断）----
# 第一版沿用了 R68 归档器的「逐行是否出现在 hay 里」当搬运判据，N1 反控当场判 FAIL：
# slab 的 36 个非空行里有 3 行**在旧归档里已经存在**（`|---|---:|` / `|---|---|---|` /
# `|---|---:|---|`，markdown 表分隔行）。这不是「内容已在归档」，而是**样板行在任何
# 63 万字节的归档里都必然出现** ⇒ 逐行成员检测**无法区分「搬过去了」与「样板碰巧重复」**。
# 这与 R72 的教训同族（判据必须对整改前后都成立）：逐行检测在 N1 这个方向上失效。
# 改法：主判据用**整块连续包含**（整段逐字、同序、同换行，样板行不构成假阳性），
# 逐行计数降为**诊断量**并显式排除表格分隔行，两条都报出来。
_RULE = re.compile(r"^[\|\-\: ]+$")


def block_in(block, hay):
    return block in hay


def missing(seg, hay):
    """诊断量：非空、且非表分隔行的行里，有多少不在 hay。空串在任何文本里都存在，
    表分隔行在长文里必然重复 —— 两者都不能当「命中」的证据。"""
    return sum(1 for l in seg if l.strip() and not _RULE.match(l) and l not in hay)


nz = sum(1 for x in slab if x.strip())
nz_d = sum(1 for x in slab if x.strip() and not _RULE.match(x))
body = "\n".join(slab)
P("[判据] slab 非空行 %d，其中表分隔样板行 %d，可判别行 %d" % (nz, nz - nz_d, nz_d))
ck("反控 N1 旧归档不含 slab 整块（主判据：整块连续包含必假）", not block_in(body, arch))
ck("反控 N1b 旧归档缺 slab 的可判别行（诊断判据同向）", missing(slab, arch) == nz_d,
   "missing=%d/%d 可判别" % (missing(slab, arch), nz_d))
ghost_block = body + "\n## 🔴 R17 第 999 轮（虚构行，归档里不得存在）"
ck("反控 N2 整块检测器对多一行敏感（改一行即判缺）", not block_in(ghost_block, arch))
ck("反控 N2b 诊断判据对虚构行敏感", missing(slab + ["## 🔴 R17 第 999 轮（虚构行）"], arch) == nz_d + 1,
   "missing=%d" % missing(slab + ["## 🔴 R17 第 999 轮（虚构行）"], arch))

# ---- 生成新归档 / 新看板 ----
new_arch = (arch.rstrip("\n")
            + "\n\n<details><summary>归档原文（%s · 逐字 slab，含其间指针行）</summary>\n\n%s\n\n</details>\n"
            % (ART, body))

ptr = []
for seg_i in (i0, i1):
    t = lines[seg_i]
    label = t[3:] if t.startswith("## ") else t
    ptr.append("> 📦 ## %s 已归档至 BOARD_ARCHIVE.md（2026-11-22 23:0x，逐字搬，"
               "missing=0；本次由 Lead 执行，卫生员 %s）" % (label, ART))
ck("指针行数 = 2", len(ptr) == 2)

new_board = "\n".join(lines[:i0] + ptr + lines[i2:])

ck("新归档 CR 数不变 (=%d)" % CR_EXP_ARCH, new_arch.count("\r") == CR_EXP_ARCH,
   str(new_arch.count("\r")))
ck("新看板 CR=0", new_board.count("\r") == 0, str(new_board.count("\r")))
ck("新归档以 </details> 结尾", new_arch.rstrip("\n").endswith("</details>"))
ck("新归档含 slab 整块（主判据，missing=0）", block_in(body, new_arch))
ck("新归档缺 slab 可判别行 0 条（诊断判据同向）", missing(slab, new_arch) == 0,
   "missing=%d" % missing(slab, new_arch))

nb = new_board.split("\n")
P("[after] 新看板行数 = %d（旧 %d − %d + 2）" % (len(nb), len(lines), len(slab)))
ck("新看板行数 = 旧 − slab + 2", len(nb) == len(lines) - len(slab) + 2, str(len(nb)))
ck("新看板行数 <= 250（留足第 73 轮余量）", len(nb) <= 250, str(len(nb)))
ck("新看板段头数 = 旧 − 2", sum(1 for x in nb if HDR.match(x)) == len(idx) - 2,
   str(sum(1 for x in nb if HDR.match(x))))
ck("反控 N3 被归档的两段标题已不以顶格出现",
   not any(HDR.match(x) and x in (lines[i0], lines[i1]) for x in nb))
ck("反控 N3 对照：旧看板里它们确实存在",
   any(HDR.match(x) and x == lines[i0] for x in lines) and any(HDR.match(x) and x == lines[i1] for x in lines))
ck("新看板仍保留最后一段（第 72 轮）", any("第 72 轮" in x and HDR.match(x) for x in nb))
ck("新看板仍保留 2 条新指针", sum(1 for x in nb if x.startswith("> 📦 ## ") and ART in x) == 2,
   str(sum(1 for x in nb if x.startswith("> 📦 ## ") and ART in x)))
# slab 里夹着的旧指针行必须仍被保住（在归档里）
mid_ptr = [x for x in slab if x.startswith("> 📦") and "已归档" in x]
P("[检查] slab 内夹带的旧指针行 %d 条：%s" % (len(mid_ptr), [x[:38] for x in mid_ptr]))
ck("slab 内旧指针行全部进入归档", all(x in new_arch for x in mid_ptr))
abort_if_fails("写前自洽")

# ---- wx 独占备份 ----
ts = time.strftime("%Y%m%d_%H%M%S")
bk = {}
for tag, p in (("STATUS_BOARD", BOARD), ("BOARD_ARCHIVE", ARCH)):
    bk[tag] = os.path.join(BASE, "SUPERSEDED.before_r73_archive_%s_%s.md" % (tag, ts))
P("")
P("[backup] wx 独占创建" + ("  [DRY-RUN 跳过]" if DRY else ""))
if not DRY:
    for tag, raw in (("STATUS_BOARD", board_raw), ("BOARD_ARCHIVE", arch_raw)):
        with open(bk[tag], "xb") as f:
            f.write(raw)
        ck("备份 %s 字节一致" % os.path.basename(bk[tag]),
           sha(io.open(bk[tag], "rb").read()) == sha(raw))
    abort_if_fails("备份校验")
    P("[write] 一次性写入（归档 -> 看板）")
    with open(ARCH, "wb") as f:
        f.write(new_arch.encode("utf-8"))
    with open(BOARD, "wb") as f:
        f.write(new_board.encode("utf-8"))

b2 = io.open(BOARD, "rb").read() if not DRY else new_board.encode("utf-8")
a2 = io.open(ARCH, "rb").read() if not DRY else new_arch.encode("utf-8")
P("[after] STATUS_BOARD   %d B  CR=%d  LF=%d  sha=%s"
  % (len(b2), b2.count(b"\r"), b2.count(b"\n"), sha(b2)[:16]))
P("[after] BOARD_ARCHIVE  %d B  CR=%d  LF=%d  sha=%s"
  % (len(a2), a2.count(b"\r"), a2.count(b"\n"), sha(a2)[:16]))
ck("回读 STATUS_BOARD 字节 == 预期", b2 == new_board.encode("utf-8"))
ck("回读 BOARD_ARCHIVE 字节 == 预期", a2 == new_arch.encode("utf-8"))
ck("回读 看板 CR=0", b2.count(b"\r") == 0)
ck("回读 归档 CR=%d" % CR_EXP_ARCH, a2.count(b"\r") == CR_EXP_ARCH)
ck("看板增量 < 0", len(b2) - len(board_raw) < 0, "%+d B" % (len(b2) - len(board_raw)))
ck("归档增量 > 0", len(a2) - len(arch_raw) > 0, "%+d B" % (len(a2) - len(arch_raw)))

P("")
P("RESULT " + ("ALL-PASS" if not FAILS else "FAIL: " + ",".join(FAILS)))
sys.exit(0 if not FAILS else 1)
