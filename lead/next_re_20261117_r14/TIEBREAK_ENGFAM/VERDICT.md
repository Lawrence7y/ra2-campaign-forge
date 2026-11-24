# TIEBREAK-ENGFAM — 对 S17 英文族 34 行 PASS 结论的异族反审（异族 B / DeepSeek）

只读 `ra2youli\gamemd.exe`。写域仅 `TIEBREAK_ENGFAM\`。未改 `coverage.tsv` / `PANEL.md` / `R14_COMMON.md` / 台账，未交 delta，未建 venv、未 pip install。

## 0. 自校验与通道

| 项 | 值 |
|---|---|
| SHA-256 | `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（自算，与卡面一致） |
| ImageBase | `0x400000` |
| `.text` | `0x401000` .. `0x7E038D`（vsize 0x3DF38D 实算，与卡面一致） |
| 工具 | Python 3.12.10 / capstone 5.0.7（`skipdata=True`）/ pefile 2024.8.26 |

通道（全部自写，脚本在 `work/`，每步可复跑）：

| 脚本 | 作用 | 是否读被审方产物 |
|---|---|---|
| `work/pe.py` | 自写 PE32 读取（struct，不经 pefile）；RTTI `[vt-4]=COL → COL+0xC=TD → TD+8 内联名` | 否 |
| `work/s1_extract.py` | 从 `coverage.tsv` 过滤 34 行、排序、抽样 | 只读 coverage.tsv |
| `work/s2_bodies.py` | 每槽 0x80 字节窗口 + 线性反汇编 + md5 | 否 |
| `work/s3_family.py` | 35 槽 + 3 个对照的循环/写/调用/eax 检查自动分类 | 否 |
| `work/s4_resolve.py` | IAT 名称、IID 常量、Save_Core 调用点、构造写入 + RTTI | 否（构造点仅以"地址"为线索，字节自己读、RTTI 自己解析） |
| `work/s5_savecore.py` | 任意区间反汇编 | 否 |
| `work/s6_callers.py` | 全 `.text` 扫 `E8 rel32`（纯字节算术）+ 链式调用 edx 追踪 | 否 |
| `work/s7_rtti.py` | 全 `.text` 扫 `C7 05 dst imm` 建索引，按需取 35 个向量 | 否 |
| `work/s8_report.py` | 模板同一性（分支目标归一为相对偏移） | 否 |
| `work/s9_atexit.py` | ㉓ 判别：装表点是否落在 `push <dtor>; call 0x7C978A` 的析构器里 | 否 |
| `work/s10_bounds.py` | 函数边界、`E8` 调用者、`.rdata` 引用 | 否 |
| `work/s11_loopbody.py` | 逐指令标注循环体（写/读/栈/非栈） | 否 |
| `work/s13_pefile.py` | pefile 独立复核导入目录（第二通道） | 否 |

证据文本：`EVIDENCE\bodies6.txt`、`family.txt`、`loopbodies.txt`、`resolve.txt`、`callers.txt`、`rtti35.txt`、`atexit35.txt`、`template.txt`、`bounds.txt`、`rows34.tsv`；原始 json：`family_raw.json`、`resolve.json`、`rtti35.json`。

## 1. 抽样

过滤命令（与实际执行一致）：

```powershell
Select-String -Path COVERAGE\coverage.tsv -Pattern "unproven|unverified|not proven" -CaseSensitive:$false
```

命中 **34 行**，全部 `subsystem=S17`、`grade=[已证]`，name 为 `Save_VectorBlock_01..35` 缺 #17。

抽样规则（确定性，见 `work/s1_extract.py`）：取 34 行地址排序后的 `idx 0`（最小）、`idx 33`（最大），中间取 `idx floor(k*(n-1)/5)`，k=1..4 → 6, 13, 19, 26。

