# R4 · 验收标准与闸门状态审计（atlas 锚定补丁块 + 十节回执）
# R4 Acceptance-Standard & Gate-Status Audit for ARCHITECTURE_ATLAS.md

> **任务**：共享任务 `task-4`（R4 流 —— 验收/证据标准）
> **执行方**：DSH 子代理 / Agent Teams 成员 `atlas-r4-acceptance`
> **写作用域（声明）**：`docs/re/atlas_rev/R4_acceptance_standard.md`、`out/re_work/atlas_rev/R4/**`
> **未触碰**：`docs/re/ARCHITECTURE_ATLAS.md`（**Lead 为 atlas 唯一写者，本文只给锚定补丁块**）、其他 R# 成员产物、`ra2render/**`、`ra2youli/**`、`REVERSE_ENGINEERING_AND_PATCHES.md`、任何既有 `docs/re/*.md`
> **基线（只读）**：`ra2youli/gamemd.exe` MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`，4,825,360 B（本批实读哈希一致，mtime 2026-09-25）
> **依据优先级**：`docs/re/EVIDENCE_STANDARD.md`（v3 + 2026-09-28 附·口径订正，最高） > `v160_acceptance*.md` / `mp_release_safety_checklist.md` / `MP_SAFETY_REVIEW.md` / `landing_equivalence_static_proof.md` / `ZCODE_LIVE_ACCEPTANCE_TASK.md`
> **补丁块计数**：**9 个**（INSERT_AFTER ×5、REPLACE_BLOCK ×3、ERRATUM ×1），全部附实跑 grep 锚点
> **门禁**：`python tools\verify_anchors.py` = **323/323 PASS**；`python tools\audit_bytes.py out/re_work/atlas_rev/R4/claims_R4.txt` = **32/32 OK**（原文见 [6]）

---

## 0. 三条必答项（摘要）

| # | 必答项 | 结论 | 证据等级 | 证据锚点 |
|:--|:---|:---|:---|:---|
| Q1 | atlas 是否把**静态分析**写成「实测 / 真机」？ | **是，共 8 处**（`实测` 全部指向静态字节复算，**无一涉及真机**；属**术语违规**，非伪造）⇒ 逐条 ERRATUM：PATCH-R4-06/07/08/09 | [实证] | `ARCHITECTURE_ATLAS.md:472,473,1372,1375,1512,1513,1515,1710`；规则 `EVIDENCE_STANDARD.md:8` |
| Q2 | atlas 是否引用已作废的唯一色数阈值（`≥2,000` / `≥20,000`）？ | **否，0 命中** ⇒ 属**未收录遗漏**（非字面冲突）：atlas 全文无任何色彩阈值口径 ⇒ 新增 §13.3 收录生效口径 `≥600`（80×80 采样）/ `≥800`（全画面） | [实证] | grep `2,000`/`2000`/`20,000`/`色数` = 全 0；口径源 `EVIDENCE_STANDARD.md:117-130` |
| Q3 | atlas 是否缺 **v160 验收状态的显式声明**？ | **是，完全缺失**：`v160`/`UNVERIFIED`/`闸门`/`verify_evidence`/`except.txt` 全文 **0 命中** ⇒ 新增 **§13 验收与闸门状态**（PATCH-R4-01）+ §0.1 三红线（PATCH-R4-02）+ §0.3 第 6 条（PATCH-R4-03） | [实证] | grep 五关键词 = 全 0；现状唯一状态行 `ARCHITECTURE_ATLAS.md:167` |

**额外 P0 发现（超出 atlas 域，交 Lead 裁决）**：机械校验器 `tools/verify_evidence.py:345-348` 仍按**旧 v2 阈值** `colors_80x80 < 1500 ⇒ FAIL`（文案仍写「建议 ≥ 2000」），与 09-28 生效口径 `≥600` **冲突** ⇒ 现网第一级过滤会**误杀**同量级合法证据（ZC-9B 实测 841–1046 < 1500）。放闸前必须先收口，否则 §13.4 两级过滤第 1 步即失效。见 [3]-E1、[9]-D1。

---

## 1. 锚定补丁块（Lead 按此机械套用）

> **通用说明**：所有「目标锚点」行号 = 本批打开时的 `docs/re/ARCHITECTURE_ATLAS.md` 快照行号，并**实跑 grep**（正则转义后字面匹配）确认**命中数 = 1**；若套用前文件已变动，请以「该行前 40 字符原文」为准重新定位。
> 「替换文本」一律用**四反引号围栏**包裹，内容为**可直接粘贴**的完整 markdown（含 §编号与证据等级标签）。

### PATCH-R4-01 新增 §13 验收与闸门状态（真机挂起 / UNVERIFIED 清单 / 阈值新口径 / 两级过滤）
- 目标锚点: L1973 `   - 依据 **G-07 规约**，必须将启动时修改的 `TYPE` 字段原`（grep 实跑：hits=1 @1973）
- 动作: INSERT_AFTER（插在 §12.4 末条之后、文档尾注「编制完成 · S17 专项终审定谳」行之前；**不修改「## 目录」**，TOC 由 Lead 统一重建）
- 现状问题: atlas 全文 **0 命中** `v160` / `UNVERIFIED` / `闸门` / `verify_evidence` / `except.txt`；唯一状态声明只有 §0.3 第 5 条末行 `:167`（verify_anchors 323/323 + 真机未执行）。⇒ 「v1.6.0 维持未验收（Gate Locked）」、「MP NO-GO」、2026-09-28 阈值订正、两级过滤机制与 7 项放闸硬指标**全部缺失**，读者/后续 AI 无法从图谱判断任何功能是否已真机验收（Q3）。
- 替换文本:
````markdown
---

## 13. §13 验收与闸门状态 (Acceptance Gates & Verification Status)

> **性质**：本节是**验收状态与证据口径的唯一权威收口**（2026-09-29 起生效）。它只登记「哪些结论已静态闭环 / 哪些仍挂起 / 放闸需要什么」，**不新增任何二进制定谳**；与 §1–§12 正文冲突时以本节状态栏为准（正文结论不删，仅加注）。
> **依据（只读）**：`docs/re/EVIDENCE_STANDARD.md`（v3 + 09-28 附·口径订正）、`docs/re/v160_acceptance.md`、`docs/re/v160_acceptance_runbook.md`、`docs/re/ZCODE_LIVE_ACCEPTANCE_TASK.md`、`docs/re/mp_release_safety_checklist.md` §四/§六、`docs/re/MP_SAFETY_REVIEW.md` §9。

### 13.1 真机挂起状态（当前闸门 = 关闭）

| 闸门 / 对象 | 当前状态 | 权威依据 |
|:---|:---|:---|
| **GATE-v1.6.0**（迷雾/雷达四项功能合入生产） | 🔴 **未验收（Gate Locked）**，不得合入生产主干 | `docs/re/v160_acceptance.md:6-7` |
| **GATE-MP**（联机发布） | 🔴 **NO-GO**：Gate1（R-01/R-02/R-03）代码层已落地；Gate2（G-03/G-06）未闭环；Gate3（真机混联 ≥5000 帧零 OOS）未执行 | `docs/re/mp_release_safety_checklist.md:79-88,144-146` |
| **真机联机对拍**（≥3 局双端逐帧 CRC） | **[待实测] 未执行** | 本文 §0.3 第 5 条末行 `:167`；`docs/re/MP_SAFETY_REVIEW.md:530` |
| **ZC-1 真机任务卡**（Q1–Q6） | **待派发**；Q2 联机项受单实例限制，**只能双机 LAN**（≥2 名玩家）构造，无法构造时须如实标「未验证」 | `docs/re/ZCODE_LIVE_ACCEPTANCE_TASK.md:4,35` |
| **静态门禁** | `python tools/verify_anchors.py` = **323/323 PASS**（**静态度量，非真机**） | 本文 §0.3 第 5 条末行 |
| **机械证据校验器** | ⚠️ `tools/verify_evidence.py:345-348` 仍按**旧口径** `colors_80x80 < 1500 ⇒ FAIL`（文案仍写「建议 ≥ 2000」）⇒ 与 13.3 生效口径冲突，**放闸前必须先收口**，否则第一级过滤会误杀同量级合法证据 | `tools/verify_evidence.py:15,345-348`；`docs/re/EVIDENCE_STANDARD.md:117-130` |

### 13.2 UNVERIFIED / 未闭环清单

| # | 项 | 状态 | 依据 |
|:--|:---|:---|:---|
| U-1 | v1.6.0 五项功能真机表现（小地图迷雾 / 建筑三态 / 灰雾 4 帧渐变 / 弹道剔除 / 读档一致性） | **待判定（UNVERIFIED）** | `v160_acceptance.md:37-43` |
| U-2 | 遥测生效性（建筑剔除 / 弹道剔除 / 小地图灰化像素 > 0） | **UNVERIFIED（零生效）** | `EVIDENCE_STANDARD.md:94` |
| U-3 | 路线 A 雷达崩溃 `EIP 0x5450202F` 是否复现 | **[待实测]**（历史崩溃 18:09:25，EIP 归属 `ra2render.dll` 注入区 `0x54500000–0x545F0000`） | `EVIDENCE_STANDARD.md:88-93`；`MP_SAFETY_REVIEW.md:171` |
| U-4 | G-03 / G-04 / G-06 / G-07 / G-10 代码落地 | **未落地**（`ThreatRetention`/`EnableFogBlendStubs`/`L4DirtyMode`/`MpStateWrites`/`RestoreSpySat` 全源码 grep 0 命中） | `mp_release_safety_checklist.md:136-142` |
> 【W3 勘误 · W3-A6/ISSUE-STALE-L4-EXIST】改前：L4DirtyMode`/`MpStateWrites`/`RestoreSpySat` 全源码 grep 0 命中；改后：L4DirtyMode 已在 blitter_hooks.cpp:757 读取并支持 force-full / vision-dirty 模式；三处 ini 均已配置出厂值。；依据：ra2render/blitter_hooks.cpp:757; ra2render/ra2render.ini:251; ra2youli/ra2render.ini:186; ra2bench/ra2render.ini:186；分级：P1
| U-5 | 联机 ≥5000 帧双端逐帧 CRC 对拍 | **[待实测] 未执行** | `mp_release_safety_checklist.md:87,146` |
| U-6 | §9.2「局内共享 RNG 消费点仅此一家 / 每逻辑帧 1 次」 | **已推翻**：帧 CRC 路径每逻辑帧 **2 次**，全 `.text` 另有约 **83** 个候选消费点 ⇒ `:1517` 首句与同节勘误**自相矛盾**，待就地加注 | 本文 `:1517` vs `:1519-1556` |
| U-7 | 不可静态判定项（DirectSound 抗压 / CRT 池长跑 / 视口打脏 GPU 降幅 / 8 玩家 60min 工作集） | **[待实测]** | `landing_equivalence_static_proof.md:124-126,305-306,399-400` |

