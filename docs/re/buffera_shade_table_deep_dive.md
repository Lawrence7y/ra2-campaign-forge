# ConvertClass BufferA 着色表深潜（R-BUFFERA）

> [META]
> task=R-BUFFERA  executor=R 轨子代理  日期 2026-10-02  mode=static-only
> 基线（只读）：`ra2youli/gamemd.exe` 4,825,360 B / MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367` · ImageBase `0x400000` · FileOffset=VA−0x400000
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> 写域：本文 + `out/re_work/re_sprint/R_buffera/**`
> 证据等级：`[实证]`（字节/反汇编可复算）/ `[推演]` / `[待实测]`
> 前作：`docs/re/fog_mixing_site_deep_dive.md`（R-FOG-STAGE）、`docs/re/lightconvert_0x420140_deep_dive.md`（R-01）
> 目标：ConvertClass BufferA 完整 ABI + 消费端合成增益 + 运行期切片归属 + 可复算 dump 规格

---

## [0] 结论摘要（≤8 行）

1. **BufferA 闭式定谳**[实证·可复算]：16-bit 路径 `BufferA[k][j] = pack(Pal[j].rgb × 2k/(S−1), clamp255)`，`factor = k·0x20000/(S−1)`，`chan·factor>>16 = chan·2k/(S−1)`。8-bit 路径同倍率，但作用于 **V 通道**（HSV 亮度）后经 `0x517440` 反变换 + `0x626200` 最近邻量化为调色板索引。
2. **表项位深**[实证]：**运行期按 DDraw 像素格式决定 RGB565 或 RGB555**，不是写死 565。移位常量 `0x8A0DD0..0x8A0DE4` 在 `0x4BA9AA` 由 `DDPIXELFORMAT` 掩码反推（ctz / clz）；565 下 HalfColorMask=`0x7BEF`，555 下=`0x3DEF`。
3. **k 的取值来源**[实证]：切片索引 k 即 **DrawTile 的 `q`**（AlphaLightingRemap 输出高字节）；`q = floor(lo·hi·(S−1)/32258)`，`hi = clamp254(max(arg,0)·261>>11)`（`0x547DB8`）。**Level 参数直接取 `ConvertClass+0x16C`（=ShadeCount）**，故 LightConvert 与 BufferA 共用 S。
4. **与 0.71875 最大残差**[实证]：S=53 下最近切片 **k=19，gain=19/26=0.730769，abs_res=+0.012019（+1.672%）**；k=18 → 0.692308（−3.679%）。精确 23/32 需 S∈{65,129,193,257,…}（`64k=23(S−1)`），**静态构造 shadeCount 仅 53/1，无精确解**。
5. **RGB565 量化不收敛到 0.71875**[实证·可复算]：S=53/k=19 灰阶 v=1..255 解包后均值 eff_gain≈0.667（std 0.127），**比名义值更偏离**，量化假说不能单独解释 0.71875。
6. **雾格切片归属**[推演]：复合增益 `G = 2q/(S−1)`，`q=floor(lo·hi·52/32258)`（S=53）。要 G≈0.71875 需 q=19，即 `lo·hi ∈ [11787, 12406]`。典型 hi_slice：lo=255→hi=47..48；lo=192→hi=62..64；lo=128→hi=93..96。对应 lighting arg ≈ `hi·2048/261`。
7. **消费端合成**[实证]：DrawTile `dst=BufferA[Table1[src]|ambient]` 纯查表；DrawSHP 经 `SelectPlain/SelectRLEBlitter` 绑 `Data=Midpoint`（k=(S−1)>>1，gain=1.0）；`0x626200` 仅在 **8-bit 表生成期**做最近邻，不在像素环内。
8. **真机 dump 最小集**[待实测]：THEATER_PAL ConvertClass 的 BufferA 全表（S=53 → 53×256 WORD = 27,136 B）+ LightConvert Level=53 全 65,536 WORD + DrawTile 像素环 256 组 (src,Table1,ambient,Table2) 采样。

---

## [1] 逐条必答项结论表

| # | 问题 | 结论 | 证据等级 | 证据锚点 |
|---|------|------|----------|----------|
| Q1 | BufferA 生成公式 | 16-bit：`pack(Pal[j]×2k/(S−1))`；8-bit：V 通道同倍率 + 最近邻 | [实证] | §2.1–2.2、`s01_disasm_core.txt` |
| Q2 | 表项位深 | 运行期 RGB565/555，由 DDraw 掩码反推移位 | [实证] | §2.3、`s04_shift_init_and_abi.txt` |
| Q3 | k 的来源 | DrawTile q = LightConvert 输出高字节；Level=ShadeCount | [实证] | §3.1–3.2 |
| Q4 | DrawTile 合成增益 | `2q/(S−1)`，q 随 (lo,hi) 变化，非常数 | [实证] | §3.3 |
| Q5 | DrawSHP 合成 | Data=Midpoint → gain=1.0（中性切片），需额外 LightConvert/extraLight | [实证] | §3.4 |
| Q6 | 0x626200 角色 | 8-bit 表生成期最近邻（加权 L1 `2dR+4dG+3dB`），非像素路径 | [实证] | §2.4 |
| Q7 | 与 0.71875 残差 | S=53 best k=19，abs_res=**+0.012019**（+1.672%） | [实证] | §4.1 |
| Q8 | 雾格切片 | q=19 需 `lo·hi∈[11776,12406]` | [推演] | §4.2 |
| Q9 | dump 最小集 | BufferA + LightConvert + 像素环采样 | [待实测] | §5 |

---

## [2] ConvertClass 完整 ABI

### 2.0 字段布局（ctor `0x48E740` 零初始化 + YRpp 对拍）[实证]

| 偏移 | 类型 | 名称 | ctor 证据 |
|------|------|------|-----------|
| +0x000 | vptr | vtable `0x7E5358` | `0x48E93B: C7 06 58 53 7E 00` |
| +0x004 | int | BytesPerPixel | `0x48E753: 89 46 04`（surface vfunc +0x70 返回） |
| +0x008..+0x0CF | ptr[50] | Blitters | 零初始化循环 `0x48E756` 起 |
| +0x0D0..+0x16B | ptr[39] | RLEBlitters | 同上 |
| **+0x16C** | size_t | **ShadeCount** | `0x48E91D: 89 86 6C 01 00 00` |
| **+0x170** | void* | **BufferA** | `0x48E9F0` / `0x48EB2A` |
| **+0x174** | void* | **Midpoint** = BufferA + ((S−1)>>1)·stride | `0x48EA10` / `0x48EB3A` |
| +0x178 | void* | BufferB（仅 8-bit，`new(0x100)`） | `0x48E95F` |
| +0x17C | DWORD | CurrentZRemap | Init_Blitters 写 |
| +0x180 | DWORD | HalfColorMask | `0x48EB5A` ← `[0x8A0DE8]` |
| +0x184 | DWORD | QuarterColorMask | `0x48EB6D` ← `[0x8A0DEA]` |

LightConvertClass 继承 ConvertClass，附加 `+0x188 UsedPalette1 / +0x18C UsedPalette2 / +0x190 unknown_buffer / +0x194 UsageCount / +0x198.. Color1 / +0x1A4.. Color2 / +0x1B0 Tinted`（`0x555DA0` ctor 写入）。

ctor 调用约定：`__thiscall`，栈参数 `palette, palette2, surface, shadeCount, skipBlitters`，`ret 0x14`。全库 `call 0x48E740` 共 **22 处**；紧邻 push 立即数实测 **shadeCount ∈ {0x35=53, 1}**（`s01_disasm_core.txt` shadeCount 表；`0x188=392` 为 `new` 大小非 shadeCount）。

### 2.1 BufferA 16-bit 生成 `0x4BBB00` [实证·可复算]

```
; edx = S, ecx = BufferA 基址, [esp+0x20] = palette（RGB 三元组 ×256）
; 外层 k = 0..S−1，[esp+0x10] 累加 k·0x20000
0x004BBB3B  mov eax, [esp+0x10]      ; k*0x20000
0x004BBB3F  lea ecx, [esi-1]         ; S−1
0x004BBB43  idiv ecx                 ; factor = k*0x20000 / (S−1)
; S≤1 时 factor = 0x10000（恒等）
0x004BBB6B  mov dl, [ecx]            ; R
0x004BBB74  imul esi, eax            ; R * factor
0x004BBB84  sar esi, 0x10            ; R' = R * factor / 65536 = R * 2k/(S−1)
; G/B 同式；clamp 255
; pack: R'>>rsr<<rsl | G'>>gsr<<gsl | B'>>bsr<<bsl
0x004BBBEC  mov [ebx-2], dx          ; BufferA[k*256 + j] = packed
0x004BBC04  add ecx, 0x20000         ; 下一 k
```

**闭式**：

```
factor(k,S) = 0x10000                      if S ≤ 1
            = (k · 0x20000) / (S − 1)      else（整除）
BufferA_16[k][j] = pack( clamp255(pal[j].c · factor >> 16) for c in {R,G,B} )
                 = pack( pal[j].rgb · 2k/(S−1) )   （无钳位溢出时）
```

stride = 512 B/slice = 256 WORD。`Midpoint = BufferA + ((S−1)>>1)·512` → 中性切片 k=(S−1)>>1，**gain = 2k/(S−1) = 1.0**（S 奇数时精确，S=53 → k=26，gain=52/52=1.0）。

### 2.2 BufferA 8-bit 生成（ctor 内联）[实证]

```
; S>1 路径 0x48EA51–0x48EB10
; 外层 [esp+0x18] = k = 0..S−1
0x0048EAA8  imul eax, [esp+0x18]    ; V * k
0x0048EAB3  shl eax, 1              ; V * k * 2
0x0048EAB6  dec ecx                 ; S−1
0x0048EAB7  idiv ecx                ; V' = V * 2k/(S−1)
; 然后 call 0x517440（HSV→RGB 反变换）→ call 0x626200（最近邻）→ 写 BufferA[k*256+j] 字节
```

S=1 时：`BufferB = new(0x100)` 另做一套（`B>>=1` 后最近邻），BufferA 填恒等映射。stride = 256 B/slice。

**与 16-bit 差异**[推演·语义]：8-bit 路径倍率施加于 **HSV 亮度通道**（`0x6613A0` RGB→HSV 取 V），反变换 `0x517440` 后 **量化到调色板**，因此会出现「暗端抬升 / 同源不同果」；16-bit 路径是 RGB 三通道线性缩放后 pack，无量化吸附。

### 2.3 表项位深：RGB565 / RGB555 运行期决定 [实证]

`0x4BA9AA–0x4BAAC2`（DDraw 像素格式回调）：

| 全局 | 含义 | 565 典型值 | 555 典型值 |
|------|------|-----------|-----------|
| `[0x8A0DD0]` | R shift-left（ctz of Rmask） | 11 | 10 |
| `[0x8A0DD4]` | R shift-right（8−bits） | 3 | 3 |
| `[0x8A0DE0]` | G shift-left | 5 | 5 |
| `[0x8A0DE4]` | G shift-right | 2 | 3 |
| `[0x8A0DD8]` | B shift-left | 0 | 0 |
| `[0x8A0DDC]` | B shift-right | 3 | 3 |
| `[0x8A0DE8]` | HalfColorMask | `0x7BEF` | `0x3DEF` |

反推法：对每个掩码 `test al,1; sar; inc` 数尾零 → shift-left；`test al,0x80; shl; inc` 数前导零 → shift-right。pack 用 `sar/shl` 可逆适配任意 15/16-bit 格式。**禁止在模板里写死 565**（与 `deep_dive_sweeps_closure.md` BlendMask 结论一致）。

### 2.4 `0x626200` 调色板最近邻 [实证]

```
; ecx = palette base（256×3），stdcall arg = 目标 RGB
; 对 i=0..255：dist = 2·|dR| + 4·|dG| + 3·|dB|   （0x661350）
; 取最小 dist 的 i；并列取先（jge 不替换）
```

距离函数 `0x661350`：`lea ecx,[esi+edx*2]; lea edx,[eax+eax*2]; lea eax,[edx+ecx*2]` ⇒ `2·dR + 4·dG + 3·dB`（加权 L1，非欧氏）。全库 `call 0x626200` 仅 6 处：ctor 8-bit 路径 3 处 + `0x4C39D7/0x4C3B30/0x4C3BD4`（调色板转换簇）。**不在 DrawTile/DrawSHP 像素环内**。

---

## [3] 消费端合成等效增益

### 3.1 DrawTile 表装填 `0x547D78–0x547DE2` [实证]

```
mov eax, [edx+0x16c]        ; ★ ShadeCount 当作 AlphaLightingRemap Level
mov ecx, 0x87E8A8
push eax
call 0x420140               ; FindOrAllocate(Level) → 65536 WORD 表
; hi_slice = clamp254( max(arg,0) * 261 >> 11 )
shl eax, 9                  ; hi_slice * 512
add eax, edi
mov [0xAA10D0], eax         ; Table1 = &data[hi_slice*256]
mov ecx, [eax+0x170]        ; ★ BufferA
mov [0xAA10C0], ecx         ; Table2 = BufferA
```

**ABI 关键耦合**[实证]：DrawTile 直接把 `ConvertClass.ShadeCount(+0x16C)` 传给 `FindOrAllocate`，故 **LightConvert 的 Level ≡ BufferA 的 S**。不存在「S=53 的 BufferA 搭配 Level=256 的 LightConvert」这种静态组合。

hi_slice 映射表[实证·可复算]：

| lighting arg | 0 | 100 | 200 | 400 | 730 | 1000 | 1500 | ≥2016 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hi_slice | 0 | 12 | 25 | 50 | 93 | 127 | 191 | 254 |

### 3.2 像素环 `0x5487B9–0x5487EB` [实证]

```
src16 = *[0xAA10C8]
t     = Table1[src16]           ; AlphaLightingRemap，输出低字节恒 0（R-01）
amb   = *[0xAA10B8]             ; 8-bit ambient
idx   = t | amb                 ; = q·256 + ambient
dst16 = BufferA[idx]            ; = BufferA[q][ambient]
```

**合成闭式**：

```
out_rgb = Pal[ambient].rgb · 2q/(S−1)          （16-bit 路径，再 pack）
q       = floor( lo · hi · (S−1) / 32258 )     （R-01；lo=idx&0xFF, hi=idx>>8）
hi      = clamp254( max(arg,0) · 261 >> 11 )
S       = ConvertClass.ShadeCount（构造恒 53 或 1）
```

无任何 imul/fmul。**合成倍率随 (lo,hi) 二次/双线性变化，不是常数 ×0.71875**（与 R-FOG-STAGE §2.3 一致）。

### 3.3 S=53 下的增益面（摘录）[实证·可复算]

`q = floor(lo·hi·52/32258)`，`gain = 2q/52 = q/26`（`s05_residual.json: composite_L53_S53`）：

| hi\lo | 64 | 128 | 192 | 255 |
|------:|---:|----:|----:|----:|
| 48 | 4 → 0.154 | 9 → 0.346 | 14 → 0.538 | **19 → 0.731** |
| 92 | 9 → 0.346 | 18 → 0.692 | 28 → 1.077 | 37 → 1.423 |
| 96 | 9 → 0.346 | **19 → 0.731** | 29 → 1.115 | 39 → 1.500 |
| 128 | 13 → 0.500 | 26 → 1.000 | 39 → 1.500 | 52 → 2.000（钳） |
| 254 | 26 → 1.000 | 52 → 2.000 | 52 → 2.000 | 52 → 2.000 |

（可见增益随 (lo,hi) 强烈变化；q≥52 后钳到 S−1=52 → gain 2.0。**不存在「整表恒 ×0.72」的静态组合**。）

### 3.4 DrawSHP `0x4AED70` [实证]

`SelectRLEBlitter 0x490E50`（call @ `0x4AF13F`）/ `SelectPlainBlitter 0x490B90`（call @ `0x4AF1D5/0x4AF2C3`）返回的 blitter 对象 `Data` 指针绑定 **`ConvertClass.Midpoint(+0x174)`**（Init_Blitters `0x48EBF0` 反复 `mov ecx,[esi+0x174]; mov [eax+4],ecx`）。

⇒ **默认 SHP 路径等效增益 = 1.0**（中性切片）。SHP 要变暗必须另走 extraLight / LightConvert `UpdateColors 0x556090` / 选定非中性 blitter，**不是 BufferA 雾切片**。DrawTile（地表）与 DrawSHP（物件）增益来源不同——雾第一段只可能在 **DrawTile 链**。

### 3.5 三层合成总表

| 层 | 算子 | 是否含 ×0.71875 |
|----|------|----------------|
| Table1 = AlphaLightingRemap | `q=floor(lo·hi·(S−1)/32258)`，输出 `q<<8` | 否（R-01 结案） |
| OR ambient | `idx = q·256 + ambient` | 否（纯位或） |
| Table2 = BufferA | `Pal[amb]·2q/(S−1)` + pack | **机制可、S=53 参数否** |
| 0x626200 最近邻 | 仅 8-bit 表生成期 | 可致暗端抬升，但不在 16-bit 像素环 |

---

## [4] 等效增益闭式 vs 实测 0.71875 残差

### 4.1 切片增益残差表 [实证·可复算]

精确解 `2k/(S−1) = 23/32 ⇔ 64k = 23(S−1)`：

| S | k | gain | abs_res | rel |
|---:|---:|---:|---:|---:|
| **65** | **23** | **0.718750** | **0** | 0 |
| **129** | **46** | **0.718750** | **0** | 0 |
| 193 | 69 | 0.718750 | 0 | 0 |
| **257** | **92** | **0.718750** | **0** | 0 |
| **53** | **19** | **0.730769** | **+0.012019** | **+1.672%** |
| 53 | 18 | 0.692308 | −0.026442 | −3.679% |
| 1 | — | 1.000000 | +0.281250 | +39.1% |

**最大残差（S=53 可达域内）= |0.730769 − 0.71875| = 0.012019**（k=19）。k=18 残差 0.026442。**无整数切片达到 23/32**。

### 4.2 RGB565 量化后的有效增益 [实证·可复算]

灰阶 v=1..255，`pack565(v·gain)` 解包均值：

| 切片 | 名义 gain | 均值 eff_gain | vs 0.71875 | std |
|------|----------:|--------------:|-----------:|----:|
| S=53 k=19 | 0.730769 | 0.667231 | −0.051519 | 0.127 |
| S=53 k=18 | 0.692308 | 0.627590 | −0.091160 | 0.125 |

**量化把增益往下拉，残差反而扩大**。⇒「BufferA + 调色板最近邻量化」复合假说（R-FOG-STAGE C11）在 **16-bit 路径上不能解释 0.71875**；若走 **8-bit 路径**（V 缩放 + `0x626200` 吸附），暗端抬升与非函数性可成立，但亮端也难以锁死 0.71875（[推演]，需真机表内容）。

### 4.3 雾格切片归属闭式 [推演]

目标 `2q/52 = 23/32` ⇒ q≈18.6875 ⇒ **q=19**。由 `q=floor(lo·hi·52/32258)=19`：

```
11787 ≤ lo·hi ≤ 12406
```

（`19·32258/52 = 11786.58`，`20·32258/52 = 12406.92`）

| lo（源色低字节） | hi_slice 域 | 近似 lighting arg = hi·2048/261 |
|---:|---:|---:|
| 255 | 47–48 | 369–377 |
| 192 | 62–64 | 487–503 |
| 128 | 93–96 | 731–754 |
| 96 | 123–129 | 966–1013 |

雾格若与无雾格共用同一 ConvertClass，差异只可能来自 **ambient（0xAA10B8）或 hi_slice（0x547DB8）**。残差 0.012019 是 **S=53 量化到整数切片的地板误差**，不是计算误差。

---

## [5] 可复算 dump 规格（真机，不实测）

供 ZC 合并卡执行的最小只读 dump 集：

| # | 对象 | 地址/来源 | 大小 | ROI | 判据 |
|---|------|-----------|------|-----|------|
| D1 | BufferA 全表 | `ConvertClass+0x170`（THEATER_PAL `0x87F6C4` 解引用） | S×256×2 B = **27,136 B**（S=53） | 全表；重点切片 **k=18,19,20,26** 各 256 WORD | 逐切片算 `mean(out/in)`；若某切片≈0.71875 ⇒ 定位；若无 ⇒ 量化/ambient 假说 |
| D2 | Midpoint | `ConvertClass+0x174` | 512 B | k=26 | 验证 gain=1.0 |
| D3 | LightConvert 表 | `FindOrAllocate(53)` 返回（断点 `0x420140`） | 0x20008 B | 全 65,536 WORD；或仅 hi_slice 行 | 检验 `q<<8` 与 R-01 公式对拍 |
| D4 | 像素环采样 | 断点 `0x5487EB` | 256 组 | 雾格 vs 无雾格各 256 | (src16, Table1_out, ambient, idx, Table2_out)；算 `out/in` |
| D5 | 运行期位深常量 | `[0x8A0DD0..0x8A0DE4]`, `[0x8A0DE8]` | 28 B | — | 确认 565/555 与 HalfColorMask |
| D6 | ambient 流 | `[0xAA10B8]` 指向缓冲 | 一帧 tile 数 | 雾格 vs 无雾格 | 是否雾=ambient 偏移 |

**最小不可约集 = D1 + D4**（表内容 + 像素环因果采样）。D5 一行读取即可排除位深误设。

**ZC 合并卡建议判定表**：

| D1 观测 | D4 观测 | 归因 |
|---------|---------|------|
| 某切片 mean≈0.71875 | out/in 与 src 无关 | BufferA 切片定谳（改 S 或改 k） |
| 无切片接近 | out/in 随 src 变、暗端抬升 | 8-bit 量化 + ambient 组合 |
| 无切片接近 | out/in 恒定≈0.72 但表内无 | 增益在 ambient/hi_slice 选择层，不在表内 |

---

## [6] 与前作差异/勘误

1. R-FOG-STAGE 称「pack RGB565（用 0x8A0DD0..0x8A0DE4 位域移位常量）」——**补充**：该常量运行期由 DDraw 掩码生成，**565 或 555 均可能**；写死 565 的模板会错。
2. R-FOG-STAGE C11「调色板最近邻量化可模拟 ×0.72 并致暗端抬升」——**限定**：`0x626200` 仅存在于 **8-bit 表生成**；16-bit DrawTile 像素环无量化，且 565 反量化使残差**扩大**（§4.2）。C11 在 16-bit 路径降权，仅 8-bit 路径存活。
3. **新证**：DrawTile 的 LightConvert Level **就是** `ConvertClass.ShadeCount`（`0x547D78` 直读 +0x16C）。此前「Level 分布」与「shadeCount 分布」是同一组数。

---

## [7] 证据等级分布

- `[实证]`：ABI 布局、BufferA 双路径闭式、位深运行期反推、距离函数、像素环、DrawSHP Midpoint 绑定、S=53 残差、shadeCount 构造分布、audit_bytes 62/62
- `[推演]`：8-bit V 通道语义（HSV 反变换）、雾格 lo·hi 域归属、C11 分路径降权
- `[待实测]`：D1–D6 dump

---

## [8] 写作用域合规声明

- 新增：`docs/re/buffera_shade_table_deep_dive.md`（本文）、`out/re_work/re_sprint/R_buffera/**`
- 未触碰：`ra2render/**`、`ra2youli/**`（exe 只读）、`tools/**`、`out/loadbench/**`、`out/reverse/**`、台账、看板、ATLAS、已有其他 deep_dive
- 只读基线：`ra2youli/gamemd.exe` MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`
- ★未启动游戏、未注入、未改任何二进制

## [9] 交付物清单

| 文件 | 内容 |
|---|---|
| `s01_disasm_core.py` / `s01_disasm_core.txt` | BufferA 16-bit 生成 / 量化 / ctor / DrawTile / DrawSHP / ctor 调用点与 shadeCount |
| `s02_pack_distance_drawshp.py` / `s02_pack_distance_drawshp.txt` | pack 尾部、RGB 常量、距离函数、AA10xx xref |
| `s03_drawshp_and_transforms.py` / `s03_drawshp_and_transforms.txt` | DrawSHP blitter 选型、0x517440/0x6613A0、626200 调用簇 |
| `s04_shift_init_and_abi.py` / `s04_shift_init_and_abi.txt` | 位深常量运行期初始化、Midpoint 绑定 |
| `s05_residual.py` / `s05_residual.json` / `s05_residual.txt` | 增益残差、RGB565 有效增益、hi_slice 映射、dump 规格 |
| `verify_closed_form.py` | 标题数字一键复算（26/26 PASS） |
| `claims_r_buffera.txt` | 字节级断言（`python tools/audit_bytes.py` → **62/62 OK**） |
