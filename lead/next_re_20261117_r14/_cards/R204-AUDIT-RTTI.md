# R204-AUDIT-RTTI — 只读审计：CHD/BCD/BCA 布局结论是否成立（不得写任何文件）

## 背景

主会话本轮（R204）对 gamemd.exe 的 MSVC RTTI 三张表做了字节实证，得出一批结论。本卡请你**只读复核**，逐条给 PASS / FAIL，不许改任何文件，不许跑反汇编。

## 输入（只读）

- 二进制：/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe
- PE 助手：_r185/pe185.py（P.RAW / P.B[段] / P.dw(va) / P.where(va) / P.cstr(va,n)）
- 主会话脚本与结果：_r204/m5_pool.py、_r204/m5_pool.json、_r204/m4_chd4.py、_r204/m4_chd4.json
- 执行员独立复核：_r204/hy4_layout.py、_r204/hy4_layout.json

## 待审计的 10 条结论（逐条给 PASS / FAIL + 你的实测数）

1. COL 记录 1214 个、不同类名 954 个。
2. 按 COL 第 5 个 dword（pCHD）分组，且**完全不看类名**，也恰好得到 954 组，组大小分布 1:860 / 2:10 / 3:6 / 4:76 / 5:1 / 7:1。即「名字判据」与「指针判据」给出同一 partition。
3. CHD 四字段：+0 恒 0；+8 = BCA 元素个数（最大 18）；+12 = BCA 数组首址且落 .rdata；+4 取值 {0,1,5}。
4. 1002 个不同 BCD 全部 8 字节对齐，但**不是** 24 字节统一网格（地址模 24 有 {0,8,16} 三种）。
5. BCA 相邻元素差分以 -24 为绝对主导（973/1661），但存在跨段大跳（-31104 出现 78 次、+19888 出现 12 次）。
6. BCD 的六个字段：+0 pTD / +4 ncb / +8 mdisp / +12 pdisp / +16 vdisp / +20 attributes；且 pdisp 恒 -1（1002/1002）、vdisp 恒 0（1002/1002）。
7. **最强判据**：每张 CHD 的「自有 pTD 集合」（来自该组 COL 的 pTD）必须 ⊆ 该 CHD 的 BCA 中所有 BCD 的 pTD 集合，954/954 成立；反控（换用同长度别的 CHD 的 BCA）成立 0/954。
8. BCD 池存在共享：1002 个唯一 BCD 中 304 个被 >= 2 张 CHD 引用，最多被引用 98 次。
9. mdisp != 0 的类有 99 个，多视图（>= 2 视图）的类有 94 个，只差 5 个 —— 这 5 个全部是 ATL 的 CComObject / 事件 sink 模板类（0x80e680 / 0x80e740 / 0x80e780 / 0x80e7c0 / 0x80e998），它们 BCA 里有 mdisp=4 的基类但没有第二张 vftable。
10. 执行员声称：BCD 在地址 b 处，则 b-16 处的 dword 直方图与 BCD+8（mdisp）直方图完全一致（978 个 0），可作 24 字节步长的证据。

## 交付格式

一条命令输出全部结果：把脚本写成 /tmp/audit_r204.py（**只允许写 /tmp**），一次跑完 10 条，每条打印 PASS/FAIL 与实测数，最后打印 FAIL 计数。禁止写 _r204/ 或仓库内任何文件。

## 纪律

- 只读，工具用 python3。禁止 capstone 全量反汇编。
- 每条的判据要**自己重写**，不要 import 主会话脚本。
- 数字先实测再写；拿不准写 UNDETERMINED 并说明卡点。
- 30 轮内完成。
