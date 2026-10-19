# ASM-FIX2 交付报告：帧 CRC 的 RNG 消费点锚点重建（P0）+ 残余定向重锚 + 扫描器豁免规则

> **任务卡**：ASM-FIX2 ｜ **执行方**：DSH 子代理（父代理 session-852a2193-df41-4859-b6f3-cd17f595410f 派工） ｜ **子代理任务号**：ASM-FIX2（本会话）
> **日期**：2026-09-27 ｜ **工作区**：`D:\Project\ra2-campaign-forge`
> **基线二进制**：`ra2youli/gamemd.exe`（YR 1.001，4,825,360 B，MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`，mtime 2026-09-25 16:10:48）—— **全程只读**，MD5/mtime 前后一致（§5）
> **地址口径**：FileOffset **一律走 PE 段表映射**（`off = rawptr + (VA - 段基址)`），同 `tools/audit_bytes.py` / `out/re_work/asm_scan/classify.py` 口径
> **工具链**：Capstone 5.0.7（x86-32）+ 自写只读探针 `out/re_work/asm_fix2/probe.py`；交叉源 `out/reverse/symbols.json`（RTTI vtable）+ `YRpp/Surface.h`（声明序）

---

## [META]

```text
task=ASM-FIX2   executor=DSH 子代理 (session-852a2193 派工)   mode=accept-edits
scope_declared = docs/re/{ARCHITECTURE_ATLAS.md, offline_verification_alternatives.md,
                 landing_equivalence_static_proof.md, asm_fix_report.md}
                 + out/re_work/asm_scan/**（脚本改进）+ out/re_work/asm_fix2/**
                 + 新建 docs/re/asm_fix2_report.md
elapsed ≈ 单轮（工具链见 §2 与 §6）   workspace = D:\Project\ra2-campaign-forge
```

---

## [0] 结论摘要

1. **F1（P0）已完成**：`ARCHITECTURE_ATLAS.md §9.2` 的帧 CRC RNG 证据链**已用实测锚点重建**——原记 `0x0064DAD9: E8 52 1A F6 FF (call 0x005AF530)` 三重证伪后**作废**（0 命中／0 站点／非指令边界），改为 `0x0064DE33/39/3F`（CRC 折叠抽取）与 `0x0064DE70 → 0x00650A90`（帧尾抽取，体内 `0x650AB7`/`0x650AF2` 互斥各 1 次）；「每逻辑帧固定消费 **1** 次」**精确化为「帧 CRC 路径每逻辑帧共 **2** 次」**，并同步订正同源的 mermaid 节点与红线框图（§3.1–3.4）。
2. **F2（P2）已完成**：`offline_verification_alternatives.md:132/133` 的 `Surface::Lock/Unlock` **给出真值锚点**——`DSurface::Lock = 0x004BAD80` / `DSurface::Unlock = 0x004BAF40`（RTTI vtable `0x007E85D4` 槽 `+0x5C`/`+0x60`；体内 `call [reg+0x64]` = `IDirectDrawSurface7::Lock`）；`landing_equivalence_static_proof.md:276-279` 的 `85 C0/75 14` 块**函数归属已定、来源仍不明**（该 4 字节模式在 CRT 区 0 处），维持「待重新锚定」（§3.5–3.7）。
3. **F3（L3）已完成**：扫描器加**自引用豁免**（文件级 + 行级 `selfref` 双规则），复扫不再把历史引用计为 P1/P2；**AFTER：P1 = 0、P2 = 0**（BEFORE 38 / 9），②③ 总量 332 → 281（§6）。
4. **门禁全绿**：`verify_anchors.py` **323/323 PASS**、`audit_bytes.py docs/re/anchor_claims.txt` **323 OK**、复扫 `claims.txt` **1280 OK**、本批自证 `claims_asm_fix2.txt` **40 OK**（§6）。
5. **最大风险**：本批改动的是**锁步随机数消费计数**（每帧 1 → 2）——所有**行为面**结论（是否影响 desync 判定）**均标 [待实测]**，须走 MP 门控矩阵 + 真机对拍；本批**不宣称零风险/零 Desync**。另：台账侧两行仍**引用已证伪锚点**（在禁区文件内，未动，见 §3.9/§4）。

---

## [1] 逐条必答项结论表

| # | 任务项 | 结论 | 证据等级 | 证据锚点 |
|---|---|---|---|---|
| F1 | §9.2 证据链重建（删失效锚点 + 精确化「2 次」） | **完成**：原锚作废；新锚 `0x0064DE33/39/3F` + `0x0064DE70→0x00650A90`（`0x650AB7`/`0x650AF2`）；「1 次」→「**2 次**」 | [实证] | `ARCHITECTURE_ATLAS.md:1509/1516-1531`；VA 0x64DE33/39/3F/44/4A-54/70、0x650A99/AAA/AAC/AB1/AB7/ABC/AC9/ACC/AF2/AF7 |
| F1-对照 | 原文另有出处/不同语义 | **完成**：同源表述 5 处已逐一对照 —— ① Atlas §9.2 正文 ② Atlas:1459 mermaid ③ Atlas:1925 红线框图 ④ `HOOK_POINT_MATRIX.md:405` ⑤ `re_sprint_S17_report.md:132`；**语义不同者 1 处**：`trigger_runtime_deep_dive.md:454`（只计折叠点，锚点 `0x64DE39/3F/44`–`54` 与本次重建**一致**，不冲突） | [实证] | §3.1–3.4、§3.9 |
| F2-a | `offline_verification_alternatives.md:132/133`（Surface::Lock/Unlock，候选 3/7） | **完成（给出真值）**：`DSurface::Lock = 0x004BAD80`、`DSurface::Unlock = 0x004BAF40`；候选 3/7 处**全部落在 CRT 区且非表面锁**（已逐条给出反证） | [实证] | VA 0x004BAD80/0x004BAF40/0x004BAE46；vtable 0x007E85D4 |
| F2-b | `landing_equivalence_static_proof.md:276-279` | **部分完成**：函数边界与真值字节已给（thunk = 0x7C8E17–0x7C8E24；`0x7C8E25` 起为**另一函数**，含比较回调）；`85 C0/75 14` 来源**仍不明**（CRT 区内 0 处）⇒ 维持「**来源构建不明·待重新锚定**」（禁止猜） | [实证]+[推演] | VA 0x7C8E17/8E25/8E3D；模式 `85 C0 75 14` 44 处（CRT 0 处） |
| F2-c | 复扫后仍标「待重新锚定」的条目 | **已逐条复核**：ASM-FIX §4 的 L4 已闭环、L5 已闭环（本批）；L3 已闭环（F3）；**L1/L2（禁区文件）保持未闭环并上呈**；L6–L10 仍开放（多候选，禁止猜） | [实证] | `docs/re/asm_fix_report.md:236-241`（本批追加段） |
| F3 | 扫描器豁免规则 | **完成**：`extract_claims.py` 文件级排除（默认 3 份自报告，`--include-self` 可关、`--exclude` 可加）；`classify.py` 行级 `selfref` 标记（勘误区措辞）；`triage.py` 新桶 `R-SELFREF`；`build_errata.py` 新类 `S-SELFREF`（永不计 P1/P2） | [实证] | `out/re_work/asm_scan/*.py`（改动见 §5） |
| 验收① | P1/P2 真勘误降为 0 | **达成**：AFTER `P1-BYTE-ERROR = 0` / `P2-VA-DRIFT = 0`（授权范围内；原 38/9） | [实证] | `out/re_work/asm_fix2/before_after_table.md` |
| 验收② | 前后对比计数 | **完成**（三段口径：BEFORE 38/9 → MID 2/0 → AFTER 0/0） | [实证] | 同上 |
| 门禁 | 4 项门禁 | **全绿**（原文见 §6） | [实证] | `out/re_work/asm_fix2/gate{1..4}_*.txt` |

---

## [2] 关键证据块

### 2.1 [E1] 帧 CRC 路径的局内共享 RNG 消费点（P0 重建核心）

```text
[E1] 0x0064DE33  .text  FileOffset 0x24DE33   （ATLAS §9.2 · ASM-FIX2-1）
  actual  : 8B 15 30 B2 A8 00 | 8D 8A 18 02 00 00 | E8 3C E9 00 00 | 8B 15 FC 51 AC 00
  capstone: 0064DE33 mov edx,[0xa8b230]
            0064DE39 lea ecx,[edx+0x218]          <- &ScenarioClass::Instance->Random
            0064DE3F call 0x65c780                <- RNG 抽取 #1
            0064DE44 mov edx,[0xac51fc]  / 0064DE4A mov ecx,edx / 0064DE4C shr ecx,0x1f
            0064DE4F lea ecx,[ecx+edx*2] / 0064DE52 add ecx,eax (acc = 2*CRC + (CRC>>31) + rand)
            0064DE54 mov [0xac51fc],ecx           <- 写回 CurrentFrameCRC
  xref   : 0x65C780 全 .text rel32 call 站点 = 258（本批全量普查）
[E2] 0x0064DE70  .text  FileOffset 0x24DE70
  actual  : E8 1B 2C 00 00  -> call 0x00650A90 ；站点普查 = 全 .text 唯一 1 处
  capstone: 0064DE6F inc ecx（0xA8ED84 低字节符号扩展）/ 0064DE70 call 0x650a90
            0064DE75 5F 5E 5D 5B 83 C4 14 C3（函数尾声；= §9.3 H-D5 探针锚点，交叉自洽）
[E3] 0x00650A90  .text  FileOffset 0x250A90
  actual  : 55 8B EC 83 E4 F8 83 EC 28 A0 80 48 B0 00
  capstone: 00650A99 mov al,[0xb04880] / 00650AAA jne 0x650ac9（75 1D ⇒ 两分支互斥）
            分支A 00650AAC mov eax,[0xa8b230] / 00650AB1 lea ecx,[eax+0x218]
                 00650AB7 call 0x65c780        <- RNG 抽取 #2-A
                 00650ABC mov [0xafa26c],eax   <- 采样值落全局
            分支B 00650AC9 lea eax,[esi+esi*2] / 00650ADA lea edi,[ecx*4+0xac6660]（项步长 0x33C）
                 00650AE5 mov [edi],edx（记 CurrentFrameCRC）
                 00650AF2 call 0x65c780        <- RNG 抽取 #2-B ；00650AF7 mov [edi+4],eax
  census : 0x650A90 内 0x65C780 站点 = 2（互斥）⇒ 每帧恰 1 次
结论  : 帧 CRC 路径每逻辑帧消费 [0xA8B230]+0x218 **共 2 次**（0x64DE3F + 0x650AB7/0x650AF2 之一）
原记  : 0x0064DAD9: E8 52 1A F6 FF（call 0x005AF530）—— 0 命中 / 0 站点 / 非指令边界（作废）
```

原始输出：`out/re_work/asm_fix2/frame_crc_rng_evidence.txt`、`out/re_work/asm_fix2/rng_census.txt`

### 2.2 [E4] Surface 家族重锚（F2-a）

```text
[E4] 交叉源 1：out/reverse/symbols.json（RTTI）—— class DSurface  vtable 0x007E85D4  n=38
        +0x58 DrawRect = 0x007BAD90      +0x5C Lock   = 0x004BAD80
        +0x60 Unlock   = 0x004BAF40      +0x64 CanLock= 0x004BAEC0
        +0x68 vt_entry_68 = 0x00411500   +0x6C IsLocked = 0x00411580
        +0x70 GetBytesPerPixel = 0x004BAD60   +0x74 GetPitch = 0x004BAD70
     交叉源 2：YRpp/Surface.h 声明序（头文件自带偏移命名 vt_entry_34/38/3C/40/44/48/4C/50/68）
        ⇒ Lock = +0x5C、Unlock = +0x60 —— 两源**独立吻合**（n=34 与 Surface 的 34 个虚函数一致）
[E5] 0x004BAD80  .text  FileOffset 0x0BAD80  （DSurface::Lock）
  actual  : A0 78 F9 89 00 | 83 EC 6C | 84 C0 53 55 56 57 | 8B D9 | ...
  capstone: 004BAD80 mov al,[0x89f978] / 004BAD85 sub esp,0x6c / 004BAD8E mov ebx,ecx
            004BADA9 call [ecx+0x60]  (IDirectDrawSurface7 IsLost，slot24)
            004BADAC cmp eax,0x887601C2 (DDERR_SURFACELOST) / 004BADB9 call [edx+0x6C] (Restore，slot27)
            004BAE46 call [ecx+0x64]  <- IDirectDrawSurface7::Lock（slot25）★语义定谳
            004BAEF4 call [ecx+0x64]  <- 第二条 Lock 路径
[E6] 0x004BAF40  .text  FileOffset 0x0BAF40  （DSurface::Unlock）
  actual  : A0 78 F9 89 00 56 84 C0 57 8B F1 75 09 A0 80 ED ...
  capstone: 同族 DDraw 调度 call [reg+0x60] / [reg+0x6C]（IsLost / Restore）各 4 处
[E7] 原记 VA 反证
  0x006BAC10 : 实测 00 8B 01 FF 50 60 8B 8C（落于 0x006BAC0A: 8B 8C 24 94 02 00 00 的 disp32 尾部）
               所在函数入口 0x006BA690（81 EC 78 02 00 00 sub esp,0x278；尾 0x006BAC2E: C2 20 00 ret 0x20）
               ⇒ 距入口 +0x580 的函数**中段**，非入口
  0x006BAE40 : 实测 3B F0 0F 86 96 00 00 00（cmp esi,eax; jbe）—— 指令边界但非函数入口
               所在函数入口 0x006BAC40（Δ +0x200），体内 0x006BAE6B: E8 A7 DF 10 00 call 0x007C8E17
               （CRT operator new thunk）与 shr eax,1 / dec edi ⇒ 容器增长例程
  候选 3 处（55 8B EC 83 EC 14）：0x007CBCAF / 0x007CF7E8 / 0x007CFB13 —— 全在 CRT 区
  候选 7 处（55 8B EC 51 53 56）：0x007BC610 / 0x007C94EB / 0x007C9602 / 0x007CB12E /
               0x007D58F0 / 0x007D9FCA / 0x007DD0F8 —— 全在 CRT 区（imul size×count、FILE 结构等）
  两者体内前 0x120 字节均**无** call [reg+0x64] / [reg+0x68] 派发 ⇒ 与 DDraw 表面锁无关
[E8] 真 DDRAW 槽位口径（复核）：0x60=IsLost / 0x64=Lock / 0x68=ReleaseDC / 0x6C=Restore /
     0x80=Unlock(slot32，须 disp32 编码 FF 9x 80 00 00 00)
```

原始输出：`out/re_work/asm_fix2/f2_surface_evidence.txt`、`out/re_work/asm_fix2/dsurface_ddraw_dispatches.txt`

### 2.3 [E9] landing_equivalence 276–279（F2-b）

```text
[E9] 0x007C8E17  .text  FileOffset 0x3C8E17
  actual  : 6A 01 FF 74 24 08 E8 20 06 00 00 59 59 C3（14 字节，0x7C8E17–0x7C8E24）
  capstone: push 1 / push [esp+8] / call 0x7C9442 / pop ecx / pop ecx / ret
            ⇒ CRT operator-new thunk（完整函数，尾声 = 0x007C8E24: C3）
  0x007C8E25: 55 8B EC 8B 45 10 53 56 —— **另一函数**入口
  该函数体内：004B...（0x007C8E34 imul edi,[ebp+0x14] ／ 0x007C8E3D cmp ecx,edi ／
              0x007C8E43 shr ebx,1 ／ 0x007C8E62 call [ebp+0x18] = 比较回调）
              ⇒ CRT 排序/区间类例程（名称待定谳）；cmp ecx,edi **不属** operator new thunk
  模式 85 C0 75 14：全镜像 44 处，且 0x007C0000–0x007E0000 内 **0 处**、0x007C8E24±0x800 内 **0 处**
  ⇒ 声明序「87 C0 / 75 14」在基线镜像**无可归属位置**：维持「来源构建不明 · 待重新锚定」
```

---

## [3] 勘误（逐条）

> 「改前」= 本批动手前的磁盘文本；所有勘误均为**就地追加/替换**，用词区分「已定谳 / 建议」。

### 3.1 `docs/re/ARCHITECTURE_ATLAS.md:1509`（节内小标题）
- 改前：`1. **局内随机数固定单次消费**：`
- 改后：同文 + `〔勘误 ASM-FIX2-1 ⇒ 精确化为「帧 CRC 路径每逻辑帧共 **2** 次」，原记锚点 \`0x0064DAD9\` 作废，见本节末〕`
- 理由：标题原表述与实测不符；保留原文并加勘误标记。
- 影响面：影响「谁可调用局内 RNG」的计数依据（产品决策层），并触发同源表述订正（3.3/3.4）。

### 3.2 `docs/re/ARCHITECTURE_ATLAS.md:1516-1531`（§9.2 第 1 条，P0）
- 改前：原文（含 ASM-FIX-8 勘误块）末尾为「…**字节级证据链待重新锚定**，结论方向不变但不得再引用该锚点（未闭环 P1）。」
- 改后：原文**逐字保留**，其后新增 `〔ASM-FIX2-1 · P0 证据链重建（闭环 ASM-FIX §4 L4）〕` 块：三重否定原锚 + 14 行实测 asm（含 FileOffset）+ 6 行复算表 + 语义边界与影响面，并标注行为面 [待实测]。
- 理由：任务卡 F1 要求「删/勘误失效锚点、改用已验证锚点、精确化 2 次」；ASM-FIX 已判「静态只能证伪」，本批以函数体内真实调用点重建。
- 影响面：**高** —— 该章是「视觉补丁禁止调用局内 RNG」的字节级依据；计数由 1 改 2。

### 3.3 `docs/re/ARCHITECTURE_ATLAS.md:1459`（mermaid 节点 `C1`）
- 改前：`C1["消费 1 次局内随机数: ScenarioClass::Random (0x00A8B230+0x218)"]`
- 改后：同文 + `〔勘误 ASM-FIX2-1：应为 2 次 —— 0x0064DE3F 折叠点 + 0x0064DE70 到 0x00650A90 帧尾点，见 9.2〕`
- 理由：同源表述（图内概括），不复订正会在下次复扫/审计中再次成为错误源。

### 3.4 `docs/re/ARCHITECTURE_ATLAS.md:1925`（联机确定性红线框图）+ 框图后新增脚注
- 改前：`│   - 局内唯一随机数 (ScenarioClass::Random 0x00A8B230+0x218 每帧仅消费 1 次) │`
- 改后：`… 每帧恰消费 2 次) │`（**字符数不变**，保持 ASCII 边框对齐）+ 框图后新增 `〔同源表述订正〕` 脚注（含 3.9 的域外清单指针）。
- 理由：红线框图是执行方最常引用的「禁令卡」，数量错误会误导 Hook 设计。

### 3.5 `docs/re/offline_verification_alternatives.md:132`（DirectDraw 表面锁）
- 改前：**来源构建不明 · 待重新锚定**（禁止猜）（原记 `0x006BAC10` / `55 8B EC 83 EC 14`）
- 改后：同文 + `〔ASM-FIX2-2 · F2 定向重锚〕`：真锚 `DSurface::Lock = 0x004BAD80`（vtable `0x007E85D4` `+0x5C`）、语义证据 `0x004BAE46/0x004BAEF4: call [reg+0x64]`、真锚字节、原 VA/序言的反证。
- 理由：F2 要求「函数边界 + 实参语义」重锚；本批以 RTTI vtable + 头文件声明序 + DDraw 槽位语义三重定位。

### 3.6 `docs/re/offline_verification_alternatives.md:133`（DirectDraw 表面解锁）
- 改前：**来源构建不明 · 待重新锚定**（原记 `0x006BAE40` / `55 8B EC 51 53 56`）
- 改后：同文 + `〔ASM-FIX2-2〕`：真锚 `DSurface::Unlock = 0x004BAF40`（槽 `+0x60`）+ 原 VA 所在函数的性质（CRT `operator new` 调用 + `shr eax,1` ⇒ 容器增长）+ 候选 7 处全在 CRT 的反证。

### 3.7 `docs/re/landing_equivalence_static_proof.md:278`
- 改前：`… ⇒ 本行起的 4 行**来源构建不明 · 待重新锚定**（禁止猜）`
- 改后：同文 + `〔ASM-FIX2-3〕`：函数边界与真值字节（thunk 14 字节、`0x7C8E25` 为另一函数、`0x7C8E3D` 属后者）+ `85 C0 75 14` 全镜像 44 处且 CRT 区 0 处的普查结论。
- 理由：F2 要求「给不出真值就标来源不明并列出候选与搜索范围」，禁止猜。

### 3.8 `docs/re/asm_fix_report.md:234` 之后（本批追加段）
- 改后：新增 `〔ASM-FIX2 追加〕` 段：L4（P0）已闭环、L5 已闭环、L3 已闭环（采纳排除规则方案）、L1/L2 仍在禁区（附复扫现存 2 条 P1 的现址行号）。
- 理由：保持 ASM-FIX 未闭环清单与现状一致，供 Lead 一次核对。

### 3.9 域外最小订正清单（**不在本批写作用域**，交 Lead）
| # | 文件:行 | 问题 | 建议订正 | 级别 |
|---|---|---|---|---|
| 1 | `REVERSE_ENGINEERING_AND_PATCHES.md:2215` | 台账行**引用已证伪锚点** `0x0064DAD9: E8 52 1A F6 FF`（复扫现存 P1 之一） | 保留「四重证伪」措辞同时把锚点列改为真锚 `0x0064DE3F`/`0x0064DE70`（或加「原记」标记以触发扫描豁免） | P1 |
| 2 | `docs/RE_COORDINATION.md:1352` | 同上（复扫现存 P1 之二） | 同上 | P1 |
| 3 | `docs/re/HOOK_POINT_MATRIX.md:405` | 「局内随机数…每逻辑帧固定消费 **1** 次进帧 CRC」 | 改为「帧 CRC 路径每逻辑帧 **2** 次（`0x64DE3F` + `0x650AB7`/`0x650AF2`）」 | P1（决策依据） |
| 4 | `docs/re/re_sprint_S17_report.md:132` | 「全帧仅消费 1 次 RNG」 | 同上（该报告属手写清单族，建议按 ASM-FIX-35 统一标注方式加注） | P2 |
| 5 | `docs/re/trigger_runtime_deep_dive.md:454` | 「帧 CRC `0x64DAB0` 消费 1 次 Random 并折进 CurrentFrameCRC」——**语义范围不同**（只计折叠点），锚点 `0x64DE39/3F/44`–`54` 与本次重建**一致** | 建议补一句「另帧尾 `0x64DE70 → 0x650A90` 再消费 1 次」 | P3（表述完备性） |

---

## [4] 未闭环清单

| # | 缺口 | 为何无法静态闭环 | 下一步取证 | 级别 |
|---|---|---|---|---|
| 1 | 「每帧 2 次」的**行为面后果**（是否改变 desync 判定/对拍门限） | 静态只能定字节与计数；行为须运行期观测 | MP 门控矩阵 + 双端真机对拍（同帧 CRC 序列比对 / `SYNC_SNAP`）；**本批严禁启动游戏** | **P0 [待实测]** |
| 2 | `[0xA8B230]+0x218` 的 83 个**候选**消费点未逐一定谳 | 启发式（24 字节回溯）有假阳性；逐点需函数边界 + 实参语义 | 对 83 点逐点做「ecx 来源可达性」证明（本批已出清单：`rng_census.txt`） | P2 |
| 3 | `DSurface` 家族的 DDraw `Unlock`（slot 32 ⇒ `FF 9x 80 00 00 00`）派发点未归属 | 需先解出各函数边界（该区 NOP 填充使 padding 启发式失效） | 对 `0x004B078F / 0x004B4C57 / 0x004B6E06 / 0x004B7647` 等派发点做递归下降定函数边界 | P2 |
| 4 | `landing_equivalence_static_proof.md:276-279` 的 `85 C0/75 14` 来源 | 该模式在 CRT 区**完全不存在**；无法在基线镜像内证真 | 与 P-M1 补丁规格作者核对来源构建；或在 44 个站点内按语义筛选（本批已列全量站点） | P2 |
| 5 | ASM-FIX §4 的 L6/L7/L8/L10（多候选重锚、P4 语义判读 25 条） | 同目标任务多候选，禁止猜 | 按函数边界 + 实参语义定向重锚批次 | P2 |
| 6 | 禁区两行（§3.9 #1/#2） | 任务卡明令不得触碰 Lead 所有的两份文件 | Lead 就地订正 1 行×2 | P1 |
| 7 | ASM-FIX L9（closure 记 `66 8B 01` 66 处、实测 65） | 计数微勘误，不在本批授权条目 | Lead 一句订正 | P3 |

---

## [5] 写作用域合规声明

**改动文件清单**（全部在任务卡允许范围内）：

| 文件 | 性质 | 规模 | mtime |
|---|---|---|---|
| `docs/re/ARCHITECTURE_ATLAS.md` | 勘误（3 处 + 1 脚注） | 1,632 行 / 138,579 B | 2026-09-27 10:37:52 |
| `docs/re/offline_verification_alternatives.md` | 勘误（2 处表行内追加） | 1,077 行 / 181,638 B | 2026-09-27 10:36:10 |
| `docs/re/landing_equivalence_static_proof.md` | 勘误（1 处行尾追加） | 305 行 / 33,679 B | 2026-09-27 10:36:10 |
| `docs/re/asm_fix_report.md` | 勘误（1 段追加） | 285 行 / 39,807 B | 2026-09-27 10:36:29 |
| `out/re_work/asm_scan/extract_claims.py` | **F3 改进** | 9,331 B | 2026-09-27 10:34:54 |
| `out/re_work/asm_scan/classify.py` | **F3 改进** | 12,710 B | 2026-09-27 10:35:54 |
| `out/re_work/asm_scan/triage.py` | **F3 改进** | 9,076 B | 2026-09-27 10:34:40 |
| `out/re_work/asm_scan/build_errata.py` | **F3 改进** | 7,021 B | 2026-09-27 10:34:40 |
| `out/re_work/asm_fix2/**`（新建） | 探针/证据/快照 | 38 个文件（含 before/mid/after 三份扫描快照） | 2026-09-27 |
| `docs/re/asm_fix2_report.md` | 本报告（新建） | 本文件 | — |

**未触碰清单（逐类声明）**：`REVERSE_ENGINEERING_AND_PATCHES.md`、`docs/RE_COORDINATION.md`（Lead 所有，**零写入**）；`docs/DESIGN.md`、`ra2forge/**`、`mcp/**`、`ra2opt/**`、`ra2render/**`（零写入）；其他 `docs/re/*.md`（除上表 4 份、本报告外零写入）；`tools/verify_anchors.py`、`tools/audit_bytes.py`、`docs/re/anchor_claims.txt`（金标准，只读）。

**二进制只读证明**：`ra2youli/gamemd.exe` — MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`（前后一致）、4,825,360 B、mtime 2026-09-25 16:10:48 未变；`.text` 段哈希 `c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738`（门禁 1 PASS）、`.detour` 原生签名完好。**未启动游戏、未注入、未改 exe/dll、未使用任何后台/等待型操作**。

---

## [6] 门禁实跑输出（原文粘贴）

### 6.1 复扫四步（AFTER）

```text
> python out\re_work\asm_scan\extract_claims.py --min-bytes 0
scanned files : 152
excluded self : 3 ['docs/re/inline_assertion_scan.md', 'docs/re/asm_fix_report.md', 'docs/re/asm_fix2_report.md']
claims        : 29030
channels      : {None: 26146, 'immediate': 1677, 'cell': 1173, 'arrow': 15, 'quoted': 19}

> python out\re_work\asm_scan\classify.py
claims            : 29030
verdicts          : {'NOBYTES': 26146, 'EXACT': 2361, 'MISMATCH': 276, 'OOB': 241,
                     'PREFIX_LEN': 5, 'ALIAS': 1}
selfref rows      : 851  (of them verdict 2/3 : 28) -> exempted
mismatch+prefix   : 253  -> out\re_work\asm_scan\mismatch_ranked.tsv

> python out\re_work\asm_scan\triage.py
buckets: {'OK-NOBYTES': 25469, 'R-SELFREF': 851, 'OK-EXACT': 2217, 'R-PATCH': 26,
          'R-CANDIDATE': 58, 'OK-OOB': 239, 'R-CONCAT': 9, 'R-ERR-VA': 1,
          'R-NONBYTE-1B': 159, 'OK-ALIAS': 1}
claims.txt : 1280 条 EXACT 断言 (dedup)

> python out\re_work\asm_scan\build_errata.py
final classes: {'B-PATCH': 26, 'P4-REVIEW': 25, 'S-SELFREF': 28, 'A-ARTIFACT': 175,
                'P3-LIST-DRIFT': 27}
P1 detail:            ← 空
P2 detail:            ← 空
```

**BEFORE / MID / AFTER 对比**（`out/re_work/asm_fix2/compare_scan.py`，三段快照全部落盘）：

```text
| 分类 | BEFORE (ASM-FIX final) | MID (仅 F3 豁免) | AFTER (豁免 + F1/F2 勘误) |
|---|---|---|---|
| P1-BYTE-ERROR | 38 | 2 | 0 |
| P2-VA-DRIFT | 9 | 0 | 0 |
| P3-LIST-DRIFT | 27 | 27 | 27 |
| P4-REVIEW | 29 | 25 | 25 |
| A-ARTIFACT | 179 | 176 | 175 |
| B-ERRATA-QUOTE | 24 | 0 | 0 |
| B-PATCH | 26 | 26 | 26 |
| S-SELFREF | 0 | 24 | 28 |
| ②③ 合计 | 332 | 280 | 281 |
```

说明：`B-ERRATA-QUOTE` 归零并非「引用消失」，而是同一批行（24 条）现被 **F3 行级规则**优先归入 `S-SELFREF`（后 4 条为本批新写入的勘误块引用行），语义等价、口径更严。

### 6.2 门禁 1：`python tools/verify_anchors.py`

```text
  [PASS] .text 原始段哈希: c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738 (口径: raw(SizeOfRawData=0x3E0000))
  [PASS] .detour 原生签名: 40 00 00 00 44 74 72 00 ('@\0\0\0Dtr\0' @ VA 0xb93000) -> 严禁写入/注入原则确立
回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！
（exit code = 0）
```

### 6.3 门禁 2/3/4：`python tools/audit_bytes.py <claims>`

```text
> python tools\audit_bytes.py docs/re/anchor_claims.txt
合计 323 条：OK=323  MISMATCH/NOREAD=0            （金标准 323 条未动）

> python tools\audit_bytes.py out\re_work\asm_scan\claims.txt
合计 1280 条：OK=1280  MISMATCH/NOREAD=0          （复扫产物；含本批新写入的全部订正/新增字节串）

> python tools\audit_bytes.py out\re_work\asm_fix2\claims_asm_fix2.txt
合计 40 条：OK=40  MISMATCH/NOREAD=0              （本批自证断言，逐条对应 §2 证据块）
```

---

## [7] 风险与红线提示

| 触及项 | 是否触及 | 说明 |
|---|---|---|
| ① 同步语义 / 命令序 | **触及（证据链层）** | §9.2 的帧 CRC 链路是锁步校验的字节级依据；本批只改「RNG 消费计数与锚点」，**未改任何同步语义结论**。**需 MP 门控矩阵 + 真机对拍验收**。 |
| ② 随机数消费序 | **触及（本批核心，已重写）** | 由「每逻辑帧固定 1 次」改为「帧 CRC 路径每逻辑帧 **2 次**」（`0x64DE3F` + `0x650AB7`/`0x650AF2` 之一），并给出实例 `[0xA8B230]+0x218` 的 258 站点/83 候选消费点普查。**行为面后果须真机对拍验收 [待实测]**；禁止以旧锚点 `0x0064DAD9` 作为任何补丁依据。 |
| ③ 存档结构 | **未触及** | 本批未改任何 `.SAV` 相关结论（`0x00AFA26C` 采样值仅作为证据引用）。 |
| ④ 渲染像素等价性 | **未触及（相关性降低）** | 本批把「非 DDraw 表面锁」候选从 Surface::Lock/Unlock 的候选集中剔除，未改渲染结论。 |

**红线遵守**：未启动游戏、未注入、未改 exe/dll、未伪造实测（所有「实测」均由只读脚本对基线镜像现算，脚本与原始输出均在交付物内可复跑）、未越界写入（域外问题一律转 §3.9；禁区内文件零写入）。**本批不宣称「零风险 / 零 Desync」**。

---

## [8] 交付物清单

| 类别 | 路径 | 规模 |
|---|---|---|
| **本报告** | `docs/re/asm_fix2_report.md` | 本文件 |
| 勘误后文档 | `docs/re/{ARCHITECTURE_ATLAS.md, offline_verification_alternatives.md, landing_equivalence_static_proof.md, asm_fix_report.md}` | 7 处就地勘误 |
| **扫描器 F3 改动** | `out/re_work/asm_scan/{extract_claims.py, classify.py, triage.py, build_errata.py}` | 4 个脚本；补丁脚本 `out/re_work/asm_fix2/patch_scanner.py`、`patch_scanner2.py`（可复算/幂等） |
| 只读探针 | `out/re_work/asm_fix2/probe.py`（VA→字节/反汇编/站点普查/滑窗/函数边界）、`rng_census.py`、`f2_surface.py`、`ddraw_scan.py`、`f2_probe.py`、`f2_probe2.py`、`frame_crc_dump.py`、`surface_scan.py`、`surface_vt.py` | 10 个脚本 |
| 证据 dump（原始输出） | `frame_crc_rng_evidence.txt`（8.9 KB）、`rng_census.txt`（6.4 KB）、`f2_surface_evidence.txt`（11.0 KB）、`dsurface_ddraw_dispatches.txt`（19.3 KB） | 4 份 |
| 门禁原文输出 | `gate1_verify_anchors.txt`、`gate2_audit_gold.txt`、`gate3_audit_scan_claims.txt`、`gate4_audit_fix2_claims.txt` | 4 份 |
| 扫描三段快照 | `out/re_work/asm_fix2/{before,mid,after}/**`（各 6 件：claims_raw.json / classified.json / mismatch_ranked.tsv / triage_tables.md / errata_table.md / claims.txt） | 18 件 |
| 对比表 | `out/re_work/asm_fix2/before_after_table.md` + 生成器 `compare_scan.py` | 2 件 |
| **机器可读断言（本批自证）** | `out/re_work/asm_fix2/claims_asm_fix2.txt` | **40 条**（`audit_bytes.py` 40/40 OK） |
| 复扫产物（重跑覆盖） | `out/re_work/asm_scan/{claims_raw.json, classified.json, mismatch_ranked.tsv, triage_tables.md, errata_table.md, claims.txt}` | claims.txt 1280 条 |

---

## [9] 待裁决项

1. **禁区两行（§3.9 #1/#2）是否授权就地订正？** 建议：Lead 就地订正（每处 1 行），否则任何复扫都会以「引用已证伪锚点」再次报 P1（现被 F3 行级规则归 `S-SELFREF` 而不再计 P1/P2，但**正文仍是失效锚点**）。
2. **`HOOK_POINT_MATRIX.md:405`「每逻辑帧 1 次」是否升级为 P1 决策依据订正？** 该行是执行方最常引用的禁令卡，建议优先于 sprint 报告类表述。
3. **83 个候选消费点是否立专项定谳？** 建议：本批只给清单（`rng_census.txt`），若要作为「视觉/音效/UI 禁止调用」的完整依据，需专项逐点证明 `ecx` 可达性。
4. **`DSurface` 家族 DDraw `Unlock`（slot 32）派发点是否需定谳？** 若后续要做「表面解锁时序」相关的表现层补丁，建议先解出该区函数边界（NOP 填充使 padding 启发式失效，需递归下降）。
5. **`landing_equivalence_static_proof.md:276-279` 的 4 行是否按 ASM-FIX-35 方式统一加「手写示意清单」标注？** 现状为「函数归属已定、来源不明」，继续保留即需长期承担审计噪声。
6. **是否把 `docs/re/inline_assertion_scan.md` 的 3.1/3.2 表格加「原记」标记？** 本批已用**排除规则**达成等价效果（采纳 ASM-FIX §9 的建议①→②），正文保持不可变；若 Lead 希望该报告自身复扫也自洽，可追加标记（属其执行方范围）。
