# VERIFY_GLM — 独立二进制复核记录

- 被复核件：`CRASH_ADDR_ANALYSIS.md`（同目录，2026-10-20）
- 二进制：`D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`（**只读**，全程 `rb` 打开，从未写入、从未执行）
- 复核员工具：自写探针 `verify_glm_probe.py`（本目录），Python 3.12.10 + capstone 5.0.7（`CS_ARCH_X86/CS_MODE_32`，`detail=True`，`skipdata=True`）
- 实际执行命令（均在本 ask 内运行）：
  - `PYTHONDONTWRITEBYTECODE=1 python verify_glm_probe.py pe`
  - `PYTHONDONTWRITEBYTECODE=1 python verify_glm_probe.py bytes`
  - `PYTHONDONTWRITEBYTECODE=1 python verify_glm_probe.py disasm`
  - `PYTHONDONTWRITEBYTECODE=1 python verify_glm_probe.py scan`
  - `PYTHONDONTWRITEBYTECODE=1 python verify_glm_probe.py hash`
- 方法独立性声明：未复用被复核报告的任何数字；PE 段表用裸 struct 自解析（非 pefile），反汇编/扫描用 capstone 重跑，字节与浮点用 struct 重读。被复核报告引用的 `addr_probe.py` 我未重跑——本记录所有数字来自我自己的探针输出。

---

## 1. 我自己重算的关键数字

### 1.1 PE 头与段表（stage pe，裸 struct 解析）

| 字段 | 实测 | 与报告一致? |
|---|---|---|
| file size | 4,825,360 B | ✓ |
| e_lfanew / machine / nsec / COFF char | 0x00000050 / 0x014C / 5 / 0x0000032F | ✓ |
| Magic / ImageBase / SecAlign / FileAlign | 0x010B / 0x00400000 / 0x1000 / 0x1000 | ✓ |
| SizeOfImage / EP / Subsystem / DllCharacteristics | 0x00796000 / 0x007CD80F / 2 / **0x00000020**（NX_COMPAT 0x0100 未置位） | ✓ |

| # | 段 | VA 范围（实测） | VirtSize | RawPtr | RawSize | Char | delta | perm |
|---|---|---|---|---|---|---|---|---|
| 0 | .text | 0x00401000–0x007E038D | 0x003DF38D | 0x00001000 | 0x003E0000 | 0x60000020 | 0x00400000 | R-X |
| 1 | .rdata | 0x007E1000–0x00811074 | 0x00030074 | 0x003E1000 | 0x00031000 | 0x40000040 | 0x00400000 | R-- |
| 2 | .data | **0x00812000–0x00B79BE4** | 0x00367BE4 | 0x00412000 | 0x0006C000 | **0xC0000040** | 0x00400000 | **RW-** |
| 3 | .rsrc | 0x00B7A000–0x00B92128 | 0x00018128 | 0x0047E000 | 0x00019000 | 0x40000040 | 0x006FC000 | R-- |
| 4 | .detour | 0x00B93000–0x00B95718 | 0x00002718 | 0x00497000 | 0x00003000 | 0xC0000040 | 0x006FC000 | RW- |

0x0084F2BA 归属实算：段 .data；段内偏移 0x0003D2BA；文件偏移 = 0x0084F2BA − 0x00400000 = **0x0044F2BA**（delta 按本段实算）；mod 4 = **2**、mod 8 = 2；页 = **0x0084F000**（页内 0x000002BA）；0xC0000040 = CNT_INITIALIZED_DATA|MEM_READ|**MEM_WRITE**，MEM_EXEC(0x20000000) 清除；文件后备范围 [0x00812000, **0x0087E000**)，页在内 ✓。