| idx | entry | 备注 |
|---|---|---|
| 00 | `0x0067FDF0` | 最小 |
| 06 | `0x006800F0` | |
| 13 | `0x00680470` | |
| 19 | `0x006807F0` | |
| 26 | `0x00680B70` | |
| 33 | `0x00680EF0` | 最大 |

---

## 2. 一、6 行独立复核

### 2.0 模板（先给一遍完整字节，后面 6 行只在偏移上复述）

`0x0067FDF0` 完整 127 字节（`md5 = 9f6770a9cd27b9fa49558adf28c92f10`）：

```
0067FDF0  83 EC 08 53 56 57 8B FA 8B D9 6A 00 8B 47 10 8D  ...SVW....j..G..
0067FE00  54 24 14 8B 0B 6A 04 52 53 89 44 24 20 FF 51 10  T$...j.RS.D$ .Q.
0067FE10  85 C0 7C 54 8B 44 24 10 33 F6 85 C0 7E 48 8B 47  ..|T.D$.3...~H.G
0067FE20  04 C7 44 24 0C 00 00 00 00 8D 54 24 0C 8B 04 B0  ..D$......T$....
0067FE30  52 68 80 7C 7F 00 50 8B 08 FF 11 85 C0 7C 29 8B  Rh.|..P......|).
0067FE40  44 24 0C 53 50 FF 15 F4 15 7E 00 85 C0 7C 19 8B  D$.SP....~...|..
0067FE50  44 24 0C 50 8B 08 FF 51 08 85 C0 7C 0B 8B 44 24  D$.P...Q...|..D$
0067FE60  10 46 3B F0 7C B8 33 C0 5F 5E 5B 83 C4 08 C3 90  .F;.|.3._^[.....
```

反汇编（关键行）：

```
+0x0A  push 0                   ; pcbWritten = NULL
+0x0C  mov  eax,[edi+0x10]      ; 取向量 Count（[vec+4]=Items 于 +0x2E 再用）
+0x0F  lea  edx,[esp+0x14]      ; &count 局部（= sub esp,8 预留的 E0-4 槽）
+0x13  mov  ecx,[ebx]           ; IStream vptr
+0x15  push 4                   ; cb = 4
+0x17  push edx                 ; pv = &count
+0x18  push ebx                 ; this = pStm
+0x19  mov  [esp+0x20],eax      ; count 溢出到局部
+0x1D  call [ecx+0x10]          ; IStream vtable slot4 = Write
+0x20  test eax,eax / +0x22 jl  ; ← HRESULT 检查 #1
+0x24  mov  eax,[esp+0x10]      ; 取回 count
+0x2A  test eax,eax / +0x2C jle ; ← 不是 HRESULT，是 count==0 提前退出
+0x2E  mov  eax,[edi+4]         ; Items 数组基址（循环目标点）
+0x31  mov  [esp+0xC],0         ; ps=NULL，**栈写**
+0x39  lea  edx,[esp+0xC]       ; &ps
+0x3D  mov  eax,[eax+esi*4]     ; Items[i]
+0x40  push edx                 ; ppv = &ps
+0x41  push 0x7F7C80            ; riid = IID_IPersistStream
+0x46  push eax                 ; this = Items[i]
+0x47  mov  ecx,[eax]           ; QI 走对象自身 vptr
+0x49  call [ecx]               ; QI（slot0）
+0x4B  test eax,eax / +0x4D jl  ; ← HRESULT 检查 #2
+0x4F  mov  eax,[esp+0xC]       ; ps
+0x53  push ebx                 ; pStm
+0x54  push eax                 ; ps
+0x55  call [0x7E15F4]          ; ole32!OleSaveToStream
+0x5B  test eax,eax / +0x5D jl  ; ← HRESULT 检查 #3
+0x5F  mov  eax,[esp+0xC]
+0x63  push eax
+0x64  mov  ecx,[eax]
+0x66  call [ecx+8]             ; Release（slot2）
+0x69  test eax,eax / +0x6B jl  ; ← HRESULT 检查 #4
+0x6D  mov  eax,[esp+0x10]
+0x71  inc  esi                 ; 推进（寄存器）
+0x72  cmp  esi,eax
+0x74  jl   0x67FE1E            ; 回边 → +0x2E
+0x76  xor  eax,eax  / pops / add esp,8 / ret     ; 成功返回 0
0x67FE68 = 失败落点：pops / add esp,8 / ret      ; eax **原样**（失败 HRESULT）
```

