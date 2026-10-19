# FOG-MIXING-SITE · 「灰雾第一段 ×0.71875(23/32)」代码站点深挖定谳

> [META]
> task=R-FOG-STAGE  executor=R 轨子代理  日期 2026-10-02  mode=static-only
> 基线（只读）：`ra2youli/gamemd.exe` 4,825,360 B / MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367` · ImageBase `0x400000` · FileOffset=VA−0x400000
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> 写域：本文 + `out/re_work/re_sprint/R_fog_stage/**`
> 证据等级：`[实证]`（字节/反汇编可复算）/ `[推演]` / `[待实测]`
> 目标：定位 ×0.71875 乘性/混色常数的**代码站点**（不是再证明常数存在）

---

## [0] 结论摘要（≤5 行）

1. **LightConvert `0x420140` 表生成：关闭（否定）**[实证·可复算]。表公式 `q=floor(lo·hi·(L−1)/32258)` 无 0.71875/23/32/184 常量层（R-01 全量 1,048,576 项已证）；本轮补充证明其**消费端**（DrawTile 像素环）把表输出当作 BufferA 色号切片选择子，合成映射是 **lo×hi 双线性**，不可能等于常数 ×0.71875。
2. **ConvertClass BufferA 着色表（`0x4bbb00` / ctor `0x48E800`）是唯一能在机制上产出 ×0.71875 的静态站点**[实证]：切片 k 的倍率 = `2k/(ShadeCount−1)`；`(S,k)=(65,23)/(129,46)/(257,92)` 恰为 23/32。但全库 ConvertClass 构造的 shadeCount 实测恒为 **0x35=53 或 1**，S=53 下**无整数切片**等于 23/32（最近 k=19 → 0.7308，误差 +1.7%）。
3. **像素环 `dst=Table2[Table1[src]|ambient]`（`0x5487B9–0x5487EB`）无乘法**[实证]；原版 Draw_Fog B1/B2 为加性 `dst=max(0,dst+fog−127)`（`0x47F42F`/`0x47F4D0`），已被我方桩替换，第一段不在其中。
4. **全渲染带无 imm=23/184 真操作数、无 ×9/32 混色形态、无 float/double 0.71875**[实证]。`0xB71D`（任务卡所称 Q16）6 处原始命中均为数据/结构巧合，无一是指令立即数。
5. **站点判定：未定位到离散乘法/混色指令**。0.71875 最可能是 **ConvertClass 着色表 + 调色板最近邻量化** 在雾格所用光照切片上的**等效合成增益**（经验拟合），而非字面 `×23/32`。剩余候选与最小真机探针见 §[F5]。

---

## [1] 逐条必答项结论表

| # | 问题 | 结论 | 证据等级 | 证据锚点 |
|---|------|------|----------|----------|
| Q1 | LightConvert `0x420140` 表生成是否含 ×0.71875？ | **否（结案）**。公式常量层无 184/23/32；消费端合成映射为双线性 | [实证] | R-01 `verify_closed_form.json` + 本文 §[3] |
| Q2 | 是否存在 `imul/lea ×23/32` 或 `×184/256` 指令？ | **否**。全 .text 无寄存器形态 `imul r,r,23/184`；渲染带无 imm=23/184 真操作数 | [实证] | `s01_scan_results.json`、`s05_final_scan.txt` |
| Q3 | 是否存在 `×9/32`（=1−23/32）混色形态？ | **否**。渲染带 0 命中；全 .text 仅 2 处 `lea [eax+eax*8];sar 5`，属十进制格式化 `/10` 魔数序列（假阳性） | [实证] | `s05_final_scan.txt` §5 |
| Q4 | ConvertClass BufferA 着色表能否产出 23/32？ | **机制可以、静态参数不吻合**。倍率 `2k/(S−1)`；精确解需 S∈{65,129,193,257…}；实测 S=53/1 | [实证] | `s04_shade_blitter.txt` §1、ctor 扫描 |
| Q5 | DrawTile 像素环是否有乘法？ | **无**。`dst=Table2[Table1[src]\|ambient]` 纯查表+OR | [实证] | `s03_convert_blitter.txt` 0x5487B9–0x5487EB |
| Q6 | 原版 Draw_Fog B1/B2 是否含 ×0.71875？ | **否**。加性 `dst+fog−127`，且已被桩替换 | [实证] | `s05_final_scan.txt` §1 |
| Q7 | float/double 0.71875 是否存在？ | **否**（仅 1 处非对齐巧合 `0x803F4E`） | [实证] | `s01_scan_results.json` |
| Q8 | 0xB71D（Q16）是否为指令立即数？ | **否**。6 处原始命中均为数据巧合 | [实证] | `s02_context.txt` §1 |
| Q9 | 最终站点 | **未定位**。等效增益最可能来自着色表+调色板量化合成 | [实证]排除 + [推演]残余 | 本文 §[F5] |

---

## [2] 新增证据块（本轮，全部可复算）

### 2.1 ConvertClass BufferA 着色表生成 `0x4bbb00`（16-bit 表面路径）[实证]

```
; edx = ShadeCount(S), ecx = BufferA 基址, [esp+0x20] = 调色板
; 外层 k = 0, 1, 2, …, S−1；每切片 256 个 WORD
0x004BBB3B  mov eax, [esp+0x10]      ; k * 0x20000（外层索引）
0x004BBB3F  lea ecx, [esi-1]         ; S−1
0x004BBB43  idiv ecx                 ; factor = k*0x20000 / (S−1)
0x004BBB6B  mov dl, [ecx]            ; R
0x004BBB74  imul esi, eax            ; R * factor
0x004BBB84  sar esi, 0x10            ; R' = R * factor / 65536
; G/B 同式；然后 pack RGB565（用 [0x8A0DD0..0x8A0DE4] 位域移位常量）
0x004BBBEC  mov [ebx-2], dx          ; BufferA[k*256 + j] = scaled_color
```

**闭式**：`BufferA[k][j] = pack565( palette[j].rgb × 2k/(S−1) )`（clamp 255）。
`factor = k·0x20000/(S−1)`，`color·factor>>16 = color·2k/(S−1)`。[实证·可复算]

**精确 23/32 解**（`2k/(S−1) = 23/32` ⇒ `64k = 23(S−1)`）[实证]：

| S | k | 倍率 | 误差 |
|---:|---:|---:|---:|
| **65** | **23** | **0.718750** | **0** |
| **129** | **46** | **0.718750** | **0** |
| 193 | 69 | 0.718750 | 0 |
| **257** | **92** | **0.718750** | **0** |
| 53 | 19 | 0.730769 | +0.012 |
| 53 | 18 | 0.692308 | −0.026 |

### 2.2 ConvertClass 构造 shadeCount 实测 [实证]

全库 `call 0x48E740`（ConvertClass ctor）共 22 处。紧邻 `push` 立即数：

| shadeCount | 出现 | 备注 |
|---:|---:|---|
| **0x35 = 53** | 6+ 处（`0x4B6ED7`/`0x52BE27`/`0x52BEF6`/`0x52BFAA`/`0x52C112`/`0x54506D`…） | THEATER_PAL / ANIM_PAL 等标准调色板 |
| **1** | 10+ 处 | 简化转换（无着色切片） |
| 0x188 = 392 | 3 处 | 后续 `new` 大小，非 shadeCount |

**无 65/129/257**。⇒ 静态构造参数下 BufferA **不可能**恰为 23/32。[实证]

### 2.3 DrawTile 像素环（`0x5487B9–0x5487EB`）[实证]

```
0x005487B9  mov edx, [0xAA10C8]      ; src 指针
0x005487C3  mov cx, [edx]            ; 16-bit 源像素
0x005487C6  mov edx, [0xAA10D0]      ; Table1 = AlphaLightingRemap 切片
0x005487CC  mov ax, [edx+ecx*2]      ; t = Table1[src]
0x005487D0  mov edx, [0xAA10B8]      ; 并行字节流指针
0x005487D8  mov cl, [edx]            ; ambient/原 8-bit 色号
0x005487DA  or  eax, ecx             ; idx = t | ambient
0x005487DC  mov ecx, [0xAA10C0]      ; Table2 = ConvertClass BufferA
0x005487E2  mov dx, [ecx+eax*2]      ; dst = BufferA[idx]
0x005487EB  mov [eax], dx            ; 写像素
```

**无任何 imul/fmul**。若 Table1 输出为 `q<<8`（R-01 已证低字节恒 0），则 `idx = q·256 + ambient`，即 **切片 q × 色号 ambient**。合成输出 = `palette[ambient] × 2q/(S−1)`。因 `q = floor(lo·hi·(S−1)/32258)` 随源色变化，**合成倍率非常数**，与「恒定 ×0.71875」矛盾。[实证]

### 2.4 Draw_Fog B1/B2 原版算子（重申+补全）[实证]

```
B1 0x47F403  8A 1F           mov bl, [edi]        ; FOG.SHP 像素
   0x47F406  80 FB 7F        cmp bl, 0x7F         ; 透明跳过
   0x47F40D  77 37           ja  skip
   0x47F40F  66 8B 08        mov cx, [eax]        ; 读地表像素（桩替换起点）
   0x47F42F  8D 4C 11 81     lea ecx, [ecx+edx-0x7F] ; dst+fog−127
   0x47F43B  23 CA           and ecx, edx         ; clamp ≥0
   0x47F43D  66 89 08        mov [eax], cx
B2 0x47F4AE–0x47F4DE         同式（第二窗口）
```

`fog=66` ⇒ `dst−61`。纯加性，无乘性。已被 ra2render 桩替换。[实证]

### 2.5 Blitter 族语义（YRpp 头 + 实现）[实证]

| Blitter | 算子 | 与 0.71875 关系 |
|---|---|---|
| `BlitPlainXlat` / `BlitTransXlat` | `dst = Data[src]` | 纯查表；表内容可含任意系数 |
| `BlitTransLucent50` | `dst = (Data[src]>>1 & mask) + (*dst>>1 & mask)` | 50% 混合，retain=0.5 |
| `BlitTransLucent25` | 25% 源 + 75% 目标 | retain=**0.75**（+4.3% vs 0.71875） |
| `BlitTransDarken` | `dst = Data & (*dst >> 1)` | 50% 压暗（=我方桩算子） |
| `BlitTransLucent75` | 75% 源 + 25% 目标 | retain=0.25 |

**无 retain=23/32 的内建 blitter**。[实证]

### 2.6 常数面扫描汇总 [实证]

| 形态 | 命中 | 判定 |
|---|---|---|
| `float 0.71875` | 1（`0x803F4E` 非对齐巧合） | 排除 |
| `double 0.71875` | 0 | 排除 |
| `float/double 0.28125`（9/32） | 0 | 排除 |
| `float/double 1.391304`（1/0.71875） | 0 | 排除 |
| `imm32=184` 作指令操作数（渲染带） | 0 | 排除 |
| `imm=23` 作指令操作数（渲染带） | 0 | 排除 |
| `imul r,r,23/184` 寄存器形态 | 0 | 排除 |
| `×23>>5` / `×184>>8` | 0 | 排除 |
| `×9>>5`（=9/32）渲染带 | 0 | 排除 |
| `imm16 0xB71D` | 6（全是数据） | 排除 |
| `imm32 0xB800`（Q16 0.71875） | 19（全是数据/常量池） | 排除 |
| 魔数 `0.71875·2^k` 作 imul 立即数 | 0 | 排除 |

---

## [3] LightConvert `0x420140` 关闭论证（关键未决 → 已决）

任务卡称「LightConvert 表生成是否含 ×0.71875 是关键未决」。**本轮结案为否定**，论证三层：

1. **表公式层**[实证·可复算]（R-01）：`q = floor(lo·hi·(L−1)/32258)`，常量仅 `0x82061029 / 14 / 0xFF / 8 / L−1`。全量 1,048,576 项对拍零误差。等效切片系数 `k=hi(L−1)/32258 = 184/256` 需 `hi(L−1)=23185.4375 ∉ ℤ`，无整数解。
2. **消费端合成层**[实证]（本文 §2.3）：像素环将表输出作 BufferA 切片选择子，合成 `out = palette[ambient] · 2q/(S−1)`，其中 `q ∝ lo·hi`。合成倍率随源色**二次变化**，不是常数 ×0.71875。
3. **着色表层**[实证]（本文 §2.1–2.2）：BufferA 倍率 `2k/(S−1)` 可在特定 (S,k) 恰为 23/32，但**实际 S=53 无解**。

⇒ **`0x420140` 不是 ×0.71875 的施加点**；其下游 BufferA 在当前 shadeCount 下也不产出精确 23/32。[实证]

---

## [4] 候选站点总表

| # | 候选 | VA / 语义 | 是否含 0.71875 或 23/32 等价 | 证据等级 | 状态 |
|---|------|-----------|------------------------------|----------|------|
| C1 | AlphaLightingRemap 表生成 | `0x420140` | **否**（公式层+消费层双重否定） | [实证] | **结案否定** |
| C2 | ConvertClass BufferA 着色表 | `0x4bbb00` + ctor `0x48E800` | **机制可、参数否**（S=53 无精确切片） | [实证] | **降权·残留** |
| C3 | DrawTile 像素环 | `0x5487B9–0x5487EB` | 否（纯查表+OR，无乘法） | [实证] | **排除** |
| C4 | Draw_Fog B1/B2 | `0x47F40F`/`0x47F4AE` | 否（加性 tint，已被桩替换） | [实证] | **排除** |
| C5 | BlitTransLucent25 | retain 0.75 | 否（+4.3% 误差） | [实证] | **排除** |
| C6 | BlitTransDarken | `Data & (dst>>1)` | 否（=0.5） | [实证] | **排除** |
| C7 | RGB565 向白插值 | `0x53B8xx` | 否（向白 fade） | [实证] | **排除** |
| C8 | imm 184/23 imul | 全 .text | 否（无真操作数） | [实证] | **排除** |
| C9 | float/double 0.71875 | 全段 | 否 | [实证] | **排除** |
| C10 | `×9/32` 混色形态 | 渲染带 | 否（0 命中） | [实证] | **排除** |
| C11 | 调色板最近邻量化 + 着色表合成 | `0x626200` + `0x4bbb00` | **等效可能**（量化可模拟 ×0.72 并致暗端抬升） | [推演] | **首选残余** |
| C12 | 运行期切片选择（ambient/hi_slice） | `0x547DB8` hi 计算 + `0xAA10B8` | **等效可能**（若雾格用特定切片） | [推演] | **次选残余** |
| C13 | 光照对象 `0x665650` 字段 | `0x8871E0` | 待实测 | [待实测] | 残余 |

---

## [F5] 最终定谳与最小真机探针

### 定谳

**「灰雾第一段 ×0.71875」未在 gamemd.exe 中定位为离散乘法/混色指令站点。**

已穷举排除：立即数乘法（184/23/9）、浮点常量、LightConvert 表生成、DrawTile 像素环、Draw_Fog 原版算子、内建 Translucent blitter、×9/32 位运算形态。

最强残余解释 [推演]：0.71875 是 **ConvertClass BufferA 着色表（`0x4bbb00` 生成的 `2k/(S−1)` 倍率）+ 调色板最近邻量化（`0x626200`）** 在雾格所用光照切片上的**等效合成增益**——非字面常数，而是「某切片倍率 × 量化吸附」的经验拟合。该解释同时容纳：
- 亮端 ≈×0.71875（切片倍率近似 23/32）
- 暗端变亮（量化吸附到更亮的调色板项）
- ~20% 非函数性（同源值因量化/上下文得不同结果）

### 最小真机探针设计（≤3 项，只读）

| # | 断点 | 看什么 | 判据 |
|---|------|--------|------|
| P1 | `0x5487EB`（像素写入） | 采样 (src16, Table1_out, ambient, idx, Table2_out) 各 256 组，雾区 vs 无雾区 | 若 `Table2_out/src ≈ 0.71875` 且与 src 无关 ⇒ 找到常数增益；若随 src 变化 ⇒ 走量化/切片假说 |
| P2 | `0x48E9F0`/`0x48EB2A`（BufferA 分配后） | dump 全切片 ×256 项，逐切片计算 `mean(out/in)` | 若某切片 ≈0.71875 ⇒ 定位切片 k；若无 ⇒ 走量化假说 |
| P3 | `0x4201C7`（LightConvert 写表） | dump 全 65536 项，检验是否有 slice 使 `q<<8` 经 BufferA 后等效 ×184/256 | 与 P1/P2 交叉验证 |

### 证据等级分布

- `[实证]`：12 条（常数扫描、指令级否定、表公式、像素环、blitter 语义、shadeCount 构造）
- `[推演]`：3 条（C11/C12 残余假说、等效增益归因）
- `[待实测]`：3 条（P1/P2/P3 探针）

---

## [6] 写作用域合规声明

- 新增：`docs/re/fog_mixing_site_deep_dive.md`（本文）、`out/re_work/re_sprint/R_fog_stage/**`
- 未触碰：`ra2render/**`、`ra2youli/**`（exe 只读）、`tools/**`、`out/loadbench/**`、台账 `REVERSE_ENGINEERING_AND_PATCHES.md`、`docs/RE_COORDINATION.md`、`ARCHITECTURE_ATLAS*.md`、`out/reverse/**`
- 只读基线：`ra2youli/gamemd.exe` MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`（自始至终未变）
- ★未启动游戏、未注入、未改任何二进制

## [7] 交付物清单

| 文件 | 内容 |
|---|---|
| `s01_scan_constants.py` / `s01_scan_results.json` | 浮点/整数常量全量扫描 |
| `s02_context_scan.py` / `s02_context.txt` | 0xB71D/0xB800 站点上下文、imul ModR/M 解码、Table2 0x170 xref |
| `s03_convert_blitter.py` / `s03_convert_blitter.txt` | ConvertClass 表生成 / Init_Blitters / 像素环 / ambient 反汇编 |
| `s04_shade_blitter.py` / `s04_shade_blitter.txt` | shadeCount 公式验证、ctor 扫描、BlitTransDarken、AlphaLightingRemap 数值 |
| `s05_final_scan.py` / `s05_final_scan.txt` | Draw_Fog 全貌、×9/32 扫描、imm23/184 渲染带扫描 |
| `claims_r_fog_stage.txt` | 字节级断言（audit_bytes 可复算） |
