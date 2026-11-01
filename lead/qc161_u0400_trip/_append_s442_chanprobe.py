# -*- coding: utf-8 -*-
# §442 ledger append: X channel probe (additive, no-game preflight + mutation-tested judge).
LEDGER = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
BLOCK = (
    "\r\n# §442　加性件：X 观测通道探针 `_x_channel_probe_20261027.py`（永不启动游戏）\r\n"
    "\r\n"
    "- 存在性理由（补 v2 故障注入的三层空白，judge-real-artifact-form-preview 第一层）：\r\n"
    "  v2 的 16 项 FT 把 capture_screen/timeline/_rec 存成 **stub**（b\"PNG\"、合成行），\r\n"
    "  故「截图非全黑、PNG 规范可解、投递记录完备」三类主张**从未在真实工件形态上证过**。\r\n"
    "  本件在**零发射**前提下把这三类主张钉实，供批准前后均作发射器就绪判据。\r\n"
    "- 固定哈希 sha256=`a1cd4dbb51a36857095d570861862087c3c3916ddf615bb42d3f6799da9439e5`。\r\n"
    "- `--selftest` rc=0：判定器对**规范 PNG 合成工件**跑 C1–C7/C9/C10/S1/S2 全绿，\r\n"
    "  负控变异 **7/7 命中**（post_fail→C3、stub_PNG→S1、all_black→S2、truncated_png→S1、\r\n"
    "  tail6_only→C5、bt_dropped→C6、missing_keys→C1）⇒ 每个 ID 是能红的真闸（非装饰）。\r\n"
    "- `--preflight` rc=0（真 OS、零游戏，红=0⇒GO-READY）：五母本哈希钉实核全中\r\n"
    "  （73201cc0/ebddf6a6/d019e8be/b063052c + c2_dll edb9a0cd）；carrier_identity 正负双证\r\n"
    "  （批准根内⇒True、ra2youli 根外⇒False）；**真 GDI 桌面截屏 3584×967 走同一判定器**\r\n"
    "  ⇒ S1 规范可解 + S2 frac=0.8927 非全黑；ini 四模式（g1/e1、g1/e0、g1/default、g0/default）\r\n"
    "  写读回全对；真实 tasklist 残留=空。记录落 `c2ab_x/_preflight/20261027T125912/_pf.json`。\r\n"
    "- `--live` **永久拒 rc=3**：本件无任何游戏 popen 路径；发射仍须走 v2 --live\r\n"
    "  （其 APPROVED_THIS_ROUND 硬闸）⇒ 探针不成为绕过审批的后门，仅就绪自检。\r\n"
    "- 纪律：加性新件、零改动 v2/设计件/历史台账；异族复核到盘前只作**本线候选**（\r\n"
    "  不自我封已核，同 §439 补⑤ 教训）；PNG 写读自实现并双对照（合成 fixture + 真桌面帧）。\r\n"
    "- 本轮真机新增仍=0（探针不启动游戏）；D-10 裁决权在监督/Codex 不变。\r\n"
)
with open(LEDGER, "ab") as f:
    f.write(BLOCK.encode("utf-8"))
print("APPENDED §442")