### 13.3 阈值新口径（2026-09-28 Lead 裁定，**取代**旧唯一色数阈值）

| 判据 | 旧口径（原文保留，**已作废**） | **生效口径** |
|:---|:---|:---|
| 战场唯一色数（80×80 均匀采样 6,400 点） | 建议 ≥ 2,000（`EVIDENCE_STANDARD.md:31`；`v160_acceptance_runbook.md:44`） | **≥ 600**，且须与同场景既有**已验收**证据同量级 |
| 战场唯一色数（全画面口径） | ≥ 20,000（`v160_acceptance.md:64`） | **≥ 800**，且同量级 |
| 菜单 / UI 类 | 基准 ≈ 249（实测 240–900） | **不变** |
| 唯一色数 = 1 | 判伪造（硬 FAIL） | **不变**（仍为硬 FAIL） |

**依据**：`docs/re/EVIDENCE_STANDARD.md:117-130`（附·口径订正，含 90 命中普查 + ZC-9B 实测：80×80 战场 **841–1046**、全画面 **978–1756**，既有已验收证据同量级）；`docs/re/v160_acceptance.md:65`；`docs/re/ZCODE_LIVE_ACCEPTANCE_TASK.md:7`。
**注意**：本表只是**阈值口径**，不构成任何真机通过结论（U-1/U-2 仍挂起）；「同量级」目前**无机器化判据**（见 13.1 表末行校验器冲突项）。

### 13.4 两级过滤机制与放闸硬指标（放闸唯一合法路径）

1. **第一级 · 机械过滤（无人工偏见）**：
   `python tools/verify_evidence.py <evidence_dir> --log ra2youli/ra2render.log --except-file ra2youli/except.txt --sav-dir ra2youli --json-out … --md-out …`
   退出码 `0` = PASS、`1` = FAIL/UNVERIFIED（`EVIDENCE_STANDARD.md:55-58`）。**任一项 FAIL/UNVERIFIED 即刻驳回重测，不得进入人工环节**。
2. **第二级 · 人工深度抽验**（机械全绿后）：① 小地图雷达静止视角敌点是否彻底消除；② 三态轮廓（未侦察 100% 隐形 / 侦察后常驻 / 盟军全彩）；③ 4 帧渐变无锯齿、色斑、通道借位黑斑；④ 读档后 `s_everSeenGrid` 按当前局重新盖章（无跨战局幽灵）。
3. **工具边界声明**：校验器可 100% 机械化排查「运行期崩溃 / 未生效连拍 / 单色占位伪造 / 尺寸下溢 / 遥测全零」，但**无法**证明图像未经后期离线篡改、亦不评估画质审美 ⇒ 两级过滤**不可省第二步**（`EVIDENCE_STANDARD.md:102-112`）。
4. **放闸 7 项硬指标（缺一不可）**：① 路线 A 落点 `0x00655D38`（9B）+ `0x0065719A`；② `ra2render.ini` 显式开启被测开关；③ 连续 3 局无新增崩溃（`except.txt` 保持 18:09:25 或更早）；④ 末行遥测三项非零；⑤ 合规证据包（截图 MD5 互异 + OLE2 `.SAV` 魔数 `D0 CF 11 E0 A1 B1 1A E1` + `PROTOCOL.md`）；⑥ `verify_evidence.py` 综合 **PASS**；⑦ 独立方人工抽验通过（`v160_acceptance_runbook.md:104-116`）。
5. **性能/真机数值类判据**（与功能放闸并列，缺一不可）：`valid_pct ≥ 10%`、采样窗口内帧推进 `≥ 3 fps`、`python tools/bench_metrics.py --run <json>` 判 `overall = PASS`；**明令禁止**的引用方式见 `out/loadbench/PROTOCOL.md` §12（旧 JSON 只判 PARTIAL/INVALID_SAMPLE；「区间表命中率 99.69%」不得单独引用，须并列「锚点支撑占比 66.26%」；未对齐截图 diff% 可达 18.75% 假回归）（`ZCODE_LIVE_ACCEPTANCE_TASK.md:94-105`）。

### 13.5 联机放闸前置（与 §9.4 / §12.2 联读）

- **Gate 读法**：Gate1（R-01/R-02/R-03）**代码层已落地**；Gate2（G-03 Retention、G-06 `MpStateWrites`）**未闭环**；Gate3（真机混联 ≥10 分钟 / ≥5000 帧无 Out of Sync）**未执行** ⇒ **不得宣判「MP 可发布」**（`mp_release_safety_checklist.md:79-88,144-146`）。
- **混联禁令**：M-10 裂缝/间谍卫星类补丁改变 `CellClass+0x134`（`GapsCoveringThisCell`，进 `.SAV` 序列化）⇒ **严禁单端注入**；与原版客户端联机须**整局不加载 `ra2render.dll`**（`landing_equivalence_static_proof.md:180-194`）。
- **判定口径订正**：`TargetScanKey=pointer` 分支 = **VIOLATION**（指针哈希受 ASLR 影响跨端必不同）；默认 `position` 键下同源三项（#7/#8/#9）**降为 RISK（待对拍）**（`MP_SAFETY_REVIEW.md:491-499`）。
- 本节与 §12.2 一律**不得**用于宣称「零风险 / 无 Desync」。

### 13.6 术语口径（本文档内「实测」的定义）

- 本文档（及 atlas 全文）出现的「**实测**」**一律指对基线镜像 `ra2youli/gamemd.exe` 的静态字节复算（复扫）**，与真机运行期观测无关；新写入内容统一用「**静态复算**」（见 §0.1 第 2 条末项）。
- 涉及进程运行、注入、对拍、截图、遥测的结论必须使用「**真机**」并标 `[待实测]`；**未实跑者严禁**写成「实测 / 已验证 / 已通过」（`docs/re/EVIDENCE_STANDARD.md:8` 伪造零容忍）。
````
- 证据: [实证] `v160_acceptance.md:6-7`（Gate Locked）、`:37-43`（五项待判定）、`:94-107`（解除闸门路线图）；`mp_release_safety_checklist.md:144-146`（Gate2/Gate3 ⇒ 不得宣判可发布）；`EVIDENCE_STANDARD.md:6-9,25-31,55-58,88-94,102-112,117-130`；`v160_acceptance_runbook.md:36-47,104-116`；`ZCODE_LIVE_ACCEPTANCE_TASK.md:4,7,35,94-105,107`；`landing_equivalence_static_proof.md:124-126,180-194,305-306,399-400`；`MP_SAFETY_REVIEW.md:171,491-499,530`；字节断言 `0x00655D38 = 89 44 24 28 A1 50 35 B7 00`、`0x0065719A = E8 91 93 00 00`（本批 `audit_bytes` OK）
- 影响面: **新增 §13**，不改动 §1–§12 任何结论；与 §0.1（PATCH-R4-02）、§0.3（PATCH-R4-03）、§9.4（G 矩阵状态，R3 域，建议同步）、§12.2（PATCH-R4-04）、§12.4（PATCH-R4-05）互指；**不影响 §11 速查表**（本节不含任何新 VA 定谳，仅引用既有 VA）；「## 目录」由 Lead 统一重建

### PATCH-R4-02 §0.1 补「验收三条硬红线 + 本文档『实测』术语口径 + 阈值指针」
- 目标锚点: L53 `   - **`[待实测]`**：涉及真机驱动底层响应、 DirectSound`（grep 实跑：hits=1 @53）
- 动作: INSERT_AFTER（插在 §0.1「2. 证据分级与标定公理」第 3 项 `[待实测]` 之后，仍属同一公理条目）
- 现状问题: §0.1 只定义 `[实证]/[推演]/[待实测]` 三档，**未吸收 v3 的三条硬红线**（崩溃零容忍 / 伪造零容忍 / 零生效禁止放行），也**未定义本文档内「实测」的语义** ⇒ 导致 `:472/:1372/:1512/:1710` 等处静态复算被读成真机实测（Q1）；且缺崩溃 EIP 模块归属判据入口（`0x54500000–0x545F0000` ⇒ 封锁闸门）与 09-28 阈值指针。
- 替换文本:
````markdown
   - **验收三条硬红线（v3，优先级高于本图谱任何静态结论；完整落点见 §13）**：
     1. **崩溃零容忍**：验收窗口 `[截图最早 mtime, 截图结束 + 10 分钟]` 内 `ra2youli/except.txt` 任一新增/更新 ⇒ **一票否决 FAIL**；**EIP 模块归属**：`0x54500000–0x545F0000` = `ra2render.dll` 注入区（判实施方代码缺陷并**封锁闸门**）、`0x00400000–0x008A0000` = `gamemd.exe` 主程序区、其他 = 外部系统/驱动；早于窗口下界的历史日志判**陈旧**、不误杀。
     2. **伪造零容忍**：禁止把**静态分析 / 编译通过 / 数学证明**标称为「实测 / 真机验证」；禁止以单色或占位图冒充游戏运行截图；同一批次截图 MD5 **必须互不相同**（碰撞 ⇒ 该步直接 FAIL，标注「疑似按键未生效 / 画面未实质刷新」）。
     3. **零生效禁止放行**：断言已开启的特性若末行遥测计数为 0（建筑剔除 / 弹道剔除 / 小地图灰化像素 / 灰雾格子）⇒ 一律标 **未生效 (UNVERIFIED)**，**绝对禁止**判 PASS。
   - **本文档内「实测」一词的语义（强制口径）**：本文全篇出现的「实测」**一律指对基线镜像 `ra2youli/gamemd.exe` 的静态字节复算（复扫）**，**与真机运行期观测无关**；新写入内容统一改写为「**静态复算**」。凡涉及进程运行、注入、对拍、截图、遥测的结论必须使用「**真机**」并标 `[待实测]`，未实跑者**严禁**写成「实测 / 已验证 / 已通过」（依据 `docs/re/EVIDENCE_STANDARD.md:8`）。
   - **阈值口径指针**：唯一色数旧口径 `≥2,000`（80×80 采样）/ `≥20,000`（全画面）**在本渲染路径不可达、已于 2026-09-28 作废**；生效口径 = **`≥600`（80×80 采样）/ `≥800`（全画面），且须与同场景既有已验收证据同量级**；采样色数 `= 1` 仍**直接判伪造**。判定表与两级过滤放闸流程见 **§13.3 / §13.4**。
