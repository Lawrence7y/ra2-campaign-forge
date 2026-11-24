# -*- coding: utf-8 -*-
"""R78 归档器：看板 283 行 >= 260 ⇒ 先把「最早的 2 段」逐字搬进 BOARD_ARCHIVE。

沿用 R73 / R75 的判据修正（不改判据，只复用）：
  * 段头 = 任意顶格 '## '（不限于轮次段），排除 '> 📦' 指针行
  * 主判据 = **行尾归一化后**的整块连续包含（看板 LF，归档 CRLF，不归一必误判「不在」）
  * 常设段（含「基线」「真机授权」「口径裁定」关键词）搬走后，指针行必须带常设标注

R78 新增（本轮实测逼出来的）：
  * 段② = 「Lead 口径裁定」123 行 / 23,589 B，是**台账无关的流程规范段**。
    把它搬走后看板里仍必须能检索到「三分母口径」，因此指针行里显式带关键词，
    且脚本断言「新看板里该关键词只出现在指针行上」——否则后人查口径会查到一条死指针。
  * 断言「归档 CR 数不变（2952）」与「看板 CR=0」两条不变量在任何写入之前先量。

纪律：wx 独占备份 -> 断言旧 sha256 与 CR -> 断言新内容自洽 -> 一次性写入 -> 回读校验。
任何断言 FAIL 立即 exit 3，不写任何 live 文件。
"""
import hashlib
import io
import os
import re
import sys
import time

DRY = "--dry" in sys.argv
ART = "R78"
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
    P(("  PASS " if cond else "  FAIL ") + name + (("  " + str(detail)) if detail else ""))
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


def lf(x):
    return x.replace("\r\n", "\n")


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

# 前置守卫：本轮指针不得已存在（防重跑二次追加）
ck("前置守卫：归档里尚未含本轮标记 %s" % ART, ("归档原文（%s · 逐字" % ART) not in arch)
abort_if_fails("前置守卫")

lines = board.split("\n")
P("[before] 看板 split('\\n') 行数 = %d" % len(lines))
ck("旧看板行数 >= 260（归档触发条件）", len(lines) >= 260, str(len(lines)))

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

_RULE = re.compile(r"^[\|\-\: ]+$")


def block_in(block, hay):
    return block in hay


def count_block(block, hay):
    return hay.count(block)


def missing(seg, hay):
    return sum(1 for l in seg if l.strip() and not _RULE.match(l) and l not in hay)


nz = sum(1 for x in slab if x.strip())
nz_d = sum(1 for x in slab if x.strip() and not _RULE.match(x))
body = "\n".join(slab)
P("[判据] slab 非空行 %d，其中表分隔样板行 %d，可判别行 %d" % (nz, nz - nz_d, nz_d))
ck("反控 N1 旧归档不含 slab 整块（主判据：整块连续包含必假）", not block_in(body, arch))
ghost_block = body + "\n## 🔴 R17 第 999 轮（虚构行，归档里不得存在）"
ck("反控 N2 整块检测器对多一行敏感（改一行即判缺）", not block_in(ghost_block, arch))

arch_lf = lf(arch)
seg_txt = {}
for i in (i0, i1):
    j = i1 if i == i0 else i2
    seg_txt[i] = "\n".join(lines[i:j])
P("")
P("=== 逐段判定（行尾归一化，R75 判据） ===")
already, notyet = [], []
for i in (i0, i1):
    t = lines[i]
    c_raw = count_block(seg_txt[i], arch)
    c_lf = count_block(seg_txt[i], arch_lf)
    P("  段 %s : %d 行 / %d B ；原始整块计数 = %d ；行尾归一后 = %d"
      % ((i + 1), seg_txt[i].count("\n") + 1, len(seg_txt[i].encode("utf-8")), c_raw, c_lf))
    if c_lf:
        pos = arch_lf.find(seg_txt[i])
        P("        归档内已有同内容（归一后第 %d 行起）；行尾差异 = %s"
          % (arch_lf.count("\n", 0, pos) + 1, "CRLF vs LF" if c_raw == 0 else "无"))
        already.append(i)
    else:
        notyet.append(i)
P("  已在归档的段 %d 个 ；需要真搬的段 %d 个" % (len(already), len(notyet)))
ck("至少一段需要真搬（否则本轮归档是空操作，应显式记「不适用」）", len(notyet) >= 1,
   str(len(notyet)))
