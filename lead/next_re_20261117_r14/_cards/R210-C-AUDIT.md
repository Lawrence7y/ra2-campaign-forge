# R210-C 跨家族只读审计：律 U / 律 V / 主视图槽普查数字（审计员卡，只读）

## 你要审的三组结论（全部由我（主会话）与两个执行员给出，你要独立复算，不许照抄）
只读：不要写任何 _r210/ 以外文件，不要修改既有文件。可以写 _r210/audit_*.py 与 .json。

### 组 1 · 律 U（额外视图集合 = {4} ∪ 本类 slot0 QI 的静态返回正偏移）
主张：gamemd.exe 里 1214 张 COL vftable 中有 101 张是「额外视图」（mdisp!=0），分属 91 个类（按 COL+16 的 pCHD 分组）。若把每类主视图（mdisp==0）slot0 指向的函数按 capstone 反汇编解析成「比较了哪些 IID -> 返回哪个 this 偏移」，则：
- 该 QI 的返回偏移集合 R（含 0）满足：本类额外视图偏移集合 == {4} ∪ {r in R : r>0}。91/91 类成立，零残留。
- 反向：954 个主视图类里 slot0 落在同一批 12 个 QI 目标上的类恰 91 个，与本表完全一致（双向等价）。
- 关键推论：QI 返回 0 时只有 {4}，所以有 91-（部分）类只有一条额外视图；0x4f6830 (HouseClass) 返回 {0,36,40,44}，对应 4 条额外视图。
请你独立复算：101/1214/91/954 这四个数；以及「视图集合 == {4} ∪ 正偏移」的类数是否 91；以及双向等价是否成立。注意 QI 体解析要区分 mov [out],this（偏移 0）与 lea reg,[this+K] 后 mov [out],reg（偏移 K），不要只看 mov 立即数。

### 组 2 · 律 V（this 调整 thunk 的通用式）
主张：对每个含 thunk 的视图槽（共 305 处：303 前三槽 + HouseClass mdisp=40 的 slot3/slot4），设该视图偏移 mT、槽号 k，则该 thunk 的立即数 imm 与 E9 落点满足：imm = mT - mV，且 E9 落点 == 同类（同 pCHD）内偏移 mV 的视图第 k 槽地址；且 mV 必在该类视图偏移集合内。305/305 成立。反控：imm+4 时命中 0。
请独立复算：305 这个数、305/305 是否成立、以及 imm+4 反控是否真的 0。

### 组 3 · 主视图 954 表 slot>=3 的槽普查（执行员 #538 报的数）
主张：主视图 954 张表总槽 12726；slot>=3 槽共 9958；slot3 ret 立即数 top1 是 ret（c3，510 次）、其后 ret 0x10（81）、ret 0x1c（60）、ret 0x4（58）；slot3 落点被 1 张表独占的 686 张表、被 >=2 张表复用的 132 张表、136 张短表无 slot3。
请独立复算这 7 个数。

## 方法与工具
- 环境 t628 本机：python3 + capstone + pefile 可用。公共映射 /home/t628/projects/ra2-campaign-forge/_r185/pe185.py：P.B[段名]（含 lo/hi_file/hi_virt/rawptr/rawsize）、P.RAW、P.dw(va)、P.where(va)、P.r2o(va)、P.cstr(va,max)。只 import，不要改。
- 上一轮产物 /home/t628/projects/ra2-campaign-forge/_r209/q3.json 含 COL 解析结果（vt/vt_of/mdisp/names/hit），可当线索但**不要直接采信**，你应自己从 PE 重解析 COL（COL 布局：sig@+0 取 0/1/2、mdisp@+4、cdOffset@+8 恒 0、pTD@+12 落 .data、pCHD@+16 落 .rdata，名字在 pTD+8）。
- 具体脚本我方的版本在 _r210/c1.py c2.py c3.py 与 a1.py b1.py，你可以对照，但结论要自己算，不许只跑我的脚本贴输出。
- 禁止：对整段 .text 开 detail=True 一次性 disasm（会 OOM）；只能对命中地址单独反汇编 <=900 字节，或对整段用 disasm_lite 分块。后台命令必须带 timeout。

## 输出要求
- 逐条给：主张值 / 你实测值 / PASS 或 FAIL / 你的复算命令要点。
- 若有一项不符，明确指出是口径差还是错，并给差量。
- 不允许出现反引号字符。报告写 /home/t628/projects/ra2-campaign-forge/_r210/audit_deepseek.md，最终回复里给 PASS/FAIL 汇总表。
- 若时间紧，优先组 2 与组 3（可机械核验），组 1 可只做 101/91/954 三个数与双向等价。