DEP 注意点（与报告 §1 相同的nuance）：段特征层 .data = 可写无执行位；但 DllCharacteristics 0x20 → NX_COMPAT 清除，默认 OptIn 策略下整镜像（含 .data）映射为**可执行**，仅 AlwaysOn 机器策略下 .data 才是 NX。被复核报告正文已如实标注该依赖；任务摘要里扁平的"PAGE_READWRITE(可写不可执行)"只在段特征/AlwaysOn 意义下成立——不算虚报，但读者须知条件。

### 1.2 哈希（stage hash）

- 主件 sha256 = `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`，4,825,360 B
- 交叉副本 `...\lead\qc161_u0400_trip\_src_L1_sf8_20261020\gamemd.exe` sha256 **全等**，4,825,360 B ✓

### 1.3 字节与表语义（stage bytes）

0x0044F2BA 起 32 字节实测：`DD 3D C3 9C DE 3D 7D 2C E0 3D 2E BC E1 3D D6 4B E3 3D 75 DB E4 3D 0C 6B E6 3D 99 FA E7 3D 1E 8A` —— 与报告逐字节相等 ✓。uint32@0x0084F2BA = **0x9CC33DDD**，按 float32 读 = −1.29e−21 ≈ −0.0 ✓。

对齐槽实测（float32，LE）：

| VA | 槽 | 值 | uint32 |
|---|---|---|---|
| 0x0084F2B0 | 139 | 0.1064098 | 0x3DD9ED64 |
| 0x0084F2B4 | 140 | 0.1071724 | 0x3DDB7D37 |
| **0x0084F2B8** | **141** | **0.1079350** | 0x3DDD0D01 |
| 0x0084F2BC | 142 | 0.1086974 | **0x3DDE9CC3** |
| 0x0084F2C0 | 143 | 0.1094599 | 0x3DE02C7D |

（彩蛋：fnstsw 的伪 disp32 **0x3DDE9CC3 恰为表槽 142 的 float32 位型**——伪位移就是表字节本身，佐证解码忠实。报告未提此点，为正向佐证。）

表常数实测：qword 0x007E8988 = **0.0007669904** = 2π/8192 ✓；dword 0x008223B0 = **2607.5944824219** = float32(8192/π) ✓；qword 0x007E8970 = **651.8986469044** = 2048/π（精确）✓。

**表的真实函数（本复核的关键修正）**：全域 10241 槽与 **sin(k·2π/8192)** 逐点吻合，与线性 ramp 不符：

| k | 表值 t[k] | sin(k·2π/8192) | 线性 k·c |
|---|---|---|---|
| 1 | 0.0007670 | 0.0007670 | 0.0007670 |
| 1024 | **0.7071068** | 0.7071068 | 0.7853982 |
| 2048 | **1.0000000** | 1.0000000 | 1.5707963 |
| 4096 | **0.0000000** | 0.0000000 | 3.1415927 |
| 6144 | **−1.0000000** | −1.0000000 | 4.7123890 |
| 8192 | −0.0000000 | −0.0000000 | 6.2831853 |
| 8193 | +0.0007670 | +0.0007670 | 6.2839523 |
| 10240 | **1.0000000** | 1.0000000（=sin 2.5π） | 7.8539816 |

相邻槽差：t141−t140 = **0.0007625371**、t142−t141 = 0.0007624775，均 ≠ 2π/8192 = 0.0007669904（是 c·cos(相位)，一阶近似 c）。报告 dump 出的 0.1071724/0.1079350 本身就只与 sin 吻合、与 ramp 不符（ramp 在槽 141 应为 0.1081456）。

### 1.4 生成循环真身（stage disasm，0x004CB0E0）

