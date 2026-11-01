#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""lead/PENDING_DECISIONS.md v12 §4.1 执行：D-01 裁决落地 + 丢单恢复（原子写）。

2026-10-24 实测发现（写台账 §424）：
  - e8dc58e（RE-ATLAS 整文件重写）静默吞掉本线 D-08 全文与 D-06；
  - 并发会话随后又重切一版（8,970→6,691 B，末行截断在半句）。
  ⇒ 本件**不用追加**，改「锚定手术 + 临时文件 + 双 assert + os.replace」原子写，
     把本线自有内容（D-01 已裁记录 / D-06 / D-07 更新段完整化 / D-08 全文）一次恢复。
  - 恢复源=本线在盘追加脚本的 SECTION 字符串（_append_d08.py / _append_d07_evidence.py），
     逐字节重建；非凭记忆改写。
  - 他人条目（D-07 主体=RE-ATLAS 自有）**原文逐字节保留**，仅在其截断的更新段后
     恢复本线追加内容。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

TARGET = Path(r"D:\Project\ra2-campaign-forge\lead\PENDING_DECISIONS.md")

# —— 从 _append_d07_evidence.py 的 BLOCK 逐字节取本线 D-07 更新全文 ——
D07_UPDATE = (
    "- **更新（2026-10-24，GOAL-3T 实测，不改本条选项）**：§409 用密封深扫\n"
    "  `scan-2026-10-23T20-36-58.833Z-8f7e7ad6abd0` 把「36 high」拆开，三条实测：\n"
    "  - **口径**：36 是 occurrence；`findingId` 唯一值 29，粒度实测为 **(规则,文件) 对**\n"
    "    （同文件同规则多行共用、跨文件从不用），**不能当缺陷数**。\n"
    "    构成 = **28 静态 sink + 8 跨文件污点链**（后者扫描器自标 `advisory: true`\n"
    "    并带 `proofGaps`「需人工确认真实数据流」）。这 8 条是深扫才出现，\n"
    "    且全部落在 harness4/5/6/7 —— 这三个件本线一个字节未碰，非本轮引入。\n"
    "  - **决定性**：**6 条落在已实测哈希冻结件上**（harness6 `ff8245d27b3db22a` /\n"
    "    harness7 `d019e8beecfb5fd8`，逐位复核仍等于冻结值）。\n"
    "    ⇒ **选项 A「清零」与「母本零改动」铁律直接冲突**，不是工作量问题；\n"
    "    A 若要成立，需先裁决「是否允许为安全告警破冻结」——**Lead 级口径冲突**。\n"
    "  - **本线无责**：本线写域（`lead/qc161_u0400_trip/`）命中 **0 条**。\n"
    "    这也解释了「commit 能过、push 不能过」：commit 走 diff-only，push 走整仓。\n"
    "- **对选项的实测影响**：**B（按写域路由）** 不是偷懒，而是与 commit 已有的\n"
    "  diff-only 档**对齐**（同一件事，push 端没跟上）；C 仍受「主仓=唯一真源」限制；\n"
    "  A 需先解上面的口径冲突。\n"
    "- **支撑件**：`lead/qc161_u0400_trip/_census_d07_gate36.py`（普查，exit 0）、\n"
    "  `_verify_census_d07.py`（负控 **11/11 PASS，6/6 变异被捕获**）。\n"
    "  台账 §409。\n"
)

# —— D-06 全文：从 8,970 B 版（=HEAD 提交 e8dc58e 之前的我读过的内容）重建 ——
D06 = """## D-06 · R-035 的 LOWER 13,352 只能当上界；D-02 是否改三档双报 [来源 XVERIFY]

- **背景**：独立核验（`xverify/re_atlas/V-001_R035_denominator.md`，模型
  `qoder-global:dfmodel`，与 A/B 不同族）用自写实现盲验 R-035。
  **15 条断言的算术全部复现**（7,279 / 2,042 / 138 / 6,499 / 13,352 / 992,227 /
  890 / 1,445 / 1,872 / 547 / 557 → 4.10%…3.91%），变异 **11/11 复现击杀**。
  机制与方向全部成立：「R-034 方向错」「E9 函数内跳转被当入口」
  「覆盖率高于 3.62%」。
  **但发现一个 R-035 未自查的同类缺陷**：`fn_walk.raw_rel32_targets()` 对
  **E8** 也使用无形状校验的字节扫描（与 E9 同一套 `re.finditer`）。
  实测 7,279 个「E8 目标」中 **560 个（7.7%）** 的 `0xE8` 字节落在**别的指令
  内部**（560/560 逐址复核为操作数字节，非 `call` 起点）。
  换成对齐解码的真实 `call` 目标后：LOWER **12,792**、UPPER **13,683**、
  覆盖率 **4.28%…4.07%**（命名点 547/557 不变）。
  ⇒ **13,352 只能当上界**，R-035 §七 与 D-02 把它当下界/可冻结基线不成立。
  另：UPPER 对序言判据敏感度实测 **≈2×**（独立定义 450 vs 对方 890）。
- **选项**：
  - **A** D-02 改**三档双报**：`13,352 / 12,792`（上界族）与
    `14,242 / 13,683`（补集族），并注明 UPPER 序言敏感度 ≈2×。
  - **B** 维持 D-02 原案（LOWER/UPPER 双界），把本报告作为已知边界挂 R-035 附录，
    不改门禁。→ 成本最低，但「13,352 是下界」的定性仍是错的。
  - **C** 先让 RE-ATLAS 修门禁（E8 改对齐解码 + 补敏感度断言 + 补区分性变异），
    修完再裁 D-02。→ 最稳，但 D-02 顺延一轮。
- **建议**：**C，之后再 A**。理由：12,792 是**核验会话的口径**，不是对方已交付的数；
  直接把我的数写进定稿等于让核验会话产出新结论（越 §0 边界）。
  正确顺序是对方按 V-001 §七 修门禁并自证，再由 Lead 裁 A。
- **阻塞**：D-02 最终裁决；`HANDOFF_TO_GOAL3T.md` 覆盖率契约定稿；R-035 能否标「已交付」。
- **状态**：待 Lead 裁决
- **提出**：2026-10-23（V-001 同提交）
"""

