# 建筑是否逐格取光照 —— 0x00705E00 逐格性诊断（U3-LIGHTPERCELL）

> [META]
> task=U3-LIGHTPERCELL  executor=DSH 子代理（父会话 session-852a2193-df41-4859-b6f3-cd17f595410f）  elapsed≈1450s  mode=read-only
> scope_declared=允许写 `docs/re/building_percell_light_rootcause.md` + `out/re_work/u3_light/**`；禁止写 ra2render/**、ra2youli/**、台账、docs/RE_COORDINATION.md、其他 docs
> 基线（只读，未打补丁）：`ra2youli/gamemd.exe` 4,825,360 B / MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`
> 只读引用（未修改）：`ra2youli/ra2render.dll` 148,992 B / MD5 `EAAA1BE95BE88BCC67F58A2AFD1A42C9`
> 工具：Python 3.12.10 + Capstone 5.0.7 直接反汇编；段映射 VA→FileOffset（.text 段 VA−rawptr = 0x400000）
> 证据文件：`out/re_work/u3_light/`（claims.txt=55 条断言 / dump_705E00.txt=653 条指令全反汇编 / 5 个脚本）

---

## [0] 结论摘要

**否 —— `0x00705E00` 及其调用链/上游不对建筑"每一格"分别取光照，也不逐格判 shroud/fog。**
最短证据链：① `0x705E00` 全长 0x809 B（0x705E00–0x706608；`0x706609 C2 40 00`=`ret 0x40` ⇒ 16 个栈参），**653 条指令内反向跳转 = 0 条** ⇒ 函数体**无任何循环**，结构上不可能逐格迭代；② 光照值全函数**只物化一次**（`0x7063E0 33 C0` 或 `0x7063E4 8B 84 24 80 00 00 00 mov eax,[esp+0x80]`），随后 3 个写屏点各 `push eax` 一次后共用；③ 核内 shroud 判定只有 1 处（`0x7063D7 call 0x487950`），格子来自 `0x706392 call [edx+0x48]`(GetCoords) 的**中心格**，与调用方 `0x43D539` **同格**；④ `0x705E00` 的 9 个调用点**全部落在 `BuildingClass::Draw` 的 3 个循环体之外**。
⇒ 「跨边界建筑半亮半黑」**不是**本函数产生的逐格明暗差；引擎侧唯一的**逐格像素**机制是逐格 shroud/fog 瓦片叠加（`0x4801F0→0x480230→0x47EFE0`，唯一调用者），它作用于"格"而非"对象"，且不参与建筑光照。
最大风险：本条为**纯静态**结论；`0x47EFE0` 逐格瓦片层与对象层的前后次序未闭环（见 [4] U3-P1）。

---

## [1] 逐条必答项结论表

| # | 问题 | 结论 | 证据等级 | 证据锚点 |
|---|---|---|---|---|
| U3-1 | `0x705E00` 内是否存在逐格循环？ | **否**：0x705E00–0x706608 共 653 条指令，**反向跳转 0 条**、跳出到 <0x705E00 的跳转 0 条 | [实证] | 0x706609=`C2 40 00`；`out/re_work/u3_light/dump_705E00.txt`；`scan_705E00.py` |
| U3-2 | 光照色是对象级取一次还是逐格重取？ | **对象级取一次**：唯一读点 `0x7063E4 8B 84 24 80 00 00 00`(`mov eax,[esp+0x80]`=arg11)，唯一清零点 `0x7063E0 33 C0` | [实证] | 0x7063E0 / 0x7063E4（claims #23/#25） |
| U3-3 | 上游 `0x43D638 push edi` 在核内是否被复用/覆盖？ | **被 `0x7063E0` 覆盖后统一使用**：arg11↔`[esp+0x80]` 已由 16 参栈核算 + 两处早调用 ret N 证明 | [实证] | 0x43D638=`57`；0x706609=`C2 40 00`；0x454537=`C2 08 00`；0x447B11=`C2 04 00` |
| U3-4 | 核内 shroud/fog 判定的粒度？ | **单格（中心格）**：核内 `call 0x487950` 仅 1 处，格源 = GetCoords→`sar 8`→GetCellAt | [实证] | 0x706392 / 0x7063D0 / 0x7063D7；全函数调用清单见 [2] E-4 |
| U3-5 | `0x705E00` 是否被"逐地基格"调用？ | **否**：9 个直呼点全部在 `BuildingClass::Draw` 的 3 个循环体之外 | [实证] | 0x43D2F5 / 0x43D7DE=`E9 F8 FE FF FF` / 0x43DC16=`0F 8C F5 FE FF FF` |
| U3-6 | 「半亮半黑」是否为引擎原生逐格行为？ | **不是逐格光照**；引擎原生逐格像素机制是逐格 shroud/fog 瓦片叠加（`0x47EFE0`），层级待闭环 | [实证]（机制）+ [待实测]（层级/表现） | 0x4801F0 / 0x480230=`E8 AB ED FF FF` / 0x47F207=`C2 0C 00` |

---

## [2] 关键证据块（VA / FileOffset / 原始字节 / Capstone / xref）

**E-1 函数边界与"零循环"**
```asm
00705E00  8B 44 24 04                mov  eax,[esp+4]      ; arg1 位于 E+4（早于 sub esp）
00705E04  83 EC 44                   sub  esp,0x44
00706609  C2 40 00                   ret  0x40             ; ⇒ 16 个栈参；函数体 = 0x705E00..0x706608 (0x809 B)
0070660C..0070661C                   jmp-table A (5 项, 0x705E3E 用)
00706620..00706630                   jmp-table B (5 项, 0x7063F8 用)  ⇒ 下一函数起于 0x706634
```
全函数线性反汇编 653 条指令：**反向跳转 0 条**，`jmp/jcc` 目标落入 <0x705E00 者 0 条。FileOffset 与 VA 同值（.text）。

**E-2 光照值唯一物化 + 3 处写屏各 push 一次**
```asm
007063D7  E8 74 15 D8 FF             call 0x487950          ; CellClass::IsShrouded()（核内唯一）
007063DC  84 C0                      test al,al
007063DE  74 04                      je   0x7063E4
007063E0  33 C0                      xor  eax,eax           ; ★光照 := 0（分支 A）
007063E2  EB 07                      jmp  0x7063EB
007063E4  8B 84 24 80 00 00 00       mov  eax,[esp+0x80]    ; ★arg11 = 光照色（唯一读点，分支 B）
007063EB  8B 4C 24 18                mov  ecx,[esp+0x18]    ; 绘制模式 1..5
007063EF  83 F9 04                   cmp  ecx,4
007063F2  0F 87 0A 02 00 00          ja   0x706602          ; >4 ⇒ 尾部
007063F8  FF 24 8D 20 66 70 00       jmp  [ecx*4+0x706620]  ; 5 路派发 → 3 个写屏体
--- 三路写屏体，各自把同一个 eax 推入 ---
00706423  50                         push eax   ; 写屏体1 → 00706458
007064FB  50                         push eax   ; 写屏体2 → 0070652D
007065CB  50                         push eax   ; 写屏体3/4/5 → 007065FD
0070644F / 00706525 / 007065F5  8B 0D 14 73 88 00  mov ecx,[0x887314]  ; DSurface::Hidden_2
00706458 / 0070652D / 007065FD  E8 ..                    call 0x4AED70       ; 全屏面写 3 处
```
表中 5 项目标 = {0x7063FF, 0x7064D4, 0x7065A3, 0x7065A3, 0x7065A3}；且 0x70645D `8A 44 24 13` 读 `[esp+0x13]`
说明 0x4AED70 是**被调方清栈**（14 参）⇒ 调用点前后 esp 无残余，`push eax` 就是光照位。

**E-3 上游 arg11 = 光照色（独立栈核算，非结构推测）**
```asm
0043D4F4  FF 52 48          call [edx+0x48]      ; v[18] GetCoords 0x447AC0 (ret 4 @0x447B11)
0043D532  E8 69 82 12 00    call 0x5657A0        ; MapClass::GetCellAt(中心格)
0043D539  E8 12 A4 04 00    call 0x487950        ; IsShrouded()  ← 仅中心格
0043D542  33 FF             xor  edi,edi         ; ★光照:=0（不跳绘制）
0043D638  57                push edi             ; ★第 12 次压栈 = arg11（16 参中）
0043D674  68 00 01 00 00    push 0x100           ; arg6
0043D683  E8 78 87 2C 00    call 0x705E00
0043D68F  C2 08 00          ret  8
```
核算：`mov eax,[esp+4]` 早于 `sub esp,0x44` ⇒ arg1@E+4；早调用 `[edx+0x68]`=v[26]=0x4544A0
`ret 8`(0x454537)、`[edx+0x48]` `ret 4`(0x447B11) 均栈平衡 ⇒ esp=E−0x54 ⇒ `[esp+0x80]`=**arg11**。
调用方 16 次压栈（最后压者=arg1）：arg16..12 = 0x43D62F/630/631/632/633；**arg11 = 0x43D638(push edi)**；
0x43D64D/64E/650 三次压栈被 v[116]=0x5F5F30（0x5F5F36 `C3`=ret 无参）证明**未**被内层消费，仍属外层。
vtable `0x007E3FD0 = 90 D2 43 00`（BuildingClass v[69] = 0x0043D290）与 `0x007E3F04`(v[18]) 交叉一致。

**E-4 `0x705E00` 全函数对外调用清单（决定"是否还有别的取光/判定/写屏"）**
接口调用仅 4 组：`0x5657A0`(GetCellAt) ×2（0x705F1C / 0x7063D0，**均为中心格**）、`0x487950`(IsShrouded) ×1（0x7063D7）、
`0x4AED70`(写屏) ×3（0x706458 / 0x70652D / 0x7065FD）；其余为辅（`0x483E30` 初始化、`0x6D20E0` 高度、`0x69E7E0` 矩形、
`0x50B6F0`、`0x70E380/0x70E4B0`）与虚调用（`[edx+0x68]`=`0x4544A0`、`[edx+0x48]`=`0x447AC0` 等）。
**没有任何一处对"地基/格数组"取光或判定 shroud 的调用。**

**E-5 xref：`0x705E00` 的 9 个直呼点均不在循环内**
```
call 0x705E00 = { 0041C0E0, 0043D1A4, 0043D27A, 0043D683, 0043D85F, 0043D8E9, 0043D9C9, 0043DA67, 0043DF3F }
BuildingClass::Draw 区段 0x43D000..0x43E100 内循环仅 3 个（含 back-edge 字节）：
  0x0043D2F5 .. 0x0043D306  jne 0x43d2f5   （Anims[21] 附属动画环）
  0x0043D6DB .. 0x0043D7DE  jmp 0x43d6db   （0x43D7DE = E9 F8 FE FF FF）
  0x0043DB11 .. 0x0043DC16  jl  0x43db11   （0x43DC16 = 0F 8C F5 FE FF FF）
⇒ 上述 9 个调用点对 3 个循环体的包含判定结果**全为"不在"**。
```

---

## [3] 勘误

| 目标文件:行号 | 改前原文 | 改后文本 | 理由 | 影响面 |
|---|---|---|---|---|
| `docs/re/building_fog_residual_deep_dive.md:83` | 「`CellClass::Draw`（以及 L3 中挂接在 `0x004801F0` 的半透明灰雾 `Draw_Fog` 0x0047F250）是在**图层底层**运行的。」 | 「该层相对**对象层**的前后次序尚未静态闭环（见 [4] U3-P1）：`0x4801F0` 的调用者仅 `0x6D3716`/`0x6D751A`，均不在 `TacticalClass::Render` `0x6D3870–0x6D4400` 内，与 `docs/re/ARCHITECTURE_ATLAS.md:426` 的 "Pass 8（迷雾与 UI 叠加）" 记述**互相冲突**。」 | 本任务实测 `call 0x4801F0` 仅 2 处且都在 `0x6D3870` 之前；"底层"这一断言当前**无字节级支撑**，而它直接决定"半块"归属 | 影响产品决策：是否把"跨边界半块"归因于引擎；不影响已验证的逐格光照结论 |
| `docs/re/building_fog_residual_deep_dive.md:73` | 「`xor eax, eax`（调色盘亮度置为 0）」 | 建议补全为「光照色 arg11 被整体替换为 0；随后**该单一值**经 `0x7063F8` 派发到 3 个写屏体共用（`push eax` @0x706423/0x7064FB/0x7065CB）」 | 原文未点明"单值共用"，易被误读为逐格亮度 | 表述性，不影响结论 |

其余既有文档（`fog_partial_building_rootcause.md`、`fog_split_report.md`）关于"单格采样、整体生效"的记录与本次字节复核**一致**，无勘误。

---

## [4] 未闭环清单

| 缺口 | 为何无法静态闭环 | 下一步取证方法（可直接执行） | 阻塞级别 |
|---|---|---|---|
| U3-P1：`0x47EFE0` 逐格 shroud/fog 瓦片层相对**对象层**的绘制前后次序 | `call 0x4801F0` 仅 2 处（`0x6D3716`/`0x6D751A`），二者均不在 `TacticalClass::Render` `0x6D3870–0x6D4400` 区间内；其外层函数入口用 `0xCC` 填充启发式扫描**未定位**（0x6D3716 处无填充），需全量函数边界表才能定序 | ① 在 `0x47EFE0` 入口下**只读**断点记录返回地址链（期望出现 `0x6D3716` 或 `0x6D751A`，再向上 2 层）并与 `0x6D3870` 内 Pass 5（建筑物）调用点比较序号；② 纯静态替代：以 `0x6D3716` 为锚向低地址扫 `push ebp; mov ebp,esp` 或 `sub esp,` 序言，重建函数边界后 xref | P1 |
| U3-P2：「半亮半黑」的最终像素归因 | 需真机复现；本条只否证了"引擎逐格光照" | 沿用 `docs/re/fog_partial_building_rootcause.md` §F5 的 E1/E2 设计（单变量：中心格跨 shroud 边界 + 迷雾开关），叠加 U3 的判据：若同一栋建筑的暗区边界**沿格菱形（dx/dy=−2.00）**则指向逐格瓦片层；若**沿 sprite 自身 extent** 则指向对象级零光照 | P1 |

---

## [5] 写作用域合规声明

**新增（唯一改动）**：`docs/re/building_percell_light_rootcause.md`（本文件，约 7.5 KB）；
`out/re_work/u3_light/`（`FINDINGS.md`、`claims.txt`、`dump_705E00.txt`、`scan_705E00.py`、`dump_core.py`、
`recon.py`、`branch_check.py`、`loops_and_passes.py`、`vtable_probe.py`、`layer_order.py`、`gen_claims.py`）。
**未触碰**：`ra2render/**`、`ra2youli/**`（含 `gamemd.exe`/`ra2render.dll`，全程只以 `open(...,"rb")` 读取）、
台账、`docs/RE_COORDINATION.md`、任何其他 `docs/**` 文件。
**二进制只读证明**：`gamemd.exe` 4,825,360 B / MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`；
`verify_anchors.py` 基线审计 `.text` 原始段哈希 `c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738` PASS。

---

## [6] 门禁实跑输出（原文）

```
> python tools/verify_anchors.py
  回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
  ★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！
  [PASS] .text 原始段哈希: c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738 (口径: raw(SizeOfRawData=0x3E0000))

> python tools/audit_bytes.py out/re_work/u3_light/claims.txt
  合计 55 条：OK=55  MISMATCH/NOREAD=0
```
（claims 解析：`0x43D683 E8 78 87 2C 00`、`0x7063E0 33 C0`、`0x706609 C2 40 00`、`0x70660C 4F 5E 70 00` 等 55 条全 OK。）

---

## [7] 风险与红线提示

1. 本次为**纯静态、只读**诊断：**未启动游戏、未注入、未修改任何二进制、未加载 DLL**；所有反汇编均由 Python+Capstone 离线读取文件完成。
2. 是否触及 ①同步语义/命令序：**否**（判定位于渲染期，不写游戏逻辑状态）；②随机数消费序：**否**（全程无 RNG 引用）；③存档结构：**否**；④渲染像素等价性：**是**——本结论直接用于解释"跨边界建筑半块"的像素表现，**若据此改动建筑光照/shroud 判据，需要 MP 门控矩阵/真机对拍验收**，禁止宣称"零风险/零 Desync"。
3. 结论强度自限：本条只否证"引擎在建筑绘制链上逐格取光照"；**不**否认存在其它逐格机制（逐格瓦片叠加层 U3-P1 未闭环）。

---

## [8] 交付物清单

- 新文档：`docs/re/building_percell_light_rootcause.md`（本文件，10 节骨架）
- 结论落盘：`out/re_work/u3_light/FINDINGS.md`
- 字节断言：`out/re_work/u3_light/claims.txt` —— **55 条**（audit_bytes 全 OK）
- 反汇编 dump：`out/re_work/u3_light/dump_705E00.txt`（653 条指令全量，含控制流目标标记）
- 脚本：`out/re_work/u3_light/` 共 **11 个**（含 `gen_claims.py` / `scan_705E00.py` / `recon.py` / `branch_check.py` / `loops_and_passes.py` / `layer_order.py` / `vtable_probe.py`）

---

## [9] 待裁决项

1. **「一半」归因口径**：建议把本条结论登记为"引擎**不**逐格取光照"的**定谳**，并把 U3-P1（逐格瓦片层与对象层的层次）单列为 P1 取证件；理由：逐格光照已被 4 条独立字节证据否证（无循环 / 单值共用 / 单格判定 / 调用点不在循环内），而层次问题需要真机或函数边界表。
2. **是否修正 `building_fog_residual_deep_dive.md:83` 的"图层底层"表述**：建议由 Lead 裁定（本任务无该文件写权限，已列入 [3] 勘误）；若保留原文，建议至少加注"相对对象层的次序未闭环"。
3. **U3-P2 实验归属**：建议与 `fog_partial_building_rootcause.md` §F5 的 E1/E2 合并为一次真机单变量实验，避免重复开游戏。