三处 vtable 位移与 COM 布局自洽：`[ecx+0]`=QueryInterface、`[ecx+8]`=Release、`[ecx+0x10]`=Write（IUnknown 3 槽 + ISequentialStream Read/Write）；三条调用的压参个数（3+this、2、1）与 `IStream::Write`、`OleSaveToStream`、`Release` 签名逐一吻合。

外部身份（两条独立通道）：

| 项 | 我方解析 | 第二通道 |
|---|---|---|
| IAT `0x7E15F4` | `work/s4` 自写导入目录遍历 → `ole32.dll!OleSaveToStream` | `work/s13` pefile → 同一结果；pefile 另示 `dir[12] IAT rva 0x3E1000 size 0x608`，故该槽位于 `.rdata` 起始的 IAT 块，静态 dword（`0x410868`）是加载前残值，不作证据 |
| IID `0x7F7C80` | `09 01 00 00 00 00 00 00 C0 00 00 00 00 00 00 46` = `{00000109-0000-0000-C000-000000000046}` = **IPersistStream** | — |

### 2.1 `0x0067FDF0`（最小行）

1. **循环真实存在**：回边 `0x0067FE64 jl`（字节 `7C B8`，rel8 = -0x48 → 目标 `0x0067FE1E`），循环体 `+0x2E .. +0x74`，27 条指令。上界从 `[edi+0x10]`（`+0x0C mov eax,[edi+0x10]`）读出，`+0x19` 溢出到 `[esp+0x20]`（即局部 `[esp+0x10]`），`+0x72 cmp esi,eax` 比较；元素基址 `[edi+4]`（`+0x2E`），按 `eax+esi*4` 索引 → 结构自洽为 `{vptr@0, Items@+4, …, Count@+0x10}`。
2. **循环体内无非栈写指令。** 循环体内写内存的指令只有两类：
   - `+0x31 0x0067FE21 C7 44 24 0C 00 00 00 00  mov dword ptr [esp+0xC],0` —— **栈写**（`ps = NULL` 初值）
   - 6 条 `push`（`0x67FE30/31/36/43/44/53`）—— 栈写
   `call dword ptr [ecx]/[ecx+8]/[0x7E15F4]` 的操作数是**读**函数指针，不是写。**循环体内非栈写 = 0 条。**
3. **四处调用真实存在**：`+0x1D call [ecx+0x10]`（见 2.0 语义）、`+0x49 call [ecx]`（QI，IID 常量 `0x7F7C80`）、`+0x55 FF 15 F4 15 7E 00 call [0x7E15F4]`（`ole32!OleSaveToStream`）、`+0x66 call [ecx+8]`（Release）。
4. **HRESULT 被检查**：`0x0067FE10 test eax,eax` → `0x0067FE12 jl 0x0067FE68`；`0x0067FE3B`→`0x0067FE3D jl`；`0x0067FE4B`→`0x0067FE4D jl`；`0x0067FE59`→`0x0067FE5B jl`。四条全部来自 call 的 eax，全部跳到 `0x0067FE68`（pops + `add esp,8` + `ret`，**不清零 eax**）→ 失败时函数原样返回该 HRESULT；成功路径 `0x0067FE66 xor eax,eax` 返回 0。
   **调用方也检查**：`0x0067DF0F call 0x67FDF0` 之后紧跟 `0x0067DF14 test eax,eax` → `0x0067DF16 jge 0x67DF22`，失败则 `xor al,al` 返回 false。契约两端都被使用。
