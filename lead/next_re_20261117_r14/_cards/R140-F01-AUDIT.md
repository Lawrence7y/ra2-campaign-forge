# R140-F01-AUDIT · 跨家族只读复核 F01 的 RTTI 三表计数裁定

## 角色
你是审计员，只读。不得修改任何文件（除你自己的 REPORT）。不改台账、看板、FACT_INDEX、门禁。
根目录 /home/t628/projects/ra2-campaign-forge，目标 ra2bench/gamemd.exe（4,825,360 B，sha256 73201cc0...）。

## 你要复核的五条主张（逐条判 CONFIRM / REFUTE / UNSURE，并给出你自己的实测数）
主会话用的是同一份 PE 节表：.text RVA 0x1000 / .rdata RVA 0x3e1000 VS 0x30074 RAW 0x31000 / .data RVA 0x412000 VS 0x367be4 RAW 0x6c000 / ImageBase 0x400000。注意节表 VirtualAddress 是 RVA，绝对 VA = ImageBase + RVA，落盘区间是 PointerToRawData..+SizeOfRawData。

C1 · TypeDescriptor = 988（.?AV 962 + .?AU 26）。判据：在 .data/.rdata 落盘字节里找 .?AV/.?AU ... @@ 可打印串，对其起点 S 检验 dword[S-8] 落在 .data/.rdata 之内 且 dword[S-4]==0，TD 的 VA = S-8。

C2 · COL 候选 1216、结构合法的 COL 是 1214。判据：找值为某 TD VA 的 dword，位置减 12 得候选 COL，要求 dword[COL+0]==0 且 dword[COL+12]==该 TD VA。然后剔除 dword[COL+16]==0 的两个，得 1214。

C3 · 被剔除的恰是 2 个，且这三件事同时成立（同一集合）：dword[COL+16]==0、dword[COL+4]==COL-0x18、没有任何虚表以 dword[vt-4]==COL 指回它。这两个的类名是 .?AVbad_cast@@ 与 .?AV_com_error@@。

C4 · 1211 这个历史数字能被两种方式复现，且两种方式选出的集合相同：(a) 在 1214 里再要求 dword[COL+4]<=0x1000；(b) 在 1216 里取「类名不以 .?AU 开头」且「只被恰好一张虚表指回」。请分别实测两个集合的基数，并比较它们是否是同一个集合。

C5 · 1201 这个历史数字无法用「结构性」判据复现。主会话扫了单谓词与两谓词组合共 60 余种（dword[COL+4] 阈值、pCD 是否为空、是否 AU 侧、每类 COL 个数、虚表槽数 >= k、名字是否含 $ 等），1201 只在「虚表前 64 个槽里落在 .text 的个数 >= 8 或 >= 9」这一族上出现，而该族的计数随 k 从 6 到 10 依次是 1206 / 1206 / 1200 / 1200 / 1198（或按 .text 判据是 1206/1201/1201/1199），是连续无断层的，故 1201 属事后阈值产物而非结构口径。请你自己算一遍 k=2..12 的该族计数，看是否有断层。

C6 · 关于 954 的一个新事实：如果按「每个类取 VA 最低的那个 COL」得 954 个，如果按「dword[COL+4]==0」也得 954 个，但这两个 954 元集合不是同一个集合，对称差 94+94=188；且 dword[COL+4]==0 的那个 COL 在其类内部总是 VA 最高的那个（94 个多 COL 的类全部满足）。请独立验证：两个集合基数、它们是否相等、对称差大小、以及 mdisp==0 的 COL 是否为类内最高 VA。

## 纪律
1. 一次取证：一个脚本跑完全部，输出表格。禁止逐项单点命令。
2. 不要读 _r140/r140*.py —— 那是被审实现，你要独立写。
3. 断言式自检：每条主张给出你实测的具体数字，不要只说 CONFIRM。
4. 只读，不要改任何台账/看板/门禁文件。产物写 _r140/audit/。
5. 报告末尾单列一节「我判 UNSURE 或与主会话数字不一致的地方」，哪怕很小也要写。

## 交付
写 _r140/audit/REPORT_F01_AUDIT.md：C1..C6 逐条 CONFIRM/REFUTE/UNSURE + 你的实测数 + 脚本路径 + 一条命令。
