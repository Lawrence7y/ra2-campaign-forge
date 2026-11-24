# W8-F8 独立复核 · 可见对象数 / 裁剪通过数（复核员 F8-review）

> 被复核件：`F8_VISIBILITY.md`（UNLOCATED，vasLocated=[]）+ `_w8_f8.py` + `_w8_f8_out.txt`（1051 行）
> 复核方法：**不导入 ra2tool.Engine**，手写 PE 解析 + capstone 5.0.7 独立线性解码 .text（1,394,120 条，resync 66，
> 与 ra2tool 逐条同数），另做 F8 没做的全文件 E8/E9 扫描、48 条深窗 + jcc 分支目标反例猎杀、
> 全 .text 绝对计数普查、xadd / 两步虚调度 / 立即数形态普查。
> 本轮实跑：`python -I -X utf8 _f8rev_probe.py > _f8rev_out.txt`（exit 0，903 行）+ 三段针对性验尸脚本
> （`_f8rev_autopsy.txt` 3105 行）。零真机、只读 gamemd.exe、写域仅 `reviews/`。

## 0. 总判：**PARTIAL**（UNLOCATED 判定本身成立且经独立重跑确认；报告有 1 处事实错误 + 1 处判据过窄，见 §4 mustFix）

---

## 1. SHA256 绑定：**成立** ✅

- 报告头部（`F8_VISIBILITY.md:3-8`）含自述 SHA256 `73201cc0…67476`、字节数 4,825,360、COVERAGE、IMAGEBASE、回件时刻。
- **我自己实算**：`_f8rev_out.txt:3-4` `R0 SHA256 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` / `R0 BYTES 4825360`，与报告、TASK.md §0、探针 S0（`_w8_f8_out.txt:4-5`）三方同值。
- 回件时刻 `2026-11-06 01:44:54` 与探针输出 `RUN_TIMESTAMP`（`_w8_f8_out.txt:2`）一致。

## 2. 独立重跑（全部我本轮实跑，非转抄）

| # | 复核点 | F8 值 | 我实测（`_f8rev_out.txt` 行） | 判 |
|---|---|---|---|---|
| 1 | `call 0x5F4B10` 直接调用 | 3 {0x422C8E,0x73B132,0x749B5B} | R2:18-22 = 3 同集合；R2 独立线性扫与裸 E8 双证；**R1 全文件（含 .detour/.rsrc/.data）= 同 3 处**（:12-13） | ✅ |
| 2 | `jmp 0x5F4B10` 尾调用 | 0 | R2:19 = 0 | ✅ |
| 3 | `call 0x6D2140` = 139 | 139 | R2:20-22 = 139，首尾 0x4146C6/0x762A5D 同；**R1 全文件 E8 = 同 139**（:14） | ✅ |
| 4 | 渲染簇 [0x6D8DB0,0x6DA1FC) | 1603 条 / 0 调用 / 0 全局写 / 19 处 inc-dec 全寄存器 / 0 内存计数 | R3:25-49 全部同数同集合；额外查**任意形态内存写** 173 处中非栈 33 处（:50-83），全为 `[esi+0x99]`/`[esi+0x80]` 布尔、`[eax*4+0xB0CEC8]` 脏矩形数组、`[reg+0xd90..db0]` Tactical 字段——无一计数 | ✅ |
| 5 | 宽域 [0x6D3D10,0x6DA200) | 7933 条 / 21 处内存增减全 STACK | R4:86-108 = 7933 / 21 / CLASS_DIST {STACK:21}，逐条同 VA | ✅ |
| 6 | vtable 槽 65 归属 | 0x7E3354/0x7F5C70/0x7F6318 | R8:237-239 直接读槽字节 u32[0x7E3458]=0x422C70、u32[0x7F5D74]=0x73B0B0、u32[0x7F641C]=0x749B20 全 match；R8:240 = .rdata 引用 16 处同 F8 S9 | ✅ |
| 7 | 0xB0CE30/34 写点 | 各 2 处（0x6D1A4C/0x6D1A51、0x6D5F7E/0x6D5F87） | R9:355-384 各 14 处访存、写者恰为同 4 VA | ✅ |
| 8 | IsVisible 边界常量 | ±360 / ±180 闭区间 | R10:877-898：`cmp 0xFFFFFE98`(-360) / `add 0x168`(+360) / `cmp 0xFFFFFF4C`(-180) / `add 0xB4`(+180) / `setle`，原字节逐条同 | ✅ |
| 9 | 视口字段 | `[P+0xB0]/[P+0xB4]` @0x6D2202/0x6D2208 | R10:867-868 同；`[0x887324]` Tactical 指针 461 处访存同数（R9:385 vs `_w8_f8_out.txt:729`） | ✅ |
| 10 | S9/S10 坐标链 | Unit=this+0x9C(0x5F65A0)、Anim=this+0xCC 转发(0x422BE0)、GetCoords=0x41BE00 | `_w8_f8_out.txt:1021-1050` 原字节核过；0x5F65A4 `add ecx,0x9C`、0x422BE7 读 `[edi+0xCC]`、0x41BE0B `call [eax+0x48]` 属实 | ✅ |