5. **② 身份可取**：调用方 `0x0067DF08 BA 30 3E A8 00  mov edx,0xA83E30` 传入向量 `0x00A83E30`；静态初始化器 `0x004E6E7D C7 05 30 3E A8 00 A4 9F 7E 00  mov dword ptr [0xA83E30],0x7E9FA4` 装活表；`vt=0x007E9FA4` → `COL=0x00801610` → `TD=0x008234E0` → 名串 `0x008234E8` = `.?AV?$DynamicVectorClass@PAVFactoryClass@@@@`（字节 `2E 3F 41 56 3F 24 44 79 6E 61 6D 69 63 56 65 63 …`，见 `EVIDENCE\resolve.txt`）。
   ㉓ 已核：该向量另有第二处装表 `0x004E6EA8 → 0x007E9FC4 = VectorClass<PAVFactoryClass>`，位于 `0x004E6EA0`，而 `0x004E6E62 68 A0 6E 4E 00 push 0x4E6EA0` + `0x004E6E96 E8 EF 28 2E 00 call 0x7C978A` 表明它是 **atexit 注册的析构器** ⇒ **死表**。活表是 DV 那张（`work/s9_atexit.py`，35/35 同形）。

### 2.2 `0x006800F0`

1. 循环：回边 `0x00680164 jl 0x0068011E`（字节 `7C B8`），体 `+0x2E..+0x74`；上界同 `[vec+0x10]`，`vec=0x00A83DC8`。
2. 循环体内非栈写：**0 条**。仅 `0x00680121 C7 44 24 0C 00 00 00 00 mov [esp+0xC],0`（栈）+ 6 push。
3. 调用：`0x0068010D call [ecx+0x10]`；`0x00680139 call [ecx]`（前一条 `68 80 7C 7F 00` 压 `0x7F7C80`）；`0x00680145 FF 15 F4 15 7E 00 call [0x7E15F4]`；`0x00680156 call [ecx+8]`。
4. HRESULT 检查：`0x00680110/0x00680112 jl 0x680168`；`0x0068013B/0x0068013D`；`0x0068014B/0x0068014D`；`0x00680159/0x0068015B` —— 全部 → `0x00680168`（失败落点，eax 不清零）。成功 `0x00680166 xor eax,eax`。调用方 `0x0067DFAB call` → `0x0067DFB0 test eax,eax` / `0x0067DFB2 jge`。
5. ② 身份：`0x004E697D mov [0xA83DC8],0x007E9D64`；`COL=0x008010B8`、`TD=0x00823138`、名串 `0x00823140` = `.?AV?$DynamicVectorClass@PAVParticleClass@@@@`；死表 `0x004E69A8 → VectorClass<PAVParticleClass>`（析构器 `0x004E69A0`，注册于 `0x004E6962`）。

### 2.3 `0x00680470`

1. 循环：`0x006804E4 jl 0x0068049E`，体 `+0x2E..+0x74`；`vec=0x00A83D80`。
2. 循环体内非栈写：**0 条**。仅 `0x006804A1 C7 44 24 0C 00 00 00 00 mov [esp+0xC],0` + 6 push。实体字节：
   ```
   006804A0  04 C7 44 24 0C 00 00 00 00 8D 54 24 0C 8B 04 B0
   ```
3. 调用：`0x006804B9 call [ecx]`（前 `68 80 7C 7F 00`）；`0x006804C5 FF 15 F4 15 7E 00`；`0x006804D6 call [ecx+8]`；`0x0068048D call [ecx+0x10]`。
4. HRESULT：`0x00680490/92`、`0x006804BB/BD`、`0x006804CB/CD`、`0x006804D9/DB`，全部 `jl 0x6804E8`；成功 `0x006804E6`。调用方 `0x0067E061 call` → `0x0067E066 test eax,eax`。
5. ②：`0x004E71FD mov [0xA83D80],0x007EA164`；`COL=0x00801A38`、`TD=0x008237C8`、名串 `0x008237D0` = `.?AV?$DynamicVectorClass@PAVOverlayTypeClass@@@@`。

