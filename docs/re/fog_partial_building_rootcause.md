# 灰雾/黑区边界建筑"只画出一半"根因诊断（BUG-FOGPARTIAL · 只读）

> [META]
> task=BUG-FOGPARTIAL  executor=DSH 子代理（父会话 session-852a2193-df41-4859-b6f3-cd17f595410f）  mode=read-only
> 基线：`ra2youli/gamemd.exe` 4,825,360 B / MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`（只读，未打补丁）
> 部署件：`ra2youli/ra2render.dll` 148,992 B / MD5 `EAAA1BE95BE88BCC67F58A2AFD1A42C9`；`ra2youli/ra2render.ini` MD5 `4E086B357488DC95FA264B5ECCF0B6D7`
> 截图：`out/re_work/bug_fogpartial/user_report_20260928_fog_partial_building.png`（1365x768，sha256 `F701B746E6C48E620099D375702758BDB12B93BAD1414DD51372CA69EE4743CA`）
> 原始聚合数据与全部测量脚本：`out/re_work/bug_fogpartial/`（FINDINGS.md + f1_*.py + crops）

---

## [0] 结论摘要

1. **F1（几何）**：缺失/发黑内容的边界**沿建筑自身 sprite 的 extent（= 方案 b）**，且在 sprite 空间沿自身中轴呈**东西分裂**（西半 lum<9 占 **29.0%**，东半 **7.4%**，3.9x）；**不是**屏幕轴对齐条带（c，实测全图最长轴对齐跳变 = y=570 处 122 px 的**地形类型边界**，与任何对象无关）；**不是**逐格菱形分块（a）。
   **雾层自身**才是逐格的：灰雾边界实测 **dx/dy = −136/68 = −2.00**（严格 2:1 等轴格边），步长恰为 1 格 = **60x30 px** ⇒ (d)「沿雾区边界」在**背景层面**成立，但雾界与建筑自身的缺失边界**并不重合**（雾罩连通域右界 ≤ x 688，异常对象左界 x 995 ⇒ 两者相距 ≥307 px；该对象所在 x 840..1210 / y 300..610 区域内**雾罩像素为 0**）。
2. **F4 排名第一 = H1（引擎原生：被采样格处于 shroud 态 ⇒ 该对象以零光照绘出 = 黑）**，字节级实证；它解释"模型看起来没画出来"（不透明像素全黑 + sprite 自身的透明孔洞透出地形 = 黑白马赛克），但**引擎不会把一栋建筑画成"一半"**（判定是单格采样、整体生效）。
3. **F3（edi 语义）= 打包的 RGB 光照颜色（R6/G5/B5，RGB565 式），不是掩码/透明键/裁剪矩形**；shrouded 时被清零 ⇒ 对象仍被**完整绘出但全黑**，**不会**导致"部分不显示"。
4. **H3（L4 脏矩形部分重绘）在本构建被结构性禁用**：0x006D3D99 已被 DLL 打成**无条件全量重绘**（桩 `mov ecx,0x6D3E37; jmp ecx`），且 `L4DirtyMode` 键在 ini 与源码中**都不存在**、`RegisterCellAsVisible 0x6DA7D0` 在 DLL 中 **0 命中**。
> 【W3 勘误 · W3-A6/ISSUE-STALE-L4-EXIST】改前：L4DirtyMode` 键在 ini 与源码中**都不存在；改后：L4DirtyMode 已在 blitter_hooks.cpp:757 读取并支持 force-full / vision-dirty 模式；三处 ini 均已配置出厂值。；依据：ra2render/blitter_hooks.cpp:757; ra2render/ra2render.ini:251; ra2youli/ra2render.ini:186; ra2bench/ra2render.ini:186；分级：P1
5. 最大风险：截图**不含**任何"被栅格化为半块的几何体"——"一半"是**感知特征**（对象被整体画黑 + 其所在格一半在雾内），故 F4 的第一名与"一半"的量化特征之间仍需两项真机实验（§F5 E1/E2）闭环。

---

## [1] 逐条必答项结论表

