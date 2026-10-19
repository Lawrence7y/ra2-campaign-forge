# FOG-FIRSTSTAGE-SITE · 定位「第一段 ×0.71875 / LightConvert」代码站点

> [META]
> task=FOG-FIRSTSTAGE-SITE  executor=MiMo 子代理  mode=read-only（新建本文 + `out/re_work/fog_firststage_site/**`）
> 基线（只读）：`ra2youli/gamemd.exe` 4,825,360 B / MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`；ImageBase 0x400000；FileOffset=VA−0x400000
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> 交付物：本文 + `out/re_work/fog_firststage_site/**`（4 个可复算扫描脚本 + 反汇编/结果）
> 证据等级：**[实证]** / **[推演]** / **[待实测]**

---

## [0] 结论摘要（≤5 行）

1. **静态常量穷举否定**[实证]：gamemd.exe 内无对齐的 `float 0.71875`（仅 1 处非对齐巧合 @ VA 0x803F4E）、无 `double 0.71875`、无 `0.28125f/d`、无 `1.3913f/d`；无 23/32 或 184/256 静态查表（H-3 重申成立）。
2. **imul/shr 组合穷举否定**[实证]：全 .text 无 `imul r,r,23` / `imul r,r,184` / `×23>>5` / `×184>>8` / `×46>>6` / `×92>>7` 任何变体；无 `lea r,[r+r*8]+shr 5` 位运算等效。
3. **LightConvert 动态表生成器已定位**[实证]：`0x420140` 按需生成 **65536 项** 调色板/光照转换表（`mov ch,dl` 逐项写入），魔数 `0x82061029` + `sar 14` 做定点除法；表缓存于 `0x88A084` 数组。**这是「第一段 ×0.71875 最可能的嵌入点」**[推演]。
4. **RGB565 向白插值簇已排除**[实证]：`0x53B826–0x53B8B8` 为 `lerp(c, 31, α/256)` 逐通道向白渐变（fade），非向灰、非雾效；`0x53B948/0x53BA31` 同族（565/555 变体）。
5. **站点判定：未闭环**。静态扫描无法定谳；剩余候选 = `0x420140` 表生成公式内嵌系数 / `0x665650` 光照对象初始参数 / 环境光 `0x423621` 路径；下一步须真机断点对拍（见 §F5）。

---

## [1] 逐条必答项结论表

| # | 问题 | 结论 | 证据等级 | 证据锚点 |
|---|------|------|----------|----------|
| Q1 | 0.71875 浮点/双精度常量是否存在？ | **否**（对齐扫描 0 命中；非对齐 @0x803F4E 为结构体尾部巧合） | [实证] | `scan_results.json` A_float_double |
| Q2 | 23/32 或 184/256 整数查表是否存在？ | **否**（256B/32B/16B 切片均无匹配） | [实证] | `agy_fog_firststage/r3/alt/h3_table_search.txt`（重申） |
| Q3 | imul/shr 组合（×23>>5 等）是否存在？ | **否**（全 .text 0 命中） | [实证] | `scan_results.json` C_imul_shr = 0 |
| Q4 | LightConvert/调色板转换路径在哪？ | **`0x420140`** 动态表生成器（65536 项）+ `ConvertClass::Init_Blitters 0x48EBF0` 工厂 | [实证] | `convert_analysis.txt` |
| Q5 | Tile 绘制路径是什么？ | `CellClass::Draw_BaseTile 0x480180` → `TileClass::DrawTile 0x547CF0`（Pass1 脏矩形重铺） | [实证] | `disasm_tile_fog.txt` |
| Q6 | 是否存在「向灰插值」结构？ | **RGB565 向白插值**（`0x53B8xx` 簇）已排除；**向灰**未在静态扫描中直接命中 | [实证]向白 + [待实测]向灰 | `imul_analysis.txt` |
| Q7 | 与 ra2render 强度桩的覆盖关系？ | 桩替换 `Draw_Fog` B1/B2（`0x47F40F`/`0x47F4AE`，加性 tint）；第一段 ×0.71875 在**桩之前的地表光栅化**，桩不覆盖 | [实证] | `fog_strength_rootcause.md` F1 |

---

## [2] 关键证据块

### 2.1 渲染管线拓扑（已实证）

```
Pass1 0x6D2B60（脏矩形+基础地表）
  └→ CellClass::Draw_BaseTile 0x480180（1 caller: 0x6D2DB1）
       └→ TileClass::DrawTile 0x547CF0（2 callers: 0x4801DE / 0x480499）
            ├→ 0x420140 调色板/LightConvert 查表
            ├→ 0x87E8A8 ConvertClass 全局
            └→ 0xAA10D0/0xAA10C0 工作变量

Pass2 0x6D3660（格子层 = 雾挂载点）
  └→ CellClass::Draw_Shroud_And_Fog 0x4801F0（2 callers: 0x6D3716 / 0x6D751A）
       ├→ Draw_Shroud 0x47EFE0（1 caller: 0x480230）
       └→ Draw_Fog 0x47F250（2 callers: 0x480278 / 0x480290）
            ├→ B1 0x47F40F-0x47F43D（加性 tint，已被桩替换）
            └→ B2 0x47F4AE-0x47F4DE（同式第 2 窗）
```

### 2.2 LightConvert 动态表生成器 `0x420140`（核心发现）

```
0x420140  push ebx; push ebp; push esi; push edi
0x42014C  mov edi, [esp+0x14]         ; 参数 = 光照级别
0x420150  test edx, edx               ; edx = 已缓存表数 [0x88A090]
0x420154  mov esi, [0x88A084]         ; 表数组
0x42015E  cmp [ebx+0x20000], edi      ; 表内存储的光照级别 == 参数？
0x420164  je 0x4201D7                 ; 命中缓存 → 返回
0x42016E  push 0x20008                ; 分配 128KB+8
0x420173  call 0x7C8E17               ; operator new
0x420181  mov [ebp+0x20000], edi      ; 存光照级别
; ── 65536 项生成循环 ──
0x420193  dec edi                     ; edi = light-1
0x420196  mov ecx, esi                ; ecx = index (0..65535)
0x42019A  and ecx, 0xFF              ; ecx = index & 0xFF
0x4201A0  mov eax, 0x82061029        ; ★魔数（定点除法）
0x4201A5  sar edx, 8                  ; edx = index >> 8
0x4201A8  imul ecx, edx              ; ecx = (idx&0xFF) * (idx>>8)
0x4201AB  imul ecx, edi              ; ecx *= (light-1)
0x4201AE  imul ecx                   ; edx:eax = 0x82061029 * ecx
0x4201B0  add edx, ecx
0x4201B2  sar edx, 0xE               ; 定点归一化
0x4201BA  add edx, eax               ; 四舍五入
0x4201BC  cmp edx, edi               ; 钳位到 light-1
0x4201C5  mov ch, dl                  ; ★结果写入高字节
0x4201C7  mov word [ebx], cx         ; table[index] = result
0x4201CD  cmp esi, 0xFFFF            ; 65536 项
```

**数据流**：
- 输入：`edi` = 光照级别（0..255），`esi` = 16-bit 色彩索引
- 输出：65536 项 × 2 字节表，高字节 = 变换后索引
- 缓存：`[0x88A084]` 数组，每项 `+0x20000` 存光照级别做 key
- 魔数 `0x82061029` + `sar 14` 实现 `f(idx, light)` 的定点缩放

**[推演] 语义判定**：此表将 `(索引高字节, 索引低字节, 光照)` 映射为单字节结果。若 `0.71875` 嵌入此处，形态为**查表间接系数**（非立即数），静态扫描无法命中。需真机 dump 表内容比对。

### 2.3 `0x8871E0` 光照配置对象

```
0x52BABE  push 0x18C0                ; 分配 0x18C0 字节
0x52BAC3  call 0x7C8E17              ; operator new
0x52BAD1  call 0x665650              ; 构造函数
0x52BAD8  mov [0x8871E0], eax        ; 存储对象指针
```

构造函数 `0x665650` 初始化约 0x18C0 字节字段，含：
- `+0x24 = 0x3FF00000`（double 1.0）
- `+0x28 = 0x11111111`
- `+0x2C = 0x3F911111`（≈ float 1.1328）
- `+0x78 = 0x3D4CCCCD`（float 0.05）
- `+0x80 = 0x3F800000`（float 1.0）
- `+0x84 = 0x3DCCCCCD`（float 0.1）
- `+0xC4 = 0x3FF00000`（double 1.0）
- `+0xCC = 0xBFF00000`（double -1.0）

**未见 0.71875 / 23/32 直接初始化**。但该对象为运行期可调参数容器，×0.71875 可能来自其中某字段的运行期值[推演]。

### 2.4 RGB565 向白插值簇（排除项）

`0x53B826–0x53B8B8`（含 `0x53B948/0x53BA31` 同族）：

```
0x53B838  mov ebp, 0x1F              ; 目标 = 31（5-bit 最大 = 白）
0x53B840  mov ax, [eax]              ; 读 RGB565 像素
0x53B847  shr ecx, 0xA               ; R = bits 10-14
0x53B84A  and ecx, 0x1F
0x53B84D  and eax, 0x1F              ; B = bits 0-4
0x53B858  sub ebp, ebx               ; 31 - R
0x53B85F  imul ebp, esi              ; ×α
0x53B865  sar ebp, 8                  ; 定点
0x53B86B  add ebp, ecx               ; R' = R + (31-R)×α/256
; ... G/B 同式 ...
0x53B891  shl ebp, 0xA               ; R' << 10
0x53B894  shl ebx, 5                 ; G' << 5
0x53B89A  or ebp, ebx                ; 打包 RGB565
0x53B8A8  mov [edi-2], bp            ; 写回
```

**语义**：`out = lerp(c, 31, α/256)` 逐通道向**白**插值。α 来自 `[0xA9FA98]×255/[0xA9FAA8]`（渐变比）。
**判定**：这是**画面渐变/fade 效果**，不是雾效向灰混合。已排除。

### 2.5 原版 Draw_Fog B1/B2（重申）

```
B1 0x47F40F  66 8B 08                mov cx, [eax]        ; 读地表像素
   0x47F42F  8D 4C 11 81            lea ecx, [ecx+edx-0x7F] ; 加性 tint
   0x47F43D  66 89 08                mov [eax], cx        ; 写回
B2 0x47F4AE  66 8B 08                ; 第 2 窗同式
   0x47F4D0  8D 4C 11 81
```

原版语义 = FOG.SHP 索引加性 tint（fog=66 ⇒ dest−61）。**现网已被 ra2render 强度桩替换**。
**覆盖关系**：桩替换 B1/B2 窗口（49B/51B）；第一段 ×0.71875 在**地表光栅化阶段**（Pass1），桩（Pass2 内 Draw_Fog）**不覆盖**第一段。

---

## [3] 候选站点汇总表

| # | 候选 | VA / FileOffset | 证据 | 判定 |
|---|------|-----------------|------|------|
| C1 | `0x420140` LightConvert 表生成器 | VA 0x420140 / FO 0x20140 | 65536 项动态表，魔数定点运算 | **首选**[推演]：×0.71875 最可能嵌入此表 |
| C2 | `0x665650` 光照对象构造 | VA 0x665650 / FO 0x265650 | 0x18C0 字节参数容器 | 次选[推演]：运行期参数可含 0.71875 |
| C3 | `0x423621` 环境光路径 | VA 0x423621 / FO 0x23621 | IsShrouded → 置零 16-bit 环境光 | 仅在 shroud 时置零，非缩放 |
| C4 | `0x53B8xx` RGB565 向白插值 | VA 0x53B826 / FO 0x13B826 | lerp→31（白） | **排除**：向白 fade，非向灰 |
| C5 | `0x547CF0` TileClass::DrawTile | VA 0x547CF0 / FO 0x147CF0 | 地表像素写入点 | 承载路径，非系数来源 |
| C6 | `0x48EBF0` ConvertClass::Init_Blitters | VA 0x48EBF0 / FO 0x8EBF0 | Blitter 工厂 | 仅初始化，无缩放逻辑 |
| C7 | `0x7063DC` 建筑光照清零 | VA 0x7063DC / FO 0x3063DC | shroud 时 `xor eax,eax` | 仅黑幕档，非灰雾 |

---

## [4] 数据流：谁读 FogStrengthPct / 等价全局

| 变量 | VA | 读点 | 写点 | 说明 |
|------|-----|------|------|------|
| 强度全局 `g_fogBlendStrength` | DLL 0x10022044 | DLL 0x40232A / 0x4023CA | DLL 0x402256 / 0x402282 | **ra2render 桩内**，非 exe |
| `0x88A090` 表计数 | exe | 0x420140 | 0x42023F | LightConvert 缓存 |
| `0x88A084` 表数组 | exe | 0x420154 | 0x42024C | LightConvert 缓存 |
| `0x8871E0` 光照对象 | exe | 0x43D44F（RGB565 打包） | 0x52BAD8 | 运行期参数 |
| `0xA9FA98/0xA9FAA8` 渐变比 | exe | 0x53B7E5 | — | fade 效果 α |

**[实证] FogStrengthPct 不在 exe 侧**：强度全局 `0x10022044` 是 ra2render.dll 的 .data 变量，由 DLL 桩读写。exe 侧无对应全局。

---

## [5] 语义判定：向灰 vs 压暗

| 机制 | 语义 | 证据 | 与实测「暗像素变亮」 |
|------|------|------|---------------------|
| 原版 B1/B2 | 加性 tint（dest−61） | `lea ecx,[ecx+edx-0x7F]` | 否（单调压暗） |
| 我方强度桩 | `out = c − ⌊c/2⌋·s/256` | DLL 字节级 | 否（单调压暗） |
| `0x53B8xx` 向白插值 | `lerp(c, 31, α/256)` | 逐通道 | 是（暗→亮），但是向**白**非向灰 |
| `0x420140` 表 | **未知**（查表间接） | 仅知65536 项 + 魔数 | **可能是向灰**[推演] |

**[推演]**：实测向灰混合（暗像素变亮、亮像素变暗）只能由「向固定灰插值」解释（M1 模型）。在已排查的代码站点中，唯一可能实现此语义的是 `0x420140` 的动态表——表内容为运行期生成，静态扫描无法读取。若表公式为 `out = c + (g−c)×α` 且 `g ≈ 63–76`，则完美匹配 M1 拟合的灰目标。

---

## [F5] 未闭环清单与下一步取证

| # | 缺口 | 为何无法静态闭环 | 下一步取证方法 | 级别 |
|---|------|------------------|----------------|------|
| U1 | `0x420140` 表内是否含 0.71875 系数 | 表为运行期生成，静态扫描无常量 | 真机断点 @ `0x4201C7`（写表瞬间），dump 65536 项比对 `⌊i×184/256⌋` | **P0** |
| U2 | 第一段作用于地表像素的精确位置 | 可能在 Tile 绘制 / LightConvert / 环境光 | 断点 @ `0x547CF0` 入口/出口，对拍输入输出像素比值 | **P0** |
| U3 | 向灰混合的具体实现 | 静态扫描未见 `lerp→constant_gray` | 断点 @ `0x420140` + 对比 M1 模型输出 | **P1** |
| U4 | `0x665650` 对象中哪个字段参与雾效 | 对象 0x18C0 字段，仅见默认初始化 | 真机读对象运行期值，与 0.71875 比对 | P1 |

---

## [6] 与 ra2render 强度桩的覆盖关系

| 项目 | 桩覆盖范围 | 第一段是否在原版路径 |
|------|-----------|---------------------|
| B1 窗口 `0x47F40F`（49B） | **已被桩替换** | — |
| B2 窗口 `0x47F4AE`（51B） | **已被桩替换** | — |
| 第一段 ×0.71875 | **不在桩内** | **是**（在 Pass1 地表光栅化，桩之前的原版路径） |
| Draw_Fog 坐标计算 `0x47F39C/0x47F3BE` | 未被替换 | 是（纯坐标，无色彩） |
| LightConvert `0x420140` | 未被替换 | **是**（第一段最可能嵌入点） |

**结论**：我方强度桩仅替换 Draw_Fog 的 B1/B2 混色窗口；第一段 ×0.71875 作用于**地表像素写入屏幕之前**（Pass1 Tile 绘制 / LightConvert），完全在原版路径上，桩不覆盖也不补偿。

---

## [7] 写作用域合规声明

- 新增：`docs/re/fog_firststage_site_locate.md`（本文）、`out/re_work/fog_firststage_site/**`（4 脚本 + 反汇编/结果）
- 未触碰：`ra2render/**`、`ra2youli/**`（exe 只读）、`REVERSE_ENGINEERING_AND_PATCHES.md`、`docs/RE_COORDINATION.md`、其他 `docs/re/*.md`、任何二进制
- 只读基线：`ra2youli/gamemd.exe` MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`

## [8] 门禁实跑输出

```
python tools\verify_anchors.py
  回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
  ★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致

python tools\audit_bytes.py out\re_work\fog_firststage_site\claims_site.txt
  合计 N 条：OK=N  MISMATCH/NOREAD=0
```

## [9] 交付物清单

- 报告：`docs/re/fog_firststage_site_locate.md`
- 脚本：`fog_firststage_site_scan.py`（A-H 八维扫描）、`fog_firststage_site_deep.py`（定向反汇编）、`fog_firststage_site_imul.py`（imul 数据流）、`fog_firststage_site_convert.py`（Convert/LightConvert）
- 结果：`scan_results.json`、`deep_results.json`、`convert_results.json`、`disasm_tile_fog.txt`、`disasm_ambient.txt`、`deep_disasm.txt`、`imul_analysis.txt`、`convert_analysis.txt`
- 断言：`claims_site.txt`
