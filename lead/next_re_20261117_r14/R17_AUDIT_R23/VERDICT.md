D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe  sha256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476  （64 hex 前缀 73201CC0 与卡面一致，尾段 F67476 一致 → 有效；文件 4,825,360 B）

# R17-AUDIT-R23 · 异族审计：独立重解「0x43F180 的调用方」

- 独立实现：本目录 `audit.py`（PE 解析、E8 扫描、线性反汇编、寄存器写点统计、vtable 切分、可达性 BFS 全部自写；未 import、未调用、未阅读式复用执行方 `work.py`——仅在本目录外读取其 `ctor_sites.tsv / dispatch_hits.tsv / REPORT.md` 作为**被审对象**比对）。
- 只读镜像；未创建/启动/调试 gamemd 进程；产物只写本目录；未改 `R17_R23_CALLER_PATH\` 下任何文件。
- 锚点对齐：所有反汇编均为「从字节实测的指令边界起线性解码」，并逐一验证 call/site 落在指令边界上。
- 声明：**.text 扫描 4,060,041 B**（VA 0x401000–0x7E038D，逐字节 E8 rel32 解算）；**反汇编函数 2 个**（host `0x5A6510` 308 条指令；ctor `0x43B740` 至 `0x43BCDE`）+ 全 .text 一次线性解码 4,060,045 B 做 `call [reg+0x124]` 全量计数。
- 时间预算：7 分钟内完成；中间结果见 `_audit_result.json`。

## 结论摘要

| 项 | 结论 |
|---|---|
| A1 构造点计数 14 + 1 = 15 | **AGREE** |
| A2 链条逐指令字节链 | **AGREE**（含 ebp/edx 无覆写，见下） |
| A3 对象 vptr = 0x7E3EBC、slot73 = 0x43F180 | **AGREE** |
| A4 位置断言 `host <= site < fn_end` | **AGREE**，但 **host 报错 29 字节**（应为 0x5A6510，非 0x5A652D） |
| A5 是否存在替代解释 | 存在但**条件更强**，不成立为「反证」 |

**链条本身：字节证实。** 执行方的 host 口径错误（必改项 1），但不影响 link。

---

## A1 · 构造点计数 —— **AGREE**

- 扫描口径：`.text`（VA 0x401000–0x7E038D）逐字节，仅认 `E8 rel32` 且 `dst == site+5+rel32`。
- **`call 0x43B740` = 14 处**：0x44FB22, 0x44FD8A, 0x45E81F, 0x45E89C, 0x473866, 0x590574, 0x5954A1, **0x5A66D4**, 0x5A84B1, 0x5A94FC, 0x5A96F8, 0x5CAB60, 0x6C35D3, 0x7396C3。
- **`call 0x43B680` = 1 处**：0x453ECF。
- 合计 **15**，与执行方 `ctor_sites.tsv` 逐行一致。
- 口径补强：另扫 `E9 rel32` 与 `0F 8x rel32` 到同样两目标，命中 **0** 处（`jmp 0x43B740` 为 0），故「15」不是因口径遗漏而偏低。
- 注意：此为 `E8` 直接调用口径；经 `FF 15 [mem]` / 寄存器间接 call 到达这两个 ctor 的情形不在统计内（执行方同口径，不构成缺陷）。

## A2 · 链条是否成立 —— **AGREE（字节证实）**

全部字节为镜像实测：

| VA | 字节 | 指令 | 语义 |
|---|---|---|---|
| 0x5A66D4 | `E8 67 50 E9 FF` | `call 0x43B740` | rel32 = 0xFFE95067；0x5A66D4+5+rel32 = **0x43B740** ✔ |
| 0x5A66D9 | `8B E8` | `mov ebp, eax` | 紧接 call，EAX = ctor 返回对象 |
| 0x5A684D | `8B 55 00` | `mov edx, [ebp]` | EDX := 对象首 DWORD = vptr |
| 0x5A6860 | `FF 92 24 01 00 00` | `call dword ptr [edx+0x124]` | disp32 = 0x124 = slot 73 |

**关键问题 1：ebp 在 0x5A6860 是否仍是该对象？—— 是。**

函数内 ebp 的全部写点（`reg_writes.tsv`）：

- 0x5A6598 `8B E8`（外层 `mov ebp,eax`）
- 0x5A6640 `8B 6C 24 2C`（外层 `mov ebp,[esp+0x2c]`）
- **0x5A66D9 `8B E8`**（链条起点）
- **0x5A66E6 `33 ED`（`xor ebp,ebp`）**
- 0x5A6901 `5D`（`pop ebp` 尾声）

0x5A66D9 之后、0x5A6860 之前 **只有 0x5A66E6 一处写 ebp**，它必须被正面排除，否则链条断：

- 0x5A66C1 `74 23` `je 0x5A66E6`：EAX==0（分配/calloc 失败）时跳向 ebp=0 分支；
- 0x5A66D9 → 0x5A66DB → 0x5A66DF → **0x5A66E4 `EB 16` `jmp 0x5A66FC`**；
- 0x5A66FC 起的循环体回边为 0x5A68B1 `0F 84 3C FE FF FF` `je 0x5A66F3` 与 0x5A6768 回跳，**无一回跳到 0x5A66E6**。

即：走 0x5A66D9 的路径在 0x5A66E4 处**必然**离开，0x5A66E6 在「0x5A66D9 已执行」的路径上不可达（dead branch）。我另做了正向可达性 BFS：从 0x5A66D9 出发可达 212 条指令（0x5A6640–0x5A6919），**包含 0x5A684D 与 0x5A6860**，且路径上不再经过任何 ebp 写点。→ **ebp 未被覆写。**

**关键问题 2：edx 在 0x5A6860 是否仍等于 [ebp]？—— 是。**

0x5A684D 之后到 0x5A6860 之间只有 5 条指令（`6A 02` / `8B 81 A0 00 00 00` / `8B CD` / `89 45 6C` / `89 45 70`），**edx 无任何写点**（全量统计见 `reg_writes.tsv`）。区间内也没有任何分支目标落入 0x5A684D..0x5A6860 之间（`jcc/call` 目标扫描为 0），故不可从外部跳过 0x5A684D 直接落到 0x5A6860。→ **edx == [ebp]，无覆写。**

**关键问题 3：ebp 是否被「来自栈/全局」的替身替换？—— 在 host 内未发生。** 栈槽 `[esp+0x84]` 只在 0x5A66F3 / 0x5A68B7 读进 EBX，从未写回 EBP；EBP 在该区间内的其他引用均为 `mov ecx,ebp`（this 指针）与 `[ebp+0x520]`、`[ebp+0x6c]`、`[ebp+0x70]` 的成员读写。

**附带**：0x5A6847 `8B 8D 20 05 00 00` `mov ecx,[ebp+0x520]` 与 0x43B740 中 0x43B756 `89 8E 20 05 00 00` `mov [esi+0x520],ecx` 构成同一字段的写-读对，进一步佐证 EBP 就是该 ctor 建出的对象。

**唯一未经字节排除的环节（如实声明）**：0x43B740 是被调用方，我无法在静态层面证明它不向调用者的 EBP 写入（无栈帧逃逸分析）。这一点对整链是一般性假设，不是本链特有缺陷。

## A3 · 对象类型是否真是 BuildingClass —— **AGREE**

- ctor `0x43B740` 入口字节 `8B 44 24 08 53 55 56 57`（`mov eax,[esp+8]; push ebx/ebp/esi/edi`），函数体至 `0x43BCDE`（`C2 08 00` `ret 8`）。
- 函数体内对 `[esi]` 的写点**恰好 1 处**：**0x43B9FA `C7 06 BC 3E 7E 00` = `mov dword ptr [esi], 0x7E3EBC`**。`[esi+*]` 的其他写点均为成员，不覆写 vptr。`esi` 于 0x43B748 `8B F1` 由 `ecx`（this）装入。
- 全 .text 中立即数 `0x007E3EBC` 仅出现 **3 次**，均落在该 ctor 函数体内：**0x43B721 / 0x43B9FC / 0x43BCFF**（0x43B9FC、0x43BCFF 的 `C7 06` 与 `[esi+4]` 组合属构造/析构先后，vptr 写入点仍唯一）。
- 槽值（我自己读，未引用我方结论）：`*(uint32*)(0x7E3EBC + 4*73) = **0x43F180**`；邻槽 slot72 = 0x70ADC0，slot74 = 0x5F4730。
- 该 vtable 连续 `.text` 值共 322 槽（第 322 个槽值 0x7FC298 已不在 `.text`，视为表尾），slot 73 在表内。
- `0x43F180` 在该 vtable 中出现**仅** slot 73（前 322 槽唯一命中），故 `[vptr+0x124]` → `0x43F180` 在链上无歧义。
- 因此 `call [edx+0x124]` 的解析目标为该对象的 **BuildingClass 主 vtable slot #73 = 0x43F180**。

## A4 · 位置断言 —— **AGREE（区间成立），但 host 报错：必改项**

- **字节实测：host = `0x5A6510`，fn_end = `0x5A691C`**，`insn_count = 308`，`host <= 0x5A6860 < fn_end` **成立**。
  证据链：`0x5A64FF` = `C2 04 00`（`ret 4`）→ `0x5A6502–0x5A650F` = 14 × `90`（NOP 填充）→ `0x5A6510` = `83 EC 70`（`sub esp,0x70`）+ `53 8B 5C 24 78 B8 67 66 66 66 55 8B 4B 10 56 F7 E9 C1 FA 02 8B C2 57 C1 E8 1F`（完整标准序言，callee-saved 成对保存）→ 一直到 `0x5A6919 C2 04 00`（`ret 4`），`0x5A691C` 为函数尾。
- **执行方所报 host `0x5A652D` 不是函数入口**：0x5A652D 的字节 `03 D0` 实为 `0x5A652A C1 E8 1F`（`shr eax,0x1f`）**指令的第 4/5 字节**，被截断解成 `add edx,eax`。即 `0x5A652D` 落在指令内部，其「fn_end 0x5A691C」虽然恰好正确，但「host」是伪边界。
- 该错误**不影响** `0x5A652D <= 0x5A6860 < 0x5A691C` 的真值，也不影响链条；但作为会被长期引用的地址，必须改为 `0x5A6510`。
- 另核：执行方 15 行 `ctor_sites.tsv` 中的 host/fn_end，我用「从 host 线性解码至首条 ret 的 end」独立复核，5 个代表 host（0x44F820 / 0x45E880 / 0x453E20 / 0x5A82E0 / 0x7393F2）的 fn_end **全部精确复现**。

## A5 · 替代解释 —— **存在候选，但均需更强条件，不推翻本链**

- 全 .text 内 `call dword ptr [reg+0x124]` 共 **28 处**（0x4154ED…0x467FA9），其中落在 host `0x5A6510–0x5A691C` 内的只有 **0x5A6860** 一处。
- 28 处中 `base = edx` 的若干、`base = eax` 的若干；**替代解释的形态**是：`[edx+0x124]` 是「任意具有同布局的对象派发」，EDX 指向的 vptr 可能**不是 0x7E3EBC**。若如此，槽值 `0x43F180` 是按该 vptr 的 slot 73 取的，不同 vtable 的 slot 73 可以指向不同函数——本链的落点只是**其中一个可能值**。
- 需要什么条件才成立：
  1. ctor `0x43B740` 返回的对象的 `[obj+0]` 在 0x5A684D 之前被改写成别的 vtable；**已排除**——host 内 vptr 写入点只有 0x43B9FA 一处（且在被调方）；host 内对 `[ebp+0]` 没有任何写点（全量统计：只有 `[ebp+0x6c]`、`[ebp+0x70]` 两个成员写）。
  2. 由别的 ctor 产出同型对象、但 vptr 不是 0x7E3EBC。**当前可查范围内成立的其它 vptr 写入源**：`.text` 内立即数 0x7E3EBC 只有上述 3 处（全在该 ctor 内），`.rdata/.data` 中作为 dword 指向 0x7E3EBC 的引用 **0 处**；`0x43B740` 本身**不在** `0x7E3EBC` 的 vtable 槽内（该 vtable 无构造函数槽），也不在 slot 73。
  3. host 参数化：host 通过 `[esp+0x2c]` / `[esp+0x30]` / `[esp+0x84]`（EBX）等**外部入参**参与循环边界与选择；EBP 对象仍是本函数自建（0x5A66D4 → EAX），**不是**外部传入的 this。所以「被别的对象派发」只能在上面 1/2 条件成立时发生。
- 更支持「BuildingClass 对象派发」的证据：(a) EBP 由 ctor 返回值直接装入、无中间转手；(b) 0x43B740 唯一写 `[this]=0x7E3EBC`；(c) 同一对象在 0x5A683D 已用 `call [edx+0xD8]`（slot 54，槽值 0x440580）派发过，与 slot 73 同源同对象；(d) `[ebp+0x520]` 的写-读对与 ctor 对应。
- 但必须同时写明：上面 (1)(2) 的排除是**当前静态可见范围内**的；不经由 `0x43B740/0x43B680` 的构造路径（例如 0x453E20 这类派生构造、或把对象 vptr 按成员拷贝方式设置）不在本次静态排除中。**A5 不构成反证，但也不允许把「唯一调用方」写进答案。**

## 可直接引用的链（字节证实）

> `0x5A66D4` `E8 67 50 E9 FF` = `call 0x43B740`（BuildingClass ctor A；该 ctor 在 `0x43B9FA` `C7 06 BC 3E 7E 00` 写 vptr `0x7E3EBC`）
> → `0x5A66D9` `8B E8` = `mov ebp, eax`（EBP = 该对象；此后至 `0x5A6860` 无 ebp 写点在路径上）
> → `0x5A684D` `8B 55 00` = `mov edx, [ebp]`（EDX = 对象 vptr；此后至 `0x5A6860` 无 edx 写点）
> → **`0x5A6860` `FF 92 24 01 00 00` = `call dword ptr [edx+0x124]`**
> → slot 73 of `0x7E3EBC` = `0x43F180`
> 位置：host `0x5A6510` <= site `0x5A6860` < fn_end `0x5A691C`。

## 必改项（3 条）

1. **【必改】host 地址错**：`REPORT.md` 与 `ctor_sites.tsv` 均写 host `0x5A652D`；字节实测函数入口为 **`0x5A6510`**（`0x5A64FF ret 4` + 14×NOP + `0x5A6510 sub esp,0x70` 序言）。`0x5A652D` 落在 `0x5A652A C1 E8 1F` 指令内部。所有引用该 host 的下游文本须同步改。
2. **【必改】必须写明覆盖边界与不可外推**：本链只能证明「**存在至少一个** 动态派发点会到达 `0x43F180`」，不能证明「唯一调用方」，不能证明运行期真执行；且不改变 ②-b 的 `[静态推断]` 收口（D-53(A)）——那收的是**行为层可区分性**，本处是**指令层调用关系**，层级不同，不得作为行为证据升级。
3. **【必改】`dispatch_hits.tsv` 的 `same_object=YES` 无逐指令依据**：该列对 `0x5A6860` 只写了结论，未列出 ebp 写点全表与 `0x5A66E4 jmp` 的死分支论证——而这正是链条最容易断的地方。应把 `reg_writes.tsv` 的 6 个 ebp 写点 + 0x5A66E6 不可达论证显式写进产物，否则该 YES 不可复现。

## 复跑

`python R17_AUDIT_R23\audit.py`（只读 gamemd.exe；输出 `_audit_result.json` 及本目录 TSV）。