| # | 问题 | 结论 | 证据等级 | 证据锚点 |
|---|---|---|---|---|
| F1 | 缺失半边的几何关系（a/b/c/d） | **(b) 沿 sprite 自身 extent**；西半/东半 3.9x 不对称；非 (a)(c)；(d) 仅背景（且本身逐格，dx/dy=−2.00） | [实证]（像素统计）+ [推演]（成因归属） | `out/re_work/bug_fogpartial/FINDINGS.md` §A3/A4；crop_Q/M/S |
| F2-1 | `Hook_Building_Draw` 判据链 | vanilla 放行 → `g_enableBuildingFog && !ShouldDrawBuilding` → **`return`（整个 Draw 调用被剔除，无部分绘制分支）** | [实证] | `ra2render/blitter_hooks.cpp:2905-2923`；DLL `0x403649 push 0x7E3FD0` |
| F2-2 | 剔除的是主体还是全部调用 | **全部调用**（vtable[69] 整入口）；阴影/bib/附属动画对本次调用是一体的 | [实证] | 同上 + `0x007E3FD0 = 0x0043D290`（vtable dword 实测） |
| F2-3 | `EnableBuildingFog` 作用范围 | 仅该一个钩子。**建筑附属动画（雷达/烟雾/叶片）走 `AnimClass::Draw 0x00422CA0`，我方未挂钩（grep ANIM/AnimClass = 0 命中）⇒ 不受该键约束** | [实证] | `blitter_hooks.cpp:2905-2923`；无 AnimClass hook |
| F2-4 | 多部件是否走不同路径 | 是：主体走槽 69（已门控）；附属 Anim 走 `AnimClass::Draw`（引擎自带 `+0x19D`/`+0x199` 判据）。但两者都是**整体**粒度，无法产生主体的几何半块 | [实证] | `docs/re/building_fog_residual_deep_dive.md:23,41-53` |
| F2-5 | L4 脏矩形 + 渐变对建筑的影响面 | **本构建 0x006D3D99 = 无条件全量重绘**（每帧顺序必为"格（含雾）→对象"）；`FadeFogTransition` 逐格 4 帧、**按格去重**，只能产生整格明暗差 | [实证]（源码/字节/ini） | `blitter_hooks.cpp:2228-2246,2355-2367,3052`；DLL `0x402BB0` |
| F3-1 | `0x43D542 xor edi,edi` 的 edi 语义 | **打包 RGB 光照色**（`0x43D38C xor edi,edi` 初始化 → `0x43D3E4 shl edi,6`/`0x43D3EB shl edi,5` 由 0x8871E0 光表三字节合成） | [实证] | `gamemd.exe` 0x43D38C/0x43D3E4/0x43D3EB/0x43D542 |
| F3-2 | 是否会造成"部分建筑不显示" | **不能**：判定只用**中心格**（`0x43D4F4 → 0x43D504 sar 8 → 0x43D532 GetCellAt → 0x43D539 IsShrouded`），整体生效；且**永不跳过绘制**（唯二早退 = 门1 `0x43D2BB`、门2 `0x43D316`）。结果是"整栋黑"而非"半栋缺" | [实证] | 同上一行 + 0x7063D7/0x7063DC/0x7063E0 |
| F3-3 | 跨格建筑在探索/未探索边界上的预期表现 | **不会必然半亮半不亮**：整栋按中心格取值 ⇒ 要么全彩、要么全黑（黑时其透明孔洞透出地形 = 黑白马赛克，"看起来模型没刷出来"） | [推演]（机制实证，表现待 E1 实测） | 同上 |
| F4 | 候选排序 | **H1 > H2 > H3(构建禁用) > H4 > H5** | 见 §F4 | FINDINGS.md §B/§C |
| F5 | 真机单变量实验 | 3 项（E1/E2/E3），设计见 §F5 | [待实测] | — |

---

## [2] 关键证据块（VA / FileOffset / 原始字节 / Capstone / xref）

