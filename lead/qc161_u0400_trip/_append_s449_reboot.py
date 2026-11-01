# -*- coding: utf-8 -*-
# §449: reboot detected 10-28 → same-session dissolution void → P3m restored as mandatory.
LEDGER = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
BLOCK = (
    "\r\n# §449　重启侦测⇒§444 前提对未来批次作废；P3m 恢复必选；D-10/设计件即改\r\n"
    "\r\n"
    "- 双通道互证：CimInstance BOOT=**2026-10-28 07:52:14**；事件 6006 干净停机\r\n"
    "  =10-28 00:37:12、6005=07:52:30 ⇒ 昨夜今晨真实重启（非读数噪声）。\r\n"
    "- 后果链：§444「开机会话仍=10-26 15:14:25」当时为真、现仅对历史有效 ⇒\r\n"
    "  ①§1c 跨会话对照需求**复活**（L1REG 局内失败=旧会话，批次=新会话）⇒ P3m 从\r\n"
    "  「可选末臂」**恢复必选**；建议回六臂 P0→P0N→P1→P2→P3→P3m ≈**27–30 min**\r\n"
    "  （§3c 单趟形状仍适用）；②批次内互比全在新会话⇒内部效度无损；③旧会话读数\r\n"
    "  （31 档 30.692、L1REG 两趟）跨会话引用按 V11-c 铁律以各臂 in_battle 帧钟自校准，\r\n"
    "  不另加档位趟；④若裁决↔发射间再重启，发射前重测重报（写进 D-10 裁③）。\r\n"
    "- 落件：D-10 ②③ 段【superseded·10-28】修正（原文保留）→ sha 前缀 `96abcae9…`；\r\n"
    "  设计件 §3b P3m 行加 superseded-10-28 批注 → 重钉 d14e66bd…→\r\n"
    "  `543eb9830470a5f3747d5d071b9b9b8e5f6a99a15ca3430482e1a2806f9170f2`（LF 保持）。\r\n"
    "- 方法自陈：本轮价值=**把「会话身份」当作会过期的前置条件例行复查**——若到发射日\r\n"
    "  才发现重启，五臂批次就缺了菜单对照；『当时为真』与『仍然为真』必须分开登记。\r\n"
)
with open(LEDGER, "ab") as f:
    f.write(BLOCK.encode("utf-8"))
print("APPENDED §449")
