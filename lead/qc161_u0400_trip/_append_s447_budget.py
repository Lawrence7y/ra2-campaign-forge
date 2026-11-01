# -*- coding: utf-8 -*-
# §447: batch-time budget correction (measured 137.1s fixed pre-close) + design re-pin.
LEDGER = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
BLOCK = (
    "\r\n# §447　批次时间预算修正（设计件 §3c）：旧「16–20 min」系结构性低估，作废重算\r\n"
    "\r\n"
    "- 依据=L1REG 两趟 `_rec.json` 直读（161412/200938 独立成趟互证）：固定前段\r\n"
    "  closed_at_s=137.1/137.1（启动沉降+导航 at=48.8/61.5/74.1+in_battle 闸+战斗窗 60\r\n"
    "  +pre5=5），watch+收尾 ≈10 ⇒ 单趟 3.1 min(watch=40)/4.5 min(watch=120)。\r\n"
    "- ⇒ §2 原「6×(140–160 s+开销)」只计关窗段漏 137 s 前段=h7a「sum(stage) 低估 16.75 s」\r\n"
    "  同族坑。修正预算：**五臂分批 ≈24 min、全六臂 ≈27 min、P3m≈1.9 min；时段按 25–30 min 留**。\r\n"
    "- 旧口径【superseded·10-27】标注于设计件 §3c（§2 原文保留不删）；D-10 裁③同步更新\r\n"
    "  （条目现 sha 前缀=63e41116…，盘面实核）。设计件重钉 70894c58…→\r\n"
    "  `d14e66bd3e17fce02ba10535e57b729db4822fe07db2ab4b87df50bf8cdda686`（§3c 增补后，LF 保持）。\r\n"
    "- 本追加仅登记不发射；真机新增仍=0；D-10 裁决权不变。教训入记忆：批次时长=固定前段\r\n"
    "  +watch+收尾三段都要实测钉，前段随导航/沉降臂不同须逐臂读 _rec 不套均值。\r\n"
)
with open(LEDGER, "ab") as f:
    f.write(BLOCK.encode("utf-8"))
print("APPENDED §447")