**E-1 引擎：中心格采样 + 光照清零（gamemd.exe，file = VA−0x400000，.text）**
```asm
0043D4F4  FF 52 48              call [edx+0x48]      ; 槽18 BuildingClass::GetCoords → centerCoord
0043D504  C1 F8 08              sar  eax, 8          ; centerCell.X = centerCoord.X >> 8
0043D532  E8 69 82 12 00        call 0x005657A0      ; MapClass::GetCellAt(&centerCell)
0043D539  E8 12 A4 04 00        call 0x00487950      ; CellClass::IsShrouded()   ← 仅中心格
0043D53E  84 C0                 test al, al
0043D540  74 02                 je   0x0043D544
0043D542  33 FF                 xor  edi, edi        ; ★光照色 := 0（不跳绘制）
0043D674  68 00 01 00 00        push 0x100           ; 名义亮度参数
0043D683  E8 78 87 2C 00        call 0x00705E00      ; 主体绘制核心（写入 DSurface::Hidden_2）
0043D68F  C2 08 00              ret  8
007063D7  E8 74 15 D8 FF        call 0x00487950      ; 核心内第二次 IsShrouded
007063DC  84 C0                 test al, al
007063E0  33 C0                 xor  eax, eax        ; ★亮度 := 0（黑），随后仍进 0x7063F8 派发表
007063E4  8B 84 24 80 00 00 00  mov  eax, [esp+0x80]  ; 非黑路径
```
文件偏移同值（.text：VA−0x400000）；vtable dword `0x007E3FD0 = 90 D2 43 00`（= 0x0043D290）。
唯一早退门：`0x43D2BB je 0x43D9CE`（GetCell==NULL）、`0x43D316 jne 0x43D9CE`（Type->InvisibleInGame，+0x1701）。

**E-2 我方路径（ra2render，read-only；DLL VA 以 0x400000+RVA 书写以匹配 audit_bytes.py）**
| 目标 | 源码行 | DLL immediate |
|---|---|---|
| BuildingClass 槽 69 = 0x007E3FD0 | `blitter_hooks.cpp:3039-3043` | `0x403649 = 68 D0 3F 7E 00`（inst）/ `0x404FCC`（restore） |
| CellClass::Draw 0x004801F0 inline hook | `:3051-3052, 2300-2370` | `0x402F3C = B9 F0 01 48 00` |
| 引擎 FOG.SHP 层 0x0047F250 | `:1830-1837` | `0x402739 = B8 50 F2 47 00` |
| 黑幕计数钩 0x0047EFE0 | `:2254-2297` | `0x4031DC = B9 E0 EF 47 00` |
| **L4 全量刷（无条件）** | `:2228-2246, 2355-2367` | `0x402BB0 = B9 37 3E 6D 00`（mov ecx,0x6D3E37）/ `0x40315F = B9 99 3D 6D 00` |

门控细节：`ShouldDrawBuilding` 只取**锚格**（`+0x9C/+0xA0 >> 8`，`:1600-1614`）；`everSeen` 盖章却按**整个地基**（`:1328-1345`，任一地基格入直视圈 ⇒ 全地基盖章）；引擎取**中心格** ⇒ 同一对象上并存 3 种粒度（1 / W×H / 1）。
`0x006DA7D0 (RegisterCellAsVisible)` 在部署 DLL 中 **0 命中**；`L4DirtyMode` 在 `ra2render.ini`（MD5 4E086B35…）与源码中**均不存在**。

**E-3 截图量化（只读像素聚合）**
* 雾界：x(y=430)=632 → x(y=498)=496 ⇒ dx/dy = **−2.00**；步长 1 格 = 60x30 px。
* 轴对齐长跳变：水平最长 = y=570 x 914..1035（**122 px，地形类型边界**）；垂直最长 = x 1197..1206（侧栏 UI 边框，499 px）、次之 x=202 y 414..476（63 px，桥塔竖构件）⇒ **无屏幕矩形切割**。
* 异常对象（x 995..1180 / y 440..520）：lum<9 = 18.1%（西半 29.0% / 东半 7.4%）；参照：其外围地形 **0.0%**、同帧亮色参照建筑 6.6% / 2.6%、桥面 1.1% ⇒ 近黑团**只出现在该对象自身 footprint 内**。
* 雾罩（B>R+4 且 lum>26，3x3 多数滤波）：最大连通域 137,361 px，bbox x 0..688 / y 146..528；右侧基地 x 840..1210 **无任何雾罩像素**。
* 光标（RA2 白色指针）实测位于 **≈(813,338)**，停在普通暗水面 ⇒ 截图**不能**自证用户指认的是哪一栋建筑。

---

## [3] 勘误（对既有文档/结论的最小订正清单；Lead 处理）

