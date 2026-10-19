# FOG-FIRSTSTAGE-R04b · `imul 184` 深挖定谳 + R-04 候选补完

> 任务：R-04b。复用 `out/re_work/re_sprint/fog_stage1_candidates/` 遗留产物，重点深挖 `0x45452c` 处 **imul 184** 立即数命中。
> 只读 `gamemd.exe`（MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`）。写域仅本文 + `fog_stage1_candidates/` 追加。
> 证据分级：[实证] 可从 exe 字节/反汇编直接复算；[推演] 语义解释；[待实测] 需真机。

---

## [0] `0x45452c` 定谳（P0，首节结论）

**结论：假阳性（FALSE_POSITIVE）。`0x45452c` 处不存在 `imul …, 184`。184 不是乘数，也不是查表偏移。与 ×0.71875(=184/256) 无任何关系。** [实证]

### 0.1 原扫描为何会命中

R-04 的 `s05_imul_and_blit.py:50-52` 用的是**朴素字节匹配**，没有解 ModR/M：

```python
for off in find_all(data, b"\x6B", ...):
    if data[off + 2] in (0x17, 0xB8):   # 6B ?? B8 就当 "imul imm8=184"
```

`imul r32, r/m32, imm8` 编码为 `6B /r ib`。仅当 ModR/M 的 **mod=11（寄存器形态）** 时 `ib` 才在 `6B` 后第 2 字节；一旦 mod≠11（内存形态），中间还夹着 disp8/disp32，`data[off+2]` 根本不是立即数。该扫描**系统性假阳性**。

### 0.2 `0x45452c` 处的真实字节与真实指令流 [实证]

文件偏移 `0x5452C` 起 8 字节：

```
6B 5F B8 03 00 00 00 5E
```

真实指令流（从 `0x45452B` 对齐反汇编，`disasm_imul23_184.txt` 与本卡 `r04b_imul184_adjudication.json` 一致）：

```
0045452B  74 6B              je    0x454598        ; 6B 是 rel8 位移
0045452D  5F                 pop   edi
0045452E  B8 03 00 00 00     mov   eax, 3
00454533  5E                 pop   esi
00454534  83 C4 0C           add   esp, 0xC
00454537  C2 08 00           ret   8
```

`0x45452C` 处的 `6B` 是 **`je rel8` 的位移低字节**，不是操作码。

若强行从 `0x45452C` 起解码（capstone）：

```
0045452C  6B 5F B8 03   imul  ebx, dword ptr [edi - 0x48], 3
```

ModR/M=`5F`（mod=01 ⇒ disp8）。此时 **`B8` 是 disp8（位移 = −0x48）**，真正的 imm8 是 `03`。所谓「imm=184」是把**位移字节**误认成**立即数**。

### 0.3 属主函数与路径归属 [实证]

- 属主函数入口 **`0x4544A0`**（`sub esp,0xC; push esi; mov esi,ecx; push edi`）。
- 符号表 `out/reverse/symbols.json` → **`BuildingClass.vfuncs[26] = 0x4544A0`**（BuildingClass vtable @ `0x7E3EBC`，共 322 项）。
- 该函数行为（`r04b_func_and_paths.json`）：
  1. 读 `this+0x6ED`（byte，与 10 / 5 比较，像阶段/状态量）；
  2. 取 `this+0x9C` 的坐标（lepton），`sar 8` 转格坐标；
  3. `mov ecx, 0x87F7E8; call 0x5657A0` → **MapClass::GetCellAt(coord)**（`0x5657A0` 计算 `index=(y<<9)+x`，界限 `0..0x40000` = 512×512 格，返回 `*(this+0x13C)[index]` 的 `CellClass*`）；
  4. `mov ecx, eax; call 0x4870D0` → `cmp word [ecx + edx*2 + 0x7C], 0; setg al`（**CellClass 格属性查询**，同族 `0x4870F0` 查 `+0xAC`）；
  5. 返回枚举 **3 或 5**（`ret 8`），另支路查 `this+0x41A`、vfunc `+0x328`、全局 `0xB73550`/`0xA8B238`/`0xA83D4C`、`call 0x4F9A50`。

**判定：这是 `BuildingClass` 的游戏逻辑谓词（返回 3/5 的状态查询），不在地表像素写入路径上（既不是 DrawTile/Blit，也不是 LightConvert/光照链）。** [实证·反汇编路径] + [推演·语义]

与环境光路径的对照：`0x4235FE` 也出现 `mov ecx,0x87F7E8; call 0x5657A0`，但下一句是 `call 0x487950`（IsShrouded）后**清零 ambient**——那是遮蔽判定后改光照累加器；`0x45452c` 这支是查完格属性就 `return 3/5`，**不写像素**。

### 0.4 与 ×0.71875(=184/256) 的关系

**无关。** [实证]

- 184 在此处不是乘数、不是除数、不是查表偏移，只是 `je rel8` 位移的巧合字节。
- 全库复核：**不存在**寄存器形态 `imul r,r,184`（`6B` mod=11 + imm=0xB8），也不存在 `imul r,r/m,imm32=184`（`69 /r`）。见 `r04b_func_and_paths.json.regform_imul_184 = []`、`regform_imul_imm32_184_23 = []`。[实证]
- 这与 R-01（`lightconvert_0x420140_deep_dive.md`）「公式常量层无 184/23/32」以及 `fog_firststage_rootcause.md`「静态扫描未见 184 立即数」**一致并加强**：现在有了**指令边界级**的否定证据，不只是常量扫描。

**定谳收口**：R-04 中间产物里的「`0x45452c` imul 184 命中」应从候选清单**撤除**。迷雾第一段 ×0.71875 **不是** `imul *,184` 形态的整数乘法。

---

## [1] imm=23 的 6 处（P1）：全部假阳性

`step5_summary.json` 的 6 个 imm=23 站点，逐个核对前驱字节（`r04b_imul184_adjudication.json.imm23_false_positive_analysis`）[实证]：

| naive VA | 真实指令形态 | 实际含义 |
|---|---|---|
| `0x64FA69` | `0x64FA68: E8 6B AD 17 00` = `call 0x7CA7D8` | rel32 高字节 `0x17` |
| `0x6505A8` | `0x6505A7: E8 6B 88 17 00` = `call 0x7C8E17` | 同上 |
| `0x651561` | `0x651560: E8 6B 7C 17 00` = `call 0x7C91D0` | 同上 |
| `0x651D69` | `0x651D68: E8 6B 8A 17 00` = `call 0x7CA7D8` | 同上 |
| `0x655ACE` | `0x655ACD: E8 6B 30 17 00` = `call 0x7C8B3D` | 同上 |
| `0x656914` | `0x656913: 7E 6B` = `jle +0x6B` | **jcc rel8 位移**，与 `0x45452c` 同型 |

五处是 CRT 堆函数（`0x7C8xxx/0x7C9xxx/0x7CAxxx`）的 `call rel32` 位移高字节被误读为 imm；一处是 `jle rel8` 位移被误读。

**与 23/32=0.71875 的关系：无关。** [实证] 全库同样**不存在**寄存器形态 `imul r,r,23`（`regform_imul_23 = []`）。

---

## [2] AA10D0 / AA10C0 在 DrawTile 族的调用语义（P1）

DrawTile `0x547CF0` 参数链（claims 1–10，`audit_claims.json` 18/18 OK）+ 像素环（`0x5487B0`）给出双级查表结构 [实证]：

```
; —— 表基址装填（0x547D78..0x547DE2）——
mov  eax, [arg0 + 0x16c]        ; LightConvert Level
mov  ecx, 0x87E8A8
push eax
call 0x420140                   ; AlphaLightingRemapClass::FindOrAllocate(Level)
mov  edi, eax                   ; 65536 项表基址（R-01 已证公式 q=floor(lo·hi·(L−1)/32258)）
; hi-slice = clamp254( (max(arg,0)*261) >> 11 )
shl  eax, 9                     ; 切片步长 = 512 项
add  eax, edi
mov  [0xAA10D0], eax            ; AA10D0 = 表基址 + hi_slice*512
mov  ecx, [arg0 + 0x170]
mov  [0xAA10C0], ecx            ; AA10C0 = 第二级表指针

