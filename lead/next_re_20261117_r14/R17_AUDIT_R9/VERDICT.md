# R17-AUDIT-R9 · 异族审计结论

目标: ra2youli/gamemd.exe | 4,825,360 B | SHA-256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476 (独立复核一致)
独立实现: audit.py (未 import/复用执行方 work.py)。只读打开 exe；无进程/无调试；产物仅写本目录。
扫描声明: .text 逐字节扫描 4,063,232 B (0x401000 起 rsize 0x3E0000, VA 上界 0x7E038D/vsize)；.rdata 200,704 B；.data 442,368 B。全部中间结果已落盘 raw_results.json / hostcheck*.json / sanity*.py。

## B1 · 零取用者（12 个候选地址） — AGREE
12 个候选 (0x7E3FDC/0x7E3FE0/0x7E3FE4/0x7E3FE8/0x7E4050/0x7E4054/0x7E4058/0x7E405C/0x7E4060/0x7E4064/0x7E4068 + 审计员补 0x7E406C) 在 .text 的 4 字节小端立即数命中数**各自为 0**。正控: push/mov 立即数 0x5A9940(54)、0x77D710(56)、0x6A00A8(126) 全命中；E8 位移反算 0x47C620 = 10 处，与卡面期望一致。反控: 4 种对齐偏移、起始/末尾注入、末 4 字节、截断 3 字节、文件边界全部通过，扫描器未坏。注意: 执行方 REPORT 声称"12 个"但只列 11 个，12th 由审计员补 0x7E406C，结论不变。

## B2 · 极大连续段界 — DISAGREE
独立复算（取值落在 .text 0x401000..0x7E038D）: **极大串 = [0x7E3EBC, 0x7E43C4) = 322 槽**；左邻 0x7E3EB8=0x7FC360、右邻 0x7E43C4=0x7FC298 均非 .text 值。放宽到任意 image 指针: [0x7E3E88, 0x7E4404) = 351 槽（左延 1 槽 0x818CE8 为 .data 指针，右界不变）。
- 对 R8 说法 [0x7E3EBC,0x7E43C4) 的判定: **R8 对** —— 与独立 .text 指针域极大串逐字节一致（322 槽，两端邻值非 .text）。
- 对 R9 说法 [0x7E3E8C,0x7E4403] 的判定: **R9 错** —— 那是 image 指针域的串被误标为 .text-only，左端早 12 槽、右端晚 16 槽（共多 28 槽），串内含 0x7FC2B0/0x7FC360/0x7FC298 等非 .text 值；其 #85/#119 槽号亦应改为 #73/#107。

## B3 · ctor 装表假设 / 间接寻址 — DISAGREE（发现取用者）
执行方" .text 内不存在任何 0x7E3E8C..0x7E4403 立即数 ⇒ ctor 装表被否"**不成立**。锚点对齐反汇编（从 C3/C2/90|CC 填充之后起步，未从任意地址线性起步）得到 12 处真立即数写入，均为 `mov dword ptr [esi/ebp+off], imm32` 的 ctor 装表形态；目标槽 0x7E3E90 / 0x7E3E98 / 0x7E3EA0 / 0x7E3EBC 的内容分别是 0x410590/0x410580/0x4105E0/0x410260，全是 .text 函数指针，不是执行方所谓的"字符串/常量地址"。取用者清单（地址 / 所属函数 host / fn_end / 位置断言 host <= site < fn_end）:
| site | 指令 | host | fn_end | 断言 |
|---|---|---|---|---|
| 0x43B721 | mov [esi],0x7E3EBC | 0x43B680 | 0x43B740 | 0x43B680 <= 0x43B721 < 0x43B740 ✔ |
| 0x43B736 | mov [esi+0xC],0x7E3E90 | 0x43B680 | 0x43B740 | ✔ |
| 0x43B9FC | mov [esi],0x7E3EBC | 0x43B740 | 0x43BCDE | 0x43B740 <= 0x43B9FC < 0x43BCDE ✔ |
| 0x43BA11 | mov [esi+0xC],0x7E3E90 | 0x43B740 | 0x43BCDE | ✔ |
| 0x43BCFF | mov [esi],0x7E3EBC | 0x43BCF0 | 0x43C0CA | 0x43BCF0 <= 0x43BCFF < 0x43C0CA ✔ |
| 0x43BD16 | mov [esi+0xC],0x7E3E90 | 0x43BCF0 | 0x43C0CA | ✔ |
（同三函数内另有 0x43B728/0x43B72F、0x43BA03/0x43BA0A、0x43BD08/0x43BD0F 写 0x7E3EA0/0x7E3E98，host/fn_end 同上。）
间接寻址复核: 扫描所有 `lea reg,[idx*scale+disp32]` (scale 1/2/4/8) 共 10 处 disp 落在宽口径带，disp 为 0x7E7B28 / 0x7F2A40，用非负索引均**无法**触达 [0x7E3EBC,0x7E4404)；.data 中指向该段的全局 0x874D40/0x874D44 在全部 5 节的取用数均为 0，故 mov reg,[global] + offset 路径未发现。取用者来自立即数写槽本身。

## B4 · RTTI/类名"未取得"诚实性 — AGREE
独立复核: 全 .rdata 200,704 B 内 `.?[A-Z]` 装饰名命中 **0**，`??_7` 命中 0；0x7E2E8C..0x7E5403 邻近窗内装饰名 0、点开头字符串 0。pTD 形态抽查: 0x7E3E88→0x818CE8 处为 ASCII "Structure..." 字符串（d0=0x75727453），0x7E3E8C/0x7E3E94/0x7E3E9C/0x7E3EB8 指向 0x7FCxxx（d0=d1=0, d2=0/0x8/0xC），均不符合 type_info 的 [vfptr|name|...] 形态。"未取得"诚实。旁注（不改变判定）: 全文件在 .text 内有 989 个 `.?AV...@@` 装饰名（如文件偏移 0x415DE8 = `.?AVFileClass@@`），但不在 .rdata，执行方关于 .rdata 的陈述成立。

## 必改项（4 条）
1. B2: 把 text-only 极大串从 [0x7E3E8C,0x7E4403]/350 槽改为 [0x7E3EBC,0x7E43C4)/322 槽；槽号 #85/#119 改为 #73/#107；明确 R8 对、R9 错。
2. B3: 撤回" .text 内不存在任何 0x7E3E8C..0x7E4403 立即数、ctor 装表被否"的结论，改为"存在 12 处立即数装表写"。
3. B3: 将 0x7E3E90/0x7E3E98/0x7E3EA0/0x7E3EBC 从"字符串/常量地址"更正为函数指针槽（内容均 .text），并按上表登记 6 条取用者与 host<=site<fn_end 断言。
4. B1: "12 个候选"与枚举 11 个不一致，补齐第 12 个（如 0x7E406C）或改口径为 11；零命中结果不变。