````
- 证据: [实证] `EVIDENCE_STANDARD.md:6-9`（三红线）、`:25-31`（崩溃窗口 / EIP 归属 / 遥测生效性 / MD5 唯一性 / 唯一色数）、`:55-58`（退出码契约）、`:102-112`（两级过滤）、`:117-130`（阈值订正）；现网措辞 `ARCHITECTURE_ATLAS.md:472,1372,1512,1710`（grep 实跑）
- 影响面: **只新增**，不改动既有三档证据定义；影响 §0.1 方法论准则（新增红线与术语口径）；与 §13（新增）互指；**不影响 §11 速查表 / §12 契约**（零地址、零补丁字节）；对 R1/R2/R3 各节无改写要求（其 `[实证]` 标签语义不变）

### PATCH-R4-03 §0.3 补第 6 条「v1.6.0 验收闸门与 2026-09-28 阈值口径订正吸收」
- 目标锚点: L167 `   - **验收状态**：`python tools/verify_ancho`（grep 实跑：hits=1 @167）
- 动作: INSERT_AFTER（作为 §0.3 第 6 条，紧随第 5 条「G-01/G-02/G-08 落地状态复核」末行「验收状态」之后）
- 现状问题: §0.3 只吸收 Lead v20–v22 裁决与 G-01/G-02/G-08 的**落地状态**，**未吸收 09-28 阈值订正**（`≥2,000`/`≥20,000` 作废 ⇒ `≥600`/`≥800`），**未声明 v1.6.0 闸门状态**（未验收 Gate Locked）与「五项待判定」，读者极易把 323/323 PASS 误读为验收通过（Q2+Q3）。
- 替换文本:
````markdown
6. **v1.6.0 验收闸门与 2026-09-28 阈值口径订正吸收（2026-09-29 补 · R4 流）**：
   - **闸门现状**：v1.6.0 **维持未验收（Gate Locked）**，不得合入生产主干；真机五项功能全部「待判定 / UNVERIFIED」——缺真实截图（MD5 互异）、真实 `.SAV`、进程留痕与 2 秒遥测（`docs/re/v160_acceptance.md:6-7,37-43`）；
   - **阈值订正（产品决策级）**：唯一色数旧口径 `≥2,000`（80×80 采样）/ `≥20,000`（全画面）**不可达、已作废**；生效口径 = **`≥600` / `≥800`，且须与同场景既有已验收证据同量级**；采样色数 `= 1` 仍硬判伪造（`docs/re/EVIDENCE_STANDARD.md:117-130`）；
   - **放闸路径**：两级过滤（机械 `tools/verify_evidence.py` → 人工深度抽验）+ 7 项硬指标 + 性能类判据，见 **§13.4**；
   - **本图谱自身状态**：`python tools/verify_anchors.py` = 323/323 PASS 属**静态度量**；真机联机 ≥3 局双端逐帧 CRC 对拍 **未执行**（`[待实测]`，同第 5 条末行）；
   - ⚠️ **校验器冲突（P0，交 Lead 裁决）**：`tools/verify_evidence.py:345-348` 仍按旧 v2 阈值 `colors_80x80 < 1500 ⇒ FAIL`（文案仍写「建议 ≥ 2000」），与本条生效口径冲突，**放闸前必须先收口**，否则 §13.4 第一级过滤会误杀同量级合法证据（详见 §13.1 表末行）。
````
- 证据: [实证] `v160_acceptance.md:6-7,37-43,94-107`；`EVIDENCE_STANDARD.md:117-130`；本文档 `:167`（现网状态行）；`tools/verify_evidence.py:15,345-348`（本批实读：`colors_80x80 < 1500` ⇒ FAIL 分支仍在）
- 影响面: 影响 §0.3 裁决吸收（新增第 6 条，不改动第 1–5 条）；**影响产品决策读法**（v1.6.0 能否合入、阈值是否作废）；与 §9.4（G 矩阵落地状态）、§13（新增）、§12.2（PATCH-R4-04）互指；**不影响 §11 速查表**；对 R1/R2/R3 无改写要求

### PATCH-R4-04 §12.2 联机红线补强：Gate2/Gate3 = NO-GO + 混联禁令 + `pointer` 分支 VIOLATION
- 目标锚点: L1946 `> **〔勘误 ASM-FIX2-1 · 同源表述订正〕** 上框「局内唯一随机`（grep 实跑：hits=1 @1946）
- 动作: INSERT_AFTER（插在 §12.2 的 ASM-FIX2-1 块引之后、§12.3 之前）
- 现状问题: §12.2 只有「🔴 绝对红线 / 🟢 允许改造」两栏，**未声明联机放闸的 Gate 状态**（Gate2 未闭环、Gate3 未执行 ⇒ NO-GO）、**未写混联禁令**（M-10 类补丁改 `CellClass+0x134` 并进 `.SAV` ⇒ 严禁单端注入、与原版混联须整局不加载 DLL），也没有 `pointer` 键降级口径 ⇒ 该节极易被读成「联机已可放行 / 零风险」。
> **套用注意**：L1943 是代码围栏内的盒底线、**L1944 才是围栏闭合行**，故锚点取围栏之后的块引 L1946，INSERT_AFTER 后新内容落在 §12.2 与 §12.3 之间。
- 替换文本:
````markdown
> **〔验收前置补充 · 2026-09-29 · 必须与 §13.5 联读〕联机放闸与混联禁令**
> 1. **Gate 状态**：Gate1（R-01 `EnableMinimapFog` 默认 0 / R-02 联机强制 `position` 键 / R-03 联机强制 `TargetScanInterval=1`）**代码层已落地**；**Gate2**（G-03 `EnableThreatRetention`、G-06 `MpStateWrites`）**未闭环**；**Gate3**（真机混联 ≥10 分钟 / ≥5000 帧零 Out of Sync）**未执行** ⇒ **不得宣称「MP 可发布」**（`docs/re/mp_release_safety_checklist.md:79-88,144-146`）。
> 2. **混联禁令（红线）**：M-10 裂缝保护/间谍卫星门控类补丁改变 `CellClass+0x134`（`GapsCoveringThisCell`，属核心可序列化状态、进 `.SAV`）⇒ **严禁在联机环境中单端注入**；与原版客户端（未加载 DLL）联机时，本端必须**整局不加载 `ra2render.dll`**（`docs/re/landing_equivalence_static_proof.md:180-194`）。
> 3. **判定口径订正**：节流键 `unitHash = (uintptr_t)pThis >> 4` 的 VIOLATION 判定**仅对 `TargetScanKey=pointer` 分支成立**；默认 `position` 键（坐标空间哈希）下同源三项（#7/#8/#9）**降为 RISK（仍待真机对拍）**（`docs/re/MP_SAFETY_REVIEW.md:491-499`）。
> 4. **本节任何结论不得用于宣称「零风险 / 无 Desync」**；真机双端逐帧 CRC 对拍状态见 §13.1 / §13.2（U-3/U-5）。
````
- 证据: [实证] `mp_release_safety_checklist.md:79-88`（Go/No-Go 决策树）、`:144-146`（Gate2/Gate3 未闭环 ⇒ 不得宣判可发布）、`:126-130`（R-01/R-02/R-03 落点）；`landing_equivalence_static_proof.md:180-194`（OOS 分叉推演 + 严禁单端注入）、`:153-159,175-177`（`0x00568273/0x00577EC5/0x00577B60` 清零点，本批 `audit_bytes` 3/3 OK）；`MP_SAFETY_REVIEW.md:491-499`（判定降级口径）、`:530`（真机对拍未执行）；字节断言 `0x00508F8F = 74 65`、`0x00508F88 = 80 B8 A5 16 00 00 00`（本批 audit_bytes OK）
- 影响面: 影响 §12.2 联机红线（**新增补充块，不改动原两栏**）；**影响产品决策**（能否宣称 MP 可发布）；与 §9.4 G 矩阵（R3 域：建议同步把 G-03/G-06 标「未落地」并给 G-02 降级口径脚注）、§13.5 互指；**不影响 §11 速查表**（无新 VA 定谳）

### PATCH-R4-05 §12.4 回滚规范补「回滚后必须重验」
- 目标锚点: L1972 `   - 当调用 `RemoveVTableHooks` 或 DLL 卸载时，必`（grep 实跑：hits=1 @1972）
- 动作: INSERT_AFTER（在 §12.4「3. 卸载期」内、**G-07 规约条之前**新增一条）
- 现状问题: §12.4 只规定「逐字节无损写回 + G-07 TYPE 还原」，**未规定回滚后的验收动作**；按 v3 标准，回滚同样必须走两级过滤——否则「关闸后是否真的回到基线」无判据（遥测是否回落、崩溃窗口是否干净、机器码是否逐字节一致），存在「回滚了但仍残留补丁字节/私有状态」的盲区。
- 替换文本:
````markdown
   - **回滚后必须重验（2026-09-29 补充 · R4 流）**：`Remove` 完成 **≠** 验收通过。回滚后必须重跑**两级过滤**（§13.4）并逐项取证：① 目标地址机器码与原版基线**逐字节一致**（用 `tools/audit_bytes.py` 断言文件全 OK，含卸载后重读）；② 验收窗口内 `ra2youli/except.txt` 无新增/更新崩溃（崩溃零容忍）；③ 末行遥测计数回落到「未开启」基线（如 `EnableStarCraftFog=0` 时建筑/弹道/小地图三计数为 0 或对应基线值）；④ 已开启特性若断言开启而计数为 0 ⇒ 标 `UNVERIFIED`。依据 `docs/re/EVIDENCE_STANDARD.md:102-112`、`docs/re/v160_acceptance_runbook.md:104-116`。
````
- 证据: [推演]（由 v3 二级过滤 + 放闸 7 项指标对回滚场景的严格外推）；佐证 [实证] `EVIDENCE_STANDARD.md:102-112`、`v160_acceptance_runbook.md:104-116`、`mp_release_safety_checklist.md:68`（MP-G07 还原判据）、`landing_equivalence_static_proof.md:199-205`（G-07 TYPE 还原规格与偏移）
- 影响面: 影响 §12.4 补丁生命周期（新增第 3 条内子条）；与 §13.4 两级过滤互指；**不影响 §11 速查表 / §12.2 红线**；对 R1/R2/R3 无改写要求（其为各自补丁的 `[待实测]` 项，回滚重验属 Lead/实施方流程）

### PATCH-R4-06 术语订正：§2.3 ABI 实证块内 2 处「实测」→「静态复算」
- 目标锚点: L472 `  0x006DA945: 8B 4C 24 1C           mov `（grep 实跑：hits=1 @472）
- 动作: REPLACE_BLOCK（块范围 **L471–L473**，位于 §2.3 的三反引号 asm 围栏内；L471 为 `  ...` 省略行，原文保留）
- 现状问题: `:472`「…全镜像 0 命中；**实测**真实写入为…」、`:473`「…全镜像 0 命中；**实测**真序列…」——两处「实测」实为**静态全镜像复扫**，违反 `docs/re/EVIDENCE_STANDARD.md:8`「禁止把静态分析标称为实测」。**结论本身无误**（本批已复算：`0x006DA949 = 89 8C 83 E4 00 00 00`、`0x006DA950 = 8B 83 E0 00 00 00`、`0x006DA956 = 40`、`0x006DA957 = 89 83 E0 00 00 00`，4/4 OK），仅措辞须订正。
- 替换文本:
````markdown
  ...
  0x006DA945: 8B 4C 24 1C           mov  ecx, [esp + 0x1C]       ; 取 pCell〔勘误 ASM-FIX-5〕原记 `89 7C 83 E4`（`mov [ebx + eax*4 + 0xE4], edi`）全镜像 0 命中；**静态复算（全镜像复扫，非真机）**真实写入为 0x006DA949: 89 8C 83 E4 00 00 00（`mov [ebx + eax*4 + 0xE4], ecx`）
  0x006DA957: 89 83 E0 00 00 00     mov  [ebx + 0xE0], eax       ; VisibleCellCount = eax〔勘误 ASM-FIX-5〕原记 `FF 43 E0`（`inc dword ptr [ebx + 0xE0]`）全镜像 0 命中；**静态复算（全镜像复扫，非真机）**真序列 0x006DA950: 8B 83 E0 00 00 00 → 0x006DA956: 40（`inc eax`）→ 本行
````
- 证据: [实证] 本批 `tools/audit_bytes.py out/re_work/atlas_rev/R4/claims_R4.txt` 32/32 OK（含上述 4 条）；规则 `EVIDENCE_STANDARD.md:8`；来源 `ARCHITECTURE_ATLAS.md:472-473`
- 影响面: 仅 §2.3 措辞；**不影响 §11 速查表 / §12 契约 / §0 准则**（VA、字节、结论均不变）；与 PATCH-R4-02 的术语口径一致

### PATCH-R4-07 术语订正：§8.3 顶层帧主循环 asm 块内 2 处「实测」→「静态复算」
- 目标锚点: L1372 `  0x0048CE8F: 84 C0             test al,`（grep 实跑：hits=1 @1372）
- 动作: REPLACE_BLOCK（块范围 **L1370–L1379**，§8.3 的三反引号 asm 围栏整体）
- 现状问题: `:1372`/`:1375` 的「实测 `84 C0`」为静态全镜像复扫结果（本批复算 2/2 OK：`0x0048CE8F = 84 C0`、`0x0048CE98 = 84 C0`），措辞违反 v3 红线 2（静态 ≠ 实测）。
- 替换文本:
````markdown
  ```asm
  0x0048CE8A: E8 D1 04 0D 00     call 0x0055D360              ; call MainLogicFrame
  0x0048CE8F: 84 C0             test al, al〔勘误 ASM-FIX-6〕原记 `85 C0`（`test eax, eax`）**静态复算（全镜像复扫，非真机）** `84 C0`（`test al, al`；该 2 字节模式全镜像 400+ 命中，非走锚）
  0x0048CE91: 74 09             je   0x0048CE9C
  0x0048CE93: E8 38 01 0D 00     call 0x0055CFD0              ; 帧采样
  0x0048CE98: 84 C0             test al, al〔勘误 ASM-FIX-6〕原记 `85 C0`（`test eax, eax`）**静态复算（全镜像复扫，非真机）** `84 C0`（`test al, al`）
  0x0048CE9A: 75 0E             jne  0x0048CEAA              ; 退出主循环
  0x0048CE9C: E8 0F FA FF FF     call 0x0048C8B0
  0x0048CEA8: 74 E0             je   0x0048CE8A              ; 循环回边！
  ```
````
- 证据: [实证] 本批 `audit_bytes` 断言 `0x0048CE8F = 84 C0`、`0x0048CE98 = 84 C0` 全 OK；规则 `EVIDENCE_STANDARD.md:8`；来源 `ARCHITECTURE_ATLAS.md:1372,1375`
- 影响面: 仅 §8.3 措辞与围栏内注释；**VA/字节/结论 0 变化**（仍 `84 C0`，仍 `call 0x0055D360` 主循环结构）；**不影响 §11 / §12 / §0**；与 PATCH-R4-02 术语口径一致

### PATCH-R4-08 术语订正：§9.2 帧 CRC asm 块内 3 处「实测」→「静态复算」
- 目标锚点: L1512 `   0x0064DACE: A1 EC 3D A8 00     mov  e`（grep 实跑：hits=1 @1512）
- 动作: REPLACE_BLOCK（块范围 **L1511–L1516**，§9.2 的三反引号 asm 围栏整体）
- 现状问题: 3 处「实测」（`:1512` 实测 `A1 EC 3D A8 00`；`:1513` 实测不符；`:1515` 实测不符）均指**静态全镜像复扫**（本批复算 `0x0064DACE = A1 EC 3D A8 00` OK），措辞违反 v3 红线 2。
- 替换文本:
````markdown
   ```asm
   0x0064DACE: A1 EC 3D A8 00     mov  eax, [0x00A83DEC]       ; 循环基址〔勘误 ASM-FIX-8〕原记 A1 30 B2 A8 00（`mov eax, [0x00A8B230]` = ScenarioClass::Instance）**静态复算（全镜像复扫，非真机）** A1 EC 3D A8 00（`mov eax, [0x00A83DEC]`）；原记锚点与字节双不符
   0x0064DAD3: 8B 04 B0           mov  eax, [eax + esi*4]      ; 按索引取表项〔勘误 ASM-FIX-8〕原记 8D 88 18 02 00 00（`lea ecx, [eax + 0x218]`）**静态复算**不符
   0x0064DAD6: 8D 88 9C 00 00 00  lea  ecx, [eax + 0x9C]       ; 取对象基址〔勘误 ASM-FIX-8〕原记锚点 0x0064DAD9 与字节串 E8 52 1A F6 FF（`call 0x005AF530`）**全镜像 0 命中**；该「每逻辑帧固定消费 1 次 RNG」的调用点在此 VA 不成立 ⇒ 来源构建不明 · 待重新锚定
   0x0064DADC: 8B B8 9C 00 00 00  mov  edi, [eax + 0x9C]       ; 取校验对象〔勘误 ASM-FIX-8〕原记 03 F8（`add edi, eax`）**静态复算**不符
   ```
````
- 证据: [实证] 本批 `audit_bytes` 断言 `0x0064DACE = A1 EC 3D A8 00` OK（claims_R4.txt）；规则 `EVIDENCE_STANDARD.md:8`；来源 `ARCHITECTURE_ATLAS.md:1512,1513,1515`
- 影响面: 仅 §9.2 措辞；VA/字节/结论 0 变化；**不影响 §11 / §12**。
- **附带项（不属本补丁范围，登记为 §13.2 U-6 与 [3]-E2）**：同节 `:1517` 首句「**全游戏局内唯一共享 RNG 仅此一家**，每逻辑帧固定消费 1 次」与紧随其后的勘误（`:1519-1556`：帧 CRC 路径每逻辑帧 **2 次**、全 `.text` 另有约 **83** 个候选消费点）**自相矛盾**，该行未加删除线/加注 ⇒ 建议 Lead 就地加注（本批未改，避免与 R3/其他流的 §9 补丁冲突）

### PATCH-R4-09 ERRATUM：§10.3 首句「实测提取」→「静态复算提取」
- 目标锚点: L1710 `从全镜像 `push imm; call _new` 及 `v[12] GetS`（grep 实跑：hits=1 @1710）
- 动作: ERRATUM（单行替换）
- 现状问题: 「…**实测**提取的**静态**尺寸频次…」——「实测」修饰静态统计，措辞自相冲突（本意即静态全镜像统计），违反 `EVIDENCE_STANDARD.md:8`；且与 PATCH-R4-02 术语口径不一致。
- 替换文本:
````markdown
从全镜像 `push imm; call _new` 与 `v[12] GetSize` 的**静态复算**（全镜像复扫，非真机）提取的静态尺寸频次与对象映射表：
````
- 证据: [实证] 原文 `ARCHITECTURE_ATLAS.md:1710`；规则 `EVIDENCE_STANDARD.md:8`；本节标题已含 `[实证]` 标签（静态标签语义正确，无需改动）
- 影响面: 仅 §10.3 首句措辞；表格数据与结论 0 变化；**不影响 §11 速查表 / §12 契约 / §10.1-10.4 其余结论**

