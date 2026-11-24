# -*- coding: utf-8 -*-
"""_gv_probe.py — 复核员独立实现：三类误报实测复算 + 回件引用行抽查。
不复用作者代码，定义从回件文字独立抄录：
  BAD_BAN = 已生效/可应用母本/放行 N-5/已入账/已追加（五词）
  否定回看 = 命中点前 24 字符内 (不|无|未|非|禁|勿|否决|排除|不宣告|不得)
  bind_naive   = 被核对象 SHA256\\s*=\\s*[0-9a-fA-F]{64}
  bind_relaxed = 被核对象[^。\\n]{0,160}?SHA256\\s*=\\s*`?[0-9a-fA-F]{64}
  bind_any     = SHA256\\s*=\\s*`?[0-9a-fA-F]{64}
"""
import json, pathlib, re

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
FILES = [
    "lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md",
    "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
    "lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md",
    "lead/c97_scope_recheck_20261108/C97_SCOPE_RECHECK.md",
]
BAD_BAN = ["已生效", "可应用母本", "放行 N-5", "已入账", "已追加"]
NEG = re.compile(r"(不|无|未|非|禁|勿|否决|排除|不宣告|不得)")
BN = re.compile(r"被核对象 SHA256\s*=\s*[0-9a-fA-F]{64}")
BR = re.compile(r"被核对象[^。\n]{0,160}?SHA256\s*=\s*`?[0-9a-fA-F]{64}")
BA = re.compile(r"SHA256\s*=\s*`?[0-9a-fA-F]{64}")

out = {}
for rel in FILES:
    t = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
    naive, neg = {}, {}
    for b in BAD_BAN:
        naive[b] = t.count(b)
        neg[b] = sum(1 for m in re.finditer(re.escape(b), t) if NEG.search(t[max(0, m.start()-24):m.start()]))
    out[rel.split("/")[-1]] = {
        "naive": naive,
        "negated": neg,
        "bind": [len(BN.findall(t)), len(BR.findall(t)), len(BA.findall(t))],
        "approve": {
            "backtick": len(re.findall(r"`APPROVE_SCOPE`", t)),
            "corner": len(re.findall(r"「APPROVE_SCOPE[」/、 ]", t)),
            "bare": len(re.findall(r"(?<![`「])APPROVE_SCOPE(?![`」/、 ])", t)),
            "split": len(re.findall(r"APPROVE[_\s]*\n\s*SCOPE", t)),
        },
    }
print(json.dumps(out, ensure_ascii=False, indent=1))

print("\n== 回件引用行抽查（行号取 splitlines 1-based）==")
c = (ROOT / FILES[0]).read_text(encoding="utf-8", errors="replace").splitlines()
l = (ROOT / FILES[1]).read_text(encoding="utf-8", errors="replace").splitlines()
o = (ROOT / FILES[2]).read_text(encoding="utf-8", errors="replace").splitlines()
c97 = (ROOT / FILES[3]).read_text(encoding="utf-8", errors="replace").splitlines()
for tag, lines, no in [("CANDIDATE:17", c, 17), ("CANDIDATE:122", c, 122), ("CANDIDATE:130", c, 130),
                       ("CANDIDATE:150", c, 150), ("CANDIDATE:155", c, 155),
                       ("LEDGER:146", l, 146), ("LEDGER:177", l, 177), ("LEDGER:186", l, 186),
                       ("LEDGER:194", l, 194), ("C97:68", c97, 68), ("C97:69", c97, 69), ("OBS:366", o, 366)]:
    print("%s | %s" % (tag, lines[no-1].strip()[:160]))
