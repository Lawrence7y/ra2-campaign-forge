# -*- coding: utf-8 -*-
"""_x.py — 独立核验方 X1-X6 机械复算（2026-11-12）。
铁律：只读 D:\\Project\\ra2-campaign-forge 下除本写域外的所有文件；
      仅在本脚本所在目录 lead\\re_chain_v2_xverify_20261112\\ 写输出。
      零真机：不启动任何 exe、不 attach、不读活进程内存、不写 hook/采样/MiniDump。
用法：python -I -X utf8 <绝对路径>/_x.py
输出：stdout 全部内容同时由本脚本写入本目录 _x_stdout.txt（UTF-8）。
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEAD = os.path.dirname(HERE)
REPO = os.path.dirname(LEAD)

BUF = []


def emit(s=""):
    BUF.append(s)
    try:
        print(s)
    except UnicodeEncodeError:
        print(s.encode("utf-8", "replace").decode("ascii", "replace"))


def fp(path):
    """hashlib 实算 sha256 + 字节数（不手写估计）。"""
    h = hashlib.sha256()
    n = 0
    with open(path, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
            n += len(b)
    return h.hexdigest(), n


def rdlines(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.readlines()


def L(rel):
    return os.path.join(LEAD, rel.replace("/", os.sep).replace("\\", os.sep))


def R(rel):
    return os.path.join(REPO, rel.replace("/", os.sep).replace("\\", os.sep))


def resolve(fname):
    p = L(fname)
    if os.path.isfile(p):
        return p
    p2 = R(fname)
    if os.path.isfile(p2):
        return p2
    return p


def show_range(path, a, b, cap=200):
    """打印 [a,b] 区间的带行号实文。"""
    ls = rdlines(path)
    out = []
    for i in range(a, min(b, len(ls)) + 1):
        out.append("      %4d | %s" % (i, ls[i - 1].rstrip("\r\n")[:cap]))
    return "\n".join(out)


emit("=" * 100)
emit("XVERIFY 机械复算输出  (repo=%s)" % REPO)
emit("写域(唯一): %s" % HERE)
emit("python: %s" % sys.version.replace("\n", " "))
emit("=" * 100)

TARGET = L("re_chain_synthesis_20261111/CHAIN_SYNTHESIS.md")
V2 = L("re_chain_synth_v2_20261111")

# ---------------------------------------------------------------- SEC 0
emit("\n########## SEC 0 · 靶件与两份交付件的 size/sha ##########")
for tag, p in (
    ("CHAIN_SYNTHESIS.md", TARGET),
    ("RE_GRADING.md", os.path.join(V2, "RE_GRADING.md")),
    ("LEDGER_SECTION_DRAFT_v2.md", os.path.join(V2, "LEDGER_SECTION_DRAFT_v2.md")),
    ("ra2bench/gamemd.exe", R("ra2bench/gamemd.exe")),
):
    if os.path.isfile(p):
        s, n = fp(p)
        emit("  %-32s %s  %d B" % (tag, s, n))
    else:
        emit("  %-32s 不存在!" % tag)

# ---------------------------------------------------------------- SEC X1
emit("\n########## SEC X1 · 【已证】计数（两种数法各跑一次） ##########")
raw = open(TARGET, "r", encoding="utf-8").read()
lines = rdlines(TARGET)                      # 154 行（与 read 工具一致）
a = sum(ln.count("【已证】") for ln in lines)   # 数法 (a) 逐行 count 求和
b = len(re.findall(r"【已证】", raw))           # 数法 (b) 正则全文 findall
emit("  文件总行数 = %d" % len(lines))
emit("  (a) sum( line.count('【已证】') ) = %d" % a)
emit("  (b) len(re.findall('【已证】', full_text)) = %d" % b)
hits = [i + 1 for i, ln in enumerate(lines) if "【已证】" in ln]
emit("  命中行 = %s" % ",".join("L%d" % x for x in hits))
emit("  声称命中行 = L66,L67,L68,L69,L70,L71,L72,L73,L75,L77,L78,L79,L80,L81,L82,L83")
claimed = [66, 67, 68, 69, 70, 71, 72, 73, 75, 77, 78, 79, 80, 81, 82, 83]
emit("  与声称一致 = %s ; 差集(实算-声称)=%s ; 差集(声称-实算)=%s" % (
    hits == claimed, sorted(set(hits) - set(claimed)), sorted(set(claimed) - set(hits))))
emit("  每行精确 count：%s" % ", ".join("L%d=%d" % (i + 1, ln.count("【已证】"))
                                        for i, ln in enumerate(lines) if ln.count("【已证】")))
# --- CFG 陷阱：两种口径 ---
exact_cnt = a
cfg_cnt = sum(ln.count("【已证（CFG）】") for ln in lines)
prefix_cnt = sum(ln.count("【已证") for ln in lines)
both_cnt = len(re.findall(r"【已证(?:（CFG）)?】", raw))
emit("  --- CFG 前缀陷阱 ---")
emit("  说明：'【已证】' 要求 '证' 后紧接 '】'；'【已证（CFG）】' 在 '证' 后是 '（'，故精确计数天然【不含】它。")
emit("        若误用裸前缀 '【已证' 计数，则 '【已证（CFG）】' 会被算进来（含口径）。")
emit("  口径「不含 CFG 前缀」= 精确 '【已证】'            = %d" % exact_cnt)
emit("  口径「含 CFG 前缀」  = 正则 '【已证(?:（CFG）)?】' = %d" % both_cnt)
emit("  裸前缀 '【已证' 全文字串计数                     = %d" % prefix_cnt)
emit("  '【已证（CFG）】' 在 CHAIN_SYNTHESIS.md 中出现     = %d" % cfg_cnt)
for tag, p in (("RE_GRADING.md", os.path.join(V2, "RE_GRADING.md")),
               ("LEDGER_SECTION_DRAFT_v2.md", os.path.join(V2, "LEDGER_SECTION_DRAFT_v2.md"))):
    t = open(p, "r", encoding="utf-8").read()
    emit("  %s: 精确'【已证】'=%d  '【已证（CFG）】'=%d  裸前缀'【已证'=%d  含口径=%d" % (
        tag, t.count("【已证】"), t.count("【已证（CFG）】"), t.count("【已证"),
        len(re.findall(r"【已证(?:（CFG）)?】", t))))
emit("  其他标记精确计数：" + "  ".join("%s=%d" % (m, raw.count(m))
      for m in ["【未证】", "【未验】", "【未决】", "【未定谳】"]))

# ---------------------------------------------------------------- SEC X2
emit("\n########## SEC X2 · 16 条【已证】的 24 个证据引用独立核验 ##########")
REF_RE = re.compile(r"`([A-Za-z0-9_\-./\\]+?\.(?:txt|json|py|md)):([^`]+)`")
refs_all = []
for n in hits:
    ln = lines[n - 1]
    cells = [c.strip() for c in ln.split("|")]
    topic = cells[1].replace("**", "") if len(cells) > 1 else "?"
    reading = cells[4] if len(cells) > 4 else "?"
    for fname, rng in REF_RE.findall(ln):
        for tok in rng.split(","):
            tok = tok.strip()
            if tok:
                refs_all.append((n, topic, reading, fname, tok))
emit("  自动解析出的引用总数 = %d （执行方声称 24）" % len(refs_all))

ok = bad = 0
bad_rows = []
cache = {}
for idx, (n, topic, reading, fname, rng) in enumerate(refs_all, 1):
    p = resolve(fname)
    exists = os.path.isfile(p)
    key = "REF%02d L%-3d %s:%s" % (idx, n, fname, rng)
    if not exists:
        emit("  %s -> 文件不存在 [BAD]" % key)
        bad += 1
        bad_rows.append((key, "文件不存在", ""))
        continue
    if p not in cache:
        cache[p] = len(rdlines(p))
    total = cache[p]
    m = re.match(r"^L(\d+)(?:-L(\d+))?$", rng)
    if m:
        aa = int(m.group(1)); bb = int(m.group(2) or m.group(1))
        valid = (1 <= aa <= bb <= total)
        first = rdlines(p)[aa - 1].rstrip("\r\n") if valid else "<越界>"
        status = "OK" if valid else "BAD"
        emit("  %s -> 存在(%d 行) 范围%s [%s]" % (key, total, "有效" if valid else "越界", status))
        emit("      首行实文: %s" % first[:200])
        emit("      条目读数: %s" % reading.replace("<br>", " ")[:200])
        if valid:
            ok += 1
        else:
            bad += 1
            bad_rows.append((key, "行号越界", first))
    else:
        # 非 文件:行 引用（json 键引用）：独立解析 JSON 核键与值
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                j = json.load(f)
            has = rng in j
            val = json.dumps(j.get(rng, None), ensure_ascii=False)[:250]
            emit("  %s -> 非'文件:行'引用；文件存在(%d 行)；JSON 顶层键 '%s' 存在=%s" % (key, total, rng, has))
            emit("      键值实文: %s" % val)
            emit("      条目读数: %s" % reading.replace("<br>", " ")[:200])
            emit("      [注意] 此类引用无'首行'可打印；执行方 _regrade_scan_out.txt 对这两条标 [OK*] 仅核文件存在")
            if has:
                ok += 1
            else:
                bad += 1
                bad_rows.append((key, "JSON 键不存在", val))
        except Exception as e:
            emit("  %s -> JSON 解析失败 %s [BAD]" % (key, e))
            bad += 1
            bad_rows.append((key, "JSON 解析失败", str(e)))
emit("  ==> X2 汇总: OK=%d BAD=%d （执行方声称 OK=24 BAD=0）" % (ok, bad))
for k, why, first in bad_rows:
    emit("      BAD: %s | %s | 实际首行: %s" % (k, why, first))

# ---------------------------------------------------------------- SEC X2b/X3 证据区间全文
emit("\n########## SEC E · 关键证据区间带行号全文（供 X2 内容核对 / X3 定级判断） ##########")
EVID = [
    ("sf  L7-L11   (R3 覆盖计数)", "slot2_fullscan_20261111/_sf_scan_out.txt", 7, 11),
    ("sf  L13-L15  (R1 直接调用普查)", "slot2_fullscan_20261111/_sf_scan_out.txt", 13, 15),
    ("sf  L18-L20  (R2 函数指针值)", "slot2_fullscan_20261111/_sf_scan_out.txt", 18, 20),
    ("sf  L21-L24  (R5 初始化/atexit)", "slot2_fullscan_20261111/_sf_scan_out.txt", 21, 24),
    ("sf  L26-L29  (R4 G4/G5 普查)", "slot2_fullscan_20261111/_sf_scan_out.txt", 26, 29),
    ("sf  L31-L35  (R4 计数)", "slot2_fullscan_20261111/_sf_scan_out.txt", 31, 35),
    ("sf  L39-L47  (R4 污点/唯一性)", "slot2_fullscan_20261111/_sf_scan_out.txt", 39, 47),
    ("sf  L66-L68  (R4 指令)", "slot2_fullscan_20261111/_sf_scan_out.txt", 66, 68),
    ("cw  L20-L24  (R5 初始化/atexit)", "re_crashwriter_static_20261110/_cw_disasm_out.txt", 20, 24),
    ("cw  L34-L42  (R7 edi==0 早退)", "re_crashwriter_static_20261110/_cw_disasm_out.txt", 34, 42),
    ("cw  L43-L68  (R7/R8 CFG 与覆盖)", "re_crashwriter_static_20261110/_cw_disasm_out.txt", 43, 68),
    ("cw  L126-L137 (可达性结论)", "re_crashwriter_static_20261110/_cw_disasm_out.txt", 126, 137),
    ("cw  L156-L177 (FACT 断言)", "re_crashwriter_static_20261110/_cw_disasm_out.txt", 156, 177),
    ("ps  L11-L12  (字符串)", "playerctrl_semantics_20261111/_ps_disasm_out.txt", 11, 12),
    ("ps  L32-L39  (0x5012ED / PercentBuilt)", "playerctrl_semantics_20261111/_ps_disasm_out.txt", 32, 39),
    ("ps  L113-L121 (R14 写入点)", "playerctrl_semantics_20261111/_ps_disasm_out.txt", 113, 121),
    ("ps  L116-L147 (R15 控制流)", "playerctrl_semantics_20261111/_ps_disasm_out.txt", 116, 147),
    ("ps  L589     (R15 8处创建点)", "playerctrl_semantics_20261111/_ps_disasm_out.txt", 585, 592),
    ("ps  L894-L905 (R16)", "playerctrl_semantics_20261111/_ps_disasm_out.txt", 894, 905),
    ("ps  L1183-L1214 (R15 创建窗口)", "playerctrl_semantics_20261111/_ps_disasm_out.txt", 1183, 1214),
    ("oo  L28-L46  (R9)", "re_orphan_owners_20261110/_oo_map_out.txt", 28, 46),
    ("md  L17-L22  (R10)", "re_map_preset_decode_20261110/_md_parse_out.txt", 17, 22),
    ("ld  L25-L31  (R11/R12)", "re_loadbench_diff_20261110/_ld_diff_out.txt", 25, 31),
    ("ld  L88-L103 (R13)", "re_loadbench_diff_20261110/_ld_diff_out.txt", 88, 103),
    ("sp  L37      (L74 历史崩溃)", "stale_pass_20261109/_sp_report.txt", 35, 39),
]
for tag, rel, aa, bb in EVID:
    p = L(rel)
    emit("\n  --- %s  [%s]" % (tag, rel))
    if not os.path.isfile(p):
        emit("      文件不存在!")
        continue
    emit(show_range(p, aa, bb))

# ---------------------------------------------------------------- SEC X4
emit("\n########## SEC X4 · _ps_disasm stdout 复现门 ##########")
PS = L("playerctrl_semantics_20261111/_ps_disasm.py")
emit("  --- X4(a) 源码行号逐个核对 ---")
ps_lines = rdlines(PS)
for k in [19, 20, 22, 23, 34, 37, 38, 113, 456, 457, 459, 471, 472, 474]:
    emit("      :%-4d %s" % (k, ps_lines[k - 1].rstrip("\r\n") if k <= len(ps_lines) else "<越界>"))
emit("  --- 全文件 stdout 写入检索 ---")
for i, ln in enumerate(ps_lines, 1):
    if re.search(r"sys\.stdout|os\.write\(\s*1|print\s*=\s*P|print\(", ln):
        if ("sys.stdout" in ln) or ("os.write" in ln) or ("print = P" in ln):
            emit("      L%-4d %s" % (i, ln.rstrip("\r\n")))
emit("  stdout 写入语句数 = %d" % sum(1 for ln in ps_lines if "sys.stdout" in ln or re.search(r"os\.write\(\s*1", ln)))
emit("  '(done)' 出现行 = %s" % [i for i, ln in enumerate(ps_lines, 1) if "(done)" in ln])
emit("  --- X4(c) 指纹实算 ---")
X4_ITEMS = [
    ("原件 _ps_disasm.py", PS),
    ("写域副本 _ps_disasm_rerun_copy.py", os.path.join(V2, "_ps_disasm_rerun_copy.py")),
    ("既有 _ps_disasm_out.txt", L("playerctrl_semantics_20261111/_ps_disasm_out.txt")),
    ("既有 _ps_disasm_out.json", L("playerctrl_semantics_20261111/_ps_disasm_out.json")),
    ("写域重跑 _ps_disasm_out.txt", os.path.join(V2, "_ps_disasm_out.txt")),
    ("写域重跑 _ps_disasm_out.json", os.path.join(V2, "_ps_disasm_out.json")),
    ("_repro_ps_disasm.txt", L("re_chain_synthesis_20261111/_repro_ps_disasm.txt")),
    ("_pssim_rerun_stdout.txt", os.path.join(V2, "_pssim_rerun_stdout.txt")),
    ("_pssim_rerun_stderr.txt", os.path.join(V2, "_pssim_rerun_stderr.txt")),
    ("_pssim_rerun_out.txt (执行方 L73/L91 引用)", os.path.join(V2, "_pssim_rerun_out.txt")),
    ("_regrade_scan_out.txt", os.path.join(V2, "_regrade_scan_out.txt")),
]
hashmap = {}
for tag, p in X4_ITEMS:
    if os.path.isfile(p):
        s, n = fp(p)
        hashmap[tag] = (s, n)
        emit("  %-46s %s  %d B" % (tag, s, n))
    else:
        emit("  %-46s 不存在 [MISSING]" % tag)
emit("  empty string sha256 = %s" % hashlib.sha256(b"").hexdigest())
emit("  副本==原件 sha: %s" % (hashmap.get("原件 _ps_disasm.py", ("?",))[0] ==
                             hashmap.get("写域副本 _ps_disasm_rerun_copy.py", ("?",))[0]))
emit("  重跑txt == 既有txt sha: %s" % (hashmap.get("写域重跑 _ps_disasm_out.txt", ("?",))[0] ==
                                    hashmap.get("既有 _ps_disasm_out.txt", ("?",))[0]))
emit("  重跑json == 既有json sha: %s" % (hashmap.get("写域重跑 _ps_disasm_out.json", ("?",))[0] ==
                                      hashmap.get("既有 _ps_disasm_out.json", ("?",))[0]))

# ---------------------------------------------------------------- SEC X5
emit("\n########## SEC X5 · 零改动实证（关键件 + 全 100 件基线独立复核） ##########")
KEY_CLAIM = {
    "ra2bench\\gamemd.exe": ("73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476", 4825360),
    "lead\\re_chain_synthesis_20261111\\CHAIN_SYNTHESIS.md": ("c88717d71c4b59d88ecd04f234843f561a829e63f5b967659e10acfdcf8254b3", 20971),
    "lead\\re_chain_synthesis_20261111\\LEDGER_SECTION_DRAFT.md": ("b40ac2a7b6fade6854fc0960aa9b01252ccff3dc292c780b979a8e56b664a800", 3415),
    "lead\\re_chain_synthesis_20261111\\_repro_ps_disasm.txt": ("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", 0),
    "lead\\playerctrl_semantics_20261111\\_ps_disasm.py": ("9a16086763924c269c2166fbcfd22c636ffb1800d6f78d54c72437c0c2d6c37e", 20572),
}
for rel, (cs, cn) in KEY_CLAIM.items():
    p = R(rel)
    if not os.path.isfile(p):
        emit("  %s -> 不存在 [BAD]" % rel); continue
    s, n = fp(p)
    emit("  %-58s %s %d B  与声称一致=%s" % (rel, s, n, (s == cs and n == cn)))

SNAP = os.path.join(V2, "_baseline_snapshot.json")
with open(SNAP, "r", encoding="utf-8") as f:
    base = json.load(f)
emit("  _baseline_snapshot.json 条目数 = %d （执行方声称 watched=100）" % len(base))
WATCHED = ["re_chain_synthesis_20261111", "playerctrl_semantics_20261111", "slot2_fullscan_20261111",
           "re_crashwriter_static_20261110", "re_orphan_owners_20261110", "re_map_preset_decode_20261110",
           "re_loadbench_diff_20261110", "stale_pass_20261109", "re_dispatch_20261111"]
now = {}
for d in WATCHED:
    full = L(d)
    if os.path.isdir(full):
        for name in sorted(os.listdir(full)):
            p = os.path.join(full, name)
            if os.path.isfile(p):
                now["%s/%s" % (d, name)] = fp(p)
for rel in KEY_CLAIM:
    p = R(rel)
    if os.path.isfile(p):
        now["__KEY__" + rel] = fp(p)
drift, missing, new = [], [], []
for k, v in base.items():
    if k not in now:
        missing.append(k)
    elif now[k][0] != v.get("sha256") or now[k][1] != v.get("size"):
        drift.append((k, v.get("sha256"), v.get("size"), now[k][0], now[k][1]))
for k in now:
    if k not in base:
        new.append(k)
emit("  独立复算 verify: watched=%d drift=%d missing=%d new=%d" % (len(base), len(drift), len(missing), len(new)))
for d in drift:
    emit("      DRIFT %s" % (d,))
for m in missing:
    emit("      MISSING %s" % m)
for n in new:
    emit("      NEW %s" % n)
emit("  执行方声称: watched=100 drift=0 missing=0 new=0  ->  一致=%s" %
     (len(base) == 100 and not drift and not missing and not new))

# 写域副本 vs baseline_backup（上轮越界覆盖事故）对拍
emit("  --- 现有证据件 vs baseline_backup 对拍（核 §0.3 / §4.9 的 7 处既有件） ---")
BK = L("re_chain_synthesis_20261111/baseline_backup")
PAIRS = [
    ("playerctrl_semantics_20261111/_ps_disasm_out.txt", "playerctrl_semantics_20261111/_ps_disasm_out.txt"),
    ("playerctrl_semantics_20261111/_ps_disasm_out.json", "playerctrl_semantics_20261111/_ps_disasm_out.json"),
    ("re_crashwriter_static_20261110/_cw_disasm_out.txt", "re_crashwriter_static_20261110/_cw_disasm_out.txt"),
    ("re_crashwriter_static_20261110/_cw_disasm_out.json", "re_crashwriter_static_20261110/_cw_disasm_out.json"),
    ("re_orphan_owners_20261110/_oo_map_out.txt", "re_orphan_owners_20261110/_oo_map_out.txt"),
    ("re_orphan_owners_20261110/_oo_map_out.json", "re_orphan_owners_20261110/_oo_map_out.json"),
    ("re_map_preset_decode_20261110/_md_parse_out.txt", "re_map_preset_decode_20261110/_md_parse_out.txt"),
    ("re_map_preset_decode_20261110/_md_parse_out.json", "re_map_preset_decode_20261110/_md_parse_out.json"),
    ("re_loadbench_diff_20261110/_ld_diff_out.txt", "re_loadbench_diff_20261110/_ld_diff_out.txt"),
    ("re_loadbench_diff_20261110/_ld_diff_out.json", "re_loadbench_diff_20261110/_ld_diff_out.json"),
    ("slot2_fullscan_20261111/_sf_scan_out.txt", "slot2_fullscan_20261111/_sf_scan_out.txt"),
    ("slot2_fullscan_20261111/_sf_scan_out.json", "slot2_fullscan_20261111/_sf_scan_out.json"),
]
for rel, bkrel in PAIRS:
    p, q = L(rel), os.path.join(BK, bkrel.replace("/", os.sep))
    if os.path.isfile(p) and os.path.isfile(q):
        emit("      %-58s MATCH=%s" % (rel, fp(p)[0] == fp(q)[0]))
    else:
        emit("      %-58s 缺件(现=%s 备=%s)" % (rel, os.path.isfile(p), os.path.isfile(q)))

# ---------------------------------------------------------------- SEC X6 helpers
emit("\n########## SEC X6 · 反向找茬辅助检索 ##########")
emit("  --- 0x5012ED 在 ps 探针输出/json 中的实文 ---")
emit(show_range(L("playerctrl_semantics_20261111/_ps_disasm_out.txt"), 30, 36))
for i, ln in enumerate(rdlines(L("playerctrl_semantics_20261111/_ps_disasm_out.json")), 1):
    if "5012ed" in ln.lower() or "5012ED" in ln:
        emit("      json L%-4d %s" % (i, ln.rstrip("\r\n")[:200]))
emit("  --- 0x7C978A / atexit 在 cw 与 sf 中的实文 ---")
for rel in ("re_crashwriter_static_20261110/_cw_disasm_out.txt", "slot2_fullscan_20261111/_sf_scan_out.txt"):
    for i, ln in enumerate(rdlines(L(rel)), 1):
        if "7C978A" in ln.upper() or "atexit" in ln.lower():
            emit("      %s L%-4d %s" % (rel, i, ln.rstrip("\r\n")[:180]))
emit("  --- RE_GRADING.md §2 理由列 / §4 边界节 的关键词 ---")
rg = rdlines(os.path.join(V2, "RE_GRADING.md"))
for i, ln in enumerate(rg, 1):
    if re.search(r"未核实|未决|未验|未证|机制|推断|读数|运行期", ln) and 76 <= i <= 88:
        emit("      RE_GRADING L%-3d %s" % (i, ln.rstrip("\r\n")[:220]))

# ---------------------------------------------------------------- 落盘
outpath = os.path.join(HERE, "_x_stdout.txt")
with open(outpath, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(BUF) + "\n")
emit("\n[EOF] stdout 已落盘: %s  (%d 行)" % (outpath, len(BUF)))