**F8 没做、我补做的排除项（全部支持其否定结论）**：
- **全文件 E8/E9 扫描**（R1）：`.detour`（0xB93000，0x2718 B，段特征 0xC0000040 **非可执行**，R0:10）、.rsrc、.data 内 **0 命中**——F8 探针只扫 .text（`_w8_f8.py:144` `raw[eng.TB:eng.TB+eng.TSZ]`；ra2tool.py:68-69,92-96 同），「全镜像」措辞事实上成立但探针自身范围应如实标注；
- **全 .text 绝对内存 inc/dec/add/sub 普查**（R6:146-228）：82 处（其中约半为线性解码碎片伪影），真实计数器全部落在逻辑/音频/系统域（0x87E28C、0xA8E7AC、0xB78xxx 等），**无一在 0xB0Cxxx–0xB0CExx 可见性域或层容器区**；
- **xadd** 全 .text = 0（R6:229）；**立即数 dword 0x6D2140** = 0 处（R6:231，无寄存器间接调用 IsVisible 的形态）；dword 0x5F4B10 = 16 处全在 .rdata vtable 槽（R6:230）；
- **两步虚调度** `mov r,[r+0x104]` 后 8 条内 `call/jmp reg` = 0/113（R7:233-234）。

## 3. 反例猎杀结果（对 UNLOCATED 的攻击全部被击退，但击退过程暴露 F8 两处缺陷）

### 3.1 IsVisible 139 点「8 条窗口」之外**真有**内存计数——验尸后全部为逐对象字段，非聚合

F8 判据（`F8_VISIBILITY.md:71-72`）是「每个调用点向后线性解 8 条指令」。我把窗口扩到 **48 条 + 每个 jcc 分支目标 16 条**（R5:110-142：139 点、306 个 jcc、4896 条目标指令），抓到 5 处旗标，逐一验尸（`_f8rev_autopsy.txt`）：

| 旗标 | 验尸结论 |
|---|---|
| `0x4C27AA/0x4C27BE` 前向 → **`0x4C281A inc dword ptr [esi+0x1c]`** | 所在函数 0x4C2790（ret@0x4C282A），esi=this；同函数 0x4C2823 每调用把 `[esi+0x28]` 折半（衰减计时器形态）。**逐对象字段，非聚合** |
| `0x4C28CE/0x4C28E2` 前向 → **`0x4C293D inc dword ptr [esi+0x1c]`** | 同型姊妹函数（`je 0x4c293d` 跳过、可见路径经 call 0x4C1F20 后 +1），esi=this。**逐对象字段** |
| `0x53CED5` 的 jcc → `0x53D2D3` → **`0x53D302 inc dword ptr [ebx+0xc]`** | 该 inc 在函数尾部、两个 `cmp 4` 循环（[esp+0x5C]/[esp+0x28]，0x53D2E2-EA / 0x53D2F4-FC）都退出后**每次调用恰 +1**，随后 epilogue ret。**每次调用一个的逐对象计数，非 IsVisible 结果聚合** |
| `0x5FF88B` 的 jcc → `0x5FFF77` | 0x5FFF77 实为**函数出口**（pop×4/add esp/ret，`_f8rev_autopsy.txt:2304-2311`）；我 R5 的 `add [ecx-6],al` 等旗标是盲解越过 ret 落进热补丁填充字节（`8bff f8f9 5f…`+nops）的**解码伪影**。反例不成立 |
| 0x6D7xxx 各 STACK 旗标 | 即 F8 S7 的栈上矩形坐标，同集合 |

**结论**：UNLOCATED 不被推翻——不存在「对 IsVisible 通过数累加」的聚合计数器；但 F8 报告 §0「139 处 IsVisible 调用零计数」、§1.3 标题「均不计数」作为**无限定语的全称命题**，其 8 条窗口不足以支撑，须改写（见 mustFix-2）。

### 3.2 0xB0CE88 的排除陈述**有事实错误**（但语义结论侥幸仍对）

