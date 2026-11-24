# D41-SUBST · PROGRESS（RULING-R15 §8.8 条 2 身份替代 · 执行 D-41(B)）

> 卡号 D41-SUBST｜目标 `ra2youli\gamemd.exe` 只读，SHA-256 `73201CC0…F67476`（实测全值吻合）｜写域仅 `D41_SUBST\` 与 `_ghidra\D41_SUBST\`(-noanalysis)；未改台账/R14_COMMON/COVERAGE/ra2youli，未建 venv、未 pip install、未 git commit。
> 环境：系统 Python 3.12.10 + capstone 5.0.7(skipdata=True) + pefile 2024.8.26。必读 §8.8 条 2、§8.6 六条、§8.1 错源 ⑬⑭⑮⑰㉓㉖、§8.5 主条均已读。

## 1. 无虚表前提核查（卡面要求「先自己核这个前提」）
- 行源 = coverage.tsv 中 subsystem∈{S02,S19} 且 grade=`[静态推断]`：**S02 14 行、S19 77 行**（盘上现值；历史截面 S02 13/14 已核）。
- 方法：对每行 entry 作为 4 字节小端 VA，在整镜像字节流中 `find(pat, i+1)` 数出现次数（S21_C3 `_audit/work/rtti_occ.py` 同法）。**0 次才算无虚表**，≥1 次走常规 RTTI、不在本卡范围。
- 自检 7/7 通过（§8.6 条 2 对照）：0053AF40/00595740/00599650/00539760/0053AB50=0，0040B880=1，005F3E30=16。
- 扫描规模与覆盖（§8.1 ㉖）：`.text` VA 0x401000 / VirtualSize 4,060,045 / RawSize 4,063,232；capstone skipdata 全扫 **1,394,186 条指令 / 68,253 E8@边界 / 81,715 原始 E8**，覆盖 `.text` **100%**（VirtualSize 全段）。站点全部落在覆盖内，口径自洽。
- **候选无虚表行数：S02 = 4/14（00407780/00407F40/00407FB0/007C9442），S19 = 56/77**。S02 远不足 8 行 ⇒ 本卡实际只做 **9 行**（S02 1 + S19 8），不伪造凑数（S21_KPROVED2 先例 0/8 照办）。

## 2. 逐行结论（9 行；每行 (a) 无虚表 (b) 通道 (c) ③b+偏移 (d) ④见证）
全部 9 行 (a) 4 字节 VA 全镜像出现 0 次；(d) 均为 E8 指令边界直调、`site+5+rel32==entry`、非自环（见 `EVIDENCE/per_row_verdict.tsv`、`final_sites.txt`）。

| entry | sub | (b) 通道与「对方给不出的信息」 | (c) ③b 档位/关键偏移 | (d) ④ 站点数 |
|---|---|---|---|---|
| 007C9442 | S02 | 2 调用者契约：CRT::malloc@7C9430(push [0xB782C4])、CRT::_new@7C8E17(push 1) 均[已证]，参数字节可核 | ③b④：+0x00 cmp/ja 边界→+0x1b realloc→+0x27 jne 回边 | 2（7C8E1D/7C943A） |
| 00406130 | S19 | 1 YRpp/Audio.h:144 JMP_THIS + 4 项吻合([ecx+C]=0x87E294=Instance、[ecx+8] Voice、[ecx+4] f_4、[ecx] f_0) | ③b②：+0x02/+0x09 falsifiable ret0、+0x30 清 f_0 | 12（含 006F9ED0 等 3 已证） |
| 00406170 | S19 | 1 YRpp/Audio.h:147 JMP_THIS + 2 项吻合([ecx+C]=0x87E294、[ecx+8] Voice) | ③b②：+0x02/+0x09 ret0、+0x12 返回 Voice | 2（750D60/750EFE） |
| 0065CA80 | S19 | 1 YRpp/CCFileClass.h:100 JMP_THIS + 3 项吻合([this]=vt 0x7F0904、ret 4 单栈参、10 字段写) | ③b③ 内存形状：vt+字段+尺寸 | 47（含 4 已证） |
| 00428B80 | S19 | 2 调用者契约：9 已证函数 lea ecx=缓冲 直调 | ③b④：+0x33 count→+0x43 read→+0x47 strcmp→+0x51 inc/cmp/jl | 74 |
| 00405190 | S19 | 2 调用者契约：PlayGlobal@750920 + PlayAt@7509E0 以 ecx=this 直调 | ③b④：+0x36 链表走、+0x2B 哨兵 cmp/jne、+0x41 free | 4 |
| 004052F0 | S19 | 2 调用者契约：PlayGlobal@750920 + PlayAt@7509E0 以 ecx=this 直调 | ③b④：+0x43 count→+0x4F read/call/写0/inc/cmp/jl | 5 |
| 00401F90 | S19 | 2 调用者契约：~AudioController@405C00 + DTOR_1@405D40 直调 | ③b②：+0x02 dec、+0x09 jge、+0x0b 钳位 0 | 12 |
| 00405BE0 | S19 | 2 调用者契约：14 已证函数 lea ecx=子对象 直调 | ③b③：+0x02 [ecx+C]=Instance、4 字段形状 | 47 |

禁项核查：未用「名字看起来对」定类（②均有 YRpp 地址行或已证调用者参数字节）；未把 `JMP_STD` 当 `CALL/JMP_THIS`（CRT.h 全为 JMP_STD，007C9442 走通道 2；0069AE90 类拒绝已避）；无单点推断（每通道 ≥2 具名锚点或 ≥2 YRpp 吻合项）。

## 3. 核心数字
- 候选无虚表行数 **S02=4 / S19=56**（池 14/77）。
- 本卡 9 行**四环齐全 9/9**（通道2 的 S02 00407F40=3 已证调用者但仅 ③a 守卫汇合、无③b，故剔除；00407780/00407FB0 无通道）。
- 通道分布：**通道 1 = 3 行**（00406130/00406170/0065CA80）、**通道 2 = 6 行**（007C9442/00428B80/00405190/004052F0/00401F90/00405BE0）。
- 随机基线（各子系统静态推断池内随机取 8 行，seed 20261119，2000 次，见 `EVIDENCE/baseline.txt`）：S02 四环代理均值 **0.5695/8**（池率 14.29%）；S19 **0.942/8**（池率 29.87%）。本卡 9 行全经逐条字节核验，非随机可复现事件。
- **DoD 增量 = 0，本条只解禁事实记录（能否把事实记成已证），不是能否达标**：S02 可升 262/S19 可升 278，proved 上界够，但 named 12.42%/11.27% 门槛 297/320 永远不达标。

## 4. 交付
`PROGRESS.md`/`coverage_delta.tsv`(9 行)/`UNKNOWNS.md`/`DISAGREE.md`/`EVIDENCE\`/`work\`/`_ghidra\D41_SUBST\` 均在本卡写域。