```
0x004CB0E0  push ecx / push esi
0x004CB0E2  mov dword ptr [esp + 4], 0        ; k = 0
0x004CB0EA  mov esi, 0x84f084                 ; 候选写点2 ✓ (be84f08400)
0x004CB0EF  fild dword ptr [esp + 4]          ; 候选写点4 ✓
0x004CB0F3  fmul qword ptr [0x7e8988]         ; ×2π/8192
0x004CB0F9  fmul dword ptr [0x8223b0]         ; ×8192/π  → st0 ≈ 2k（偏差<0.0008）
0x004CB0FF  call 0x7c5f00                     ; FPU 控制字 fistp 取整助手（本体无乘法）
0x004CB104-0x004CB12E  cdq/sub/sar eax,1 → k；and eax,0x80001fff；±0x2000 折叠；cl 奇偶修正（2k 恒偶，实际不触发）
0x004CB12F  fld dword ptr [eax*4 + 0x84f084]  ; 候选写点3 ✓ —— 读槽 (k mod 8192)
0x004CB13A  add esi, 4
0x004CB13D  fstp dword ptr [esi - 4]          ; 候选写点1 ✓ —— 写槽 k
0x004CB141  cmp esi, 0x859088
0x004CB147  mov dword ptr [esp + 4], edx
0x004CB14B  jne 0x4cb0ef                      ; 循环体范围 0x004CB0EF–0x004CB14B ✓
```

即：**索引 = k mod 8192**。k<8192 时读槽 k 写槽 k（恒等重写，造不出正弦值）；k≥8192 时把槽 k−8192 复制到槽 k（尾部 8192..10240 = 0..2048 的周期复制，服务消费端 +0x2000/+0x2800 负角折叠，非"饱和于 1.0"）。写覆盖 [0x0084F084, 0x00859084] 步 4，恒 0 mod 4。消费端 fld 出口实测 7 处：0x004CACEA、0x004CAD41、0x004CB12F、0x004CB193、0x004CB1EA（基址 +0x84F084）与 0x004CB189、0x004CB1E0（+0x84F088）；`and eax, 0x80001fff` 共 5 处（0x004CACC9/0x004CAD19/0x004CB10E/0x004CB169/0x004CB1B9）。取整助手 0x007C5F00 反汇编 = `fnstcw/cmp [0x822D80]/fldcw/fistp qword`，无乘法；×(8192/π) 在调用方 0x004CB0F9。

### 1.5 0x0054A56E 例程（stage disasm）

0x0054A4FA `mov esi, ecx`（provenance 根）→ 0x0054A506 `mov byte [esi+0xc],0` → 0x0054A50E `lea eax,[ebp*4]` → 0x0054A515 `push eax` → 0x0054A516 `call 0x7c8e17`（malloc）→ 0x0054A51E `mov edi,eax` → 0x0054A535/0x0054A54B `mov eax/edx,[esi+4]` → 0x0054A551 `mov edx,[edx+eax*4-4]` → 0x0054A555 `mov [edi+eax*4-4],edx` → 0x0054A562 `mov eax,[esi+4]` → 0x0054A565 `push eax` → **0x0054A566 `call 0x7c8b3d`（free 旧块）** → 0x0054A56B `add esp,4` → **0x0054A56E `mov dword ptr [esi+4], 0`**（崩点，写目标 = esi+4）。与报告逐条一致（报告把 lea/push/call 压成一行标注 0x0054A515，实际 lea 在 0x0054A50E、call 在 0x0054A516，内容无误）。

链路：0x007C8B3D `push [esp+4]; call 0x7c93e8` → 0x007C93E8 … 0x007C93F9 `call 0x7cf7bd` → 0x007CF7BD 首两条即 `mov eax,[0xb78b94]` / `mov eax,[0xb78b98]` ✓。malloc 侧 0x007C8E17→0x007C9442→0x007C946E ✓。RC-1 守卫 0x007CFC9B 实测 `mov edx,[ecx+edi*8+4]; mov ecx,[edx]; sub ecx,[ebp-0x10]; mov esi,ecx; sar esi,4; dec esi; cmp esi,0x3f` ✓ 与报告引文一致。`.detour` 头部（VA 0x00B93000）解码为 add 形乱码 ✓。

---

## 2. 独立反向搜索（stage scan，全 .text 1,392,592 条指令、终点 0x007E038D；与报告扫描数完全同数）

