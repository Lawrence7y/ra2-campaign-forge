# -*- coding: utf-8 -*-
# §448: batch-premise verifications from disk (P0 factory-ini pin + P2 log read-back channel).
LEDGER = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
BLOCK = (
    "\r\n# §448　批次前提盘面核验（零发射）：P0 出厂态 ini 钉值 + P2 日志读回通道实证在盘\r\n"
    "\r\n"
    "- **P0 前提**（载体图=sf8 原件、ini 不写三键=出厂态）：源 `ra2render.ini` 盘面直读\r\n"
    "  sha16=`27c9a60c55a8a1b4`（9,841 B），含 [Logic] 节、**全文无 EnableRC4Guard/ExitBail/**\r\n"
    "  DryRun 三键** ⇒ 出厂态成立。**发射序纪律补一条**：批准批次 P0 发射前重验此钉值\r\n"
    "  （一行命令），防裁决与发射之间源件被污染；已写入 D-10 裁决后执行行。\r\n"
    "  注：v2 `_precheck_shas` 现不查 ini 哈希（88 件计数查）——非阻断（发射前人工重验已入\r\n"
    "  协议）；若要驱动内加闸=新 FT+新变异+重钉，登记为可选改进不强推。\r\n"
    "- **P2 前提**（缺省 0 的运行时日志读回可判）：读回通道**源级亲验**——候选源\r\n"
    "  `d09a_c2_candidate/src/*.cpp:693` `g_exitBail=(GetIniInt(\"Logic\",\"EnableRC4ExitBail\",0)!=0)`\r\n"
    "  （键缺省⇒值 0）+ `:699` `Log(\"...EnableRC4ExitBail=%d...\")` **恒显解析后值**；\r\n"
    "  两趟实档首行（133604/200938 均 `EnableRC4ExitBail=1` 与当趟 ini 一致）为同型旁证。\r\n"
    "  ★ 判读细则：日志 `=0` 单通道**不分辨**「键缺失默认 0」vs「显式写 0」⇒ P2 须\r\n"
    "  ini 面+日志面**合判**：v2 `apply_bail_mode(default)` 已断言键必不存在（:406-407\r\n"
    "  「default 臂键未清除」TripFail），日志再显 0 ⇒ 「默认关已验证」成立。判据可执行。\r\n"
    "- 真机新增仍=0；本件仅盘面直读+登记，不启动任何进程。\r\n"
)
with open(LEDGER, "ab") as f:
    f.write(BLOCK.encode("utf-8"))
print("APPENDED §448")
