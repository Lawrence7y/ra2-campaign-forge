# -*- coding: utf-8 -*-
# GOAL anchor append: 收口更新④ (A2-b fix round). LF file.
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
BLOCK = (
    "\n"
    "### 收口更新④（A2-b 修复轮，台账 §443；异族复核 V1–V6 在途）\n"
    "\n"
    "- **② 通道探针审计出真缺陷并修复**：异族书 XVERIFY_CHANPROBE（b7e5aa4a…）A2-b\n"
    "  FALSIFIED 抓到 v2 `_capture` stride 错配（32bpp 自换 B/R 后按 w*3 切 stride=w*4 ⇒\n"
    "  发射截图「结构合法内容损坏」、S1/S2 恒绿无效闸）。修复=h7 自家口径（24bpp+pad4）；\n"
    "  修复后同屏差分 0.9057→0.2541（<同法噪声地板 0.31）⇒ 截图通道对真实发射产物成立。\n"
    "- 重钉：驱动 v2=94881cc2…（旧 65e086e7 留档）；探针=597e9359…（加 C8 时轴互校+\n"
    "  S3 写侧对合+R1 码页修；selftest 12+10 变异全中、preflight 15 查 GO-READY、live rc=3）；\n"
    "  设计件=4ebc7143…（增 §3a）。三套件复跑 16/16+9/9+rc=3 不变。\n"
    "- 附带新事实：h7:182 `SetProcessDPIAware` 使截屏尺寸随导入序在两态翻转（3584×967 逻辑\n"
    "  /5376×1451 物理）——坐标/像素口径须按此读；发射序恒物理态。\n"
    "- 真机新增仍=0。下一动作权在 Codex/用户（D-10 三裁：批次构成顺序、P2∧P3m 存废、\n"
    "  时段）；修复轮本身的异族复核（V1–V6）已派 GLM 在途，红项到盘即处理。\n"
    "- 三目标句态不变：①受测窗有限未复现、②菜单态有限通过+局内失败项开放、③保持态。\n"
)
d = open(GOAL, "rb").read()
assert d.endswith(b"\n") and d.count(b"\r\n") == 0, "anchor LF check"
open(GOAL, "ab").write(BLOCK.encode("utf-8"))
import hashlib
print("APPENDED sha=", hashlib.sha256(open(GOAL, "rb").read()).hexdigest()[:16])