---

## 2. 覆盖度自证（来源小节 → 补丁归属）

| 来源文档 §小节 | 命中归属 | 说明 / 「不入 atlas」理由 |
|:---|:---|:---|
| `EVIDENCE_STANDARD.md` 硬性红线 :6-9 | PATCH-R4-02（§0.1）+ §13.1 | 三条红线 + 崩溃零容忍直接入准则层 |
| `EVIDENCE_STANDARD.md` §一 标准演进 :13-17 | PATCH-R4-02 / §13.3 | 只收**当前生效口径**；v1/v2 历史沿革细节**不入 atlas**（沿革属该文档自身；且 v2 阈值已被 09-28 推翻） |
| `EVIDENCE_STANDARD.md` §二 判据总表 9 条 :21-33 | §13.1 / §13.3 / §13.4 + PATCH-R4-02 | 崩溃窗口、EIP 段归属、遥测生效性、MD5 唯一性、体量、色数、时间线、存档魔数全部落到 §13；细则表**不整表复制**（避免 atlas 与源文档双维护） |
| `EVIDENCE_STANDARD.md` §三 校验器 CLI/退出码 :37-58 | §13.4 | 命令与退出码契约入 §13.4 第 1 条 |
| `EVIDENCE_STANDARD.md` §四 三批回跑自证 :61-95 | §13.2（U-2） | 仅收录「零生效 ⇒ UNVERIFIED」与崩溃会话结论；三批报告路径明细**不入 atlas**（一次性自证痕迹，随 `out/re_work/evidence_check/` 存在） |
| `EVIDENCE_STANDARD.md` §五 两级过滤 + 工具边界 :99-112 | §13.4（第 2/3 条） | 两级过滤为放闸唯一路径，必须入 atlas |
| `EVIDENCE_STANDARD.md` 附·口径订正 :117-130 | §13.3 + §0.1/§0.3 指针 | 生效阈值 `≥600/≥800` + `=1` 判伪造 |
| `v160_acceptance.md` §一 驳回原因 :12-27 | §13.2（U-1） | 4 张同哈希单色图（MD5 全同 `9BA587…`、色数=1）作为**反例**入档 |
| `v160_acceptance.md` §二 状态矩阵 + DA4-4 :31-51 | §13.1 / §13.2 | 五项「待判定」入 U-1；雷达落点 `0x006574C3 → 0x00655D38` 订正属 §2.6（R2 域，已由 DA1/DA4 就地订正）⇒ **本条不重复出补丁** |
| `v160_acceptance.md` §三 验收准则 :55-88 | §13.4（+ 阈值见 §13.3） | 含截图体量/哈希互异/存档/时间线要求 |
| `v160_acceptance.md` §四 综合判定与放闸路线图 :92-109 | §13.1（GATE-v1.6.0 行） | 「维持未验收 + 三方解锁链路」压缩为一行状态 + 依据锚点 |
| `v160_acceptance_runbook.md` §一 CLI 规程 :11-30 | §13.4 第 1 条 | 命令模板 |
| `v160_acceptance_runbook.md` §二 判定总表 :34-46 | §13.3 / §13.4 | 与 v3 判据总表同源；旧 `≥2,000`/`≥1,500` 行已在 §13.3 列为**作废口径** |
| `v160_acceptance_runbook.md` §三 五大失败模式 :50-96 | **不入 atlas** | 属**操作排障手册**（面向执行人查询表），非架构契约；atlas §13.4 只保留入口命令与驳回规则 |
| `v160_acceptance_runbook.md` §四 放闸 7 项硬指标 :100-116 | §13.4 第 4 条 | 逐项收录（7 项） |
| `v160_static_contract.md` §一~§五 :10-218 | **不入 atlas** | 属 §2/§9 域静态契约，已由 R1/R2/R3 各自覆盖；本批只取其纪律声明 `:6`「绝不冒称真机实测」入 PATCH-R4-02 |
| `v160_static_contract.md` §六 效力边界 :222-230 | PATCH-R4-02（术语口径） | 「静态核验 ≠ 真机表现」的原始表述来源 |
| `ZCODE_LIVE_ACCEPTANCE_TASK.md` 任务卡 Q1–Q6 :11-71 | §13.1（ZC-1 行）/ §13.2（U-3/U-5） | 真机挂起与 Q2 双机 LAN 前提；Q3 四项功能细节**不入 atlas**（属 §2 域） |
| `ZCODE_LIVE_ACCEPTANCE_TASK.md` Lead 备注 :75-79 | §13.1 | 「通过后登记 [v1.6.9] 并解除闸门」流程 |
| `ZCODE_LIVE_ACCEPTANCE_TASK.md` 附 harness/唯一合法形态 :82-107 | §13.4 第 5 条 | 性能达标唯一合法形态 + PROTOCOL §12 防误用条款 |
| `landing_equivalence_static_proof.md` §0 裁决矩阵 :16-25 | PATCH-R4-04（M-10 红线部分） | 「严禁混端联机」入 §12.2 补充块；H-D5 `movzx` 修正、CRT 池、音频、L4 等**不入本批**（分别属 §9.3/§6/§10/§2 域，R1/R2/R3 覆盖） |
| `landing_equivalence_static_proof.md` §1 证据标准 :29-34 | PATCH-R4-02 | 与 v3 同源的 [实证]/[推演]/[待实测] 定义 |
| `landing_equivalence_static_proof.md` §2.3/§5.3/§7.3 不可静态判定项 :120-126,301-306,395-400 | §13.2（U-7） | 全部登记为 [待实测]，附可执行判据 |
| `landing_equivalence_static_proof.md` §8 放行清单 :407-418 | **不入 atlas** | 落地准入结论已由 §0.3 第 4/5 条与 §9.4 承载；重复收录会造成双维护 |
| `mp_release_safety_checklist.md` §一 四项裁定 :15-24 | §0.3 第 5 条（既有）+ §13.5 | 已完成收录，本批只补 Gate 状态 |
| `mp_release_safety_checklist.md` §二 W1–W6 降级矩阵 :28-54 | **不入 atlas** | 与 §9.4 G-01…G-10 矩阵同构，G 矩阵为唯一口径；为避免两套编号并存不再收录 |
| `mp_release_safety_checklist.md` §三 逐条核验表 :58-73 | §13.2（U-4）+ §13.5 | G-03/04/06/07/10「未落地」入 U-4；已过时的「现网状态」列不再复制 |
| `mp_release_safety_checklist.md` §四 Go/No-Go 决策树 :77-88 | §13.1（GATE-MP 行）+ §13.5 | Gate1/2/3 读法 |
| `mp_release_safety_checklist.md` §五 ZCode 落地指南 :92-111 | **不入 atlas** | 属已落地的历史建议（R-01/R-02/R-04 已实现），atlas 只留生效口径 |
| `mp_release_safety_checklist.md` §六 闭环状态同步 :115-146 | §13.5 + PATCH-R4-04 | 含「不得据本节宣判 MP 可发布」（`:146`） |
| `MP_SAFETY_REVIEW.md` §0 摘要 :15-23 | §13.5 + [3]-E6 | VIOLATION×3 / RISK×4 的**收口后口径**见 §9.2 更正；atlas 不复制旧判定 |
| `MP_SAFETY_REVIEW.md` §1 红线基准 :27-37 | PATCH-R4-04 第 2/3 条 | 可序列化状态/枚举序/帧 CRC 红线与混联禁令 |
| `MP_SAFETY_REVIEW.md` §2.x 逐条复核 :41-290 | **不入 atlas** | 21 Hook + S1–S4 逐条表属 §1/§2/§9/§10/§12 域，由 R1/R2/R3 与 §9.4 承载 |
| `MP_SAFETY_REVIEW.md` §3 判定推导 :296-307 | §13.5 第 3 条 | `pointer` 分支 VIOLATION / 默认键降 RISK 的口径 |
| `MP_SAFETY_REVIEW.md` §4 ini 推荐集 :324-391 | **不入 atlas** | 配置建议属 `ra2render.ini` 及用户文档域 |
| `MP_SAFETY_REVIEW.md` §5 修复优先级 :398-407 | §13.2（U-4）+ §13.5 | P0/P1/P2 与 G-0x 缺口映射 |
| `MP_SAFETY_REVIEW.md` §6 遗留与边界 :411-417 | §13.2（U-5/U-7） | 真机对拍未执行、不可静态判定项 |
| `MP_SAFETY_REVIEW.md` §7 产出物 :421-441 | **不入 atlas** | 任务产出清单，非架构契约 |
| `MP_SAFETY_REVIEW.md` §8/§9/§10 勘误 :445-559 | §13.5 + [3]-E5/E6 | 判级更正（#7/#8/#9 降 RISK）；E1 原版语义（FOG.SHP alpha 插值）属 §2.8/§2.4（R2 域）⇒ 转交 |
| `tools/verify_evidence.py` :15,345-348（**非来源文档，属证据链实测对象**） | §13.1 表末行 + [3]-E1 + [9]-D1 | 校验器旧阈值与 09-28 口径冲突（P0） |
| 本文档 `ARCHITECTURE_ATLAS.md` §2.4/§2.5「50% 半暗」表述 | **不入本批，转 R2/Lead** | 与 FOG-ERRATA E1「引擎原版 = FOG.SHP alpha 插值混色，非固定 50% 减法」存在口径耦合风险；属 fog 语义域，避免与本流冲突 ⇒ 见 [3]-E5 |

