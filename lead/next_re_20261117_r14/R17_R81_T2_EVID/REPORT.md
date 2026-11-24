Q1 | 写域约定原文 ≥5 处（卡名:行号:逐字）: NAMED-PUSH.md:63:`- \`EVIDENCE\ROW_<entry>.txt\`：逐行，四环的地址与字节` ; S09-KPROVED8.md:58:`- \`EVIDENCE\`（逐行反汇编与站点清单，不截断）、\`work\`（脚本可复跑）、\`UNKNOWNS.md\`、\`DISAGREE.md\`` ; SEMFIX-ENGFAM.md:43:`- \`SEMFIX_ENGFAM\EVIDENCE\ROW_<entry>.txt\`：每行一个，含第 1–3 步的地址与字节` ; PATCH-D35.md:62:`- \`EVIDENCE\`（字节 diff、启动日志、except.txt 副本）、\`work\`（脚本可复跑）、\`UNKNOWNS.md\`、\`DISAGREE.md\`` ; GATE-BEHAV.md:65:`- \`EVIDENCE\`（逐次读数、必要的截图仅作旁证）、\`work\`、\`UNKNOWNS.md\`、\`DISAGREE.md\`` ; a-SEMFIX-BATCH.md:18:`- 执行器自留证据（**只当线索，不作证据**）：\`EVIDENCE\ROW_<entry>.txt\`、\`REPORT.md\`、\`base_rate.tsv\`` ; a-S17-ENGFAM.md:21:`- 原始普查：\`S17-F1\EVIDENCE\analysis_deep2.txt\`（**只能当线索，不能当证据**）` ; R16-SIEVE-D1-WIDE.md:37:`3. **排除**产出方自己的 \`EVIDENCE/\` 文件与 \`REPORT.md\`（那些是执行器自述，不是审计）` | 要求写的是: 两者都有——EVIDENCE\ 是执行员在其卡写域内「自留」的混合工作域：以对象抄本为主（逐行反汇编、地址与字节、站点清单、字节 diff），同时允许启动日志/逐次读数/截图作旁证，但「只当线索，不作证据」；故目录名「EVIDENCE」不是内容可靠声明。
Q2 | 1,242 件分布（源=R17_R78_T1_RECLASS\files_excluded_prime.tsv 列 rel/label/ext/bytes；脚本=analyze_q2.py + q5_posctrl.py/ps1）: basename=stdout 233 / stderr 38 / _out 6 / report 5 / result 0 / 其他 960（合计 1242） ; ext=.txt 1096(11,842,403 B) / .json 116(34,374,288 B) / .log 21(391,932 B) / .md 8(74,561 B) / .tsv 1(1,595 B)，字节合计 46,684,779 B ; 顶层卡 Top5（按件数）=S09_KPROVED 36 / S05_KPROVED2 24 / S10_KPROVED3 24 / W32_campaign_menu_entries 21 / S03_C7 20（轮次分布 next_re_20261117_r14 901 / r02 190 / r12 38 / r11 28 / 其余 85） ; 冲突最多的卡=按件数 S09_KPROVED(36 件/1,339,857 B)，按字节 D41_SUBST(13 件/17,718,626 B，含 a2_sites.json 17,624,355 B)。
Q3 | 20 件抽样（前 8 KiB；VA=行首 0x[0-9A-Fa-f]{6,8} 行占比；脚本=analyze_q3q4.py，明细=_samples20.txt；未看 why 列）:
 1 next_re_20261112/RE-N02/EVIDENCE/scan_stdout.txt VA=0.0%(0/111) 横幅=有(=== PE MAP) 我判=对象
 2 next_re_20261112_r02/W32_campaign_menu_entries/EVIDENCE/recon8_stdout.txt VA=0.0%(0/64) 横幅=有(=== byte writes) 我判=对象
 3 next_re_20261112_r02/W54_save_determinism/EVIDENCE/step0_inspect.stdout.txt VA=0.0%(0/88) 横幅=有(=== FILE:) 我判=对象
 4 next_re_20261112_r02/W61_third_badge_route/EVIDENCE/pcx_render_stdout.txt VA=0.0%(0/2) 横幅=无 我判=过程
 5 next_re_20261112_r04/W89_adversarial/EVIDENCE/check_1_2_3_4_geom.stdout.txt VA=0.0%(0/96) 横幅=有(=== [JSON]) 我判=对象
 6 next_re_20261116_r12/W160_aidispatch/EVIDENCE/W160_identify_arrays.stdout.txt VA=42.0%(21/50) 横幅=无 我判=对象
 7 next_re_20261112_r02/W32_campaign_menu_entries/EVIDENCE/parse_dialog_stderr.txt VA=0.0%(空) 横幅=无 我判=过程
 8 next_re_20261112_r02/W32_campaign_menu_entries/EVIDENCE/recon9_stderr.txt VA=0.0%(空) 横幅=无 我判=过程
 9 next_re_20261112_r02/W49_debug_list_gate/EVIDENCE/w49_env_stderr.txt VA=0.0%(空) 横幅=无 我判=过程