### 2.4 `0x006807F0`

1. 循环：`0x00680864 jl 0x0068081E`，体 `+0x2E..+0x74`；`vec=0x00A83CB8`。字节串与 2.3 逐字节相同（见 `EVIDENCE\bodies6.txt`）。
2. 循环体内非栈写：**0 条**（`0x00680821 mov [esp+0xC],0` + 6 push）。
3. 调用：`0x0068080D`/`0x00680839`(QI)/`0x00680845`(IAT)/`0x00680856`(Release)。
4. HRESULT：`0x00680810/12`、`0x0068083B/3D`、`0x0068084B/4D`、`0x00680859/5B`，全部 `jl 0x680868`；调用方 `0x0067E117` → `0x0067E11C test eax,eax`。
5. ②：`0x004E78FD mov [0xA83CB8],0x007EA4E4`；`COL=0x00802288`、`TD=0x00823E28`、名串 `0x00823E30` = `.?AV?$DynamicVectorClass@PAVSuperClass@@@@`。

### 2.5 `0x00680B70`

1. 循环：`0x00680BE4 jl 0x00680B9E`，体 `+0x2E..+0x74`；`vec=0x008A0208`。
2. 循环体内非栈写：**0 条**（`0x00680BA1 mov [esp+0xC],0` + 6 push）。
3. 调用：`0x00680B8D`/`0x00680BB9`(QI)/`0x00680BC5`(IAT `0x7E15F4`)/`0x00680BD6`(Release)。
4. HRESULT：`0x00680B90/92`、`0x00680BBB/BD`、`0x00680BCB/CD`、`0x00680BD9/DB` → `0x680BE8`；调用方 `0x0067E2A9` → `0x0067E2AE test eax,eax`。
5. ②：`0x004A6C8D mov [0x8A0208],0x007E5EDC`；`COL=0x007FFB10`、`TD=0x0081FF58`、名串 `0x0081FF60` = `.?AV?$DynamicVectorClass@PAVDiskLaserClass@@@@`。

### 2.6 `0x00680EF0`（最大行）

1. 循环：`0x00680F64 jl 0x00680F1E`，体 `+0x2E..+0x74`；`vec=0x00B04BD0`。
2. 循环体内非栈写：**0 条**（`0x00680F21 mov [esp+0xC],0` + 6 push）。
3. 调用：`0x00680F0D`/`0x00680F39`(QI)/`0x00680F45`(IAT)/`0x00680F56`(Release)。
4. HRESULT：`0x00680F10/12`、`0x00680F3B/3D`、`0x00680F4B/4D`、`0x00680F59/5B` → `0x680F68`；调用方 `0x0067E3AA` → `0x0067E3AF test eax,eax`。
5. ②：`0x0065B17D mov [0xB04BD0],0x007F07A4`；`COL=0x008085F8`、`TD=0x008395C8`、名串 `0x008395D0` = `.?AV?$DynamicVectorClass@PAVRadSiteClass@@@@`。

### 2.7 ④（附核，不在卡的三件事内，但 PASS 需要它）

全 `.text` 纯字节扫描 `E8 rel32`（`work/s6_callers.py` chan A）：**每个槽恰好 1 个调用点**，全部在 `0x67D300` 起的函数体内，且调用前 `mov edx,<.bss 向量>`、`mov ecx,esi`：

| entry | 唯一 call site | edx 向量 |
|---|---|---|
| `0x0067FDF0` | `0x0067DF0F`（`E8 DC 1E 00 00`） | `0x00A83E30` |
| `0x006800F0` | `0x0067DFAB` | `0x00A83DC8` |
| `0x00680470` | `0x0067E061` | `0x00A83D80` |
| `0x006807F0` | `0x0067E117` | `0x00A83CB8` |
| `0x00680B70` | `0x0067E2A9` | `0x008A0208` |
| `0x00680EF0` | `0x0067E3AA` | `0x00B04BD0` |

