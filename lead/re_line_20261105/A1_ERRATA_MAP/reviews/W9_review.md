# W9_review · 独立复核员对 ERRATA_W9.md 的复核（W9 组）

被核对象 = W9_SINGLESTEP.md / W8_STATIC_LOCATE.md / W7_W4_REVIEW.md / V6_V3_REVIEW.md
W9_SINGLESTEP.md  SHA256 = 13fa9fe35339ea40d123cf340b09c9ac692e848305ebc48d9d35f5421d895e36，字节数 = 40592
W8_STATIC_LOCATE.md SHA256 = 20e4eeac49254b274a8382e94505525a614ec5bf24ccb89316fcd8f914406262，字节数 = 26485
W7_W4_REVIEW.md  SHA256 = 22753a0ef603c6999c95b25e28a2b5a2d5820ded39c9b59559d088bf20da6ca6，字节数 = 19225
V6_V3_REVIEW.md  SHA256 = 75cad20763952e7a6d92274f8d29e7db30c307194e45437d8d459242baceffdb，字节数 = 17892
gamemd.exe SHA256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476，字节数 = 4825360（本员实算）
被核回件 = ERRATA_W9.md SHA256 = c211207b09502acdf410600a93d06155b20c273192a5ec0201ac0c4923c224ab，字节数 = 40978（复核开算时点值）
回件时刻 = 2026-11-06 09:0x +0800（复核定稿）

> 五个哈希/字节数均为本员本会话 `sha256sum` + `wc -c` 实算（命令：`sha256sum <四件> && wc -c <四件>`、
> `sha256sum ra2youli/gamemd.exe && wc -c ra2youli/gamemd.exe`），与参考值逐一相符 ⇒ 被核对象未漂移。
> 本复核零真机、零采样注入、零活进程读取、零 `ra2tool.Engine`；唯一写入 = 本件；未 commit / 未 push。

## 0 总判

**CONFIRMED**（五项指定检查全过；20/20 条六列映射的承重点全部独立复现；三处 leader 自述发现全部复现；
发现 4 处**行号引用精度**缺陷（不改判定，见 §4 / mustFix）。

## 1 检查 1：SHA256 绑定 —— 通过

- 本员实跑：`cd lead/re_line_20261105 && sha256sum W9_SINGLESTEP_7CFC9F/W9_SINGLESTEP.md W8_STATIC_LOCATE/W8_STATIC_LOCATE.md W7_W4_REVIEW/W7_W4_REVIEW.md V6_V3_REVIEW/V6_V3_REVIEW.md && wc -c <同四件>` → 四组值与 ERRATA_W9.md 头部（:4-7）**逐字节一致**，与任务书参考值一致。
- `sha256sum ra2youli/gamemd.exe && wc -c` → `73201cc0…f67476 / 4825360`，与 ERRATA_W9.md:8,:11 的实算声明一致。
- ⇒ `shaBindingPresent = true`；对象未变。

## 2 检查 2：20 条逐条覆盖 —— 通过（checkedEveryRow = true）

- `grep -c '^### W9-' ERRATA_W9.md` = **20**；`grep -c '^| W9-'` = **20**（§1 映射 20 节 + §2 矩阵 20 行，编号 W9-1…W9-20 连续无缺）。
- 源条数复核：W9_SINGLESTEP.md §7 实测 20 条在 :192-211（本员全文 Read 确认；`_a1_w9_probe_out.txt:6-27` 同）。五道复核 mustFix 源逐一亲读：Q1_review.md §6 :288-294 = 3 条（:290-292）、Q2_review.md §8 :216-223 = 4 条（:218-221）、Q3_review.md §6 :268-284 = 4 条（:271-284）、Q4_review.md §6 :423-457 = 8 条（#8 在 :456-457）、Q5_review.md §6 :492-528 = 8 条 —— 3+4+4+8+8 = **27**，与 ERRATA_W9.md §0 与汇总件 :190 的「27 去重为 20」一致；「Q4 #7、Q5 #8 为汇总件一致性元条目」属实（Q4_review.md:453-455、Q5_review.md:526-528 亲读）。
- 每行六列（where / 原断言逐字 / 修订表述 / evidenceRef / alreadyLanded / grade）齐备。

## 3 检查 3：alreadyLanded 是否真看行号 —— 通过（全部独立复现）

本员全文 Read `W9_SINGLESTEP.md`（240 行）+ 定向 grep，对 20 行的落实处行号逐一核对：