| 搜索项 | 实测 | 报告对应断言 |
|---|---|---|
| imm32/disp32 == 0x0084F2BA（.text） | **0** | ✓ 0 次 |
| 窄带 [0x0084F200,0x0084F400] 内任何 imm/disp（含读与写） | **0** | ✓ imm32=0、绝对 disp 写=0 |
| jmp/call 目标落入窄带 | **0** | ✓ |
| 全文件 raw LE dword `BA F2 84 00` | **0** | ✓ |
| **【加扫】全文件任何指入窄带的 raw LE 指针（513 个值逐一匹配）** | **0** | 报告未做此项，结果支持其结论 |
| **【加扫】.detour 4,551 条解码中窄带引用** | **0** | 同上 |
| 表 disp/imm 引用（0x0084F084/0x0084F088/0x00859088） | **恰 9 处**：7×fld 读 + mov esi,0x84F084 + cmp esi,0x859088；**store=0** | ✓ "只被 4 对齐 fld 读" |
| 带 index 的写、disp ∈ [0x0084E000,0x0085A000] | **0** | ✓ 表邻域无带索引写 |
| 全文件 raw 0xFE00FFFF / 0xFEFEFEFE / CD·DD·BA·F1 填充 | **0 / 44 / 0·0·0·0** | ✓（retail 非 debug CRT） |
| 宽带 [0x0084E000,0x00851000] 命中 | 仅 0x0084E000–0x0084E871 全局/字节旗标（写点集中在 0x007C5F46、0x007C5FEx–0x007C60xx、0x007DExxx）与表基址 0x0084F084/088 | ✓ 与报告宽带描述一致 |

**反向搜索结论：未发现被报告遗漏的写点候选。** 我加扫的三项（全文件指入窄带的裸指针、.detour 引用、表邻域带索引写）也全部为 0，报告"无静态写点产出 EA=0x0084F2BA"的裁决以更强口径成立。

---

## 3. 逐条裁决表