---

## 3. 十节回执

```text
[META]
task=task-4（R4 流 · 验收/证据标准 · atlas 合规审计）
executor=DSH 子代理 / Agent Teams 成员 atlas-r4-acceptance（provider=spawn, context=fresh, model=deepseek-v4.1-flash）
elapsed≈60 分钟（会话墙钟估算，未精确计时；含 7 份来源文档只读 + 全篇 grep 扫描 + 2 次门禁实跑）
mode=read-only 对既有文件/二进制；唯一写盘 = docs/re/atlas_rev/R4_acceptance_standard.md、out/re_work/atlas_rev/R4/**
scope_declared=docs/re/atlas_rev/R4_acceptance_standard.md、out/re_work/atlas_rev/R4/claims_R4.txt、out/re_work/atlas_rev/R4/**
```

### [0] 结论摘要（≤5 行）
1. **Q1 成立**：atlas 有 **8 处**把静态字节复算写成「实测」（`:472,473,1372,1375,1512,1513,1515,1710`），违反 `EVIDENCE_STANDARD.md:8` 伪造零容忍；**无一处真机伪造**，属术语违规 ⇒ 4 个 ERRATUM/REPLACE 补丁块（PATCH-R4-06…09）。
2. **Q2 成立（未收录遗漏）**：atlas 全文 **0 命中**旧唯一色数阈值 ⇒ 需以 **§13.3** 收录生效口径 `≥600`（80×80 采样）/ `≥800`（全画面），并明确 `≥2,000`/`≥20,000` 作废。
3. **Q3 成立**：atlas **完全没有** v160 验收状态声明（`v160/UNVERIFIED/闸门/verify_evidence/except.txt` 全 0 命中）⇒ 新增 **§13 验收与闸门状态**（6 小节：闸门表 / UNVERIFIED 清单 / 阈值新口径 / 两级过滤与 7 项硬指标 / 联机放闸前置 / 术语口径）。
4. **准则层缺口**：§0.1 未吸收 v3 三条硬红线、§0.3 未吸收 09-28 阈值订正、§12.2 未声明 Gate2/Gate3 NO-GO 与混联禁令、§12.4 未规定「回滚后必须重验」⇒ PATCH-R4-02…05。
5. **最大风险（P0）**：`tools/verify_evidence.py:345-348` 仍按**旧阈值** `colors_80x80 < 1500 ⇒ FAIL` 判定 —— 放闸时第一级机械过滤会**误杀**同量级合法证据（ZC-9B 实测 841–1046），必须与 09-28 订正同步收口（见 [3]-E1 / [9]-D1）。