; —— 像素环（0x5487B6..0x5487E6）——
mov  cx, [0xAA10C8]             ; src（16-bit 索引）
mov  ax, [edx + ecx*2]          ; edx=AA10D0 → 第一级 LightConvert 查表 → 16-bit 色
mov  cl, [0xAA10B8]             ; ambient 字节
or   eax, ecx                   ; 累加环境光
mov  dx, [ecx + eax*2]          ; ecx=AA10C0 → 第二级表查表
mov  [dst], dx                  ; 写 16-bit 像素
```

语义判定 [推演]：

- **AA10D0** = LightConvert 65536 项 16-bit 转换表的**当前切片基址**（`hi_slice<<9` 步长）。8/9-bit 源色 → 16-bit（RGB555/565）光照转换色。
- **AA10C0** = 来自绘制参数 `arg0+0x170` 的**第二级 16-bit 查表**（再映射/调色板混合）。
- **0xAA10B8** = 8-bit ambient 累加（`or`）。
- 像素公式：`dst16 = Table2[ Table1[src] | ambient ]`。

**对第一段 ×0.71875 的含义**：代码层只有「查表 + OR」，**没有**乘法。若 0.71875 真在地表写入路径上，只能藏在 **Table1 内容（运行期生成）**、**Table2（arg0+0x170）内容** 或 **ambient 值** 里——静态扫描天然读不到，与 `fog_firststage_site_locate.md` U1/C1 降权后的局面一致。R-01 已证 Table1 生成公式**不含** 0.71875，故剩余落点收窄到 **Table2** 与 **ambient**。[推演]

AA10D0 共 9 处 xref，全部在 DrawTile 族（`0x547Dxx`–`0x5497xx`）：1 处装填 + 8 处像素环。[实证]

---

## [3] 82 个 lerp 簇中是否有地表向灰插值（P2）

### 3.1 渲染带子集

s05 宽扫（sub+imul+shift，32B 窗）82 簇；落在 `0x47F000–0x55A000`（DrawTile/Blit/Convert 带）的有 **37 个**（`r04b_imul184_adjudication.json.lerp_clusters_in_render_band`）[实证]。

### 3.2 逐类甄别

| 站点 | 反汇编 | 判定 |
|---|---|---|
| `0x547F74` / `0x547F8F`（DrawTile 内） | `sub ecx,eax; and ecx,0xFFFF; imul eax,[esp+0x54]; sar eax,1; neg; add` | **坐标/偏移整数运算**（半宽折算），非颜色插值 [实证] |
| `0x53B850` 簇（函数头 `0x53B560`） | RGB555 通道拆分 `and 0x1F` / RGB565 `and 0x3F`，`sub reg, 0x1F/0x3F; imul reg, t; sar 8; add reg, c` | **向白插值** `out = c + (max−c)·t/256`（max=31/63），不是向灰 [实证] |
| `0x4843B6` | `div edi` + 魔数 `0x10624DD3` `sar 6`（÷100） | 百分比/进度算术，非颜色 [实证] |

### 3.3 「向常量灰 g」定点扫描

形态：`mov r, g; sub r, c; imul; sar; add`，g∈[40,120]（对应 g≈67–72）。
结果（`r04b_gray_lerp_scan.json`）：5 命中，`gray_imm` 全部为 **63**（RGB565 绿通道上限）或 **100**（百分比），**无一落在 67–72 灰区间**。[实证]

**结论**：82 簇中**未发现**地表「向灰（g≈67–72）插值」。渲染带内唯一颜色插值是 **0x53B850 的向白衰减**，且属 `0x53B560` 屏幕效果状态机（读全局 `0xA9FAB0` 做 `jmp [eax*4+disp]` 分派），不是地表 Tile 光栅化内核。[实证+推演]

---

## [4] 浮点面复核（覆盖 fmul/fld/fstp/movsd/mulsd 口径）

| 常量 | 对齐扫描结果 | 备注 |
|---|---|---|
| `double 0.71875` | **0 命中** | [实证] `r04b_func_and_paths.json` |
| `float 0.71875` | 仅 `0x803F4E` | 已知非对齐/结构体尾部巧合（`fog_firststage_site_locate.md` Q1）[实证] |
| `float/double 184.0` | **0 命中** | [实证] |
| `float 23.0` | 1 处 `0x8041CE` | 与 23/32 无关 [实证] |
| `double 256.0` | `0x7E1710` | 常规缩放常量 [实证] |

`0x7ED0B0 = 0.065536`（LightConvert 侧，claims 15）等邻域常量亦无 0.71875。与 R-01 静态穷举否定**一致**。[实证]

---

## [5] 候选清单收口（对照 `fog_firststage_site_locate.md`）

| 候选 | R-04b 状态 | 依据 |
|---|---|---|
| C1 `0x420140` LightConvert 表生成 | **维持降权**（R-01 否定） | 公式无 184/23/32；本卡再证无 imul 184 |
| C2 `0x665650` 光照对象 | 未动 | 仍待实测字段 |
| **R-04 遗留 `0x45452c` imul 184** | **撤除（假阳性）** | 本文 §0 |
| **R-04 遗留 imm=23 ×6** | **撤除（假阳性）** | 本文 §1 |
| U1 表内是否含 0.71875 | 已由 R-01 结案（不含） | — |
| **新收窄：AA10C0 第二级表（arg0+0x170）** | **新候选** [推演] | DrawTile 像素环第二查表，内容静态不可见 |
| **新收窄：ambient（0xAA10B8 / 0x423621 路径）** | **维持** | 环境光累加；`0x487950` IsShrouded 可清零 |
| 82 lerp 簇 | **无向灰** | §3 |
| 0x4544A0 BuildingClass vfunc[26] | **排除** | 不在像素写入路径 |

**剩余搜索面（P0 级，下一步）**：
1. AA10C0 第二级表来源（`arg0+0x170` 的写入者/生成者）；
2. ambient 值合成链（`0x423580` 附近 5:5:5/5:6:5 打包后 `sar 8` 归一，再 `0x423621` 遮蔽清零）；
3. 真机只读断点（`0x47F40F` / `0x547CF0`）做写入/原始像素比值判定——静态已排除「imul 184」后，此断点仍是机理判定的唯一硬证据 [待实测]。

---

## [6] 交付物清单

**报告**：`docs/re/fog_firststage_candidates_deep_dive.md`（本文）

**`out/re_work/re_sprint/fog_stage1_candidates/` 追加**（不删已有）：

| 文件 | 内容 |
|---|---|
| `s09_imul184_adjudication.py` | 正确解码复核 + 假阳性归因 + AA10/lerp 首扫 |
| `r04b_imul184_adjudication.json` | 字节级定谳、真/假 imul 对比、imm23 FP 表、AA10 窗口、渲染带 lerp |
| `s10_func_and_paths.py` | 属主函数定界、寄存器形态 imul 全库复核、浮点常量复核 |
| `r04b_func_and_paths.json` | `0x4544A0` 函数反汇编、`0x4870D0`/`0x5657A0` 语义、DrawTile 头、regform=∅ |
| `s11_gray_lerp_scan.py` | 向灰插值形态定点扫描 |
| `r04b_gray_lerp_scan.json` | 5 命中均为 63/100，无 g≈67–72；`0x53B560` 函数头 |

---

## [7] 一句话收口

**`0x45452c` 的「imul 184」是扫描器未解 ModR/M 造成的假阳性——`6B` 实为 `je rel8` 的位移字节，`B8` 实为误解码中的 disp8；全库不存在任何 `imul r,r,184/23`。×0.71875 不是代码层立即数乘法，地表像素链是 `dst = Table2[Table1[src]|ambient]` 的双级查表；第一段系数若存在，只能在 Table2/ambient/运行期表内容中，或根本是 DLL 侧经验拟合常量（`fog_cal3` 已定位 `0x423060`）。**