`0x67D300` 自身是函数入口（前一字节 `0x67D2FF` 是 `C2 04 00` 的 `ret 4`），并被 `0x67D1AF E8 4C 01 00 00` 直调。这些槽的 VA 在 `.rdata` 中出现 **0 次**（`work/s10`），故 ④ 只能靠 direct call，而 direct call 确实存在且唯一。

> **引自被审方、未独立复核**：`0x67D300` 的 EP 可达性（`0x7CD80F → 3 roots`）与其反向闭包 81 个 vtable 成员；「Save_Core」这个名字；`Save_VectorBlock_NN` 命名。我只核到「`0x67D300` 是一个真函数入口，有 1 个 `E8` 调用者 `0x67D1AF`」，未做 CFG 正向可达性证明。

---

## 3. 二、③b 子形态裁定

### 3.1 逐行两个独立判定

| entry | ③b② | 依据 | ③b④ | 依据 |
|---|---|---|---|---|
| `0x0067FDF0` | **yes** | 4 条 call 派生 HRESULT 检查 `0x67FE10/12`、`0x67FE3B/3D`、`0x67FE4B/4D`、`0x67FE59/5B`，全 `jl 0x67FE68`，失败不清 eax、成功 `xor eax,eax` | **no** | 循环体内非栈写 0 条；唯一普通写 `0x67FE21 mov [esp+0xC],0` 是栈写，另 6 条 push |
| `0x006800F0` | **yes** | `0x680110/12`、`0x68013B/3D`、`0x68014B/4D`、`0x680159/5B` → `0x680168` | **no** | 同上（`0x680121` 栈写 + 6 push） |
| `0x00680470` | **yes** | `0x680490/92`、`0x6804BB/BD`、`0x6804CB/CD`、`0x6804D9/DB` → `0x6804E8` | **no** | 同上（`0x6804A1` 栈写 + 6 push） |
| `0x006807F0` | **yes** | `0x680810/12`、`0x68083B/3D`、`0x68084B/4D`、`0x680859/5B` → `0x680868` | **no** | 同上（`0x680821` 栈写 + 6 push） |
| `0x00680B70` | **yes** | `0x680B90/92`、`0x680BBB/BD`、`0x680BCB/CD`、`0x680BD9/DB` → `0x680BE8` | **no** | 同上（`0x680BA1` 栈写 + 6 push） |
| `0x00680EF0` | **yes** | `0x680F10/12`、`0x680F3B/3D`、`0x680F4B/4D`、`0x680F59/5B` → `0x680F68` | **no** | 同上（`0x680F21` 栈写 + 6 push） |

### 3.2 直接回答

> **这 6 行里，靠 ③b② 成立的有 6 行；靠 ③b④ 成立的有 0 行；两者都不成立的有 0 行。**

### 3.3 逐条说明这两条判定为什么这样落

**③b④ = no（与被审方说法相反，这条必须改口）。**
被审方的 `verdict.tsv` 34 行 reason 都写 `IStream::Write(&Count,4,NULL)@+0x1D; … OleSaveToStream via IAT[0x7E15F4]@+0x55 (non-stack write)`，把「调用了会写 IStream 的函数」当作「循环体内有非栈写」。按 D-42 ③b④ 的原文（读→判→写→推进）与 `0045A640` 被推翻时用过的那条界线（写必须落在**本函数循环体内**的指令上）：

- 循环体 `+0x2E..+0x74` 里所有显式写内存指令都是 `[esp+0xC]`（栈）；
- 另外 6 条 `push` 也是栈；
- `call [ecx+0x10]` / `call [0x7E15F4]` 的 `[...]` 是**读**函数指针；
- 真正的流写发生在 `IStream::Write` / `OleSaveToStream` 的**被调用者内部**，不构成本函数的循环内写。

