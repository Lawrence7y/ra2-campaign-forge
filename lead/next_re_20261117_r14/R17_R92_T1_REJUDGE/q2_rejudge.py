#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R92-T1-REJUDGE / Q2 : 按 R14_COMMON.md §2.49 新口径逐件重判 EVIDENCE 全集 1242 件。

口径原文（§2.49 二节表 + 四节三问）：
  判据不是「它是不是运行时产生的」，而是「它记录的是被测对象的内容，还是我读它的动作」。
    记「我读了哪个地址/何时/成功没」             → 过程
    记「那个地址里是什么字节/值」且可回原址复核  → 对象侧输入，可计入
    记「事件名/符号名/字符串表」且逐条列出内容   → 对象侧输入，可计入
    记「校验和/哈希/差分结果」                   → 过程（哈希是我算的）
    原文件已无对象内容                           → 永久判不了

三问顺序（§2.49 四）：内容优先
  问1 有没有列出对象侧的值本身（字节/地址/名字/字符串/结构体字段的具体内容）？
      → 有：记下能否回原址复核；不能复核的降为过程
  问2 是不是只记动作（读了/写了/比对了/耗时/退出码/哈希）？→ 过程
  问3 原文件是否已不含对象内容？→ 永久判不了

§2.49 只定义「口径」，不定义「用哪个统计量」。「运行时不作为分界」这句只否掉了
R44 的 strong-proc-frame 分支（一见到 RUN_ID/COMMAND/时间戳就整件判死），并没有换成
「运行时痕迹占多数就判死」。所以本脚本的主导量是 **对象侧输入的内容密度**：

    density = 携带对象侧内容的段数 / 全部段数

  · density >= 0.5 且至少 1 段「地址↔值」并存可回原址 → 对象（内容占主体）
  · 否则若有过程动作段 → 过程（动作占主体）
  · 两者皆无 → 问3 → 永久判不了