| # | 断言（摘自被复核核心断言） | 裁决 | 依据 |
|---|---|---|---|
| 1 | section：0x0084F2BA ∈ .data；段表五元组/Char 0xC0000040/delta 0x00400000/文件偏移 0x0044F2BA/页 0x0084F000/文件后备 | **HOLDS** | §1.1 全部实测吻合 |
| 2 | 页保护=可写、MEM_EXEC 清除；DllCharacteristics 0x20 NX 清除（执行性依赖 DEP 策略） | **HOLDS** | §1.1；报告 §1 已自带该条件说明 |
| 3 | 交叉副本 sha256 全等 73201cc021497c95… | **HOLDS** | §1.2，两文件全 sha256 相等 |
| 4 | bytes_at_addr 32 字节 | **HOLDS** | §1.3 逐字节相等 |
| 5 | 磁盘字节解码 = `fnstsw word ptr [0x3DDE9CC3]`（+jge/loopne/mov esp 序列）；写目标低于 ImageBase | **HOLDS** | capstone 解码逐字一致；0x3DDE9CC3 < 0x00400000；且恰为槽 142 位型 |
| 6 | LUT 结构：基址 0x0084F084/末 0x00859088/10241 槽/消费端 5 处 fld[+0x84F084]/and 0x80001fff | **HOLDS** | §1.4 + 扫描（7 fld、0 store、5 mask） |
| 7 | 常数 2π/8192、8192/π、2048/π 三个值与地址 | **HOLDS** | §1.3 实测 |
| 8 | "等差查表、公差**正好**=2π/8192、head 区=ramp" | **FALSIFIED** | 表值=sin(k·2π/8192)（t[1024]=0.7071068 vs 线性 0.7853982）；t141−t140=0.0007625≠0.0007670；报告自己 dump 的值也只与 sin 吻合 |
| 9 | "远端槽 idx≈8192 后饱和于 1.0" | **FALSIFIED** | t[8192]=−0.0、t[8193]=+0.0007670、t[10240]=1.0=sin(2.5π)：尾部是 0..2048 的周期复制，非饱和 |
| 10 | "8192 分度圆周相位/角度查找表（几何/旋转），非光照衰减/混色权重" | **HOLDS** | 实为正弦相位表，定性更强；消费端为 radians→×(8192/π)→round→sar1→±8192 折叠→查表 |
| 11 | mid-element：%4=2、0x0084F2B8=第141槽=0.107935≈0.108、错位读=0x9CC33DDD≈−0.0 | **HOLDS** | §1.3 实测（0x0084F2BA=槽141 byte[2..3]+槽142 byte[0..1]） |
| 12 | conclusion(1) 静态事实：.data 可写无执行位+NX clear；fnstsw 目标图像外未映射 | **HOLDS** | §1.1/§1.3；"未映射"为合理静态推断（0x3DDE9CC3 远低于映像底） |
| 13 | conclusion(1) 机制选择（取指/DEP vs 写未映射 vs 运行时字节发散） | **INSUFFICIENT** | 无运行时转储可裁决；报告本身以两种并列读法呈现，未越权断言 |
| 14 | conclusion(2)：半槽错位、对齐邻居=0.108、公差≈0.0007 | **HOLDS** | §1.3（0.0007625/0.0007670，一阶≈0.0007 成立） |
| 15 | conclusion(3)：三条写线索全负（窄带 imm/disp/branch=0、全文件 LE=0、表只 4 对齐 fstp 写/fld 读） | **HOLDS** | §2 独立扫描逐项复现，另加三项加扫也为 0 |
| 16 | conclusion(4)/§5：0x0054A56E 前一条确凿=free([esi+4])@0x0054A566，链 0x7C8B3D→0x7C93E8→0x7CF7BD，与 RC-1 守卫 0x7CFC9B 同簇 0x00B78B94/98 | **HOLDS** | §1.5 反汇编逐条证实（注：0x00B78B94 引用实测 16 处/范围 0x007CF6F0–0x007D066E，报告写 7 处/0x7CF7BD–0x7D0398，见 misses） |
| 17 | esi 具体腐化值/毒值是否=0xFE00FFFF | **INSUFFICIENT** | 0xFE00FFFF 文件 0 次、无运行时寄存器/内存证据；报告已如实标注此边界 |
| 18 | same_family_as_rc1 = true（按分配器+机制，非同值；0x0084F2BA 属 .data 执行面、不等同 RC-1 freelist 解引用） | **HOLDS** | §1.5 分配器/守卫/全局簇静态证实；报告的证据边界与我的实测一致 |
| 19 | 候选写点 1：0x004CB13D `fstp dword ptr [esi-4]` [low]；esi 恒 0 mod 4 | **HOLDS** | §1.4：add esi,4@0x004CB13A → fstp[esi−4]@0x004CB13D，覆盖 [0x0084F084,0x00859084] 步 4；×(2π/8192)×(8192/π)=2k 偏差<0.0008，esi 无漂移 |
| 20 | 候选写点 2：0x004CB0EA `mov esi, 0x0084F084` [low]；差 0x236=566 | **HOLDS** | 反汇编 be84f08400；0x0084F2BA−0x0084F084=0x236 ✓；全 .text 该 imm 仅此 1 处 |
| 21 | 候选写点 3：0x004CB12F `fld dword ptr [eax*4 + 0x0084F084]` [low]；恒 4 对齐读 | **HOLDS** | 反汇编吻合；0x0084F084%4=0 ⇒ EA 恒 0 mod 4，且是读非写 |
| 22 | 候选写点 4：0x004CB0EF 循环体 fild/fmul/call，范围 0x004CB0EF–0x004CB14B [low] | **HOLDS** | §1.4 反汇编范围与流水线一致（补充：×(8192/π) 在调用方 0x004CB0F9） |
| 23 | "在文件里就是实数据，不是运行时才生成" | **HOLDS** | 磁盘全域=sin；生成循环索引=k mod 8192（恒等重写+周期复制），造不出正弦值，头部值只能来自文件 |
| 24 | §2 reading-2 "LUT 加载时重算→运行时字节可能发散" | **INSUFFICIENT** | "重算"前提被 §1.4 削弱（循环不产生新值）；.data 仍可被外部堆损坏改写，读法未完全排除 |
| 25 | 反向搜索：报告未漏写点 | **HOLDS** | §2：未发现任何报告未列候选；加扫三项均 0 |