被审方的「非栈写」在字节上不存在。这不是措辞偏好问题，是把「被调用者做的事」记成了「本函数做的事」。

> **一处必须说明的边界**（避免把话说死）：项目对 ③b④ 的措辞是「『写』必须是**栈外写**或**可伪证返回码**」。若把后半句读进来，循环体内那三条 HRESULT 检查（`+0x4B/+0x5D/+0x69`）确实构成「每轮可伪证」的分支，③b④ 就能以这条支路成立。但这样一来 ③b④ 与 ③b② 变成同一个证据的两种叫法（同源不得双计，参见 `⑰` 同源判据），本卡按卡面给定口径（「循环体内是否存在**非栈写指令**」）判 **no**，并在 `sample.tsv` 里如实标 `ring3b4=no`。**两种读法下该行的 PASS 都不变**，变的只是 reason 该写 ③b② 还是 ③b④ —— 这正是本族最该改的一处措辞。

**③b② = yes（这条站得住，而且比 0045A640 强）。**
`0045A640` 被判 ③b② 不成立的两条实质理由在这里都不成立：
1. 那里「体内 0 条 `call`，取不到被调返回值」——这里体内 4 条 call，被比较操作数**就是** call 的 eax（正是项目已采纳的实操口径）；
2. 那里是 `bool` 主输出（D-46(A) 明写「bool 主输出不算」）——这里是 **HRESULT 错误码**：成功 `xor eax,eax`=S_OK、失败原样返回首个失败 HRESULT，且负值走 `jl`（S_FALSE=1 视为成功，是标准 HRESULT 惯用法）；
3. 契约还被**调用方消费**：`0x67DF14 test eax,eax` / `0x67DF16 jge`（每槽后同形），失败则 `xor al,al` 返回 false。可伪证性来自两端。

故：**被审方的「③b④ 有界循环带非栈写」描述属措辞用错，但「该行 ③b 成立」的结论仍成立，成立通道是 ③b②。**

### 3.4 分类器的正负对照（证明「0 条非栈写」不是检测盲）

同一分类器（`work/s3_family.py`，判据：`mnem ∈ 写集合 ∧ operand0 = 内存`，栈判定 `base ∈ {esp,ebp}`）：

| 对照 | 期望 | 实测 |
|---|---|---|
| `0x0045A640`（先例：应判无写） | 循环体内 0 写 | 回边 `0x45A66C jl 0x45A65D`、体 8 条、**写 0 条**、push 0、call 0 —— 与 `TIEBREAK_0045A640\PROGRESS.md` 独立结论一致 |
| `0x0045A680`（正对照） | 循环体内有非栈写 | 回边 `0x45A6DC jl 0x45A6CE`，体内 `0x0045A6D8 89 54 87 FC  mov dword ptr [edi+eax*4-4],edx` → **NON-STACK** |
| 34 槽 | — | 体内写 1 条，非栈 **0** 条 |

即：该检测器在同族相邻代码上确实能看见「循环体内非栈写」，在 34 槽上给出 0 是字节事实而非漏检。

> 附一条纪律说明：`call dword ptr [ecx]` 这类指令在 capstone 里首个操作数是 `MEM`，若按「operand0 是内存即写」粗暴判定，会把三条 call 误判成「非栈写」而错给 ③b④。我最初的标注脚本就犯过这个错（`EVIDENCE` 里未保留该错版），修正后 call/jmp 一律按「读函数指针」处理。这正是本族结论最容易被弄错的那一步。

---

## 4. 三、能否外推到 34 行（摘要；完整论证见 `FAMILY.md`）

**同模板？——是，且是字节等同而不是「同族相似」。**