两条盲区修复（卡 §二 Q2 第 3–4 点）：
  盲区A  ROW_*.txt 地址不带 0x（entry=00524D70）⇒ 新正则同时收 0x 前缀与裸十六进制，
        并用「上下文锚 + .text VA 区间 + 大小写一致 + 纯数字拒绝」四道闸防误判。
  盲区B  单行大 JSON ⇒ 按内容分隔符（}{ / \n / ; / ","）切段算占比，不用「行」当分母。
"""
import csv, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")

LEAD = r"D:\Project\ra2-campaign-forge\lead"
OUT = os.path.join(LEAD, "next_re_20261117_r14", "R17_R92_T1_REJUDGE")
CAP = 1 << 20      # 每件最多读 1 MiB（846 KB 的 q3_cfg.json 可整读）

# ============================================================
# 0 · 读取
# ============================================================


def read_text(rel):
    p = os.path.join(LEAD, rel.replace("/", os.sep))
    try:
        total = os.path.getsize(p)
        with open(p, "rb") as f:
            b = f.read(CAP)
    except Exception:
        return None, 0, 0
    if b[:2] in (b"\xff\xfe", b"\xfe\xff"):
        t = b.decode("utf-16", errors="replace")
    else:
        t = b.decode("utf-8", errors="replace")
    return t, len(b), total


# ============================================================
# 1 · 盲区B 修复：按内容分隔符切段（不用「行」当分母）
# ============================================================


def segments(t):
    """把文本切成「内容段」。单行大 JSON 与普通多行文本走同一条路。

    分隔符（命中即切）：}{   }\n{   \n   ;
    若整份文件既无换行、也无 }{，再退回按 '","' 切。
    """
    s = t.replace("}{", "}\n{").replace("},\n{", "}\n{")
    parts = [p for p in s.split("\n") if p.strip()]
    if len(parts) <= 1:
        parts = [p for p in re.split(r"[;]", s) if p.strip()]
        if len(parts) <= 1:
            parts = [p for p in re.split(r'"\s*,\s*"', s) if p.strip()]
    return parts


# ============================================================
# 2 · 盲区A 修复：地址识别（0x 前缀 + 裸十六进制 + 防误判）
# ============================================================
ADDR_PREFIX = re.compile(r"0[xX][0-9A-Fa-f]{6,8}")
BARE = re.compile(r"(?<![0-9A-Za-z_])([0-9A-Fa-f]{6,8})(?![0-9A-Za-z_])")
TEXT_LO, TEXT_HI = 0x00400000, 0x00B00000     # gamemd.exe .text 显式 VA 区间
# 上下文锚：地址正前方 24 字符内出现「地址语义」关键字或分隔符
ANCHOR_PRE = re.compile(
    r"(entry|target|tgt|callee|call|site|jmp|jcc|va|rva|foff|off|ptr|base|addr|ret|loc|sub|at|slot)"
    r"\s*[=:]?\s*$|[@\[]\s*$|\bsub_\s*$|地址|入口|站点|偏移|槽", re.I)
HEXCTX_PRE = re.compile(r"(hex|bytes?|dump|raw|insn)\s*[=:]?\s*$|字节|十六进制", re.I)


def bare_is_addr(tok, prefix):
    """裸十六进制是否算地址。

    四道闸：
      (1) 位数闸：正则已是 6..8 位。
      (2) 纯数字闸：不含 A-F 的 6..8 位十进制，只有落在 .text VA 区间
          [0x00400000,0x00B00000) 才收；否则当普通计量数（如 1234567）拒掉。
      (3) 大小写闸：含字母时须全大写或全小写（ROW 00459900 / entry=00524D70 都是全大写），
          混合大小写只在明确 hex 语境（hex=/dump/字节）里才收。
      (4) 上下文锚闸：须紧贴地址语义锚，或落在 .text VA 区间。
    """
    v = int(tok, 16)
    has_alpha = bool(re.search(r"[A-Fa-f]", tok))
    if not has_alpha:
        return TEXT_LO <= v <= TEXT_HI          # 闸2
    if not (tok.upper() == tok or tok.lower() == tok):   # 闸3
        return bool(HEXCTX_PRE.search(prefix[-24:]))
    if TEXT_LO <= v <= TEXT_HI:                 # 闸4 前半
        return True
    return bool(ANCHOR_PRE.search(prefix[-24:]) or HEXCTX_PRE.search(prefix[-24:]))


def find_addrs(seg):
    out = []
    for m in ADDR_PREFIX.finditer(seg):
        out.append(m.group(0))
    for m in BARE.finditer(seg):
        if bare_is_addr(m.group(1), seg[:m.start()]):
            out.append(m.group(1))
    seen, uniq = set(), []
    for a in out:
        k = a.lower()
        if k.startswith("0x"):
            k = k[2:]
        k = k.lstrip("0") or "0"
        if k not in seen:
            seen.add(k)
            uniq.append(a)
    return uniq


# ---- 十进制 VA 对：JSON 里常见 [4198410, 4223232] 这类十进制地址对 ----
# 闸：整对必须 *两* 个数都落在 .text VA 区间 [4194304, 11534336)（= 0x400000..0xB00000），
#     且第二个 >= 第一个。这样排除 [K=73,N=387]、[n=642, mine=0.199] 这类计数/比例对。
DEC_PAIR = re.compile(r"\[\s*(\d{7,8})\s*,\s*(\d{7,8})\s*\]")
DEC_TEXT_LO, DEC_TEXT_HI = 4194304, 11534336


def find_dec_pairs(seg):
    n = 0
    for m in DEC_PAIR.finditer(seg):
        a, b = int(m.group(1)), int(m.group(2))
        if DEC_TEXT_LO <= a < DEC_TEXT_HI and DEC_TEXT_LO <= b < DEC_TEXT_HI and b >= a:
            n += 1
    return n


# ============================================================
# 3 · 信号正则
# ============================================================
# ---- 对象侧「值本身」 ----
R_BYTES = re.compile(r"\b[0-9A-Fa-f]{2}(?:[ ][0-9A-Fa-f]{2}){3,}\b")      # 字节串
R_RAWBYTES = re.compile(r"b'(?:\\x[0-9a-f]{2}){2,}")
R_INSNDUMP = re.compile(r"^\s*(?:0x)?[0-9A-Fa-f]{6,8}\s*:\s*[a-z]{2,6}\b|^\s*0x[0-9A-Fa-f]{6,8}\s{2}[0-9a-f]{4,}")
# 入口相对偏移的反汇编行：「  +0x0000  83ec0c   sub esp, 0xc」
# 偏移 + 指令字节 + 助记符 三者并存 ⇒ 可回原址复核（偏移是对象内的确定位置）
R_INSNDUMP_REL = re.compile(r"^\s*\+\s*0x[0-9A-Fa-f]{2,8}\s{1,}[0-9A-Fa-f]{2,}(?:\s+[0-9A-Fa-f]{2,})*\s{1,}[a-z]{2,6}\b")
# 裸指令字节列：「83ec0c   sub esp, 0xc」（无地址但有字节+助记符）
R_INSNHEX = re.compile(r"^\s*[0-9A-Fa-f]{4,}(?:\s+[0-9A-Fa-f]{2,})*\s{1,}[a-z]{2,6}\s")
# 字节转储行：「0x010  C   0D -> 0E  (cDlgItems 13 -> 14)」「0x2B7  +   00」——
# 「对象内偏移 + 该偏移处的字节值」并存 ⇒ 正是 §2.49 问1 要的「地址↔值」，且可回原址复核。
R_BYTEDUMP = re.compile(
    r"^\s*(?:0x)?[0-9A-Fa-f]{3,8}\s{1,}(?:[NCc+]|0x[0-9A-Fa-f]{2})\s{1,}[0-9A-Fa-f]{2}\b")
R_STR = re.compile(r"\?\?__?\w|\.\?A(?:V|U)|[A-Za-z_]\w*(?:::\w+){1,}")   # RTTI / 符号名 Class::slot
R_NAME_ROW = re.compile(r"name\[\s*\d+\]\s*@|\bname\s*=")                  # 事件名表逐条
R_INI = re.compile(r"^\s*[^=;#\s][^=]{0,60}=\s*\S")                       # ini 键值（内容）
R_INI_SEC = re.compile(r"^\s*\[[A-Za-z0-9_]+\]\s*$")                       # ini 节名
R_FIELD = re.compile(r"\[(?:esi|edi|eax|ebx|ecx|edx|ebp|esp|reg|v|this)\s*[+\-]\s*0x[0-9A-Fa-f]+\]")
R_STRUCT = re.compile(r"struct\[|\bwaypoints\s*=|\brc\s*=\(|\bfnd\s*=\d|slot\s*offset|vtable base"
                      r"|slot#|Foundation\s*=\s*\d", re.I)
R_JSONKV = re.compile(r'"(?:a|hex|entry|lo|hi|name|slot|off|va|rva|size|type|addr|tgt|op|m|o)"\s*:')
# JSON 里「键是十六进制地址、值是列表」的映射表：「"00401950": [...]」
R_JSONKEYADDR = re.compile(r'"\s*(?:0x)?[0-9A-Fa-f]{6,8}\s*"\s*:\s*[\[\{]')
# 声明了「下面是什么」却什么都没跟上的小标题（内容缺失的现场）
# 例 verify_w151b.log：「=== disassembly 0x55B860 .. 0x55B905 ===」之后整段为空
R_SECTION_HEAD = re.compile(
    r"^\s*=+[\s\w:/.,\-()\[\]#]*\b(?:disassembly|dump|hexdump|listing|listing of|bytes|"
    r"instructions?)\b[\s\w:/.,\-()\[\]#]*=+\s*$"
    r"|^\s*(?:disassembly|disasm|dump|hexdump|listing)\s+"
    r"(?:of\s+)?(?:0x|[\w]+)[0-9A-Fa-fx]*\s*(?:\.\.|to|-)\s*(?:0x)?[0-9A-Fa-f]{3,}\s*[:=]?\s*$",
    re.I)
# 同段内「键值对」个数（用于识别一段里塞了多个条目的长行）
R_KVCOUNT = re.compile(r'"[A-Za-z_][A-Za-z0-9_]*(?:\[\d+\])?"\s*:\s*(?:"|\{|\[|\d|true|false|null)')
# ---- 过程侧「动作」 ----
R_HASH = re.compile(r"\bsha256\b|\bsha1\b|\bmd5\b|Get-FileHash|crc32\s*\(|\bhash\b", re.I)
R_EXIT = re.compile(r"exit\s*code|exitcode|exit=|EXITCODE|returncode|退出码", re.I)
R_TS = re.compile(r"20\d\d[-/]\d\d[-/]\d\d[T ]\d\d:\d\d|run_at|read_at|TIMESTAMP|mtime|ctime"
                  r"|耗时|elapsed|wall|cpu_ms|总趟数|趟数|样本", re.I)
R_CMD = re.compile(r"^\s*(COMMAND|CWD|RUN_ID|TASK)\s*[:=]|^>\s|^\s*python\s|^\s*git\s"
                   r"|\[write\]|\[copy\]|\[mv\]|saved\s+[A-Za-z]:", re.I)
R_ASSERT = re.compile(r"\bPASS\b|\bFAIL\b|VERIFIED|ASSERT|\[assert\]|identical\s*=\s*(True|False)"
                      r"|MATCH\s*=\s*(True|False)|\bproblems\s*:|\bassertions?\b|\bOK\b", re.I)
R_PATH = re.compile(r"[A-Za-z]:\\[^\s]{3,}|[A-Za-z]:/[^\s]{3,}")
R_DIFFWORD = re.compile(r"differing|dSize|LCP|LCS|idxDiff|before/after|vs\s+A2|equal\s*=\s*False"
                        r"|差分|比对|对照|shifted|identical|expected|->\s*True|n\s*=\s*\d", re.I)
R_MEASURE = re.compile(r"^(?:\s*)(?:dframe|span|rate|count|n|p50|p95|p99|min|max|mean|avg|std)\b"
                       r".*=|分布|占比|%\s*$|\d+(?:\.\d+)?\s*%", re.I)
R_BANNER = re.compile(r"^\s*(={3,}|-{3,}|#{3,}|\*{3,})")
# ---- 发布元数据头：整件是「我核过哪个二进制 + 它的哈希/规模」，没有任何对象内容 ----
# 例 scan_mine.json 开头：{"sha": "...64位...", "ib": 4194304, "soi": 7954432, ...}
R_META_PREFIX = re.compile(r'^\s*\{\s*"sha(?:256)?"\s*:\s*"[0-9A-Fa-f]{32,}"', re.I)
# ---- 「头部框架块」：RUN_ID/COMMAND/CWD/TIMESTAMP/EXITCODE 之类运行封装 ----
# R44 的 strong-proc-frame 分支就是见到这些整件判死；§2.49 只把它当「运行时痕迹」，
# 不是分界。但「可回原址复核」必须扣掉这一块——它们不是对象内容。
R_FRAME_LINE = re.compile(
    r"^\s*(?:RUN_ID|TASK|COMMAND|CWD|TIMESTAMP_LOCAL|TIMESTAMP|EXITCODE|EXIT_CODE|"
    r"run_at\w*|python\s*=|RE-\w+\s+args\b|.*BEGIN RAW STDOUT)", re.I)
# ---- 过程侧「我算出来的统计量」 ----
# 这类内容是「我跑了扫描、数了多少条、命中率多少」，对象里不存任何一项。
R_STATNAME = re.compile(
    r"(?:^|[\s{,(\[])(?:n|N|K|k|p|raw_hits\w*|whole_insn\w*|entry_insn\w*|call_\w+|"
    r"pool\w*|total|count\w*|cnt|rows?|n_\w+|by_\w+|conf|grade|sites?|hits?|miss\w*|cov\w*|"
    r"rate|ratio|mean|avg|median|p50|p95|p99|std|mc_mean|E8|abnormal|negret|identity)\s*[=:]\s*[-+]?\d")
R_STATWORD = re.compile(r"分母|占比|比例|命中率|覆盖率|总数|个数|条数|行数|趟数|样本|概率|置信|百分位"
                        r"|distribut|histogram|base\s*rate|pass\s*rate|\bby\s+\w+\s*:", re.I)
# 单键值段：「"key": 数字」独占一段（切段后的 JSON 常态）
KVSINGLE = re.compile(r'^\s*"?([A-Za-z_][A-Za-z0-9_ ]*)"?\s*:\s*[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?,?\s*$')
# 数字陈述句：「UNDECIDABLE 5598 | already-in-coverage 3929」「rows 18479, unique 18479」
R_NUMSTMT = re.compile(r"(?:[A-Za-z_][\w\- ]{2,})\s*[=:]?\s*\d{2,}")
# ---- 过程侧「只报了口径/结论/写过文件」，没留下任何内容 ----
# 例：「done; candidates=91」「Wrote EVIDENCE/T2_sub_bodies.txt (51 sub rows)」
#     「merged into foundation_evidence.json」「raw E8 candidates 0 … 0」
R_STATUS_ONLY = re.compile(
    r"^\s*(?:done|ok|finished|complete[d]?|wrote|written|saved|merged|copied|moved|"
    r"skipped|already|nothing|no\s+op|raw\s+\w+\s+candidates)\b"
    r"|\b(?:done;|Wrote\s|written to|merged into|candidates\s*[=:])\s*\S"
    r"|(?:已写入|已合并|已保存|完成)", re.I)
# ---- 过程侧「分类/分档计数」：{'BUCKET': 120, ...} ----
R_BUCKET = re.compile(r"\{[^{}]*':\s*\d+", re.UNICODE)
R_BUCKET_ANY = re.compile(r"\{[^{}]{0,400}'\s*:\s*\d+")
# 「名字=数字 / 名字 数字」重复 >=2 次 ⇒ 计数陈述。R14_R10_NOT_FUNC_DETAILS.txt 这类
# 全角分号、中文轨道前缀也能覆盖。
R_NUMSTMT2 = re.compile(r"[A-Za-z_\u4e00-\u9fff][\w\- \u4e00-\u9fff]{0,30}\s*[=:]\s*\d{1,}")
# 「"key": 数字」键值表（同一段里 >=3 组）——统计表的通用形态
KVTAB = re.compile(r'"[A-Za-z_][A-Za-z0-9_ ]*"\s*:\s*[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?')


def is_stat_only(s):
    """该段是否只是「我算出来的统计量」（计数/比率/池规模/分类计数），而不是对象侧的值本身。"""
    if R_BYTES.search(s) or R_RAWBYTES.search(s) or R_INSNDUMP.search(s):
        return False
    if find_addrs(s) or find_dec_pairs(s):
        return False
    if R_STR.search(s) or R_FIELD.search(s) or R_NAME_ROW.search(s):
        return False
    if R_BUCKET.search(s):
        return True
    if R_STATNAME.search(s) or R_STATWORD.search(s):
        return True
    # 一条 JSON 段/行里全是「"key": 数字」，也算统计量表
    if len(KVTAB.findall(s)) >= 3:
        return True
    return bool(KVSINGLE.match(s) or len(R_NUMSTMT.findall(s)) >= 2
                or len(R_NUMSTMT2.findall(s)) >= 2)


def cls_seg(s):
    """返回 (is_obj_content, is_reverifiable, is_proc_action)。"""
    addrs = find_addrs(s)
    decp = find_dec_pairs(s)
    rel_insn = bool(R_INSNDUMP_REL.search(s))
    bytedump = bool(R_BYTEDUMP.search(s))
    keyaddr = bool(R_JSONKEYADDR.search(s))
    nkv = len(R_KVCOUNT.findall(s))
    value = bool(R_BYTES.search(s) or R_RAWBYTES.search(s) or R_INSNDUMP.search(s)
                 or R_STR.search(s) or R_NAME_ROW.search(s) or R_FIELD.search(s)
                 or R_STRUCT.search(s) or R_JSONKV.search(s) or rel_insn
                 or R_INSNHEX.search(s) or keyaddr or bytedump)
    is_obj = bool(addrs or decp or value)
    # 可回原址复核：地址(或 RVA/偏移) 与 值/字节/符号/字段 同段共存。
    # 「入口相对偏移 + 指令字节 + 助记符」同段 ⇒ 也满足（偏移即对象内确定位置）。
    reverifiable = bool(((addrs or decp) and (value or decp)) or rel_insn or bytedump)
    # 一行塞了多个对象条目（如 entry_to_vt.json 的「"00401950": [...], "00401940": [...]」）
    if nkv >= 2 and keyaddr:
        is_obj = True
        reverifiable = True
    is_proc = bool(R_HASH.search(s) or R_EXIT.search(s) or R_TS.search(s) or R_CMD.search(s)
                   or R_ASSERT.search(s) or R_PATH.search(s) or R_DIFFWORD.search(s)
                   or R_MEASURE.search(s) or R_BANNER.search(s) or is_stat_only(s)
                   or R_STATUS_ONLY.search(s))
    # 「纯统计量」段不算对象内容（即使其中含数字）
    if is_stat_only(s) and not value and not addrs:
        is_obj = False
        reverifiable = False
    return is_obj, reverifiable, is_proc


# ============================================================
# 4 · 三问判决
# ============================================================
def judge(text, total):
    if text is None:
        return ("永久判不了", "未取得：文件不可读，内容取不到（非口径问题）", {})
    segs = segments(text)
    n = len(segs)
    if n == 0:
        # 空文件：§2.49 三问的落点要看清「永久判不了」的定义——
        # §2.49 表末行说的是「原文件已无对象内容（日志里反汇编体缺失等）」，
        # §2.46 三节也把 verify_w151b.log 单列为「内容本身缺失 ⇒ 永久判不了」。
        # 空文件的区别在于：它连「曾经有过对象内容、后来丢了」的痕迹都没有，
        # 记录的只是「我跑了一次、没产出内容」这一动作 ⇒ 按问2 归过程。
        return ("过程输出",
                f"§2.49 问2：文件 {total} B 全空/全空白，未列出任何对象侧内容，"
                f"只留下「跑了一次、无产出」这一动作痕迹 ⇒ 过程（与 R44 empty 分支同结论）", {})

    n_obj = n_rev = n_proc = n_frame = 0
    for s in segs:
        if R_FRAME_LINE.match(s):
            n_frame += 1
            continue
        o, rv, p = cls_seg(s)
        n_obj += o
        n_rev += rv
        n_proc += p
    # 分母一律用「扣掉运行封装之后的段数」（盲区B 的正解：分母随切分法走，不随行数走）
    n_eff = n - n_frame
    dens = n_obj / n_eff if n_eff else 0.0
    pdens = n_proc / n_eff if n_eff else 0.0
    stat = dict(seg_n=n, frame_segs=n_frame, obj_segs=n_obj, rev_segs=n_rev,
                proc_segs=n_proc, obj_ratio=round(dens, 3), proc_ratio=round(pdens, 3), addrs=0)
    stat["addrs"] = sum(len(find_addrs(s)) for s in segs)

    # ---- 发布元数据头：整件只有「我核的是哪个二进制 + 哈希 + 规模」⇒ 问2 过程 ----
    if R_META_PREFIX.match(text):
        return ("过程输出",
                f"§2.49 问2：文件以 \"sha\"(64 位哈希) 开头，内容是「我核的是哪个二进制、"
                f"它的字节数/规模/偏移」（{n} 段、统计型键值），无任何对象侧内容值"
                f"（其后纵有十进制地址对，也只是我算出的地址清单，不是「地址里是什么」）", stat)

    # ---- 问3（先于问1/问2 判）：原文件是否已不含对象内容？----
    # §2.49 表末行与 §2.46 三节把 verify_w151b.log 单列为「内容本身缺失 ⇒ 永久判不了」：
    # 该件写了「=== disassembly 0x55B860 .. 0x55B905 ===」小标题，下面一行内容都没有。
    # 判定必须只看「末尾的空小节」——小节标题本身在文件中部是正常的，
    # 只有「声明了内容、而其后到文件结束都没有任何内容」才算证据不完整。
    j = len(segs) - 1
    # 只看「被指向的内容在不在」——小节标题里写着的两个地址不算内容
    has_content = bool(R_INSNDUMP_REL.search(segs[j]) or R_INSNHEX.search(segs[j])
                       or R_BYTEDUMP.search(segs[j])
                       or R_INSNDUMP.search(segs[j]) or R_BYTES.search(segs[j])
                       or R_RAWBYTES.search(segs[j]) or R_STR.search(segs[j])
                       or R_FIELD.search(segs[j]) or find_dec_pairs(segs[j]))
    if R_SECTION_HEAD.match(segs[j]) and not has_content:
        return ("永久判不了",
                f"§2.49 问3：文件最后一个内容小节「{segs[j].strip()[:64]}」之下"
                f"到文件结束无任何对象内容（共 {total} B、{n} 段）⇒ 原文件已不含可复核内容，"
                f"属证据不完整，非口径问题（与 §2.46 对 verify_w151b.log 的处置一致）", stat)

    # ---- 问1：有没有列出对象侧的值本身？----
    if n_obj > 0:
        # 判「内容占主体」必须同时满足：
        #   (a) 可回原址复核的段 >= 5（足以支撑「内容」而不是顺手带出的几行）
        #   (b) 内容段数 > 过程动作段数（东西多过动作）
        #   (c) 内容段在扣掉运行封装后的段里 >= 40%
        if n_rev >= 5 and n_obj > n_proc and dens >= 0.40:
            return ("对象抄本",
                    f"§2.49 问1：{n_obj} 段含对象侧值本身（占扣封装后 {n_eff} 段的 {dens:.0%}），"
                    f"其中 {n_rev} 段「地址↔值」同段可回原址复核，地址命中 {stat['addrs']} 个；"
                    f"过程动作段仅 {n_proc} ⇒ 内容占主体", stat)
        if n_rev > 0:
            return ("过程输出",
                    f"§2.49 问1+问2：内容段 {n_obj}（{dens:.0%}）/ 可回原址 {n_rev} 段，"
                    f"不占主体（判据要求 rev>=5 且 obj>proc 且 dens>=40%）；"
                    f"过程动作段 {n_proc}（{pdens:.0%}）主导（哈希/差分/耗时/退出码/统计/断言之属）", stat)
        # 有内容但不可回原址复核 → 问1 末句「不能复核的降为过程」
        return ("过程输出",
                f"§2.49 问1 末句：{n_obj} 段有对象字样但无一「地址↔值」并存，"
                f"不可回原址复核 ⇒ 降为过程（动作段 {n_proc}）", stat)

    # ---- 问2：只有动作？----
    if n_proc > 0:
        return ("过程输出",
                f"§2.49 问2：{n_proc}/{n} 段（{pdens:.0%}）只记动作（读取/写入/比对/耗时/"
                f"退出码/哈希/断言），无任何对象侧值 ⇒ 过程", stat)

    # ---- 问3：原文件不含可判内容 ----
    return ("永久判不了",
            f"§2.49 问3：{total} B、{n} 段内既无对象侧值也无过程动作，"
            f"原文件已不含可判内容（非口径问题）", stat)


def main():
    rows = list(csv.DictReader(open(os.path.join(OUT, "base1242.tsv"), encoding="utf-8"), delimiter="\t"))
    out = []
    for r in rows:
        text, nread, total = read_text(r["rel"])
        v, why, stat = judge(text, total)
        out.append({
            "rel": r["rel"],
            "bytes": r["bytes"],
            "new_verdict": v,
            "basis": why,
            "old_verdict": r["old_verdict"],
            "changed": "Y" if v != r["old_verdict"] else "N",
            "old_basis": r["R44_basis"],
            "seg_n": stat.get("seg_n", 0),
            "obj_segs": stat.get("obj_segs", 0),
            "rev_segs": stat.get("rev_segs", 0),
            "frame_segs": stat.get("frame_segs", 0),
            "proc_segs": stat.get("proc_segs", 0),
            "obj_ratio": stat.get("obj_ratio", ""),
            "addr_hits": stat.get("addrs", 0),
            "truncated": "Y" if total > nread else "N",
        })
    with open(os.path.join(OUT, "rejudge1242.tsv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, delimiter="\t", fieldnames=list(out[0].keys()))
        w.writeheader()
        for x in out:
            w.writerow(x)
    from collections import Counter
    print("new_verdict:", dict(Counter(x["new_verdict"] for x in out)))
    print("rows:", len(out), "bytes:", sum(int(x["bytes"]) for x in out))


if __name__ == "__main__":
    main()
