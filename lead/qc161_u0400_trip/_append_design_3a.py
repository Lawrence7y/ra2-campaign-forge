# -*- coding: utf-8 -*-
# Append §3a to design doc (LF file — keep LF).
DOC = r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\x_ingame_close_20261026\X_CONTROL_DESIGN_20261026.md"
BLOCK = (
    "\n"
    "## 3a. 通道探针轮（10-27 补，含异族审计 A2-b 红项处理）\n"
    "\n"
    "- 新增加性件 `_x_channel_probe_20261027.py`（零发射就绪判据：判定器 C1–C10/S1/S2\n"
    "  +`--selftest` 负控变异 +`--preflight` 真 OS 实核+`--live` 永久 rc=3）。\n"
    "- 异族审计书 `XVERIFY_CHANPROBE_20261027.md`（sha256=`b7e5aa4a…`，GLM-5.3，20,207 B）：\n"
    "  A1/A3/A4/A5/A6 CONFIRMED；**A2-b FALSIFIED——抓到 v2 `_capture` 真实缺陷**：32bpp DIB\n"
    "  自换 B/R 后按 `w*3` 切 `stride=w*4` 缓冲 ⇒ 几何剪切+二次交换，发射产物「结构合法\n"
    "  内容损坏」（同屏差分 0.9057、屏幕真值 0/5）。**v2 哈希冻结期被红项正当突破**：\n"
    "  修复=改 h7 自家口径（24bpp+pad4 stride，交 `write_png_no_filter` 一次交换，同 h7:2490/2491）。\n"
    "  修复后 S3 同态背靠背差分=**0.2541**（低于方法噪声地板 0.31/0.25/0.32，vs 损坏签名 0.9057\n"
    "  ⇒ 对合成立；差分残余=桌面动画噪声，同法复采 v2-vs-v2 亦 0.3099 为证）。\n"
    "  本线字节独立复验成立；全仓同类坑普查：`write_png_no_filter` 其余调用点全在 h7/h4/h5/h6\n"
    "  自家 capture_frame（24bpp+pad4 正确口径），仅 v2 一处错，无第二现场。\n"
    "- 审计附带两小项已修：BS-2/6 同步截断盲区⇒判器加 **C8**（时间轴单调+衔接+窗跨度，\n"
    "  sync_truncation 变异实证转红）；BS-5 tasklist 码页脆⇒bytes 捕获+replace 解码（UTF-8\n"
    "  模式变体复跑 14/14 全绿）。**新发现并修**：h7 导入设 DPI-aware ⇒ 截图尺寸跨 3584×967\n"
    "  (逻辑)/5376×1451 (物理) 两态；发射序 v2 恒在载 h7 后截屏（物理态），S3 对合须同态背靠背\n"
    "  （首版 S3 拿修复前物理帧比逻辑帧⇒假红「尺寸不等」，红项自曝口径错，非掩盖）。\n"
    "- 重钉值（旧值保留不删）：`_drive_c2_x_probe_v2.py` 65e086e7…→**94881cc2**\n"
    "  `94881cc2d55d8eb012ff8d5ab447a7c469457c1d9c301f6f75d8a48303b6aafe`（修复+wt.UINT 自纠后\n"
    "  FT 16/16+变异 9/9 复跑 rc=0、live 仍 rc=3）；探针 a1cd4dbb…→**597e9359**\n"
    "  `597e9359c2148537f098b5bb19aadc98576beb088325df6d87f38754f4935b16`（selftest 12 判+10 变异\n"
    "  全中 rc=0；preflight 15 查 GO-READY rc=0）。设计件本增补再钉（哈希见台账 §443）。\n"
    "- §2「每臂只读记录面」注记更新：截图通道除故障注入外，另经 S3 与发射器写侧同屏对合\n"
    "  证实——「截图非全黑」判据对真实发射产物**不再是恒绿无效闸**（A2-b 前状态）。\n"
)
d = open(DOC, "rb").read()
assert d.count(b"\r\n") == 0, "doc is LF; abort"
assert d.endswith(b"\n"), "doc must end newline"
open(DOC, "ab").write(BLOCK.encode("utf-8"))
import hashlib
print("NEW-SHA", hashlib.sha256(open(DOC, "rb").read()).hexdigest())