| 证据 | 结果 |
|---|---|
| 127 字节体 md5 | 35/35 全为 `9f6770a9cd27b9fa49558adf28c92f10`（34 行 + `0x6805F0`） |
| 归一后指令序列 `(相对偏移, mnemonic, operands)` | **35/35 完全一致**，54 条指令无一处偏差（分支目标归一为相对偏移后比较） |
| 相对偏移同一性 | `+0x1D` `+0x20/22` `+0x2A/2C` `+0x2E` `+0x31` `+0x49` `+0x4B/4D` `+0x55` `+0x5B/5D` `+0x66` `+0x69/6B` `+0x72/74` `+0x76` 全部同位 |
| 全 `.text` 字节相同副本 | **恰 35 份**，`0x0067FDF0`..`0x00680EF0` 连号，步长 `0x80` |

**外推条件（成立所需的三条，均已满足）**：
1. ③ **不需要外推** —— 34 行是同一段字节，「一行 ③ 成立 ⇒ 全族成立」是同义反复；
2. ② ④ **未被外推，而是全量枚举** —— 二者逐行不同（不同 `.bss` 向量 / 构造点 / RTTI 名 / 调用点），我查了全部 35 行：35/35 拿到唯一活表 RTTI（死表全部定位在 atexit 析构器内，㉓ 通过），35/35 每槽恰好 1 个 `E8` 调用点且 `edx` 与 ② 的 `.bss` 地址一一对应；
3. ① 入口形态 35/35 同形（前一字节 `0x90`、同序言、`ret` 在 `+0x7E`）。

**残余风险（摘要，详见 `FAMILY.md §3.2`）**：
1. 34 行的 ③ 判定**完全相关、同涨同落**，抽样再多也不降低该风险；
2. ③b② 是**政策旋钮**：若把它收窄到「本体自生错误码（GetLastError 式）」而不认 HRESULT 透传，34 行全掉 —— 字节只证明「4 处检查 + 返回值区分成败」，不证明「HRESULT 一定算 ③b②」；
3. ④ 的 EP 可达性（`0x7CD80F → 3 roots`、闭包 81 vt 成员）**引自被审方、未独立复核**；
4. ② 的强度边界：拿到的是**容器实例**名 `DynamicVectorClass<PAVXxx>`，元素类名只作为模板实参出现，没有元素类自身的 COL/TD；
5. 「35 个槽」是模板副本数，**不是 S17 的行数**（S17 = 34）。

**`0x6805F0` 是不是第 17 个成员？——是。** 体字节与 34 行同一 md5；地址正好在第 17 格（`0x680570` → **`0x6805F0`** → `0x680670`，步长 `0x80`）；`0x0067E0AF E8 3C 25 00 00` 是它全 `.text` 唯一的 `E8` 调用点，前一条 `0x0067E0A8 BA 20 41 8B 00 mov edx,0x8B4120`，位置夹在 #16（`0x67E095`）与 #18（`0x67E0C9`）之间；向量 `0x8B4120` 的活表 `0x004E6F7D → 0x007EA024`，`COL=0x00801740`、`TD=0x008235B0`、名串 `0x008235B8` = `.?AV?$DynamicVectorClass@PAVSideClass@@@@`。故它与 `coverage.tsv` 里 S05 `Unsorted::Save_Sides` 对得上，**属同一指令模板，但不属 S17 的 34 行**。→ 「34 行」不变；「35 个槽」作为模板实例数成立。

---

## 5. 判定

**6 行抽样：6 PASS / 0 FAIL。** 每行的 ①②③④ 都有我方独立反汇编地址支撑，③ 的成立通道是 **③b②**，不是被审方声称的 ③b④。

`sample.tsv` 同此结论（`ring3b2=yes`、`ring3b4=no`、`verdict=PASS`）。

全部断言可用 `work/s14_assert.py` 一把复跑（35 槽 / 34 行逐地址，输出见 `EVIDENCE\assert.txt`，当前 `result: ALL OK`）。
