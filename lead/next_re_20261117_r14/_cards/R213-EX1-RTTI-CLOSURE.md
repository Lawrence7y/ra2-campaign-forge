# R213 EX1 — RTTI 闭环 1214 / 954 / 260 独立复算（role=exec）

工作目录 /home/t628/projects/ra2-campaign-forge
目标 ra2bench/gamemd.exe（PE32，ImageBase 0x400000）
允许写盘路径仅限：_r213/x1.py、_r213/x1.json、_r213/x1_out.txt

## 任务

完全独立地重建 MSVC RTTI 三段结构并给出下列实测计数。可以读 _r185/pe185.py 作为 PE 映射工具库（它提供 P.RAW / P.B[段名] / P.dw(va) / P.where(va) / P.cstr(va) / P.r2o(va)），但不要照抄 _r212 或 _r209 里的任何结论性数字，也不要引用它们的判据实现；一切自己从字节重算。

## 结构口径（先自行验证再使用，验证不成立就写 UNKNOWN 并说明）

- COL 类头记录 20 字节：+0 signature、+4 mdisp、+8 cdOffset（恒 0）、+12 pTD（指向 .data）、+16 pCHD（指向 .rdata）
- TD 类型描述符：+0 pVFTable、+4 spare（0）、+8 内联名字（.?A 开头、@@ 结尾）
- CHD 16 字节：+0 signature、+4 attributes、+8 numBaseClasses、+12 pBCA；BCA 元素是 BCD 记录地址（24 字节，6 个 dword）
- vftable 起点 = COL 地址 + 4；COL 地址处那 4 字节是指向该 COL 自身的指针

## 必须实测并打印 + 写入 JSON 的条目

- A1 COL 记录总数（判据：sig in {0,1,2} 且 +8==0 且 +12 指向 .data 内 .?A...@@ 名 且 +16 在 .rdata）
- A2 前驱位点：.rdata 与 .data 中 word 等于某 COL 地址、且其下一个 word 落在 .text 的位点总数；每个 COL 是否恰好一个前驱；前驱地址集合是否与 COL 集合一一对应
- A3 CHD 数（按 pCHD 去重）与 own 记录数（pCHD+16 落在 COL 内的类数）
- A4 COL 指向的不同 pTD 数；被 2 条及以上 COL 引用的 pTD 数（并给前 8 个样例的地址与记录数）
- A5 TD+8 名与 COL 名相等的条数 / 总数
- A6 mdisp==0 的记录条数，以及这些记录 TD+0 是否等于 COL+4（给 x/y）
- A7 mdisp!=0 的记录条数、mdisp 取值全分布（value:count），以及这些记录 TD+0==COL+4 的条数
- A8 每条 COL 的 vftable 长度（从 COL+4 起连续 .text 指针个数，上限 4096），给长度分布与总槽数
- A9 正反控一：去掉 +8==0 约束后的 COL 计数
- A10 正反控二：名字前缀放宽为 .?A（含 .?AU）后的计数
- A11 正反控三：去掉「+12 在 .data」约束后的计数

## 纪律

1. 一条命令跑完全部条目，stdout 同时 tee 到 _r213/x1_out.txt；每条打出实测值与 PASS/FAIL。
2. 严禁对整段 .text 开 md.detail=True 全量反汇编；A1 到 A11 均不需要指令级反汇编。
3. 所有数字必须实测，禁止预估；算不出就写 UNKNOWN 并说明卡在哪。
4. 回复正文给一张 A1 到 A11 的实测值表 + 任何与我方口径冲突的地方。