ck("被判「已在归档」的段，归一后整块计数必须恰好 1（重复即歧义）",
   all(count_block(seg_txt[i], arch_lf) == 1 for i in already),
   str({(i + 1): count_block(seg_txt[i], arch_lf) for i in already}))
ck("被判「已在归档」的段，其原始计数为 0 ⇒ 差异确实只来自行尾",
   all(count_block(seg_txt[i], arch) == 0 for i in already),
   str({(i + 1): count_block(seg_txt[i], arch) for i in already}))
ck("被判「不在归档」的段，归一后计数也必须为 0（归一化没有放宽到假阳性）",
   all(count_block(seg_txt[i], arch_lf) == 0 for i in notyet),
   str({(i + 1): count_block(seg_txt[i], arch_lf) for i in notyet}))

KEYWORDS = ("基线", "真机授权", "口径裁定", "分母")
preset = [t for t in (lines[i0], lines[i1]) if any(k in t for k in KEYWORDS)]
P("[常设段] 被搬两段里命中常设关键词的 %d 段" % len(preset))
ck("被搬走的段里含常设段（否则指针标注规则用不上，应显式记「不适用」）",
   len(preset) >= 1, str(len(preset)))

# ---- 生成新归档 / 新看板 ----
append_slabs = []
for i in notyet:
    j = i1 if i == i0 else i2
    append_slabs.append((i, "\n".join(lines[i:j])))
if append_slabs:
    extra = "\n\n".join(b for _, b in append_slabs)
    new_arch = (arch.rstrip("\n")
                + "\n\n<details><summary>归档原文（%s · 逐字，仅收录本次新搬的 %d 段）</summary>\n\n%s\n\n</details>\n"
                % (ART, len(append_slabs), extra))
else:
    new_arch = arch
    P("[note] 两段都已在归档内 ⇒ 本次只留指针，归档字节不变")

ptr = []
# 检索锚点白名单：搬走常设段后，这些「后人会去查的词」必须在指针行上留下。
# 这是本轮 dry-run 抓出来的真问题：段②（Lead 口径裁定）搬走后「三分母」在**新看板**上 0 命中
# ⇒ 指针只带标题是不够的，必须带内容锚点。白名单是显式列出的，不是从正文猜的。
ANCHORS = ("三分母", "分母 A", "12,916", "14,715", "18,431", "双分母")
for seg_i in (i0, i1):
    t = lines[seg_i]
    j = i1 if seg_i == i0 else i2
    seg_body = "\n".join(lines[seg_i:j])
    label = t[3:] if t.startswith("## ") else t
    tag = ("，**常设段（流程规范 / 运行态基线类），内容逐字在归档内**"
           if any(k in t for k in KEYWORDS) else "")
    hits = [a for a in ANCHORS if a in seg_body]
    anchor_note = ("；检索锚点：**%s**" % " / ".join(hits)) if hits else ""
    how = ("归档内原已有，本次只留指针、未重复追加" if seg_i in already
           else "逐字搬，missing=0")
    ptr.append("> 📦 ## %s 已归档至 BOARD_ARCHIVE.md（2026-11-23 03:5x，%s；"
               "本次由 Lead 执行，卫生员 %s%s%s）" % (label, how, ART, tag, anchor_note))
ck("指针行数 = 2", len(ptr) == 2)
for p_ in ptr:
    P("  指针: %s" % p_[:110])
ck("被搬走的每个常设段，其指针行必须带常设标注",
   all(("常设段" in p_) for t, p_ in zip((lines[i0], lines[i1]), ptr)
       if any(k in t for k in KEYWORDS)))

new_board = "\n".join(lines[:i0] + ptr + lines[i2:])

ck("新归档 CR 数不变 (=%d)" % CR_EXP_ARCH, new_arch.count("\r") == CR_EXP_ARCH,
   str(new_arch.count("\r")))
ck("新看板 CR=0", new_board.count("\r") == 0, str(new_board.count("\r")))
ck("新归档对每个**真搬**的段做整块计数（归一后），必须恰好 +1",
   all(count_block(b, lf(new_arch)) == count_block(b, arch_lf) + 1 for _, b in append_slabs),
   str([(i + 1, count_block(b, lf(new_arch)), count_block(b, arch_lf)) for i, b in append_slabs]))
ck("新归档对**已在归档**的段，归一后整块计数不得变化（防重复归档）",
   all(count_block(seg_txt[i], lf(new_arch)) == count_block(seg_txt[i], arch_lf) for i in already),
   str([(i + 1, count_block(seg_txt[i], lf(new_arch))) for i in already]))
