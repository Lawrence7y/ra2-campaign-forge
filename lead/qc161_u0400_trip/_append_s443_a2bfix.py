# -*- coding: utf-8 -*-
# §443 ledger append: XVERIFY_CHANPROBE receipt, A2-b fix, re-pins.
LEDGER = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
BLOCK = (
    "\r\n# §443　异族审计通道探针到盘处理：A2-b FALSIFIED⇒修 v2 截图真缺陷；三件重钉\r\n"
    "\r\n"
    "- 审计书在盘：`x_ingame_close_20261026/XVERIFY_CHANPROBE_20261027.md`（20,207 B，\r\n"
    "  sha256=`b7e5aa4a4ff17d50d5f06b9c34e0e460ea2708595fba5e4fe98a48f51dae1102`，\r\n"
    "  身份=GLM-5.3 异族）。A1/A3/A4/A5/A6 CONFIRMED；**A2-b FALSIFIED（核心红项）**。\r\n"
    "- **A2-b 本线字节独立复验成立**（非散文采信）：v2 `_capture` 取 32bpp DIB、自行 B/R\r\n"
    "  交换进 stride=4 缓冲，却交 `write_png_no_filter(..., w*3)`——写入器按 `raw[y*3w:...]`\r\n"
    "  切 stride=4w 的行⇒每行几何剪切 + D-115 二次 B/R 交换。h7 自家 capture_frame（:2490）\r\n"
    "  正确口径=24bpp+`stride=((w*3+3)//4)*4` 直交 buf.raw+stride。⇒ 发射截图「结构合法、\r\n"
    "  内容损坏」，探针 S1/S2 对其恒绿（判据无效闸）。审计四路同证：同屏差分 0.9057、\r\n"
    "  屏幕真值 GetPixel v2 0/5、仿真错行 8/8、Pillow 照收（排除严格度差）。\r\n"
    "- **修复（v2 哈希冻结期被红项正当突破）**：`_capture` 改 h7 口径。修复后 S3 同态\r\n"
    "  背靠背差分=0.2541 < 方法噪声地板（v2-vs-v2 同法复采 0.3099、probe-vs-probe 0.3196）\r\n"
    "  ⇒ 对合成立，残余=桌面动画非方法差。本线自跑 `_recheck_a2v_noise.py` 复现四值。\r\n"
    "  ★ 修中自曝两次：① 首用 `_c.UINT`（ctypes 无此属性）⇒审计件脚本秒抛 AttributeError，\r\n"
    "  改 `wt.UINT`；② 首版 S3 拿修复前物理帧比探针逻辑帧⇒假红「尺寸不等」，揭出 **h7 导入\r\n"
    "  设 DPI-aware ⇒ 截图尺寸有 3584×967(逻辑)/5376×1451(物理) 两态**（发射序恒载 h7 后截图\r\n"
    "  =物理态）⇒ S3 须同态背靠背。两处均如实登记不掩盖。\r\n"
    "- 附带项处理：BS-2/6 同步截断盲区⇒判器加 C8（sync_truncation 变异实证转红）；\r\n"
    "  BS-5 tasklist 码页脆⇒bytes 捕获+replace 解码（PYTHONUTF8=1 变体 14/14 全绿 rc=0）；\r\n"
    "  A6 C5 盲区确认为「keep=6..39 全绿+时轴未互校」⇒C8 补时轴跨度封堵。\r\n"
    "- 重钉（旧值保留）：驱动 v2 65e086e7…→`94881cc2d55d8eb012ff8d5ab447a7c469457c1d9c301f6f75d8a48303b6aafe`\r\n"
    "  （FT16/16+变异9/9 复跑 rc=0、live rc=3）；探针 a1cd4dbb…→\r\n"
    "  `597e9359c2148537f098b5bb19aadc98576beb088325df6d87f38754f4935b16`（selftest 12+10变异全中、\r\n"
    "  preflight 15查 GO-READY rc=0）；设计件 b66466b6…（增 §3a 后）→\r\n"
    "  `4ebc7143be101d919df4143a7a5a6703f401e31f9bab3d16bad8ddab141f7971`；D-10 条目随重钉更新。\r\n"
    "- 交付包现七件钉值：驱动 v2 / 自检件 8c74bba6（未动）/ 设计件终值 / 静态审计 77bb6d6c（未动）/\r\n"
    "  探针 / 探针审计书 b7e5aa4a / GOAL 锚。真机新增仍=0；D-10 裁决权在监督/Codex。\r\n"
    "- 纪律核验：异族代理仅写其判定书+9 个 `_auditprobe_*`（在其允许目录，只读留存）；\r\n"
    "  本线未改历史台账（追加 §443）；PYTHONDONTWRITEBYTECODE=1 全程零 pyc 落盘。\r\n"
)
with open(LEDGER, "ab") as f:
    f.write(BLOCK.encode("utf-8"))
print("APPENDED §443")
