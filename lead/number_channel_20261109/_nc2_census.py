# -*- coding: utf-8 -*-
"""_nc2_census.py —— 213/216 份草稿的散文裸数字普查（本轮实跑，留盘输出）。

零真机、零采样代码；只读 .zcode/workflow-drafts/ 与 .zcode/workflow-runs/。
口径：抽每个 .dwf.ts 里所有 `const ASK_ANALYST = [ ... ].join` 数组，
      取数组内的纯字符串字面量行作为「散文行」，统计阿拉伯数字 token。
用法： python -I -X utf8 <绝对路径>/_nc2_census.py > <绝对路径>/_nc2_census_out.json
"""
from __future__ import annotations

import io
import json
import os
import re
import statistics

ROOT = r"D:\Project\ra2-campaign-forge"
DRAFTS = os.path.join(ROOT, ".zcode", "workflow-drafts")
RUNS = os.path.join(ROOT, ".zcode", "workflow-runs")

# 与 _nc2_lint.py 的 EXEMPT_PATTERNS 保持同一套（避免两套口径）
EXEMPT = tuple(re.compile(r) for r in (
    r"[\w./\\-]+:\d+(?:-\d+)?",
    r"\b[0-9a-f]{12,64}\b",
    r"tail:\s*\d+",
    r"§\s*\d+(?:[.\-]\d+)*",
    r"\b\d{4}-\d{2}-\d{2}\b",
    r"\b(?:R|V|C|D|A|B|E|F|H|N)-?\d+\b",
    r"\bdwfrun-[0-9a-f\-]{20,}",
    r"\b\d+\s*B\b",
    r"python\s+-I\s+-X\s+utf8",
    r"被核对象 SHA256\s*=\s*[0-9a-f]{64}",
    r"字节数\s*=\s*\d+",
    r"(?<![A-Za-z0-9])20\d{2}(?![A-Za-z0-9])",
    r"\b[A-Za-z_][A-Za-z0-9_]*=\d+(?:\.\d+)?\b",
    r"(?<![A-Za-z0-9])0(?![A-Za-z0-9.])",
))
CJK_GRAMMATICAL = re.compile(
    r"(?:一个|一类|一样|一下|一点|一并|一度|一概|一旦|一两|"
    r"一件|两件|这件事|两件事|这两|那一|第一|第二|第三|"
    r"一回事|两回事|一者|二者|三者|两者|一方面|另一方面|"
    r"一来|二来|一时|一问|一答|一体)")
ARABIC = re.compile(r"(?<![A-Za-z0-9_])\d+(?:\.\d+)?(?![A-Za-z0-9_])")
CJK_NUM = re.compile(r"[一二三四五六七八九十百千万零两]\s*"
                     r"(?:个|件|条|域|行|处|倍|层|分|项|次|组|份|轮|版|道|类|种)")
PROSE_STRING = re.compile(r'^\s*"(.*)"\s*,?\s*$')
INLINE_CODE = re.compile(r"`[^`]*`")
FENCE = re.compile(r"^\s*```")


def mask(text: str) -> str:
    text = INLINE_CODE.sub(" ", text)
    for p in EXEMPT:
        text = p.sub(" ", text)
    return text


def extract_prose_lines(txt: str):
    """抽所有 ASK_ANALYST 数组的纯字符串字面量（跳过 ``` 围栏与 + IDENT 拼接行）。"""
    out, in_fence = [], False
    for m in re.finditer(r"const\s+ASK_ANALYST\s*=\s*\[(.*?)\n\s*\]\.join", txt, re.S):
        for line in m.group(1).split("\n"):
            if FENCE.match(line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            if re.search(r'"\s*\+\s*[A-Za-z_$]', line) or "CLAIM_NUMBERS" in line:
                continue  # 机器段 / 声明行不算散文
            pm = PROSE_STRING.match(line)
            if pm:
                out.append(pm.group(1))
            elif re.search(r"\+\s*[A-Za-z_$]", line):
                # 拼接行里若含字符串字面量也取出来（保守）
                for sm in re.finditer(r'"((?:[^"\\]|\\.)*)"', line):
                    out.append(sm.group(1))
    return out


def main():
    dwf = [p for p in sorted(os.listdir(DRAFTS)) if p.endswith(".dwf.ts")]
    mjs = [p for p in sorted(os.listdir(RUNS))
           if p.startswith("dwfrun-") and p.endswith(".mjs")]
    per_draft, prose_total, raw_total, after_code_total = [], 0, 0, 0
    cjk_suppressed = 0
    affected_by_masking = 0
    for p in dwf:
        txt = io.open(os.path.join(DRAFTS, p), "r", encoding="utf-8",
                      errors="replace").read()
        if "ASK_ANALYST" not in txt:
            continue
        lines = extract_prose_lines(txt)
        if not lines:
            continue
        prose_total += len(lines)
        raw = 0
        for l in lines:
            raw += len(ARABIC.findall(l))                 # 未做任何屏蔽
            cjk_suppressed += len(CJK_NUM.findall(l)) - len(
                CJK_NUM.findall(CJK_GRAMMATICAL.sub(" ", l)))
        after = 0
        for l in lines:
            after += len(ARABIC.findall(mask(l)))
        raw_total += raw
        after_code_total += after
        if after < raw:
            affected_by_masking += 1
        per_draft.append({"file": p, "prose_lines": len(lines),
                          "raw_arabic": raw, "after_mask": after})
    resid = [d["after_mask"] for d in per_draft]
    s = sorted(resid)
    p90 = s[int(0.9 * (len(s) - 1))] if s else 0
    out = {
        "n_dwf_ts": len(dwf),
        "n_mjs": len(mjs),
        "n_drafts_with_ASK_ANALYST": len(per_draft),
        "n_mjs_with_CLAIM_NUMBERS": sum(
            1 for p in mjs if "CLAIM_NUMBERS" in io.open(
                os.path.join(RUNS, p), "r", encoding="utf-8",
                errors="replace").read()),
        "sum_prose_lines": prose_total,
        "raw_arabic_tokens": raw_total,
        "after_code_and_exempt_mask": after_code_total,
        "suppressed_by_masking": raw_total - after_code_total,
        "suppressed_pct": round(100.0 * (raw_total - after_code_total) / raw_total, 2)
        if raw_total else 0,
        "n_drafts_affected_by_masking": affected_by_masking,
        "cjk_grammatical_suppressed": cjk_suppressed,
        "residual_arabic_tokens": after_code_total,
        "residual_per_draft": {
            "mean": round(statistics.mean(resid), 2) if resid else 0,
            "median": statistics.median(resid) if resid else 0,
            "p90": p90,
            "max": max(resid) if resid else 0,
            "n_drafts_with_zero_residual": sum(1 for x in resid if x == 0),
        },
        "note": "草稿/归档目录会被并行会话追加；此为本轮实跑时点值，非 §3.4 旧值 213/256。",
        "per_draft": per_draft,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