### [1] 逐条必答项结论表

| # | 问题 | 结论 | 证据等级 | 证据锚点 |
|:--|:---|:---|:---|:---|
| 1 | atlas 是否把静态分析写成「实测/真机」？ | 是，8 处（`实测`=静态复算，误读风险）；无「真机」滥用（`真机` 4 处均为**否定式**「未执行 / 保持挂起」） | [实证] | `ARCHITECTURE_ATLAS.md:472,473,1372,1375,1512,1513,1515,1710`（grep 8 命中）；`真机` 于 `:11,53,167,1556` |
| 2 | 是否引用已作废阈值 `≥2000`？ | 否，0 命中 ⇒ 未收录遗漏；须新增收录 | [实证] | grep `2,000`/`20,000`/`色数` = **全 0**；`2000` 4 命中均为非色彩语境：`:49`（`0x00812000` 段基址）+ `:572,657,658`（`0x7D0=2000` 寻路扩展节点上限） |
| 3 | 是否缺 v160 验收状态显式声明？ | 缺；全文 0 命中五关键词 | [实证] | grep `v160/UNVERIFIED/闸门/verify_evidence/except.txt` = 全 0；仅有 `:167` 一行验收状态 |
| 4 | §0.1 是否吸收 v3 三条硬红线？ | 未吸收（仅三档证据分级） | [实证] | `EVIDENCE_STANDARD.md:6-9,25-27` vs `ARCHITECTURE_ATLAS.md:50-53` |
| 5 | §0.3 是否吸收 09-28 阈值订正？ | 未吸收（第 1–5 条无阈值内容） | [实证] | `EVIDENCE_STANDARD.md:117-130` vs `ARCHITECTURE_ATLAS.md:138-167` |
| 6 | §12.2 是否声明 MP 放闸 Gate 状态与混联禁令？ | 未声明 | [实证] | `mp_release_safety_checklist.md:79-88,144-146`；`landing_equivalence_static_proof.md:180-194` vs `ARCHITECTURE_ATLAS.md:1918-1946` |
| 7 | §12.4 是否规定回滚后重验？ | 未规定（只有写回与 G-07 还原） | [推演] | `ARCHITECTURE_ATLAS.md:1961-1973`；对照 `EVIDENCE_STANDARD.md:102-112` |
| 8 | atlas 是否已声明「验收期间不启动游戏」纪律？ | 已声明且正确（`:11`「真机与游戏在研制期间严格保持挂起」） | [实证] | `ARCHITECTURE_ATLAS.md:11,53`；`landing_equivalence_static_proof.md:10` |
| 9 | 校验器是否已按 09-28 新阈值执行？ | **否**（仍 `<1500 ⇒ FAIL`，文案「建议 ≥ 2000」）⇒ P0 冲突 | [实证] | `tools/verify_evidence.py:15,345-348`（本批实读源码）；`EVIDENCE_STANDARD.md:117-130` |
| 10 | atlas §9.2 RNG 消费点结论是否闭环？ | 未闭环且自相矛盾（`:1517` vs `:1519-1556`） | [实证] | `ARCHITECTURE_ATLAS.md:1517`、`:1553`（2 次）、`:1556`（约 83 候选点） |
| 11 | 本报告结论是否触及 §11 速查表？ | 否（9 个补丁块零新增 VA 定谳；§11 不受影响） | [推演] | 见各补丁块「影响面」字段 |
| 12 | 门禁是否全绿？ | 是：`verify_anchors` 323/323 PASS；`audit_bytes` 32/32 OK | [实证] | [6] 原文 |

### [2] 关键证据块（VA / FileOffset / 原始字节 / Capstone 反汇编 / xref）

> 机器可读断言全量 **32 条**见 `out/re_work/atlas_rev/R4/claims_R4.txt`（`tools/audit_bytes.py` 32/32 OK，原文见 [6]）。下表为支撑本批结论的代表性 12 条（`FileOffset = VA − 0x400000`，仅 `.text/.rdata/.data` 段成立）。

| VA | FileOffset | 原始字节 | Capstone 反汇编（本批实读） | 用途 / xref |
|:---|:---|:---|:---|:---|
| `0x0065719A` | `0x0025719A` | `E8 91 93 00 00` | `call 0x00660530` | 雷达跳帧抑制 5B 等长点（放闸第①项之一） |
| `0x00655D38` | `0x00255D38` | `89 44 24 28 A1 50 35 B7 00` | `mov dword ptr [esp + 0x28], eax` | 路线 A 9B 补丁覆盖区起点（放闸第①项） |
| `0x00660530` | `0x00260530` | `A1 B8 4D B0 00 85 C0 0F 94 C0 C3` | `mov eax,[0xB04DB8]; test eax,eax; sete al; ret` | 原版跳帧判定函数体（被 0x0065719A 调用） |
| `0x006D3D99` | `0x002D3D99` | `0F 8D 98 00 00 00` | `jge 0x006D3E37` | L4 双模切换点（`force-full`/vision-dirty 基线） |
| `0x006D3D10` | `0x002D3D10` | `81 EC F4 00 00 00` | `sub esp, 0xF4` | `TacticalClass::Render` 真实入口（U3-P1 订正后） |
| `0x005865E0` | `0x001865E0` | `32 C0 C2 04 00` | `xor al, al; ret 4` | 原版 `IsCellShrouded` 恒 0 空桩（粒子迷雾裁剪瘫痪根因） |
| `0x00508F8F` | `0x00108F8F` | `74 65` | `je 0x00508FF6` | SpySat 全图开图门控改写点（M-10） |
| `0x00568273` | `0x00168273` | `89 99 34 01 00 00` | `mov dword ptr [ecx + 0x134], ebx` | Gap1 引用计数清零（M-10 NOP 点，进 `.SAV` ⇒ 混联禁令依据） |
| `0x00577B60` | `0x00177B60` | `89 98 34 01 00 00` | `mov dword ptr [eax + 0x134], ebx` | Gap2/Gap3（同源） |
| `0x0075092E` | `0x0035092E` | `33 C0 59 C2 08 00` | `xor eax,eax; pop ecx; ret 8` | `PlayGlobal` 早退 ABI 契约（音频条件等效） |
| `0x007C8E17` | `0x003C8E17` | `6A 01 FF 74 24 08 E8 20 06 00 00 59 59 C3` | `push 1; push [esp+8]; call 0x007C9442; pop ecx; pop ecx; ret` | `operator new` 14B thunk（ASM-FIX-33 定界） |
| `0x00647260` | `0x00247260` | `A0 F8 D5 A8 00` | `mov al, byte ptr [0xA8D5F8]` | `MpActive()` 一级主判定（bit1）的原始指令证据 |

- **xref 说明**：上表 12 条中，`0x0065719A → 0x00660530`、`0x00655D38`（位于 `Plot_Cell` `0x00655C50` 内）、`0x00647260 → [0xA8D5F8]` 三处为**调用/数据引用**关系，已由源文档反汇编摘录与 atlas §2.6/§9.4 交叉印证；其余为**站点自身字节**。
- **本批未做**：未对 atlas 全书做 VA 复算（不在本流任务面；Lead 侧另有 `atlas_va_crosscheck`）；本批字节断言只覆盖「放闸判据 + 闸门状态 + 术语订正」所引锚点。

### [3] 勘误（对既有文档/结论的更正；**单列，不藏在正文**）