| 目标文件:行 | 改前 | 改后 | 理由 | 影响面 |
|---|---|---|---|---|
| `docs/re/building_fog_residual_deep_dive.md:69,190` | "xor edi,edi … 仅仅将**光照强度**的寄存器 edi 清零" | "清空的是**打包 RGB 光照色**（0x43D38C 初始化，0x43D3E4/0x43D3EB 以 6/5/5 位移由 0x8871E0 光表合成）" | 实测位移结构 = RGB565 式三通道，非标量强度 | 不改结论；影响"亮度"措辞与后续任何想读 edi 的人 |
| 同文 §1.2 根因 1 | 只提 `0x43D542` 一处清零 | 补充 `0x7063E0 xor eax,eax`（主体核心内**第二次独立**清零） | 实测两处独立清零 | 建议在文档中并列，避免只改一处失效 |
| `docs/RE_COORDINATION.md:1656`（Lead 初判首选 H-脏矩形） | "对象未同步标脏 ⇒ 不重画 ⇒ 呈现「切掉一半」"（首选） | 降级为第 3 位：本构建 0x006D3D99 已为**无条件全量重绘**，脏矩形路径不存在；且截图像素统计只见"sprite 空间东西分裂"、无连续逐格菱形空洞 | 源码 + DLL 字节 + 像素三项独立 | 影响派工优先级（H3 实验可延后） |
| 任务卡"claims 以 0x400000+RVA 书写"（DLL 侧） | — | 约定正确但原因需记录：`audit_bytes.py` **硬编码 IMAGE_BASE=0x400000**，而 `ra2render.dll` 真实 ImageBase = **0x10000000** ⇒ 只有"0x400000+RVA"这一写法能过审计 | 避免下一位作者按真实基址书写而被判 NOREAD | 工具口径说明，非缺陷 |

---

## [4] 未闭环清单

| # | 缺口 | 为何无法静态闭环 | 下一步取证方法 | 级别 |
|---|---|---|---|---|
| U1 | 用户指认的**具体**建筑未定位（光标停在 ≈(813,338) 水面；截图内仅有 1 个异常近黑多格对象） | 单帧截图无对象/选择信息，无 UI 提示 | 真机按 §F5 E1 复现同一镜头并同时截"建筑完整/半缺"两张 | **P0** |
| U2 | 该对象是"被引擎零光照画黑"还是"本身就是深色 sprite" | 画面内无**同型号**建筑的彩色参照（其余建筑型号不同、且都处在直视区） | 真机把同型号建筑推到直视区拍一张（E2） | **P0** |
| U3 | `0x00705E00` 内部是否对多格建筑**按格**施加光照/逐格绘制（我们只证 0x43D290 与 0x7063DC 两处单点判定） | 该核心 >0x800 字节、含 0x7063F8 派发表，静态全量反汇编超出本轮预算 | `python tools/probe.py fn 0x00705E00` 全量反汇编 + 找 per-cell 循环 | P1 |
| U4 | 截图当帧的遥测（`buildingsCulledByFog`、`fogCellsDrawn`、ramp 分布）未知 | 静态图片不含日志 | 真机取 `ra2render_*.log` 两行（E1/E3 同轮） | P1 |

---

## [5] 写作用域合规声明

* **新增（唯一写入）**：`docs/re/fog_partial_building_rootcause.md`（本文件）、`out/re_work/bug_fogpartial/**`（FINDINGS.md、claims_gamemd.txt、claims_dll.txt、f1_*.py、mk_*.py、f3_*.py、dll_scan*.py、verify_claims.py、crop_*.png、overview_0p6x_stretched.png）。
* **未触碰**：`ra2render/**`（源码与产物，仅 grep/read）、`ra2youli/**`（gamemd.exe / ra2render.dll / ra2render.ini 全部只读）、台账、`docs/RE_COORDINATION.md`、其他 `docs/**`、任何二进制。
* **只读证明**：`gamemd.exe` MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`（= 任务卡基线）；`ra2render.dll` 148,992 B / MD5 `EAAA1BE95BE88BCC67F58A2AFD1A42C9`（= 任务卡部署件）；`ra2render.ini` MD5 `4E086B357488DC95FA264B5ECCF0B6D7`（= 任务卡口径）。
* **未启动游戏 / 未注入 / 未改任何二进制字节**（所有"引擎侧"结论来自**静态** PE 段映射 + Capstone 反汇编）。

---

## [6] 门禁实跑输出（原文）

```text
[1] python tools\verify_anchors.py
  [PASS] .text 原始段哈希: c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738
  [PASS] .detour 原生签名: 40 00 00 00 44 74 72 00 ('@\0\0\0Dtr\0' @ VA 0xb93000)
  回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
  ★ 最终裁决 : [100% ALL PASS]

