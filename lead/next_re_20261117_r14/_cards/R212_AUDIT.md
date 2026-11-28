# R212 跨家族审核卡（只读复核，禁止改写任何落盘文件）

## 环境
- 根目录 /home/t628/projects/ra2-campaign-forge
- 目标 exe: ra2bench/gamemd.exe（4825360 B）
- 可复用解析器: _r185/pe185.py（提供 RAW / B / dw(va) / cstr(va) / r2o(va) / where(va)）

## 结构定义（本卡给定，勿另行臆测）
- COL 类头记录 24 B 判据: +0 sig in {0,1,2} / +4 mdisp(int32) / +8 cdOffset 恒 0 / +12 pTD(指向 .data) / +16 pCHD(指向 .rdata)
- CHD 16 B: +0 / +4 / +8 NB / +12 pBCA
- BCA 是 NB 个 dword 数组，每个元素是 **BCD 记录地址**（不是 COL）
- BCD 24 B: +0 pTD / +4 nc / +8 mdisp(int32) / +12 pdisp / +16 vdisp / +20 attributes
- TD 布局: +0 与 +4 各 4 B，+8 起内联类名（NUL 结尾）

## 待复核断言（逐条给 PASS/FAIL + 你的实测数字）
A1 COL=1214、CHD=954、own=954、BCA 元素=2615。
A2 全域 pTD 池 988 个；INTERFACE（TD 名以 .?AU 开头）恰 26 个；TD_OWN（954 个 own COL 的 pTD 集合）954 个。
A3 律 W 复验：对 954 类，令 W(c) = { mdisp(r) : r in BCA(c), mdisp!=0, pTD(r) in INTERFACE ∪ TD_OWN }，V(c) 取 _r209/q3.json 的 vftable 侧 mdisp 集合（去 0），比较 W(c) 与 V(c)，失配类数应为 0。
A4 mdisp==8 的 BCA 记录恰 78 条，pTD 全为 .?AVINoticeSink@@（TD 址 0x816b50）。
A5 mdisp==12 的 BCA 记录恰 78 条，pTD 全为 .?AVINoticeSource@@（TD 址 0x8177e8）。
A6 上述两条记录的 (nc,pdisp,vdisp,attr) 全为 (0,-1,0,0)，78 条逐一如此。
A7 含 mdisp==8 的类集合与含 mdisp==12 的类集合完全相同，规模 78。
A8 对每个含该对的类，8 记录索引 = 12 记录索引 − 1（即 8 紧跟 12 之后/索引更大？请实测方向并只报实测差值分布）。
A9 8 的 BCA 索引跨度 6..12（不固定），12 索引跨度 7..13。
A10 mdisp==21784 的 BCA 记录恰 3 条，pTD 亦为 .?AVINoticeSink@@，attr 恒 9，对应类为 MouseClass/TabClass/ScrollClass。
A11 5 个 ATL EventSink 的 CHD 为 0x80e680 / 0x80e740 / 0x80e780 / 0x80e7c0 / 0x80e998；其 BCA 非零 mdisp 记录各 2 条，pTD 均为 ?$CComObjectRootEx@VCComMultiThreadModel@ATL@@ 与 CComObjectRootBase@ATL@@（两者均 ∉ INTERFACE ∪ TD_OWN），故律 W 对它们得空集，与实测空视图一致。
A12 反控：若律 W 不做 pTD 过滤，失配类数应为 15；仅用 TD_OWN 为 91；仅用 INTERFACE 为 81。请实测这三数。

## 纪律
- 只用 python3 + _r185/pe185.py，一条命令输出全部复核数字。
- 不要写任何文件到项目目录；只把结论打印出来。
- 不要对整段 .text 开 capstone detail。本轮不需反汇编。
- 结论必须给实测数字，不得引用本卡数字作为结论。
