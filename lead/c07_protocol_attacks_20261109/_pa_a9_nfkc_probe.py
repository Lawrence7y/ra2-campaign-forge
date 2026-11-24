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