| 编号 | 目标文件:行号 | 改前原文（逐字） | 改后文本 | 理由 | 影响面 |
|:---|:---|:---|:---|:---|:---|
| **E1（P0）** | `tools/verify_evidence.py:345-348`（另 `:15` 文档串） | `if colors_80x80 < 1500:` / `issues.append(f"战场画面色数不足: {colors_80x80} (标准 v2 建议 ≥ 2000)")` / `verdict = "FAIL"` | 按 09-28 生效口径改为 **`< 600 ⇒ FAIL`**（并给「同量级」提示：与同场景既有已验收证据比对）；文案改为「新口径 ≥600（80×80 采样）/ ≥800（全画面）；=1 判伪造」；:15 文档串同步 | 旧 v2 阈值已被 Lead 2026-09-28 裁定**不可达、作废**；现网执行旧阈值会**误杀**同量级合法证据（ZC-9B 实测 841–1046 < 1500）⇒ 第一级机械过滤失效 | **影响产品决策/放闸**；该文件**不在本批写作用域** ⇒ 交 Lead 派工（[9]-D1） |
| **E2（P1）** | `docs/re/ARCHITECTURE_ATLAS.md:1517` | `**全游戏局内唯一共享 RNG 仅此一家**，每逻辑帧固定消费 1 次。` | 加删除线并加注：「**【原记·已推翻】** 消费点**不唯一**（全 `.text` 约 **83** 个候选消费点），且帧 CRC 路径每逻辑帧 **2 次** —— 见本行下方 ASM-FIX2-1 勘误 `:1519-1556`」 | 同节既有勘误已推翻该句，但首句未加删除线/加注，读者先读到错误结论 | 影响 §9.2 证据强度读法；属 R3/主写者域 ⇒ 转交（[9]-D2） |
| **E3（P1）** | `docs/re/EVIDENCE_STANDARD.md:31`（判据总表第 7 行） | `战场类：**建议 ≥ 2,000 种唯一色**【勘误↓见文末】…战场画面色数 < 1,500 判 **FAIL**` | 保留原文（文档既定策略：原文字保留不删字），但在该行**就地加脚注指针**：「**生效口径见本文末〈附·口径订正〉：≥600（80×80）/ ≥800（全画面）；<1,500 判 FAIL 一栏失效**」 | 表内旧阈值与文末订正**同文冲突**，且**校验器实现恰取自该表**（见 E1）⇒ 必须显式指向 | 影响放闸判据读法与校验器实现；该文件不在本批作用域 ⇒ 转交（[9]-D3） |
| **E4（P2）** | `docs/re/v160_acceptance_runbook.md:42` / `:44` | `“单色退化”…唯一色数 ≥ 200  PASS 条件` / `“画面色数”…战场建议 ≥ 2,000 种色彩…战场色数 < 1,500（疑似假战场）FAIL` | 同 E3：行内加订正指针（≥600/≥800 生效；`=1` 判伪造），并把 `≥200` 与 `≥2,000` 两级不一致标注为「历史口径」 | 同一表内两级阈值自相矛盾，且均被 09-28 订正覆盖 | 影响验收执行人判读；该文件不在本批作用域 ⇒ 转交（[9]-D3） |
| **E5（P1，**转 R2/Lead**）** | `docs/re/ARCHITECTURE_ATLAS.md:497` / `:516`（另 `:400` 拓扑节点） | `地表呈现 50% 半暗灰度…敌方建筑保留 50% 残影` / `未直视但已探索时，绘制 50% 半暗残影` | 建议加注：「『50%』为**我方桩 `s=256` 的等效观感**；引擎原版对应路径为 **FOG.SHP 逐像素 alpha 插值混色（无固定 50% 半化算子）**（FOG-ERRATA E1）」 | `MP_SAFETY_REVIEW.md:542-552` 已定谳原版无固定 50% 算子；atlas 该处若被读成「引擎原生 50%」即与 E1 冲突 | 影响视觉语义与关闸验收判据（关闸出口证据）；**属 fog 语义域（R2/主写者）** ⇒ 本批不改，转交裁决 |
| **E6（P2，**转 R3/Lead**）** | `docs/re/ARCHITECTURE_ATLAS.md:1580-1597`（§9.4 G 矩阵） | 表中 G-03/G-04/G-06/G-07 未标注落地状态；G-02 行未标「默认键下 #7/#8/#9 降 RISK」 | 建议：G 矩阵表加「落地状态」列（G-01/G-02/G-08 = 已落地；G-03/G-04/G-06/G-07/G-10 = 未落地）+ G-02 行脚注（`pointer` 分支 VIOLATION / 默认 `position` 键降 RISK，依据 `MP_SAFETY_REVIEW.md:491-499`） | §9.4 是联机门控的唯一速查口径，缺状态列会被误读为「全部已实现」 | 影响发布门禁读法；属 R3 域 ⇒ 本批不改，转交 |
| **E7（P2，**元数据**）** | 本报告 [5] 节 / 任务卡 | — | 基线二进制 `gamemd.exe` 本批实测 mtime = **2026-09-25**（非「09-26/09-27 快照」），MD5 与任务卡一致 | 声明快照时点（AGENT_DELIVERY_FORMAT §B-5） | 仅影响证据时点表述 |

> 无勘误的领域不列；**本批未直接修改任何既有文档或工具**（见 [5]）。

### [4] 未闭环清单

| # | 缺口 | 为何无法静态闭环 | 下一步取证方法（可直接执行） | 阻塞级别 |
|:--|:---|:---|:---|:---|
| N1 | v1.6.0 五项功能真机表现（U-1/U-2） | 需真机运行 + 截图/存档/遥测；本批**禁跑游戏/禁注入** | 按 `ZCODE_LIVE_ACCEPTANCE_TASK.md` Q3 执行；证据落 `out/re_work/zcode_live/evidence/**`；跑 `python tools/verify_evidence.py out/loadbench/shots/v160_real --log ra2youli/ra2render.log --except-file ra2youli/except.txt --sav-dir ra2youli`，须退出码 0 | **P0** |
| N2 | 崩溃窗口与 EIP 归属（U-3） | 需对局中复现/排除 `0x5450202F`；静态只能给归属规则 | 连续 3 局对局，记录 `ra2youli/except.txt` mtime 是否 > 截图最早 mtime；若命中则解析 `Eip` 是否 ∈ `0x54500000–0x545F0000` | **P0** |
| N3 | 联机 Gate2/Gate3（U-4/U-5） | 需 ≥2 玩家双机 LAN + ≥5000 帧双端 CRC 对拍；Q2 已证遭遇战**不置位** MP 位 | 双机 LAN 开局（DLL 两端一致 / 或整局不加载 DLL 的对照组），用 H-D5 镜像环导出 `g_MirrorRing` 逐帧比对 ≥5000 帧无 `TXT_OUT_OF_SYNC` | **P1** |
| N4 | 阈值「同量级」无机器化判据（E1 连带） | 需先收口 `verify_evidence.py` 阈值与「同场景既有已验收证据」比对逻辑 | 修 `:345-348` 为 `<600 ⇒ FAIL`，并新增「与 `out/loadbench/shots` 内既有已验收同场景样本中位数同量级」检查；改后自跑三批历史证据回归（须仍正确 FAIL 单色图 batching） | **P0** |
| N5 | atlas §9.2 首句矛盾（E2）与 §9.4 状态列（E6） | 属其他流写作用域，Lead 统一套用 | Lead 就地加注（无需新证据，锚点已在 [3]） | **P1** |
| N6 | §13 新节与 TOC 同步 | 本批按 Lead 指示不提交 TOC 补丁 | Lead 重建「## 目录」并加入 §13 一行 | **P2** |

### [5] 写作用域合规声明

**本批新增/改动文件（全部在授权作用域内）**：见 [8] 表（路径 + 字节数 + 起止时间）。
**未触碰清单（逐项声明）**：`docs/re/ARCHITECTURE_ATLAS.md`（**只读，仅输出补丁块**）、其他 `docs/re/atlas_rev/*.md`、`out/re_work/atlas_rev/R1|R2|R3|lead/**`、`ra2render/**`、`ra2youli/**`、`REVERSE_ENGINEERING_AND_PATCHES.md`、全部既有 `docs/re/*.md`、`tools/**`（**含 E1 所述 `verify_evidence.py`：只读，未修改**）。
**目标二进制只读证明**：`ra2youli/gamemd.exe` = 4,825,360 B，MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`（本批实读；与任务卡一致）；未启动游戏进程、未注入、未挂调试器、未改任何字节。

### [6] 门禁实跑输出（原文粘贴，未做任何概述）

**门禁 1**：`python tools\verify_anchors.py`（退出码 0）
```text
===================================================================================================================
  RA2/YR 二进制决定性锚点自动化回归测试套件 (verify_anchors.py)
===================================================================================================================
目标文件 : D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe (大小: 4,825,360 字节, ImageBase: 0x400000)
断言文件 : D:\Project\ra2-campaign-forge\docs\re\anchor_claims.txt
反汇编器 : Capstone x86-32 引擎已就绪
-------------------------------------------------------------------------------------------------------------------
[基线完整性审计]
  [PASS] .text 原始段哈希: c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738 (口径: raw(SizeOfRawData=0x3E0000))
  [INFO] PE头特征判定 : RA2OPT_PERF_APPLIED (0xAE=0x20, Stack=4MB, .text未变) (DllChar: 0x20, StackReserve: 0x400000)
  [PASS] .detour 原生签名: 40 00 00 00 44 74 72 00 ('@\0\0\0Dtr\0' @ VA 0xb93000) -> 严禁写入/注入原则确立