---

## 4. misses（报告的偏差/可修正点）

1. **"等差 ramp / 公差正好 = 2π/8192" 不成立**：表实为 **sin(k·2π/8192) 正弦相位表**（t[1024]=0.7071068=sin(π/4)，线性应为 0.7853982；t141−t140=0.0007625≠0.0007670）。观测 0.108/0.0007 与"8192 分度圆周相位表"结论不受影响，定性反而更强。
2. **"idx≈8192 之后饱和于 1.0" 错**：尾部 8192..10240 是 0..2048 的**周期复制**（t[8192]=−0.0、t[8193]=+0.0007670、t[10240]=1.0=sin(2.5π)），机制是生成循环 `and eax,0x80001fff` 把索引折成 k mod 8192，服务消费端 +0x2000/+0x2800 负角折叠路径；不存在饱和平台。
3. **"LUT 由 0x004CB0E0 生成 / 运行时重算"表述不成立**：该循环读槽 (k mod 8192) 写槽 k——头部恒等重写、尾部周期复制，**造不出正弦值**；磁盘 LUT 是权威且完整的数据。这削弱 §2.2 "recomputed at load" 读法的前提（外部堆损坏改写 .data 仍可能，读法未完全排除）。
4. **0x00B78B94 引用计数/范围**：实测 0x00B78B94 在 .text 有 **16 处**引用（0x00B78B94+0x00B78B98 合计 29 处），范围 **0x007CF6F0–0x007D066E**；报告写"7 处 / 0x7CF7BD–0x7D0398"。同属单一 SBH 簇的结论不变。
5. **"indexed stores to a .data disp: 1,755 total, 1,143 writes" 未按同口径复现**：我的口径（带 index 的写且 disp ∈ .data VA 域）= 207；表邻域 [0x0084E000,0x0085A000] 内带索引写 = 0。承重结论（表内 store=0）一致，仅总量口径存疑。
6. **§3 "the round helper scaled by 8192/π" 措辞不准**：×(8192/π) 在调用方 0x004CB0F9（`fmul dword ptr [0x8223b0]`）；0x007C5F00 本体是 FPU 控制字 fistp 取整助手（fnstcw/cmp [0x822D80]/fldcw/fistp），无乘法。候选写点 4 的流水线描述本身正确。
7. （正向佐证，非缺陷）fnstsw 伪 disp32 **0x3DDE9CC3 恰为表槽 142 的 float32 位型**（0x0084F2BC 的 uint32）——伪位移就是表字节本身，进一步佐证磁盘解码忠实、并解释了该"写目标"为何恰落在映像外。

## 5. 复核结论总评

被复核报告的**核心裁决全部经独立重算成立**：段归属与页属性、32 字节、fnstsw 解码与写目标算术、mid-element/槽 141=0.107935、三条写线索全负（含全文件级搜索）、0x0054A56E 的 free 链与 SBH 同族判定、四个候选写点的指令原文与地址算术。我的全量扫描与报告逐数吻合（1,392,592 条指令、终点 0x007E038D、窄带 0 命中、表 store=0、0xFE00FFFF=0）。需要修正的是三处语义细节（等差→正弦、饱和→周期复制、重算→恒等重写/复制）与两处小误差（SBH 全局引用计数、索引写总量口径）；这些都不动摇报告的结论与证据分级，其中"表在文件里就是实数据"经算法层核实后反而更稳固。
