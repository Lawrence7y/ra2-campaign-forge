# -*- coding: utf-8 -*-
# §444 (short): D-10 item-2 input update — session confound dissolved, P3m demoted to optional.
LEDGER = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
BLOCK = (
    "\r\n# §444　D-10 输入更新：开机会话仍=10-26 15:14:25 ⇒ §1c 跨会话混杂自然消解\r\n"
    "\r\n"
    "- 实测（LastBootUpTime 直读）：现会话=selftest/preflight 全轮所用会话，且 L1REG 两趟\r\n"
    "  （16:14/20:09）同在此会话 ⇒ 未来批次任一臂与「局内失败」观测**天然同会话**。\r\n"
    "- ⇒ P3m 原立据（消解 1c 混杂）失效；仅余 d09b 旧菜单臂交叉价值（≈2 min）。\r\n"
    "  D-10 条目②已更新：本线建议=五臂批次 P0→P0N→P1→P2→P3，**P3m 列可选末臂**；\r\n"
    "  P2 保留（配置合同独立位）。批次上界由 6 趟≈16–20 min 收至 5 趟≈13–17 min。\r\n"
    "- 条目并记「在途」：修复轮异族复核 V1–V6（XVERIFY_V2FIX，GLM）到盘即处理红项。\r\n"
    "- 纪律：历史条目零改写（本行为 §441 三裁清单的追加式输入更新）；真机新增仍=0。\r\n"
)
with open(LEDGER, "ab") as f:
    f.write(BLOCK.encode("utf-8"))
print("APPENDED §444")