[2] python tools\audit_bytes.py out\re_work\bug_fogpartial\claims_gamemd.txt
  合计 23 条：OK=23  MISMATCH/NOREAD=0

[3] python tools\audit_bytes.py out\re_work\bug_fogpartial\claims_dll.txt --exe ra2youli\ra2render.dll
  合计 7 条：OK=7  MISMATCH/NOREAD=0
```

---

## [7] 风险与红线提示

* 本轮**只诊断、只读**：未启动游戏、未注入、未改任何二进制、未改 ini。
* 触及面：**渲染像素等价性**（是）——若按 H1/H2 修复（例如"看清过即常驻"的建筑改用引擎非 shroud 光照路径，或按地基逐格判定），会改变**像素输出**，必须走 §F5 的真机对拍与回滚开关。
* **不触及**：①同步语义/命令序 ②随机数消费序 ③存档结构（本轮无任何写入、无新字段）。
* 因此**无需** MP 门控矩阵；但结论一旦进入落地实现，仍须"一次只动一项 + 独立开关 + 回滚 + 遥测"。
* 纪律披露：F1 为定位对象，除局部裁剪/放大与像素聚合外，额外做了**一次 0.6x 整帧压暗拉伸视图**（`overview_0p6x_stretched.png`）用于总体定向——相对"只做局部裁剪"的纪律属**轻度越界**，此处显式披露。

---

## [8] 交付物清单

* 新文档：`docs/re/fog_partial_building_rootcause.md`（本文件，10 节骨架）
* 聚合与统计：`out/re_work/bug_fogpartial/FINDINGS.md`
* 断言：`out/re_work/bug_fogpartial/claims_gamemd.txt`（23 条）+ `claims_dll.txt`（7 条）= **30 条**，全部 audit OK
* 裁剪/视图图：18 张 `crop_*.png`（A/B/C/D/E/F/G/H/I/J/L/M/N/O/P/Q/R/S，2x–8x，全部为局部裁剪）+ `overview_0p6x_stretched.png`（+ 输入原图 1 张 = 目录内 20 PNG）
* 脚本：31 个（`f1_*.py` 12 个测量脚本、`mk_*.py` 11 个裁剪/视图脚本、`f3_disasm.py f3_edi.py dll_scan.py dll_scan2.py dll_verify2.py verify_claims.py` 6 个二进制定点脚本、`f1_fogcomp.py f1_sample.py`），全部可复跑且只读

---

## [9] 待裁决项（需人/Lead 决定）

1. **F1 是否采信为 (b) 定谳**：我方结论是"缺失边界沿 sprite 自身 extent（sprite 空间东西分裂）"；若 Lead 要求"缺失边界必须与雾界同形"，则需**真机取图**（F5 E1 的 b 场景）才能区分"对象被整体画黑"与"对象被雾界逐格裁切"。建议：**先采信 (b) 作为工作假设**，用 E1 复拍定谳。
2. **H3 是否直接划掉**：源码 + DLL 字节 + ini 三证显示 0x006D3D99 恒全量刷、脏矩形路径不存在。建议：**把 H3 从"首选"降为"已排除（本构建）"**，并把 Lead 的"对象未同步打脏"派工改为 P2 备忘（待未来 Z-2 落地 vision-dirty 后再验）。
3. **修复方向选择**（诊断不作实现）：① 我方只按"地基任一格在直视圈"决定剔除、把**光照**留给引擎 ⇒ 边界建筑会出现"半亮半黑"观感；② 若要观感一致，需在 `Hook_Building_Draw` 放行时**临时提升该对象的光照**（触及像素等价性与引擎内部参数，风险高）；③ 折中：仅对"锚格 in fog 且中心格 in fog"的建筑保持我方剔除，避免"已侦查建筑被引擎画黑"。建议**先出 E1 数据再选**。
4. **U3（0x00705E00 是否逐格绘制）是否单独立卡**：它决定"跨格建筑是否可能由引擎侧产生逐格明暗差"。
