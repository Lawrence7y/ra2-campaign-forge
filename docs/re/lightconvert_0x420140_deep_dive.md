# LightConvert / AlphaLightingRemap `0x420140` 深潜（R-01）

> [META]
> task=R-01 · executor=R 轨子代理 · 日期 2026-10-02
> 基线（只读）：`ra2youli/gamemd.exe` MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367` · ImageBase `0x400000` · FileOffset=VA−0x400000
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> 写域：本文 + `out/re_work/re_sprint/lightconvert/**`
> 证据等级：`[实证]` / `[推演]` / `[待实测]`
> 问题：表内容是否包含 0.71875(=184/256=23/32) 系数？表映射精确数学形式？

---

## [0] 结论摘要

1. **身份**[实证]：`0x420140` = `AlphaLightingRemapClass::FindOrAllocate(int Level)`（YRpp `Vault.h:96-105` `JMP_STD(0x420140)`），布局 `WORD data[0x10000]; DWORD TranslucencyLevel(+0x20000); DWORD RefCount(+0x20004)` 与字节级完全吻合。全函数 `0x420140–0x420262`（双 `ret 4`：缓存命中 `0x4201F4` / 插入返回 `0x420262`）。
2. **表映射闭式**[实证·可复算]：
   `data[hi<<8|lo] = (clamp(floor(lo·hi·(Level−1) / 32258), 0, Level−1) << 8)`，WORD 低字节恒 0。
   魔数 `0x82061029`+`sar 14` 即 **÷32258** 的定点实现。16 个 Level × 65536 项全量对拍 **1,048,576/1,048,576 零误差**。
3. **判定：不含 0.71875 系数**[实证·可复算]。公式常量层无 184/23/32/0.71875；等效切片系数 `k=hi·(Level−1)/32258` 与 184/256 **无整数解**（需 `hi·(Level−1)=23185.4375`）。最近近似 `23184/32258=0.718705…`（误差 4.46e−5），属积参数化巧合，**不是**迷雾第一段乘子。
4. **与 M1 向灰混合不吻合**[实证·可复算]：暗端 `q(0)=0` 恒不抬升（M1 预测 ≈24–26）；最佳 mad≥14.63（g=67 最优）。本表是 **积×尺度+饱和**，不是 `lerp→constant_gray`。
5. **推论**[推演]：迷雾「第一段 ×0.71875」**不在**本表生成公式内；`fog_firststage_site_locate.md` U1 就此结案（否定）。剩余候选收窄到 Tile 光照参数 / 环境光 / 其他像素路径。

---

## [1] 调用面与缓存

| 项 | 值 | 等级 |
|---|---|---|
| 入口 | VA `0x420140` / FO `0x20140` | [实证] |
| 签名 | `stdcall FindOrAllocate(int Level)`，`ret 4` | [实证] |
| 表对象 | `new(0x20008)` = `WORD[0x10000]` + Level + RefCount | [实证] |
| 缓存数组 | `[0x88A084]` 指针表；`[0x88A090]` 计数；`[0x88A088]` 容量 | [实证] |
| cache key | `[table+0x20000] == Level` | [实证] |
| refcount | `[table+0x20004]`，命中 +1 / 新建 0 后 +1 | [实证] |
| 全 exe `call 0x420140` | **40** 处（`0x48F4xx–0x48F8xx` 为主，Convert/Blitter 簇；含 `0x547D95` TileClass::DrawTile） | [实证] |
| 配套释放 | `0x420270`：`--RefCount`，归零后从向量移除 | [实证] |

DrawTile 用法[实证]（`0x547D95` 之后）：
```
edi = FindOrAllocate(obj+0x16c)          ; Level
eax = clamp254( (max(arg,0) * 261) >> 11 ) ; 261/2048≈0.12744 → hi 切片 0..254
[0xAA10D0] = edi + (eax << 9)            ; = &data[hi*256]（每切片 256 WORD）
```
即消费方按 **hi 切片 × lo 色标** 二维索引，结果取 WORD 高字节。

---

## [2] 逐指令语义（`0x420140–0x420262`）

### 2.1 缓存查找

| VA | 字节 | 指令 | 语义 |
|---|---|---|---|
| 0x420140 | `8B 15 90 A0 88 00` | mov edx,[0x88A090] | count |
| 0x420146–14B | `53 55 56 33C0 57` | push ebx/ebp/esi; xor eax,eax; push edi | eax=扫描下标 |
| 0x42014C | `8B 7C 24 14` | mov edi,[esp+0x14] | **Level**（stdcall 实参） |
| 0x420150 | `85 D2` | test edx,edx | count≤0 → 分配 |
| 0x420154 | `8B 35 84 A0 88 00` | mov esi,[0x88A084] | 表指针数组 |
| 0x42015C | `8B 19` | mov ebx,[ecx] | tables[i] |
| 0x42015E | `39 BB 00 00 02 00` | cmp [ebx+0x20000],edi | Level==key? |
| 0x420164 | `74 71` | je 0x4201D7 | 命中 |
| 0x420166–16C | `40 83C104 3BC2 7CEE` | i++ / ptr+=4 / 循环 | 线性扫缓存 |

### 2.2 分配与表头

| VA | 字节 | 指令 | 语义 |
|---|---|---|---|
| 0x42016E | `68 08 00 02 00` | push 0x20008 | 128KB+8 |
| 0x420173 | `E8 9F 8C 3A 00` | call 0x7C8E17 | operator new |
| 0x420181 | `89 BD 00 00 02 00` | mov [ebp+0x20000],edi | TranslucencyLevel=Level |
| 0x420189 | `C7 85 04 00 02 00 00…` | mov [ebp+0x20004],0 | RefCount=0 |
| 0x420193 | `4F` | dec edi | **L = Level−1** |
| 0x420194 | `8B DD` | mov ebx,ebp | 写指针 |

### 2.3 生成循环（核心公式）

| VA | 字节 | 指令 | 语义 |
|---|---|---|---|
| 0x420196 | `8B CE` | mov ecx,esi | idx |
| 0x420198 | `8B D6` | mov edx,esi | |
| 0x42019A | `81 E1 FF 00 00 00` | and ecx,0xFF | **lo = idx&0xFF** |
| 0x4201A0 | `B8 29 10 06 82` | mov eax,0x82061029 | 魔数 |
| 0x4201A5 | `C1 FA 08` | sar edx,8 | **hi = idx>>8** |
| 0x4201A8 | `0F AF CA` | imul ecx,edx | lo·hi |
| 0x4201AB | `0F AF CF` | imul ecx,edi | n=lo·hi·L |
| 0x4201AE | `F7 E9` | imul ecx | EDX:EAX = i64(MAGIC·n) |
| 0x4201B0 | `03 D1` | add edx,ecx | high+n |
| 0x4201B2 | `C1 FA 0E` | sar edx,14 | (high+n)>>14 |
| 0x4201B5–1BA | `8BC2 C1E81F 03D0` | shr 0x1f; add | 负值向零取整 |
| 0x4201BC–1C0 | `3BD7 7E02 8BD7` | cmp edx,edi; jle; mov edx,edi | **上钳位 → L** |
| 0x4201C2 | `33 C9` | xor ecx,ecx | 低字节清零 |
| 0x4201C5–1C7 | `8A EA 66 89 0B` | mov ch,dl; mov [ebx],cx | **word = q<<8** |
| 0x4201CA–1D3 | `83C302 81FEFFFF0000 7EC1` | +2; cmp esi,0xFFFF; jle | 65536 项 |
| 0x4201D5 | `EB 22` | jmp 0x4201F9 | 插入缓存 |

### 2.4 命中返回 / 插入 / 尾

| VA | 语义 |
|---|---|
| 0x4201D7–1F4 | 命中：RefCount++，`eax=tables[i]`，`ret 4` |
| 0x4201F7 | OOM：ebp=0 后仍进插入路径（不写表） |
| 0x4201F9–235 | 容量检查 `[0x88A090]<[0x88A088]`，否则 `call [vtable+8]` 扩容 |
| 0x420237–24C | count++，`tables[old]=ebp` |
| 0x42024F–262 | RefCount++，`eax=ebp`，`ret 4` |

---

## [3] 表映射闭式公式

### 3.1 魔数反演 [实证]

```
MAGIC = 0x82061029  (i32 = −2113531863)
序列: EDX:EAX = MAGIC×n ; q0 = (high32 + n) >> 14 ; 负则 +1
⇒ q0 ≈ n · 0x82061029 / 2^46 = n / D ,  D = 2^46/0x82061029 = 32257.99999… ≡ **32258**
```

### 3.2 闭式（与指令级路径全等）[实证·可复算]

```
lo = idx & 0xFF
hi = idx >> 8
L  = Level − 1
n  = lo * hi * L                          # 32-bit 有符号
q  = floor(n / 32258)   if n ≥ 0
   = −floor(−n / 32258) if n < 0          # 向零，对应 shr1f+add
if q > L: q = L                           # 仅有上钳位（无钳到 0）
data[idx] = (q & 0xFF) << 8               # 低字节恒 0
```

全量对拍：Level ∈ {0,1,2,3,8,16,32,33,64,85,128,184,185,200,255,256} × 全部 65536 idx
→ **1,048,576 项 magic 路径 vs 闭式零误差**（`verify_closed_form.json`）[实证]。

### 3.3 可复算数值证据（代入典型输入）

| lo | hi | Level | n | q | word | n/32258 |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 256 | 0 | 0 | 0x0000 | 0 |
| 255 | 0 | 256 | 0 | 0 | 0x0000 | 0 |
| 1 | 1 | 256 | 255 | 0 | 0x0000 | 0.0079 |
| 128 | 128 | 256 | 4177920 | 129 | 0x8100 | 129.52 |
| 255 | 255 | 256 | 16581375 | **255（钳）** | 0xFF00 | 514.03 |
| 128 | 128 | 32 | 516096 | 16 | 0x1000 | 16.00 |
| 255 | 254 | 32 | 2004510 | **31（钳）** | 0x1F00 | 62.14 |
| 255 | 92 | 253 | 5852340 | 181 | 0xB500 | 181.42 |

自算一行（推荐复算）：
`lo=128, hi=128, Level=256` → `n=128·128·255=4177920` → `4177920//32258=129` → word `0x8100`。

---

## [4] 「含 / 不含 0.71875」判定

### 4.1 判定：**不含**（作为嵌入系数）[实证·可复算]

| 检验层 | 结果 | 证据 |
|---|---|---|
| A. 公式常量 | 仅 `0x82061029 / 14 / 0xFF / 8 / 0xFFFF / Level−1`；无 184、23、32 系数、无 0.71875 浮点 | 逐指令 §2.3；claims 12/12 OK |
| B. 除数 | D=**32258**（=2·127²），不是 256/32 的 184 倍关系 | 魔数反演 + 全量对拍 |
| C. 等效切片系数 | 固定 (hi,Level) 时 `q≈lo·k`，`k=hi(Level−1)/32258` | §3.2 |
| D. k=184/256 整数解 | 需 `hi(Level−1)=184·32258/256=23185.4375` ∉ ℤ ⇒ **无解** | `verify_closed_form.json` |
| E. 最近近似 | `hi(Level−1)=23184` ⇒ k=0.718705437…（如 hi=92,Level=253）误差 **4.46e−5**；成族 8+ 组 | 同上 |
| F. 逐项 out/in=184/256 | 个别 (lo,hi,L) 因整除截断可凑出 `q·256=lo·184`，**无参数意义**（floor 混叠） | `formula_and_071875.json` exact 列表 |

**口径**：否定依据是 **闭式重构 + 1,048,576 项全量数值**，不是「静态立即数 0 命中」。满足验收「查表间接系数不能仅靠静态否定」。

### 4.2 若误把 k≈0.71875 当第一段的反例

即使取最接近切片 (hi=92, Level=253)：
- 该 k 是 **hi·L 的积参数化**，随切片连续变化（L=32 时同 hi 的 k≈0.087），不是场景常量；
- 输出还有 `floor` + 上钳位，不是精确 ×23/32；
- 迷雾第一段作用于 **单色标像素**；本表是 **lo×hi 双字节积**，算子族不同。

---

## [5] 与 M1 向灰混合模型定量吻合度

M1：`out = c + (g−c)·α`，`g≈67–72`，`α=0.71875(1−s/512)`，s=256 ⇒ α=0.359375。

| 切片 (hi,Level) | 表 q(0) | M1(0) g=70 | 表 q(255) | M1(255) | mad | max_err |
|---|---:|---:|---:|---:|---:|---:|
| 92, 253（k≈0.7187 最优） | **0** | 25.16 | 183 | 188.52 | **15.71** | 25.80 |
| 184, 185 | **0** | 25.16 | 184 | 188.52 | 19.99 | 46.09 |
| 128, 256 | **0** | 25.16 | 255 | 188.52 | 更差 | — |
| 254, 32 | **0** | 25.16 | 31（钳） | 188.52 | 极差 | — |

**结构性冲突**[实证]：
1. 向灰要求 **暗端抬升**（c=0 → g·α≈25）；本表 `q(0)=0` 对所有切片恒成立（`n=0`）。
2. 向灰要求 **亮端下压**（255→188）；本表在高 k 切片是 **放大/饱和**（255→183 或钳到 L）。
3. 本表算子 = 积×(1/32258)+饱和，**无仿射截距**，无法表示 `c+(g−c)α`。

**结论**[实证·可复算]：M1 吻合度 **差**（最佳 mad 仍 ≥14.6，且暗端符号相反）。`0x420140` 表 **不是** 迷雾向灰混合实现，也 **不是** 第一段 ×0.71875 施加点。

---

## [6] 未闭环项与下一步

| # | 缺口 | 下一步 | 级别 |
|---|---|---|---|
| N1 | 第一段 ×0.71875 真正站点仍未定位 | 从 U1 撤销本表；改查 DrawTile 光照参数链（`obj+0x16c` 的写入者）、环境光 `0x423621`、`0x665650` 运行期字段 | **P0** |
| N2 | 表消费端 blitter 如何取高字节 | 反汇编 `BlitTransXlatAlpha*` / `0x48EBF0` 挂接的 Data 用法；确认 `mov ch,dl` 的读侧 | P1 |
| N3 | 40 个 caller 的 Level 实参分布 | 真机断点 `0x420140` 记录 Level 直方图（ZCode 卡） | P1 |
| N4 | Level=0 边界（edi=−1）行为 | 闭式已覆盖；是否被调用需动态 | P2 |
| N5 | 32258=2·127² 的设计含义 | 对照 TS 源码/调色板公式（非阻塞） | P3 |

**明确否定（本卡）**：`0x420140` 表生成公式 **不含** 0.71875 系数；该表 **不是** M1 向灰实现。`fog_firststage_site_locate.md` 候选 C1 可降权。

---

## [7] 交付物与合规

- 报告：`docs/re/lightconvert_0x420140_deep_dive.md`（本文）
- 脚本/输出：`out/re_work/re_sprint/lightconvert/`
  - `disasm_and_claims.py` / `disasm_420140.txt` / `claims.txt`
  - `magic_and_formula.py` / `formula_and_071875.json`
  - `supplement_analysis.py` / `supplement.json`
  - `verify_closed_form.py` / `verify_closed_form.json` / `disasm_full.txt`
- `python tools/audit_bytes.py out/re_work/re_sprint/lightconvert/claims.txt` → **合计 12 条：OK=12 MISMATCH/NOREAD=0** [实证]
- 只读：`ra2youli/gamemd.exe`；未写 `ra2render/**`、`tools/**`、`out/loadbench/**`、`out/re_work/zcode_live/**`、其他 `docs/re/*.md`
- 参考（只读）：`YRpp/Vault.h`（符号名/布局）、`docs/re/fog_firststage_site_locate.md`、`docs/re/fog_model_hypothesis.md`