-------------------------------------------------------------------------------------------------------------------
回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！
===================================================================================================================
```

**门禁 2**：`python tools\audit_bytes.py out/re_work/atlas_rev/R4/claims_R4.txt`（退出码 0）
```text
VA         期望字节                       实际字节                   判定     标签/上下文
--------------------------------------------------------------------------------------------------------------
0x6574c3   e8 88 e7 ff ff             e8 88 e7 ff ff         OK     原版 RadarClass::Refresh 内 call 0x00655C50（v1.6.0 调用点口径）docs/re/v160_static_contract.md:41,50 | call 0x655c50
0x655d38   89 44 24 28 a1 50 35 b7 00 89 44 24 28 a1 50 35 b7 00 OK     Plot_Cell 下沉点 9B（路线A 安装点）docs/re/v160_static_contract.md:104 | mov dword ptr [esp + 0x28], eax
0x655d41   3b c5 74 18                3b c5 74 18            OK     路线A 跳板还原 9B 后 jmp 落点起点 docs/re/v160_static_contract.md:104 | cmp eax, ebp
0x65719a   e8 91 93 00 00             e8 91 93 00 00         OK     call 0x00660530（雷达跳帧抑制 5B 等长点）docs/re/ARCHITECTURE_ATLAS.md:534 | call 0x660530
0x660530   a1 b8 4d b0 00 85 c0 0f 94 c0 c3 a1 b8 4d b0 00 85 c0 0f 94 c0 c3 OK     原版跳帧判定函数体 docs/re/v160_static_contract.md:73-76 | mov eax, dword ptr [0xb04db8]
0x6d3d99   0f 8d 98 00 00 00          0f 8d 98 00 00 00      OK     原版 jge 0x006D3E37（L4 双模切换点）docs/re/ARCHITECTURE_ATLAS.md:438 | jge 0x6d3e37
0x6d3d10   81 ec f4 00 00 00          81 ec f4 00 00 00      OK     TacticalClass::Render 真实入口 sub esp,0xF4 docs/re/ARCHITECTURE_ATLAS.md:416 | sub esp, 0xf4
0x64c6f2   0f 85 69 05 00 00          0f 85 69 05 00 00      OK     H-D1 jne 0x0064CC61 docs/re/landing_equivalence_static_proof.md:44 | jne 0x64cc61
0x64cc61   a0 80 48 b0 00             a0 80 48 b0 00         OK     H-D2 mov al,[0x00B04880] docs/re/landing_equivalence_static_proof.md:45 | mov al, byte ptr [0xb04880]
0x64de75   5f 5e 5d 5b 83 c4 14 c3    5f 5e 5d 5b 83 c4 14 c3 OK     H-D5 原版函数尾声 docs/re/landing_equivalence_static_proof.md:46 | pop edi
0x64c911   e8 9a a3 e7 ff             e8 9a a3 e7 ff         OK     H-D6 call 0x004C6CB0 docs/re/landing_equivalence_static_proof.md:47 | call 0x4c6cb0
0x64cc0a   e8 a1 a0 e7 ff             e8 a1 a0 e7 ff         OK     H-D6b call 0x004C6CB0（次级缓冲）docs/re/landing_equivalence_static_proof.md:48 | call 0x4c6cb0
0x750920   51                         51                     OK     VocClass::PlayGlobal 入口 push ecx docs/re/landing_equivalence_static_proof.md:319 | push ecx
0x75092e   33 c0 59 c2 08 00          33 c0 59 c2 08 00      OK     PlayGlobal 失败分支 xor eax,eax; pop ecx; ret 8 docs/re/landing_equivalence_static_proof.md:322-324 | xor eax, eax
0x7509ef   c2 04 00                   c2 04 00               OK     PlayAt ret 4（清栈契约）docs/re/landing_equivalence_static_proof.md:332 | ret 4
0x508f88   80 b8 a5 16 00 00 00       80 b8 a5 16 00 00 00   OK     SpySat 判定 cmp byte [eax+0x16A5],0 docs/re/landing_equivalence_static_proof.md:166 | cmp byte ptr [eax + 0x16a5], 0
0x508f8f   74 65                      74 65                  OK     je 0x00508FF6（门控改写点）docs/re/landing_equivalence_static_proof.md:167 | je 0x508ff6
0x568273   89 99 34 01 00 00          89 99 34 01 00 00      OK     Gap1 引用计数暴力清零（NOP 保护点）docs/re/landing_equivalence_static_proof.md:153 | mov dword ptr [ecx + 0x134], ebx
0x577ec5   89 b8 34 01 00 00          89 b8 34 01 00 00      OK     Gap2 清零（NOP 保护点）docs/re/landing_equivalence_static_proof.md:156 | mov dword ptr [eax + 0x134], edi
0x577b60   89 98 34 01 00 00          89 98 34 01 00 00      OK     Gap3 清零（NOP 保护点）docs/re/landing_equivalence_static_proof.md:159 | mov dword ptr [eax + 0x134], ebx
0x5865e0   32 c0 c2 04 00             32 c0 c2 04 00         OK     MapClass::IsCellShrouded 恒 0 空桩（迷雾裁剪瘫痪根因）docs/re/landing_equivalence_static_proof.md:224 | xor al, al
0x7efa68   c0 ce 62 00                c0 ce 62 00            OK     ParticleClass 虚表槽69 -> 0x0062CEC0 docs/re/landing_equivalence_static_proof.md:217 | ror dh, 0x62
0x7efcb0   80 e2 62 00                80 e2 62 00            OK     ParticleSystemClass 虚表槽69 -> 0x0062E280 docs/re/landing_equivalence_static_proof.md:219 | and dl, 0x62
0x7c8e17   6a 01 ff 74 24 08 e8 20 06 00 00 59 59 c3 6a 01 ff 74 24 08 e8 20 06 00 00 59 59 c3 OK     operator new 14B thunk（ASM-FIX-33 定界）docs/re/ARCHITECTURE_ATLAS.md:278 | push 1
0x7c8b3d   ff 74 24 04 e8 a2 08 00 00 59 c3 ff 74 24 04 e8 a2 08 00 00 59 c3 OK     operator delete 透传 free docs/re/landing_equivalence_static_proof.md:282-285 | push dword ptr [esp + 4]
0x48ce8f   84 c0                      84 c0                  OK     顶层帧主循环 test al,al（ASM-FIX-6 订正后）docs/re/ARCHITECTURE_ATLAS.md:1372 | test al, al
0x48ce98   84 c0                      84 c0                  OK     帧采样 test al,al（ASM-FIX-6 订正后）docs/re/ARCHITECTURE_ATLAS.md:1375 | test al, al
0x6da949   89 8c 83 e4 00 00 00       89 8c 83 e4 00 00 00   OK     RegisterCellAsVisible 真实写入（ASM-FIX-5 订正后）docs/re/ARCHITECTURE_ATLAS.md:472 | mov dword ptr [ebx + eax*4 + 0xe4], ecx
0x6da950   8b 83 e0 00 00 00          8b 83 e0 00 00 00      OK     VisibleCellCount 读改写序列首 docs/re/ARCHITECTURE_ATLAS.md:473 | mov eax, dword ptr [ebx + 0xe0]
0x6da956   40                         40                     OK     inc eax（计数自增）docs/re/ARCHITECTURE_ATLAS.md:473 | inc eax
0x6da957   89 83 e0 00 00 00          89 83 e0 00 00 00      OK     VisibleCellCount 写回 docs/re/ARCHITECTURE_ATLAS.md:473 | mov dword ptr [ebx + 0xe0], eax
0x647260   a0 f8 d5 a8 00             a0 f8 d5 a8 00         OK     会话标志字节读取指令（MpActive 一级主判定证据）docs/re/mp_release_safety_checklist.md:33 | mov al, byte ptr [0xa8d5f8]
--------------------------------------------------------------------------------------------------------------
合计 32 条：OK=32  MISMATCH/NOREAD=0
```

**门禁 3（附加自证，非任务卡要求）**：全文补丁块四反引号围栏配对与 claims 条数自检：
```text
四反引号围栏行数 = 18（应为 patch 数 ×2 = 18，偶数 ⇒ 配对完整）
三反引号围栏行数 = 26
PATCH 块数 = 9（须 = 9）
带「grep 实跑：hits=1」的补丁块 = 9（须 = 9）
claims_R4.txt 行数 = 35（含 3 行注释 + 32 条断言）
在库引用四反引号围栏 = OK
```

### [7] 风险与红线提示

| 提问 | 回答 |
|:---|:---|
| ① 同步语义 / 命令序 | **触及**（间接）：§12.2 补充块与 §13.5 明确「MP **NO-GO**」、混联禁令、`pointer` 键 VIOLATION ⇒ **需要 MP 门控矩阵 + 真机对拍验收**，不得宣称「零风险 / 无 Desync」 |
| ② 随机数消费序 | **触及**（文档层）：标注 atlas §9.2 首句与勘误自相矛盾（每逻辑帧 2 次 + 约 83 候选消费点）⇒ 在真机对拍前不得引用旧口径；**本批未做任何随机数相关改动** |
| ③ 存档结构 | **触及**（判据层）：M-10 类补丁改 `CellClass+0x134`（进 `.SAV`）⇒ 混联禁令；且 §13.4 要求 `.SAV` OLE2 魔数 `D0 CF 11 E0 A1 B1 1A E1` 作为放闸凭证 |
| ④ 渲染像素等价性 | **触及**（判据层）：§13.4 第二级人工抽验（渐变无锯齿/色斑/借位）+ 阈值口径（`≥600/≥800`）即为像素等价性的验收闸门；真机像素对拍 **未执行** |
| ⑤ 本次是否启动游戏/注入/改二进制 | **否**（全程只读；未启动任何游戏进程） |
| ⑥ 是否伪造「实测」标记 | **否**；本批所有未运行项一律标 `[待实测]`，并把 atlas 内 8 处误用逐条订正 |

### [8] 交付物清单

| 类型 | 路径 | 规模 |
|:---|:---|:---|
| 主报告（本文件） | `docs/re/atlas_rev/R4_acceptance_standard.md` | **463 行 / 65181 B**（写入时间 2026-09-29 05:09:12 UTC） |
| 断言文件 | `out/re_work/atlas_rev/R4/claims_R4.txt` | 35 行 / **32 条**断言（`audit_bytes` 32/32 OK） |
| 门禁留痕 | `out/re_work/atlas_rev/R4/gate1_verify_anchors.txt`、`gate2_audit_bytes.txt` | 15 / 36 行 |
| scratch | `out/re_work/atlas_rev/R4/_part1.md … _part4.md` | 组装中间件（可删） |
| 补丁块 | 本文件 §1 | **9 个**（INSERT_AFTER ×5、REPLACE_BLOCK ×3、ERRATUM ×1） |

### [9] 待裁决项（需 Lead 决定的分叉）

| # | 分叉 | 建议方案 | 理由 |
|:--|:---|:---|:---|
| **D1** | `verify_evidence.py` 旧阈值（P0）如何收口 | **本批派工修**：改 `:345-348` 为 `<600 ⇒ FAIL` + 文案改新口径 + 加「同量级」检查；改后跑三批历史证据回归（须保持对单色伪造批次的 FAIL） | 不动则放闸第一级过滤与 09-28 裁定冲突，会误杀 ZC 证据；属放闸路径的关键工具 |
| **D2** | §9.2 首句矛盾（E2）由谁就地加注 | 建议由 **Lead 在合并 §13 同一批**内顺手加注（锚点已给） | 纯文档加注，无需新证据；留给 R3 会与其 §9 补丁块产生行号漂移 |
| **D3** | `EVIDENCE_STANDARD.md` / `v160_acceptance_runbook.md` 表内旧阈值（E3/E4） | 建议 Lead 派一个「文档同步」小任务：行内加订正指针（不删字）；或由 Lead 直接在 EVIDENCE_STANDARD 表末加一行「本表第 7 行判据作废」 | 该两文件是验收方（Antigravity/ZCode）的直接操作依据，不修则同一份标准内自相矛盾 |
| **D4** | atlas「50% 半暗」（E5）是否改口径 | 建议**只加注**（保留 50% 作为「我方等效观感」），不在 R4 批内改 fog 语义 | FOG-ERRATA E1 已定谳原版为 alpha 插值；改动属 R2 域，跨流改会与其补丁块冲突 |
| **D5** | §13 的 UNVERIFIED 清单是否要加「时间戳/责任人」列 | 建议**不加**，维持「状态 + 依据锚点」两列，责任人信息留在派工任务卡 | atlas 是架构契约，动态责任人会快速过期；状态由任务卡驱动 |