- F8 报告 §3 表 / §4 行6：「27 处访存（W@0x6D1A91/0x6D2995/0x6D2AA1/0x6D2CA1），**全部落在 Tactical 脏矩形管理域 0x6D1Axx–0x6D31xx**」。
- **我全量列表（R9:327-354，27 条不截断）**：访存实际横跨 **0x6D1A91..0x6DA9B5**，写者 **6 个**而非 4 个——除 F8 所列 4 个外还有 **0x6D451C(写)**、**0x6DA993(写)**；另有 0x6D33C1/0x6D35AD/0x6D378E/0x6D3850/0x6D3988/0x6D3BD8/0x6D3DF0/0x6D44FC/0x6D453C/0x6DA980/0x6DA9B5 共 11 处读在 0x6D31xx 之外。
- **根因**：`_w8_f8.py:359` `for t in h[:14]` —— DISP_HITS 只打印前 14 条，F8 把截断列表当了全集（count=27 有打印但没列表）。0xB0CE30/34 恰好 14 条未受损，0x887324（461 条）同被截断但报告未据其作域界断言。
- **验尸**（本轮第三段脚本）：0x6D451C 上下文 = 读 Count→`dec ecx`→写回的**条目移除**循环（前邻 call 0x6D3870/0x6D3040）；0x6DA993 同为读→dec→写回移除。**语义仍属脏矩形管理，且 27 条中确无一条落在渲染簇 [0x6D8DB0,0x6DA1FC) 内**——「与渲染簇零交集」这一承重结论为真，但支撑它的域界陈述为假。

### 3.3 我自己被推翻的怀疑（记录在案，防复核员自身确证偏误）

初看 0x6D8F2B `mov ecx,[ebx+0x8A0370]` 以为层容器是 `[0x886FA8]+disp` 两级寻址、F8 写绝对 VA 有错。对齐解码（`_w8_f8_out.txt:378-385` 与 0x4AA2D1 上下文）显示 ebx 在 0x6D8F19-24 被 `lea ebx,[eax+eax*2]; shl ebx,3` 重赋值为 **0x18·层号**——有效地址就是绝对 0x8A0370+0x18·L。**F8 的绝对 VA 写法正确**，怀疑撤销。同理 R6 里大量 `add byte ptr [imm]` 为线性解码碎片，非真实计数器。

## 4. mustFix（不修不入账）

1. **改正 0xB0CE88 的域界与写者数**（F8_VISIBILITY.md §3 表、§4 行6）：改为「27 处访存横跨 0x6D1A91–0x6DA9B5、写者 6 个（+0x6D451C、0x6DA993）；越界两处经复核为脏矩形条目移除的 dec-写回（`reviews/_f8rev_autopsy.txt`），语义仍属脏矩形管理，渲染簇 [0x6D8DB0,0x6DA1FC) 内确为零交集」。并修 `_w8_f8.py` 的 `h[:14]` 截断（或注明列表截断至 14）。
2. **收窄「139 处均不计数」的措辞**（§0、§1.3、headline）：明确为「调用点后 8 条指令窗口内零内存计数（实测判据）；复核员 48 条+jcc 分支目标深窗另见 5 处逐对象字段计数（`[esi+0x1c]`×4 站点、`[ebx+0xc]`×1，均非聚合），不构成现成可见计数 VA」。
3. （微）§1.3 引用标签 `S3 NEXT_INSN1_DIST` 应为 `S3 NEXT_INSN_DIST`（`_w8_f8_out.txt:54`，数值本身一致）。
4. （微）「全镜像」措辞：注明探针 E8/E9 与 stream 扫描实际范围为 .text；复核员全文件扫描（含非可执行的 .detour）已补证无额外命中。

## 5. 复核员账

- 本轮亲跑：`_f8rev_probe.py`（独立 PE 解析 + capstone 5.0.7 线性扫，21.6 s 解码 + 全文件 E8 扫描，exit 0）、两段验尸脚本、`grep/sed` 取证；全部输出在 `reviews/_f8rev_out.txt`（903 行）与 `reviews/_f8rev_autopsy.txt`。
- 未做/不可静态做：真机观测（铁律禁止）；0xB0CE88 与可见数的定量关系（D-19 已判未校准，本轮不改判）；F8 §6 已如实自报的 7 项未验（类名 RTTI 全链、FPU 常量数值等）本轮亦未展开——均不承载 UNLOCATED 判定。
- 写域合规：本轮仅写 `reviews/_f8rev_probe.py`、`reviews/_f8rev_out.txt`、`reviews/_f8rev_autopsy.txt`、本文件；被复核件与其它目录零改动。
