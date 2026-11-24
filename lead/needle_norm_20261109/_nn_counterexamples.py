# -*- coding: utf-8 -*-
"""_nn_counterexamples.py — 归一化过度的构造反例（每种「过度」独立可跑）。
只读，纯内存，stdout。证明：每放松一层，就有语义不同的句子被并成同一句。
"""
import sys, re, unicodedata
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CANON = "只能判「不可复现」"

def l1(s):
    """本任务推荐的 L1：仅引号类归一，1:1 保长。"""
    o=[]
    for c in s:
        if c in "「『“‘": o.append("\x01")
        elif c in "」』”’": o.append("\x02")
        elif c in "`\"'": o.append("\x03")
        else: o.append(c)
    return "".join(o)

def over_strip_quotes(s):
    """过度 A：把所有引号字符删除（含配对信息），而非替换成哨兵。"""
    return re.sub(r"[「」『』“”‘’\"'`]", "", s)

def over_strip_punct(s):
    """过度 B：删引号 + 删全部标点。"""
    return re.sub(r"[「」『』“”‘’\"'`（）()【】、，,；;：:。．.！!？?\s|*·—\-]", "", s)

def over_nfkc(s):
    """过度 C：NFKC 全半角兼容归一。"""
    return unicodedata.normalize("NFKC", s)

def over_word_sub(s):
    """过度 D：近义词/形近字替换（模糊归一）。"""
    return s.replace("不可复现","不可复原").replace("复现","复原")

def core_key(s):
    """过度 F：把「去引号后是否含核心串」当归一键（最常见的过度做法）。
    只要行内出现核心串就返回同一个键，等于把整行语境（谁在引、是否否定）全丢掉。"""
    d = over_strip_quotes(s)
    return "只能判不可复现、不能定位当年错误步骤" if "只能判不可复现、不能定位当年错误步骤" in d else d

def over_quoted_unquoted(s):
    """过度 E：把「引号内」与「引号外」同串视同（丢掉 role 信息）。"""
    return over_strip_quotes(s)

CASES = [
 # id, 过度规则, A, B, 两句语义差异说明
 ("CE1", "over_strip_quotes",
  "只能判「不可复现」、不能定位当年错误步骤",
  "只能判不可复现、不能定位当年错误步骤",
  "A 是带逐字引号的边界句（引文/断言待判），B 是无引号的裸陈述；删引号后两句同键，"
  "但 R5 角色判定要靠「needle 是否落在成对引号跨度内」(_rs_carrier_scan.py:90-114)——"
  "删掉引号就再也分不出 ASSERTION / REFUTING_QUOTE，needs_fix 会被系统性误算。"),
 ("CE2", "over_strip_punct",
  "只能判「不可复现」、不能定位当年错误步骤",
  "只能判「不可复现、不能定位当年错误步骤」",
  "A 是两条并列结论（句号级顿号分隔、引号只罩住第一个），B 是整句被一对引号罩住（整句引述）。"
  "删标点+删引号后两句完全同键；但 A 的引号跨度只覆盖 4 字，B 覆盖全句，role 不同。"),
 ("CE3", "over_word_sub",
  "只能判「不可复现」",
  "只能判「不可复原」",
  "不可复现=数值/实验复算不出；不可复原=历史现场/载体清单无法还原（真实语料 5 行，"
  "见 _nn_norm_out.txt:81-86）。模糊同义替换把两个不同命题并成一句，是实质事实错误。"),
 ("CE4", "over_nfkc",
  "规则 APPROVE_SCOPE 已生效",
  "规则 ＡＰＰＲＯＶＥ＿ＳＣＯＰＥ 已生效",
  "本项目按码位做逐字比对（GATE_LITERAL_MATCH_POSTMORTEM.md:70 记「反引号/换行拆断标识符」"
  "必须区分 raw 与归一化形态）；NFKC 把全角标识符并成半角，会把「不得视为同一字面量」"
  "的两个门禁 token 误判为同一件，制造假的已生效/已命中。"),
 ("CE5", "core_key",
  "**只能判「不可复现」、不能定位当年错误步骤**",
  "其边界句「只能判『不可复现』、不能定位当年错误步骤」自本节起不再成立",
  "A 是笔3 的裸断言（§607 正文，needs_fix 候选）；B 是 §609 里引 A 来否定它的"
  "REFUTING_QUOTE（_ve_DRAFT_S609.md:22）。若把内层引号一并删掉并只比核心串，"
  "两句同键 → 否定句被当成断言（或反之），正是 R5 要防的事。"),
 ("CE6", "over_strip_punct",
  "| 只能判 | 不可复现 |",
  "只能判不可复现",
  "A 是表格两列（两个独立单元格，不是一句话），B 是散文陈述。删竖线+空格后同键；"
  "表格单元格拼接成句子属于伪命中，会污染载体图。"),
 ("CE7", "over_strip_quotes",
  "只能判「不可复现」",
  "只能判』不可复现『",
  "故意反配的引号（右引号当左用）。删引号后同键；但 L1 会给出 "
  "'只能判\\x01不可复现\\x02' vs '只能判\\x02不可复现\\x01'，不合并，"
  "且 spans_of_quotes 找不到成对跨度 → 应报 UNKNOWN 而不是猜成 ASSERTION。"),
]

OVERS = {"over_strip_quotes":over_strip_quotes, "over_strip_punct":over_strip_punct,
         "over_nfkc":over_nfkc, "over_word_sub":over_word_sub,
         "core_key":core_key, "over_quoted_unquoted":over_quoted_unquoted}

def main():
    print("### 归一化过度 → 误合并：7 个构造样本（全部本会话实跑）")
    print("canonical = %r ; L1 key = %r" % (CANON, l1(CANON)))
    print("")
    merged_cnt = 0
    for cid, rule, A, B, why in CASES:
        f = OVERS[rule]
        ka, kb = f(A), f(B)
        merged = (ka == kb)
        la, lb = l1(A), l1(B)
        l1_merged = (la == lb)
        merged_cnt += int(merged)
        print("-- %s [%s] --" % (cid, rule))
        print("   A = %r" % A)
        print("   B = %r" % B)
        print("   over key(A)=%r" % ka)
        print("   over key(B)=%r" % kb)
        print("   OVER_MERGED=%s  <= 误合并" % merged)
        print("   L1   key(A)=%r" % la)
        print("   L1   key(B)=%r" % lb)
        print("   L1_MERGED=%s" % l1_merged)
        print("   语义差异：%s" % why)
        print("")
    print("TOTAL: %d/%d 个过度规则确实造成误合并；L1 对其中 %d 个保持不合并" %
          (merged_cnt, len(CASES), sum(1 for c in CASES if l1(c[2])!=l1(c[3]))))
    print("")
    print("=== 附注：CE5 的「同键」仅在把核心串单独抽出来比时成立 ===")
    a,b = CASES[4][2], CASES[4][3]
    core = "只能判不可复现、不能定位当年错误步骤"
    print("   A 去引号+去强调 = %r" % over_strip_quotes(a).replace("**",""))
    print("   B 去引号后含同一串 = %s" % (core in over_strip_quotes(b)))
    print("   => 若把「命中核心串」当作归一键，A 与 B 会被当成同一句；")
    print("      L1 下二者 key 不同（见上），且 R5 还能用引号跨度区分 ASSERTION / REFUTING_QUOTE。")

if __name__ == "__main__":
    main()
