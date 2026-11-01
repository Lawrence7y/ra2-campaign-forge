# -*- coding: utf-8 -*-
# §445 (short): queued finding — v2 lacks carrier-pathlen assertion; measured all arms OK today.
LEDGER = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
BLOCK = (
    "\r\n# §445　挂账发现（复核到盘前不动 v2）：缺 carrier-pathlen 断言\r\n"
    "\r\n"
    "- 盘面实测：v2 `_drive_c2_x_probe_v2.py` 全文无 `carrier_len/CARRIER_PATH_MAX` 断言\r\n"
    "  （旧 c2ab 驱动 `_drive_c2_ab.py:62/387` 有 130 闸；v2 未继承）——路径门禁纪律\r\n"
    "  （[[pathlen-gate-dir-scope]]：130 作用在载体目录）在 v2 里成了「恰好满足」非「断言把关」。\r\n"
    "- 今日各臂载体目录长度实测：P0/P0N/P1/P2/P3/P3m = 101/105/104/104/101/102（最长文件路径\r\n"
    "  124）⇒ 全 ≤130 无现实阻断；但时间戳格式变动或臂名加长即越界无拦。\r\n"
    "- 处置=**挂账勿现在动**：异族复核 V1 正逐字节核 v2（钉值 94881cc2），此刻改件=制造假红。\r\n"
    "  到盘后与红项一并处理：在 fire_arm `phase=mkdir` 前加 `len(str(carrier))<=130` TripFail\r\n"
    "  断言+变异负控（M10 越界⇒FAIL@precheck_mkdir），重钉第 N 版哈希。\r\n"
    "- 真机新增仍=0；D-10 状态不变（五臂建议+P3m 可选末臂在条目内）。\r\n"
)
with open(LEDGER, "ab") as f:
    f.write(BLOCK.encode("utf-8"))
print("APPENDED §445")