10 next_re_20261112_r02/W57_gate_writer_adjudication/EVIDENCE/w57_prior_classify_stderr.txt VA=0.0%(空) 横幅=无 我判=过程
11 next_re_20261112_r10/W106_classid6/EVIDENCE/bytescan_out.txt VA=0.0%(0/163) 横幅=无 我判=对象
12 next_re_20261117_r14/S13_K8RECHK/_audit/EVIDENCE/a2_rows_out.txt VA=0.0%(0/127) 横幅=有(===) 我判=对象
13 next_re_20261112_r02/W62_bline_new_criteria/EVIDENCE/sandbox/C-A/build_out/W62C1/BUILD_REPORT.txt VA=0.0%(0/29) 横幅=无(build report 标题) 我判=过程
14 next_re_20261116_r12/W158_baseline/EVIDENCE/recompute_report.txt VA=0.0%(0/103) 横幅=有(# 报告标题) 我判=过程
15 next_re_20261112_r02/W2_static/EVIDENCE/00_commands_and_exit.txt VA=0.0%(0/16) 横幅=有(RUN_ID=) 我判=过程
16 next_re_20261112_r02/W2_static/EVIDENCE/00_run_log.txt VA=0.0%(0/27) 横幅=有(RUN_ID=) 我判=过程
17 next_re_20261112_r02/W42_b_line_s2/EVIDENCE/exit_codes.txt VA=0.0%(0/17) 横幅=无(有命令行表) 我判=过程
18 next_re_20261112_r02/W42_b_line_s2/EVIDENCE/git_before.txt VA=0.0%(0/22) 横幅=无(有时间戳) 我判=过程
19 next_re_20261112_r02/W47_baseline_adjudication/EVIDENCE/exit_codes.txt VA=0.0%(0/35) 横幅=无(有时间戳) 我判=过程
20 next_re_20261112_r02/W47_baseline_adjudication/EVIDENCE/w47_probe_v2.console.txt VA=0.0%(0/89) 横幅=有(===+PROGRESS+时间戳) 我判=过程
Q4 | 判据（脚本 judge_q4_v2.py，全量结果 _verdicts.tsv）=读前 8 KiB：①命中过程帧头 RUN_ID=/COMMAND=/run_at=/[PROGRESS/构建报告标题，或空流/≤5 行且无对象信号 ⇒ 过程输出；②否则「记录被测对象」信号行（0x[0-9A-Fa-f]{6,8}、VA=/FOFF=/ctx=、PE 段表、站点清单、结构化 key=value、逐行地址+字节）≥3 行且多于过程信号行 ⇒ 对象抄本；③两者皆弱 ⇒ 无法判定单列。为何可用：Q1 写域约定证明 EVIDENCE 是执行员自留混合域，目录名非可靠声明，故按「内容记录对象还是过程」判，符合纪律 23。 ; 样本准确率=20/20（样本内调参命中，非无偏；样本外另抽 10 件人工复核约 6–8/10 一致，见 _oos10.txt） ; 1,242 件可解决区间=[580, 880]（判据明确裁决 976=对象 732+过程 244，无法判定 266 件单列不硬塞；按样本外有效裁决率 60%–90% 折算 976×[0.6,0.9]≈[586,878] 取整；高置信子集 O≥5&P=0 或 P≥3&O=0 或空流共 352 件为下界锚）。
Q5 | 正控（源同 Q2，两实现互不复用代码）: 法1=PowerShell q5_posctrl.ps1 → TOTAL 1242;stdout 233;stderr 38;_out 6;report 5;result 0;OTHER 960 ; 法2=Python q5_posctrl.py → TOTAL 1242;stdout 233;stderr 38;_out 6;report 5;result 0;OTHER 960 | 一致。
OVERALL | 能收敛：写域约定已找到——EVIDENCE\ 是执行员在各自卡写域内「自留」的混合工作域（对象抄本为主、过程输出仅作线索旁证，目录名非可靠声明），据此内容判据可把 1,242 件中的约 580–880 件裁为对象/过程（至少 266 件仍无法判定，单列），收敛后 EVIDENCE 族归属不变——仍以「被测对象」为基础盘，仅其中过程输出子集（判据判 244 件，折算约 150–220 件）移向过程侧，不翻转全族定性。

---
## 附：证据链与口径（纪律 1/3/4）
- 清单：R17_R78_T1_RECLASS\files_excluded_prime.tsv（6011 数据行，列 rel/ext/bytes/mtime_ns/family/label/why/layer/in_tier_C_old）；UNDECIDED 共 1242 行，全部含 EVIDENCE 路径，字节合计 46,684,779（与卡面 §一 一致）。Q3 判定全程未读 why 列。
- 上游报告：R17_R78_T1_RECLASS\REPORT.md:265「这个二元问题的答案取决于"谁写的这个 EVIDENCE 目录"，清单里没有作者信息。给不出来就说给不出来。」、:320「EVIDENCE/ 目录的作者/生成者归属——清单无作者字段……未取得。」——本卡用卡面写域原文补上该缺口。
- Q1 卡面逐字行均已用 read 工具在 _cards\*.md 原文核对（NAMED-PUSH:57-63、S09-KPROVED8:55-58、SEMFIX-ENGFAM:39-43、PATCH-D35:59-62、GATE-BEHAV:62-65、a-SEMFIX-BATCH:15-18、a-S17-ENGFAM:19-21、R16-SIEVE-D1-WIDE:37）。
- 样本分层：stdout 6 / stderr 4 / _out 2 / report 2 / 其他 6（result=0 故不抽），种子 rel 字典序均匀取，其他族跨 ext（json/log/md/tsv/txt）。
- 未取得/判不了：266 件判据平票（O、P 皆弱）单列于 _verdicts.tsv（verdict=无法判定），不硬塞。样本外 10 件中 ROW_0051AA40.txt（地址无 0x 前缀）、gen_s3_artifacts.stdout.txt（[assert]/[write] 日志）、selftest_stdout.txt 为已知失配例，列入误裁上界。
- 唯一写目标 R17_R81_T2_EVID\；未运行 mev675.py；未写 lead\ 下任何既有目录。