| 行 | ERRATA 声称落实处 | 本员核验 |
|---|---|---|
| W9-1 | :154,:157,:21 | ✓（:154 删除令、:157 收窄句、:21 §0 表 Q4 行均在） |
| W9-2 | :155,:156,:157,:230；缺口=BASELINE_A4_PROPOSAL/74-87 仅 :193 | ✓ 主链四处均在；`grep -n "BASELINE_A4_PROPOSAL\|74-87" W9_SINGLESTEP.md` = 仅 :193 ⇒ 缺口坐实，**部分落实判定正确** |
| W9-3 | :158,:162-166,:168 | ✓ 五件表 :162-166、259/211 在 :158、「未验」在 :168 |
| W9-4 | :21,:25,:169,:170 | ✓（:170 降级句、:169 施动者句；Q4:170 原论据句本员 grep 坐实在 Q4_RELATION.md:170） |
| W9-5 | :94-95,:113,:18 | ✓ |
| W9-6 | :176 | ✓ |
| W9-7 | :180,:182 | ✓ |
| W9-8 | :199,:225,:181（指针形式） | ✓ |
| W9-9 | :184,:182；缺口=正文无版本时刻 + PD 再漂移 | ✓ 汇总件正文确无 PD 版本时刻标注；PD 漂移见 §3.1 |
| W9-10 | :123 | ✓（`e.rd(0x7E8880,4)=04 00 00 80`、`0x7E8888=FF FF FF FF`） |
| W9-11 | :138-139 | ✓ |
| W9-12 | :158,:148,:238 | ✓ |
| W9-13 | :68,:227 | ✓ |
| W9-14 | :67 | ✓ |
| W9-15 | :111,:91 | ✓ |
| W9-16 | :107 | ✓ |
| W9-17 | :169,:224 | ✓ |
| W9-18 | :169,:219 | ✓ |
| W9-19 | :151,:184；缺口=Q4 三口径仅 :210 | ✓ `grep -n "02:15:47\|02:10:46" W9_SINGLESTEP.md` = 仅 :210 ⇒ 缺口坐实，**部分落实判定正确** |
| W9-20 | :180,:184 | ✓ |

- 14 条自declared标注（汇总件 §7 各条「**汇总件 §X 已…**」）逐一对照汇总件原文**全部属实**；6 条无标注（#8/#10/#12/#13/#17/#18）中 5 条实测确已落实、1 条（#8）以 §7/§8/指针落实 —— 与 ERRATA §2 结论一致。
- 落实事实的下游抽样独立复现（不止抄行号）：`wc -l _w9_q1_out.txt`=236 / `grep -n "PROBE DONE"`=235 ✓；`sed -n 2p _w9_q2_out.txt`=01:20:23 ✓；`sed -n 89p _w9_q3_final_out.txt`=0x7E8888 错值 ✓ 且 Q3_MECHANISM.md 零 `7E8888` 命中 ✓；`sed -n '4574,4577p' qc151_trip.py` ⇒ :4575 = `    if not src.exists():` ✓；本员二进制实读 `except.txt.final_isolated`：LF=1046 / splitlines=1047 / L1=`…\r\r` / L17=`\r` / L18=`Bytes at CS:EIP (007CFC9F) : 8B 0A …` / L62=`00F9D1EC: 00000000 DATA_PTR` ✓；drift bin 实算 `6694b75e…a8c251 / 26405 B / mtime 2026-10-16 19:21:11.816389100 +0800` ✓；107/44 子树计数与 mtime 首末 `2026-10-17 08:14 .. 2026-11-04 18:26` ✓；`sed -n 3p D22_RULING/RULING_D22.md` = `★ 定谳：D-22 = A` ✓；qc119 反例哈希抽验 `77f5a4cb…b822f` 与汇总件 :162 一致 ✓。

### 3.1 leader 三项自述发现 —— 全部独立复现

