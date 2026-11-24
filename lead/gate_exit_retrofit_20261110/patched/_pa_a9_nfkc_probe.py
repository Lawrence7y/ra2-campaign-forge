# -*- coding: utf-8 -*-
# _pa_a9_nfkc_probe.py — 攻样本【A9 归一化绕过探针】：西里尔同形异码字 vs NFKC/SESSION_RE/normalize_id。
# 只读探针：不触碰任何登记件。
import re
import sys
import unicodedata

SESSION_RE = re.compile(
    r"sess_dwf-dwfrun-[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}-actor_\d+_\d+")


def normalize_id(s):
    t = unicodedata.normalize("NFKC", s)
    return "".join(ch for ch in t if not ch.isspace() and unicodedata.category(ch) != "Cf").casefold()


BASE = "sess_dwf-dwfrun-0123abcd-1234-4abc-8abc-0123456789ab-actor_1_1"
# 同形异码：a(U+0061)→а(U+0430)、c(U+0063)→с(U+0431? no U+0441)、e(U+0065)→е(U+0435)
CYR = {"a": "\u0430", "c": "\u0441", "e": "\u0435", "o": "\u043e", "p": "\u0440", "x": "\u0445", "y": "\u0443"}
HOMO = BASE.translate(str.maketrans(CYR))
FULLWIDTH = "ｓｅｓｓ＿ｄｗｆ－ｄｗｆｒｕｎ－０１２３ａｂｃｄ－１２３４－４ａｂｃ－８ａｂｃ－０１２３４５６７８９ａｂ－ａｃｔｏｒ＿１＿１"
ZWSP = BASE[:10] + "\u200b" + BASE[10:]

for name, s in [("BASE", BASE), ("HOMOGLYPH-Cyrillic", HOMO), ("FULLWIDTH", FULLWIDTH), ("ZWSP", ZWSP)]:
    print("%-20s N07形制=%-5s NFKC后==BASE的归一化=%-5s codepoints=%s" % (
        name,
        "PASS" if SESSION_RE.fullmatch(s) else "FAIL",
        normalize_id(s) == normalize_id(BASE),
        " ".join("U+%04X" % ord(ch) for ch in s[:16]) + " …"))

print()
print("normalize_id(BASE)    =", normalize_id(BASE))
print("normalize_id(HOMO)    =", normalize_id(HOMO))
print("归一化相等? ", normalize_id(BASE) == normalize_id(HOMO))
# ---------- 出口改造（纯追加：以上原件 1-34 行一字未改） ----------
# 原型：lead/dtrigger_compare_20261107/_check_dtrigger.py:31-35 + :226-228
# A. 原件对自身的检查 / 输出通道（本会话实读原件全文 34 行）：
#    :24-29 循环内 print 里，:27 `"PASS" if SESSION_RE.fullmatch(s) else "FAIL"`
#      —— EXIT_CRITERION.md:492 登记的互斥 PASS/FAIL 裁决对；
#      :28 `normalize_id(s) == normalize_id(BASE)` —— 同一 print 内第二个布尔判定；
#    :32/:33 两行 normalize_id 字符串观测；:34 "归一化相等? " 后接第三个布尔判定。
#    9 个布尔结果全部只走 stdout print（:25-29 / :34）：无 assert、无写盘、
#    无 sys.exit/SystemExit；原件基线实跑 EXIT=0。
#    全库 grep 无 `import _pa_a9_nfkc_probe`；复核员 _pav_recon.py:3 明写「不 import 攻样本脚本」；
#    原件无 if __name__ == "__main__" 块、无库本体、无 import 调用方（约束 C2/C3 不适用/已满足）。
#
# 聚合口径（不改语义的关键）：上列 9 个布尔是对【4 个攻样本】的观测，不是「脚本失败」；
# 3 个 FAIL 与 2 个 False 正是原件自己的结论（_pa_ATTACK_REPORT.md:95：A9 死于 N07）。
# 故绝不直接 all()/and 这些原值（那会让基线恒 FAIL，把判定倒过来），也不取反、不改写
# 任何原有判定式、不替换任何原有 print。做法同在库样板 patched/_sc_scan.py:564-594：
# 在追加段里逐字重算同一批比较式，逐项与原件基线输出对账后喂 check()。
# 「本脚本判定」= 本探针复现了自己文档化的 9 个观测；任一项漂移 ⇒ 该检查失败 ⇒ EXIT=1。
# 新增名字 ok/check/_name/_s/_n07/_nfkc 均以 _ 前缀或模板名出现，不覆盖原件
# name/s/BASE 等全局量；无调用方，故不污染任何命名空间。
ok = True
def check(name, cond, detail=""):
    global ok
    ok = ok and bool(cond)          # 合取聚合：全部检查通过才真；唯一置假点
    print(("  [PASS] " if cond else "  [FAIL] ") + name + ((" | " + detail) if detail else ""))

# (样本名, 字符串, :27 基线打印值, :28 基线打印值)：
# 只有 BASE 过 N07；NFKC 映射全角/零宽但不映射西里尔。
for _name, _s, _n07, _nfkc in (
        ("BASE", BASE, True, True),
        ("HOMOGLYPH-Cyrillic", HOMO, False, False),
        ("FULLWIDTH", FULLWIDTH, False, True),
        ("ZWSP", ZWSP, False, True)):
    check(":27 " + _name + " N07形制==基线", bool(SESSION_RE.fullmatch(_s)) == _n07)
    check(":28 " + _name + " NFKC归一化相等==基线",
          (normalize_id(_s) == normalize_id(BASE)) == _nfkc)
# :34 原件打印 False；此处比较「重算值 == 基线值」，不是把原判定取反塞进合取。
check(":34 归一化相等? ==基线", (normalize_id(BASE) == normalize_id(HOMO)) == False)

print("核验结论: " + ("ALL PASS" if ok else "FAIL"))
raise SystemExit(0 if ok else 1)
