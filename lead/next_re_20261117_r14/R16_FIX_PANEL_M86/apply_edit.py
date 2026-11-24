#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R16-FIX-PANEL-M86: apply the single scoped edit to PANEL.md (M86 block only).

Reads the exact pre-edit backup (PANEL.before.bak), replaces OLD_BLOCK with
NEW_BLOCK byte-for-byte, and writes the result to PANEL.md. Pure LF endings,
UTF-8, no other line touched.

This script is NOT the verifier; see verify.py for the re-runnable checks.
"""
from pathlib import Path

ART = Path(__file__).resolve().parent
PANEL = ART.parent / "COVERAGE" / "PANEL.md"
BACKUP = ART / "PANEL.before.bak"

# Exact original M86 block: PANEL.md lines 214..221 (8 lines), each ends in LF.
OLD_LINES = [
    "> \u2705 **M86 \u8865\u8bb0\uff1a43 \u884c `slotN` \u7684 \u2463 \u5f00\u59cb\u6210\u6587 \u2014\u2014 \u6279\u6b21 1 \u5e76\u5165 15 \u884c\uff08D-47(A) \u88c1\u51b3\u540e\u89e3\u5c01\uff09**",
    "> \u4f9d\u636e **D-47 (A)**\uff08`R14_COMMON \u00a712.6`\uff09\uff1a\u69fd\u4f4d\u5360\u7528\u5373 \u2463\uff0c\u00a712.3 \u5bf9\u8be5\u5f62\u6001\u8ba9\u4f4d\uff1b",
    "> \u672c\u6279 15 \u884c\u53d6\u81ea `PROBE_802\\slotN43.tsv` \u6570\u636e\u884c 1\u201315\uff0c`col_ok=match` / `install_ext=y` 15/15\uff1b",
    "> \u6bcf\u884c \u2463 \u542b vt/COL/offset/RTTI/\u88c5\u8868\u70b9\u56db\u5143\u7ec4\uff0c\u5e76**\u81ea\u5e26 D-47 \u62ab\u9732\u6307\u9488**\uff1b",
    "> \u5ba1\u8ba1\uff08\u5f02\u65cf\uff09\u5224 **PASS 15 / FAIL 0 / \u5fc5\u6539 0**\uff0c90/90 \u5b57\u8282\u9879\u72ec\u7acb\u590d\u7b97\u4e3a\u771f\uff1b",
    "> \u300c**\u2463 \u5df2\u6210\u6587**\u300d\u7531 **319 / 1,654\uff0819.29%\uff09\u5347\u81f3 334 / 1,654\uff0820.19%\uff09**\uff1b",
    "> **\u672c\u6b21\u53ea\u8865 \u2463 \u6210\u6587\uff0cgrade / \u5224\u5b9a / named / proved / strict \u5168\u4e0d\u53d8\uff0c\u65e0\u8fbe\u6807\u7ffb\u8f6c**\uff1b",
    "> \u5f15\u7528\u7eaa\u5f8b\uff1a\u5f15\u7528\u8fd9 15 \u884c\u65f6\u987b\u540c\u5f15 D-47 \u88c1\u51b3\u4e0e\u672c\u8282\u62ab\u9732\uff0c**\u4e0d\u5f97**\u8868\u8ff0\u4e3a\u300c\u5df2\u8fc7 \u00a712.3\u300d\u3002",
]

# New M86 block: lines 1..5 unchanged; line 6 replaced by corrected number +
# explicit +15-vs-+9 disclosure; new heterogeneity-disclosure line inserted;
# then original last two lines unchanged. Total 10 lines (net +2).
NEW_LINES = [
    OLD_LINES[0],
    OLD_LINES[1],
    OLD_LINES[2],
    OLD_LINES[3],
    OLD_LINES[4],
    "> \u300c**\u2463 \u5df2\u6210\u6587**\u300d\uff08\u53e3\u5f84 A\uff1a\u7b2c 4 \u5217\u542b\u5b57\u7b26 `\u2463`\uff09\u7531 **319 / 1,654\uff0819.29%\uff09\u5347\u81f3 328 / 1,654\uff0819.83%\uff09**\uff0c**\u51c0\u589e 9 \u884c**\uff1b",
    "> **\u4e0d\u662f +15**\uff1a\u672c\u6279 15 \u884c\u91cc\u6709 **6 \u884c**\uff08`0045A560`/`0045A680`/`0045A730`/`004A9890`/`004D24A0`/`004D2510`\uff09\u6539\u524d\u7b2c 4 \u5217\u5df2\u5728\u300c\u5408\u540c\u95ed\u5408 \u2462b\u2463\u300d\u6807\u7b7e\u91cc\u542b\u5b57\u7b26 `\u2463`\uff0c\u6539\u540e\u8ba1\u6570\u4e0d\u589e\u3002**\u8be5 +15 \u4e0e +9 \u7684\u5dee\u503c\u5df2\u5728\u6b64\u663e\u5f0f\u62ab\u9732\uff0c\u4e0d\u5f97\u518d\u8868\u8ff0\u4e3a\u6574\u6279 +15**\u3002",
    "> \u26a0\ufe0f **\u53e3\u5f84 A \u7684\u5df2\u77e5\u5f02\u8d28\u6027**\uff1a`[\u5df2\u8bc1]` 1,654 \u884c\u4e2d\uff0c\u53e3\u5f84 A \u8ba1 **328** \u884c\uff0c\u4f46\u5176\u4e2d\u771f\u6b63\u5199\u6210\u300c`\u2463 \u6d3b\u8868\u69fd\u4f4d\u89c1\u8bc1`\u300d\u5f62\u6001\u7684\u53ea\u6709 **106 \u884c\uff086.41%\uff09**\uff1bA\u2212B = **222 \u884c**\u542b `\u2463` \u800c\u975e\u69fd\u4f4d\u89c1\u8bc1\u5f62\u6001\uff0c\u5176\u4e2d\u81f3\u5c11 `74 \u884c` \u53ea\u662f `\u2462b\u2463` \u7684**\u5206\u7c7b/\u73af\u6807\u7b7e**\uff0c\u53e6\u6709\u300c`\u2463 N \u4e2a E8 \u76f4\u8c03\u7ad9\u70b9`\u300d\u300c`\u2463 \u6d3b vt \u6784\u9020\u5b89\u88c5\u70b9`\u300d\u7b49\u8868\u8ff0\u3002\u21d2 **\u53e3\u5f84 A \u4e0d\u5f97\u5f53\u4f5c\u300c\u56db\u73af\u9f50\u5168\u300d\u7684\u7b49\u4ef7\u7269\u5f15\u7528**\uff1b\u5f15\u7528 \u2463 \u6210\u6587\u7387\u65f6\u5fc5\u987b\u540c\u65f6\u8bf4\u660e\u7528\u7684\u662f A \u8fd8\u662f B\u3002",
    OLD_LINES[6],
    OLD_LINES[7],
]

OLD_BLOCK = ("\n".join(OLD_LINES) + "\n").encode("utf-8")
NEW_BLOCK = ("\n".join(NEW_LINES) + "\n").encode("utf-8")

def main():
    before = BACKUP.read_bytes()
    assert before.count(OLD_BLOCK) == 1, (
        "OLD_BLOCK must appear exactly once in backup; got %d" % before.count(OLD_BLOCK)
    )
    after = before.replace(OLD_BLOCK, NEW_BLOCK, 1)
    assert after != before
    PANEL.write_bytes(after)
    print("WROTE", PANEL)
    print("OLD block lines:", len(OLD_LINES), "NEW block lines:", len(NEW_LINES))
    print("bytes:", len(before), "->", len(after), "(delta", len(after) - len(before), ")")

if __name__ == "__main__":
    main()
