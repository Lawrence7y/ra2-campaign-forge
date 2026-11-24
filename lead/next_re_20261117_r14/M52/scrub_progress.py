# -*- coding: utf-8 -*-
"""Comply with Lead STOP order: scrub PANEL after-SHA from M52/PROGRESS.md."""
P = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M52\PROGRESS.md"
with open(P, "r", encoding="utf-8", newline="") as f:
    s = f.read()

old_b = """- **(b) PANEL.md 改前/改后 SHA-256 与字节数**：改前 `457fb6928e28af11a12f24862da750fdc1be9f2ba3d29e3294722a7f9e16cf36` / **94,309 B**（417 行）；备份 `_hygiene/PANEL.M52.bak` SHA 与改前一致。M52 自身编辑完成时 SHA `2a19478621c0a281a51b8113810ee8ab22825da82a69bae42948d99370b803c9` / **98,156 B**。其后另一路 R15 工作流（非本卡，非 agent-95；其内容为「R15 named 实测修正」「D-38 已裁(A)/D-44 严格列」「严格口径双列表」）并发向同一 PANEL.md 追加内容（M52 段与三分母表未被其改动）；本卡收尾时盘上最终 SHA `4d431d637ba04fd69dae59a30fdb101c99fcf4423cdec86b7bd79cff6f44024b` / **101,651 B**（477 行），连续两次读取稳定。"""

new_b = """- **(b) PANEL.md 改前 SHA-256 与字节数 / 备份**：改前 `457fb6928e28af11a12f24862da750fdc1be9f2ba3d29e3294722a7f9e16cf36` / **94,309 B**（417 行）；备份 `_hygiene/PANEL.M52.bak` SHA 与改前一致。**改后 SHA 按 Lead STOP 指令暂不写入** —— 见本目录 `STOP_CONCURRENT_WRITE.txt`：第二路 RULING_R15_20261119 并发编辑同一 PANEL.md，单写者规则被破坏，Lead 尚未接受 RULING_R15，待 Lead 向用户确认后仲裁。M52 自身编辑（仅标题/三分母 B·C 行/行数行/新增 M52 节）完成时状态与后续并发追加均保留在工作脚本证据中，不在本文件锁定「改后」值。"""

old_4 = """- **异常登记**：编辑期间有并发工作流修改同一 PANEL.md（见自检 (b)）。本卡未回滚、未覆盖其 R15 内容；M52 自身改动经 grep/difflib 复核仍完整存在（标题 M52 段、B/C 行、行数行、M52 节）。本卡以收尾时盘上最终 SHA 作为「改后」值上报；若 Lead 需要仅含 M52 改动的纯截面 SHA，为 `2a194786...`（98,156 B），但盘上当前已是含 R15 并发追加的 `4d431d63...`。"""

new_4 = """- **异常登记**：编辑期间有并发工作流修改同一 PANEL.md（见自检 (b)、`STOP_CONCURRENT_WRITE.txt`）。本卡未回滚、未覆盖其 R15 内容；M52 自身改动经 grep/difflib 复核仍完整存在（标题 M52 段、B/C 行、行数行、M52 节）。本卡于 22:14:54 完成最后一次 PANEL.md 写入后未再改 PANEL.md；收到 Lead STOP（22:17:30）后遵守指令，不在本 PROGRESS 锁定 PANEL「改后」SHA，留待 Lead 仲裁。"""

assert old_b in s, "old (b) not found"
assert old_4 in s, "old section4 note not found"
s = s.replace(old_b, new_b).replace(old_4, new_4)
with open(P, "w", encoding="utf-8", newline="") as f:
    f.write(s)
print("PROGRESS.md scrubbed per STOP order")