# —— D-08 全文：与 _append_d08.py 的 SECTION 逐字一致 ——
D08 = open(Path(__file__).with_name("_append_d08.py"), encoding="utf-8").read()
import re as _re
_m = _re.search(r'SECTION = """(.*?)"""', D08, _re.S)
assert _m, "无法从 _append_d08.py 重建 D-08 全文"
D08 = _m.group(1).strip("\n") + "\n"

D01_CLOSED = ("- **D-01 已裁决（2026-10-24，Lead）**：**C'**（停在方案 A）。\n"
              "  **执行**：条目已删除。**事实更正（本线 unshallow 后实测）**：根提交是\n"
              "  `c4923c8`（`git rev-list --max-parents=0 HEAD` 唯一输出）；截至 `66eef68`\n"
              "  完整历史 **192** 个提交（HEAD 现 `e79f4b0` 为 194）。条目原写法\n"
              "  「b7f0508 是根提交 / 共 105 提交」系**浅历史假象**（当时仓库 shallow）。\n"
              "  B' 用户可随时重开；「不确认即视为同意」的写法违规，今后禁止。\n")


def main() -> int:
    raw = TARGET.read_bytes()
    text = raw.decode("utf-8")

    # 1) 删除 D-01 整块（从 '## D-01' 到其后第一个 '\n---\n\n' 结束）
    i0 = text.index("## D-01")
    i1 = text.index("\n---\n\n", i0) + len("\n---\n\n")
    d01_block = text[i0:i1]
    assert "B'" in d01_block and len(d01_block) > 1000, "D-01 块锚不符"
    text = text[:i0] + text[i1:]

    # 2) 已裁记录段插 D-01 行（D-05 记录之后）
    anchor = "台账 §399。\n"
    assert text.count(anchor) == 1, "D-05 记录锚不唯一"
    text = text.replace(anchor, anchor + D01_CLOSED, 1)

    # 3) 恢复 D-06（插在 D-07 之前，编号升序）
    d07_at = text.index("## D-07 ")
    text = text[:d07_at] + D06 + "\n---\n\n" + text[d07_at:]

    # 4) 修复 D-07 更新段：当前末行截断在 '…用密封深扫'（无换行闭合）
    #    ⇒ 找到截断行，丢弃该行残段，用完整 D07_UPDATE 替换。
    lines = text.split("\n")
    cut_idx = None
    for k in range(len(lines) - 1, -1, -1):
        if "§409 用密封深扫" in lines[k]:
            cut_idx = k
            break
    assert cut_idx is not None, "截断行未找到"
    assert cut_idx == len(lines) - 1 or all("§409" not in l for l in lines[cut_idx+1:]), \
        "截断行后仍有内容，手术面扩大，停手"
    lines = lines[:cut_idx] + D07_UPDATE.rstrip("\n").split("\n")
    text = "\n".join(lines) + "\n"

    # 5) 恢复 D-08（文件尾）
    text = text + "\n" + D08

    payload = text.encode("utf-8")
    assert "## D-01" not in text and "D-01 已裁决（2026-10-24，Lead）" in text
    assert "## D-06" in text and "## D-08" in text
    assert "（本条为 RE-ATLAS 自有条目）" in text  # D-07 主体未被我动过
    tmp = TARGET.with_suffix(".md.tmp_s424")
    tmp.write_bytes(payload)
    # 双 assert：写盘内容与预期逐字节一致；且只增长不丢他人字节面无法全验（移动靶），
    # 改为逐段断言关键内容都在。
    back = tmp.read_bytes()
    assert back == payload, "回读不一致"
    for needle in ("## D-07 · L3 政策墙", "## D-06 · R-035", "## D-08 · harness7",
                   "D-01 已裁决（2026-10-24，Lead）", "镜像仓旁路已直接实测排除"):
        assert needle.encode() in back, needle
    os.replace(tmp, TARGET)
    print("surgical rewrite OK: %d -> %d bytes" % (len(raw), len(payload)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