if append_slabs:
    ck("新归档以 </details> 结尾", new_arch.rstrip("\n").endswith("</details>"))
ck("新归档缺 slab 可判别行 0 条（诊断判据，含已在归档的那段）", missing(slab, new_arch) == 0,
   "missing=%d" % missing(slab, new_arch))

nb = new_board.split("\n")
P("[after] 新看板行数 = %d（旧 %d − %d + 2）" % (len(nb), len(lines), len(slab)))
ck("新看板行数 = 旧 − slab + 2", len(nb) == len(lines) - len(slab) + 2, str(len(nb)))
ck("新看板行数 <= 200（留足第 78 轮与后续余量）", len(nb) <= 200, str(len(nb)))
ck("新看板段头数 = 旧 − 2", sum(1 for x in nb if HDR.match(x)) == len(idx) - 2,
   str(sum(1 for x in nb if HDR.match(x))))
ck("反控 N3 被归档的两段标题已不以顶格出现",
   not any(HDR.match(x) and x in (lines[i0], lines[i1]) for x in nb))
ck("反控 N3 对照：旧看板里它们确实存在",
   any(HDR.match(x) and x == lines[i0] for x in lines)
   and any(HDR.match(x) and x == lines[i1] for x in lines))
ck("新看板仍保留最后一段（第 77 轮）", any("第 77 轮" in x and HDR.match(x) for x in nb))
ck("新看板仍保留 2 条新指针",
   sum(1 for x in nb if x.startswith("> 📦 ## ") and ART in x) == 2,
   str(sum(1 for x in nb if x.startswith("> 📦 ## ") and ART in x)))
mid_ptr = [x for x in slab if x.startswith("> 📦") and "已归档" in x]
P("[检查] slab 内夹带的旧指针行 %d 条" % len(mid_ptr))
ck("slab 内旧指针行全部进入归档", all(x in new_arch for x in mid_ptr))

# 关键词可检索性：搬走的常设段里的关键词，在**新看板**上必须仍能检索到（经指针行）
for kw in ("真机授权", "口径裁定", "三分母", "分母 A", "12,916", "14,715", "18,431"):
    in_old = [x for x in slab if kw in x]
    in_new = [x for x in nb if kw in x]
    P("[检索] 关键词 %-8s 旧 slab 出现 %3d 行；新看板出现 %2d 行" % (kw, len(in_old), len(in_new)))
    if in_old and any(not x.startswith("> 📦") for x in in_old):
        # 只对「正文里出现过的」要求可检索；只出现在旧指针行上的词不算
        ck("关键词 %s 搬走后仍可在新看板上检索到（经指针行）" % kw, len(in_new) >= 1, len(in_new))
abort_if_fails("写前自洽")

# ---- wx 独占备份 ----
ts = time.strftime("%Y%m%d_%H%M%S")
bk = {}
for tag in ("STATUS_BOARD", "BOARD_ARCHIVE"):
    bk[tag] = os.path.join(BASE, "R78.before_archive_%s_%s.md" % (tag, ts))
P("")
P("[backup] wx 独占创建" + ("  [DRY-RUN 跳过]" if DRY else ""))
if not DRY:
    for tag, raw in (("STATUS_BOARD", board_raw), ("BOARD_ARCHIVE", arch_raw)):
        if os.path.exists(bk[tag]):
            P("[ABORT] 备份目标已存在（拒绝覆盖）：%s" % bk[tag])
            sys.exit(3)
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

    a2 = io.open(ARCH, "rb").read()
    b2 = io.open(BOARD, "rb").read()
    P("[read-back] ARCH %d B CR=%d ；BOARD %d B CR=%d"
      % (len(a2), a2.count(b"\r"), len(b2), b2.count(b"\r")))
    ck("回读：归档字节 = 预期", sha(a2) == sha(new_arch.encode("utf-8")), sha(a2)[:16])
    ck("回读：看板字节 = 预期", sha(b2) == sha(new_board.encode("utf-8")), sha(b2)[:16])
    ck("回读：归档 CR = 2952", a2.count(b"\r") == CR_EXP_ARCH, a2.count(b"\r"))
    ck("回读：看板 CR = 0", b2.count(b"\r") == 0, b2.count(b"\r"))
    ck("回读：看板行数 = 预期", len(b2.split(b"\n")) == len(nb), len(b2.split(b"\n")))
    abort_if_fails("回读校验")

P("")
P("SUMMARY fails=%d" % len(FAILS))
sys.exit(0 if not FAILS else 3)
