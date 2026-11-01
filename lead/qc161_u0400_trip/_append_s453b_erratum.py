# -*- coding: utf-8 -*-
# §453补: census erratum for "×5" (correct=7 battle trips incl. repeats); conclusion unchanged.
LEDGER = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
BLOCK = (
    "\r\n# §453补（勘正·自察）：§453「战斗 137 s 关窗×5」漏计重复批两趟（P0r/P1r），\r\n"
    "#   全表普查（本行实测）=战斗×7、菜单就绪×2、早窗×3（latch 3/3、兑现退 2/3）；\r\n"
    "#   「闩 1 只在早窗出现」结论**不受影响**（七趟全恒{0}）。TRIP_INDEX 同步改正值；\r\n"
    "#   原文保留（追加式）。教训回登：引用『×N』计数时 N 的集合边界=全表重算非记忆。\r\n"
)
with open(LEDGER, "ab") as f:
    f.write(BLOCK.encode("utf-8"))
print("APPENDED §453补")