1. **PD 第三次漂移**：本员实跑 `python -I -X utf8` 读 `lead/PENDING_DECISIONS.md` ⇒ **299 行**；:123=D-22 已裁决（2026-11-06）A、:121=D-15 已裁决、:22=D-13 条目、:39=(暂停) E3 暂不执行、:144=「不修改用户的数据/存档」、:114=证据行（引 W9_SINGLESTEP.md:188-215）、:78-80=F6/G3（W7/W8）内容 —— 汇总件 :184 所记「D-13 实在 :78-80、E3 暂停在 :114、PD:144」在当前盘面**确已不可复现**，ERRATA W9-9/W9-20 的重写锚点（:123/:121/:22-25/:39/:147-149）实测成立。
2. **partVerdict=CONFIRMED 为仓外自述**：`grep -c "partVerdict\|verdict" Q5_ROUTES.md` = 0、`_w9_q5_out.txt` = 0；CONFIRMED 在 Q5_ROUTES.md 仅 :20,:21,:250；唯一出处 = Q5_review.md:411「被核者自述 `partVerdict: "CONFIRMED"`」——ERRATA §4.2 的精度注成立。
3. **L12-14 → L11-14**：本员二进制实读 EXCEPT 件：L11=`Eip:007CFC9F Esp:00F9C614 Ebp:00F9C634`、L12=`Eax…`、L13=`Edx…`、L14=`EFlags:00000286`；汇总件 :155 比对块含 Eip ⇒ 汇总件 :131/:155/:193/:225 四处写「L12-14」确系少计一行，Q4_review.md 原文（:436）为「其寄存器 == EXCEPT L11-14」——**收正方向正确**（但 ERRATA 把该原文行号写成 :427，见 §4-①）。

## 4 检查 4/5：无 phase 2 痕迹、未改既有件 —— 通过

- **W7 phase 2**：ERRATA_W9.md 通篇为 W9 组映射，无任何 phase 2 重做内容；`_a1_w9_probe.py` 全文亲读（158 行）——纯只读（仅 `open(p,"r"/"rb")`，无写模式、无写入调用）、无 `ra2tool.Engine` import、无 hook/注入/内存读取、无 W7 phase 2 重跑；探针仅**展示** PD:79-80 的 W7 字样（读取≠重做）。⇒ 无违反 D-24 痕迹。
- **未改既有件**：`git status --porcelain`（非 untracked 部分）与会话起始快照**逐条相同**（MM GOAL_THREE_TARGETS/PENDING_DECISIONS/ROUND_SUBAGENT_LOG + offline_waittrace A 组）——无新增改动；A1 写域外关键件 mtime 全部早于勘误件写入窗（ERRATA_W9.md=08:14:39）：W9_SINGLESTEP.md=05:04:21、Q5_ROUTES.md=03:05:03、Q5_review.md=04:44:26、GOAL_THREE_TARGETS=06:53:04、PENDING_DECISIONS.md=07:44:33（早于 08:03 探针运行，与「07:50 盘面」自述相容）；A1_ERRATA_MAP/ 内仅 TASK.md + 4 个 ERRATA 件 + 2 对探针件。⇒ 唯一写域铁律遵守。

## 5 Objections（不改判定的精度缺陷，均已实测坐实）

1. **ERRATA_W9.md W9-2（:52）把 Q4_review 原文行号写错**：注写「`Q4_review.md:427` 原文为 L11-14」，实测该句「与「其寄存器 == EXCEPT L11-14」的比对」在 **:436**（:427 是 mustFix #1 的替换文本行）。实质判断（L11-14 正确、L12-14 少计 Eip）本员已独立坐实，仅行号引错。
2. **ERRATA_W9.md W9-19 evidenceRef 把 Q4 §6 #8 的行号写错**：写「`Q4_review.md:453-455（§6 #8）`」，实测 :453-455 是 **#7**（汇总件一致性元条目），#8 在 **:456-457**；连带 §0 的源范围「Q4_review.md:423-455（8 条）」实为 ：423-**457**。
3. **ERRATA_W9.md §0 的 Q2 源范围超出文件末尾**：写「`Q2_review.md:216-232`」，实测 Q2_review.md 全文仅 **223 行**（`wc -l`），4 条 mustFix 实在 :218-221。
4. **（登记性）** ERRATA_W9.md 自述「回件时刻 08:14:30」与文件 mtime 08:14:39 相差 9 s —— 与「定稿 08:14:30 后落盘」自述相容，非缺陷，仅记录。

## 6 mustFix（针对 ERRATA_W9.md 的行号引用，均属低危文字修订）

1. 按 §5-①②③ 改正四处行号引用：`Q4_review.md:427`→`:436`（W9-2 注）；`Q4_review.md:453-455（§6 #8）`→`:456-457`（W9-19 evidenceRef）；§0 源范围 `Q4:423-455`→`:423-457`、`Q2:216-232`→`:216-223`。修订后本组维持 CONFIRMED，不需重开任何调查。

## 7 结论

20/20 条逐条核验通过；alreadyLanded 判定（17 已落实 / 3 部分落实 / 0 未落实）经本员独立复现成立；
leader 三项自述发现全部复现；无 phase 2 痕迹；未改任何既有件；SHA 绑定真实自算。
**verdict = CONFIRMED**；`shaBindingPresent = true`；`checkedEveryRow = true`。
