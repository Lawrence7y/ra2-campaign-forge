# R204-EXEC-CHDLAYOUT — 独立复核 MSVC RTTI 的 CHD/BCD/BCA 字节布局（只读，不改任何文件）

## 目标

主会话已在 _r204/m1_chd.py 与 _r204/m2_chd2.py 上取得一批 CHD/BCD 布局数字。本卡要求你用**自己重写的提取器**（不要 import 主会话脚本，不要照抄其断言）独立复核下列 7 项，并把结果写成 JSON。

## 输入（只读）

- 二进制：/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe
- 可复用的 PE 映射助手：_r185/pe185.py（提供 P.RAW / P.B[段名] / P.dw(va) / P.where(va) / P.cstr(va,len) / P.r2o(va)；段字典键 lo / hi_file / rawptr / rawsize）
- 参考（只读，仅用于比对，不要当成事实抄）：_r204/m1_chd.py、_r204/m2_chd2.py

## 必须独立复核的 7 项

1. COL 记录数：按判据「w[i] in (0,1,2) 且 w[i+2]==0 且 w[i+3] 落 .data 且 w[i+4] 落 .rdata 且 w[i+3]+8 处的 C 串以 .?A 开头以 @@ 结尾」，在 .rdata 与 .data 全段扫描，报告命中数与不同类名数（主会话报 1214 / 954）。
2. pCHD 分组：按 COL 第 5 个 dword（pchd）分组，报告不同 pCHD 个数与每组的 COL 个数分布（主会话报 954 与 1:860 / 2:10 / 3:6 / 4:76 / 5:1 / 7:1）。**这一步必须不看类名**，只用 pCHD 指针。
3. CHD 四字段：对每个 pCHD 地址读 +0 / +4 / +8 / +12，报告各自的取值直方图与所在段（主会话报 +0 恒 0、+8 最大 18 且恒 <= 200、+12 全部落 .rdata、+4 取值集合 {0,1,5} 且 0:855 / 1:66 / 5:33）。
4. BCA 取元素：用 CHD+8 作个数 n、CHD+12 作数组首址，读 n 个 dword，报告总引用数与不同 BCD 数（主会话报 2615 / 1002）。
5. **BCD 24 字节定长**：把 1002 个不同 BCD 地址排序，报告相邻地址差的集合；断言所有差都是 24 的倍数（这是 24 字节定长的最强机械证据）。
6. **BCA 是否连续降序段**：对每个 CHD，检验其 BCA 是否恰为 {pBCA, pBCA-24, pBCA-48, ...} 共 n 个；报告成立的 CHD 数（主会话预期绝大多数成立）。
7. BCD 字段：对 1002 个不同 BCD 读 +0(pTD) / +4(ncb) / +8(mdisp) / +12(pdisp) / +16(vdisp) / +20(attributes)，报告各字段取值直方图（主会话报 pdisp 恒 -1、vdisp 恒 0、attributes 0:991 / 2:7 / 9:4）。

## 纪律

- 一条命令输出全部证据：写一个 /home/t628/projects/ra2-campaign-forge/_r204/hy4_layout.py，一次跑完 7 项，结果同时打印并落 _r204/hy4_layout.json。
- 每项都要打印**你的实测值**，不要打印「与主会话一致」这类字样；一致性由主会话自己比对。
- 只读：除 _r204/hy4_layout.py 与 _r204/hy4_layout.json 外不得写任何文件。
- 禁止对整段 .text 开 capstone 全量反汇编；本卡不需要反汇编，全部是 PE 数据段的 dword 读取。
- 任何数字先实测再写，禁止预估；拿不准的项写 UNDETERMINED 并说明卡在哪一步。
