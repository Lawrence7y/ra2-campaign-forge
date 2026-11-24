# N-6 · 低负载崩溃语料三链登记与签出（A5 重定位 / P1 毒值 / UAF 写者）

- 任务锚：`lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md:61-68`（N-6 原文；本轮上游指纹六件全 MATCH，见 `_n6_hash_anchor_out.txt`）。
- 写域：`lead/crash_diag_n6_20261107/`（唯一写域；零真机、零采样、零母本写入、未 commit、未 push）。
- 纪律：每个数字追「实跑命令+输出」（记为【实跑】）或「文件:行」；拿不到写「未验」。
- ★ 前缀硬约束沿用：凡涉崩溃发生与否、规模表述，逐字带「在现有低负载语料内」。

## 0 被核对象指纹（本轮亲算，完整 64 位）

被核对象 SHA256 与字节数（【实跑】`python -I -X utf8 _n6_hash_anchor.py`，输出全量见 `_n6_hash_anchor_out.txt`）：

| 对象 | SHA256（完整） | 字节数 |
|---|---|---|
| lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md | `c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c` | 27,225 |
| lead/re_line_20261105/D24_RULING/RULING_D24.md | `56167a5e869540d7e14a7f13d29a2ed9d780d0c6352635e6e12b36cd633dcdf5` | 15,301 |
| lead/GOAL_THREE_TARGETS_20261018.md | `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 759,518 |
| out/…/a34_crash_final/A34_CRASH_FINAL.md | `c79a1988cb0ffcaad6e252507965f23cae4eaad878a32a44875c08498087833d` | 46,222 |
| out/…/goal2_dump_20261021/REPRO_ATTEMPT_RECEIPT.md | `12f96d2dc48a0f56610c82e1a35ccc2a494a4f73cbc4a1f9a4fc45730bfff1a0` | 4,860 |
| lead/b2b_candidate_review3_20261107/CANDIDATE_SEMANTIC_REVIEW_R3.md | `96071dd9d58e30a54966a2a1e16f4af918c2f8dd5825363510e8ced8bc6a8fea` | 24,661 |
| ra2youli/gamemd.exe | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | 4,825,360 |
| ra2bench/gamemd.exe（同上，双载体一致） | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | 4,825,360 |
| ra2youli/except.txt（现势崩溃件） | `584069adfe5b4a5b7587a383620f716edbe79c52cf899b43038d599d4ed52cfa` | 27,631 |
| out/…/qc135_objloc/qc135_objloc.py（P1 仪器现值） | `b27e870b266a47ccc2d10ad8e5b69ea00540fb33ed68ad045274f307ddecd680` | 312,537 |
| out/…/qc163_a5_objloc_trip/qc135_readings.json（现值） | `8eeed79d39e29ddfa78998ffedfcee06b8928962fc08daf72a048935f2549e4a` | 196,413 |
| out/…/qc163_a5_objloc_trip/evidence_preserved/outdir/qc135_readings.json | `05a269e1390787607dac6dcc6cc13fa367596fce0b633866b866532cdbb9e220` | 194,061 |
| out/…/qc163_a5_objloc_trip/evidence_preserved/carrier/except.txt | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` | 26,405 |

六件上游指纹全部 MATCH（脚本逐件标注）；R3 的 `verdict: PASS` 实际在 `CANDIDATE_SEMANTIC_REVIEW_R3.md:21`（:23 为总括行，同样含 PASS 表述——两处均已亲读）。

## 1 语料盘点（文件命令，铁律 11：未上全仓 Python 遍历）

【实跑】`ls -la out/re_work/work_chain/CONTINUE_20261003/lead/` 与逐目录 `ls`：`a22_crashfam_fold`、`a28_crash_prereg_design`、`a32_crash_evidence`、`a34_crash_final`、`a35_crash_repro_continue`、`a38_crash_first_fail`、`crash_census`、`crash_repro`、`crashfamily_crosscheck`、`crashfam_ext`、`goal2_dump_20261021`、`boot_hang_triage_20261018`、`goal2_crashaddr_20261020`、`goal2_l3_disambig_20261018`、`goal2_poison_gen_20261018`、`goal2_writer_20261021`、`goal2_corpus_provenance_20261021`、`goal2_sbh_guard_20261020`、`goal2_wer_observation_20261022`、`goal2_rc4_power_20261022`、`qc135_objloc`、`qc163_a5_objloc_trip`、`qc161_patch_QC205_verify_20261018` 等目录均在盘。

except/dmp 证据文件（【实跑】`find … -name "*.dmp" -o -name "*except*"`）：
- `boot_hang_triage_20261018/gamemd_crawl.dmp` = 306,027,236 B（唯一非零 dmp）。
- `goal2_dump_20261021/l1e_crash.dmp`、`l3_crash.dmp` = **0 B**（两次 dump 落空——复现回执 REPRO_ATTEMPT_RECEIPT.md:35 记 O2 为 exit 0 正常退出，无 dump 可抓）。
- `qc161_u0400_trip/except_post_20261018T*.txt` 30+ 份、`census/except_index.json`、`except_triage/except_triage.json`。
- `qc163_a5_objloc_trip/evidence_preserved/carrier/except.txt` = `6694b75e…`/26,405 B —— ★ 按 §599/§601 订正口径，这是 QC124 group2 人为 DR0=0x007CFC9F 断点命中写出的运行期产物、被 harness 反复复制（§599 引 QC124_VERDICT.json `answer_detail`「这是断点异常无人处理的必然后果，不是游戏本身的崩溃」；§601 撤回「唯一一次」，订正为「至少 5 个不同哈希、Esp 各异的真实运行期异常记录，但它是最常被复制的那一次，不是游戏自身崩溃」）。本轮**不把它当 RC-1/游戏崩溃证据使用**，仅登记其存在与订正口径。

## 2 链 1 · A5 重定位链（登记）

**对象**：RC-1 族（`Eip=0x007CFC9F` `mov ecx,[edx]`、`Edx=0xFE00FFFF`、`Esp=00F9D148`）的候选 entry 重定位。
- 机制锚：RC-1 位于 `.text`，文件偏移 `0x3CFC9F`，字节 `8B 0A 2B 4D F0 …`（crashfam_ext/CRASHFAM_EXT.md §2.1【亲读】）；SBH 分配器簇 `0x7c8b3d→0x7c93e8→0x7cf7bd`、守卫 `0x7CFC9B`、全局簇 `0x00B78B94/98`（goal2_crashaddr_20261020/CRASH_ADDR_ANALYSIS.md:138【亲读】）。

| 维度 | 证据 | 结论 |
|---|---|---|
| 新鲜性可判性 | 可判；判为**旧**：RC-1 在语料内仅 2 份真转储、末次 2026-09-30 00:28、22 天零发生（goal2_corpus_provenance_20261021/CORPUS_PROVENANCE_20261021.md:17【亲读】）；全语料三态分类 `n_any_对局内=0`（crash_census/CRASH_CENSUS.md:32-34【亲读】） | 非新鲜异常 |
| 版本 | 载体 gamemd.exe 双拷贝 `73201cc0…67476`/4,825,360 B【实跑，本轮亲算，与 A34 §1.1 同值】；A5 readings 现值 `8eeed79d…`/196,413 B、preserved 版 `05a269e1…`/194,061 B【实跑】——L3 分析引用版 `9fd5ea8a…313f37`（goal2_l3_disambig_20261018/L3_DISAMBIG_ANALYSIS.md:4）在 trip 目录 5 件候选+evidence_preserved 递归中**均无匹配**【实跑】 | L3 终端证据版本漂移，引用版不可复钉（缺口） |
| 异常时序 | A5 第三跑 `final_exit_code=31`（EXIT_L3_AMBIGUOUS，verdict=null note=`feature_A_multi_hit`，132 条 readings：128 scan=119 成功+9 失败+4 聚合；L3_DISAMBIG_ANALYSIS.md:4,:11,:21,:182-187【亲读】）；run7/run8 `exitcode=71`（收尾 rmdir WinError 32、residue=[]，qc135_final_record.json【亲读】；台账 :44「exit=71 良性残留」）——均为 harness 判定码，非游戏异常 | 多义未消歧；无游戏自身异常时序 |
| 责任写者证据 | 写点候选已静态点名：unlink 落点 `0x7CFD30/0x7CFD39`（goal2_poison_gen_20261018/POISON_GEN_DESIGN.md §1「P1=写点捕获」【亲读】）；守卫位 `0x7CFC9B`；但「谁腐化了 freelist 节点」无任何运行期证据 | 候选位点在、写者未指认 |
| 正常退出记录 | QC196b A5 第五趟 exit0、收尾链 0 失败首次全绿（GOAL_THREE_TARGETS_20261018.md:40【亲读】） | 在案 |

## 3 链 2 · P1 毒值链（登记）

**对象**：RC-1 面的毒值事件捕获仪器（`qc135_objloc.py` 的 `l3_poison_poll`/B 臂）+ crashspec #4 A/B 毒值事件发生器。

| 维度 | 证据 | 结论 |
|---|---|---|
| 新鲜性可判性 | 无任何已捕获毒值事件 ⇒ 无异常可判。台账 :38「待真机 B 臂七连标定趟」至今未跑【亲读 GOAL_THREE_TARGETS_20261018.md:38】 | 零事件、零新鲜性 |
| 版本 | ★【实跑】仪器现值 `b27e870b…`/312,537 B / mtime 2026-10-18 09:07:20 ≠ QC205 验件锚 `1355dead…e77e`/299,887 B（qc161_patch_QC205_verify_20261018/QC205_VERIFY.md:18,:73-74）⇒ QC205 的 7/0/0 CONFIRMED **不绑定现值版本**；现值版本无对应已核锚 | 版本漂移（缺口） |
| 异常时序 | 无事件，无时序 | — |
| 责任写者证据 | 无（写点捕获本身从未运行）。设计面判别式已固定：任槽出现 `0xFE00FFFF` ⇒ `k=(slot−eax−0x144)/0x204`、`c=((slot−entry)−4)/8` 整除+区间自证唯一（L3_DISAMBIG_ANALYSIS.md §5-P1:199【亲读】）；毒值定义 `0xFE00FFFF` = MSVC6 SBH「无节点」哨兵、映像内零立即数命中（POISON_GEN_DESIGN.md §3；CRASH_ADDR_ANALYSIS.md:137「0xFE00FFFF 全镜像 0 次」） | 判别器就绪但未产证 |
| 正常退出记录 | 不适用（零真机趟）；配套 SBH 守卫补丁 CL_EXIT=0、13/13 语义检查、默认 `EnableSbhGuard=0`、未部署（goal2_sbh_guard_20261020/RECEIPT.md【亲读】） | 离线就绪态 |

## 4 链 3 · UAF 写者链（登记）

**对象**：`0x0054A56E` `mov dword [esi+4],0`（`VectorClass/DynamicVectorClass<PAUTileInsertType>` 析构/Resize 路径）。

| 维度 | 证据 | 结论 |
|---|---|---|
| 新鲜性可判性 | 可判；判为**次生**：崩溃对象来自 E1c csf 初始化失败载体进程（`l1_u0800_e1c_dump_20261020`，该趟 except.txt 零新增、WER 接管）；2026-10-22 依用户裁决 2 追加定位声明，本文由「②a 根因链定谳」**下调为「次生崩溃分析」**（goal2_writer_20261021/WRITER_VERDICT.md:1-19【亲读】）；现势崩溃族是 RC-4 不是它（同件 :15-17） | 非对局内、非现势族 |
| 版本 | 同一载体 `73201cc0…67476`【实跑】 | 一致 |
| 异常时序 | E1c 趟内崩溃发生在 csf 失败框之后（次生时序）；无独立对局内时序 | 次生 |
| 责任写者证据 | 直接写者定谳=`0x0054A56E` 本条指令（正常「free 后置空」语义；WRITER_VERDICT.md §一、§3.3【亲读】）；根因写者（使 `esi` 变 `.text` 地址的那次腐化）**未定谳**：(a) 函数指针错位 vs (b) 栈槽腐化未分；vptr-fixup 双重排除（w12 `count=0` + w14 两 vtable「stored at +4: 0 sites」，同件 §3.1）；毒值是否=0xFE00FFFF 未证（§五） | 直接写者在、根因写者缺 |
| 正常退出记录 | E1c 趟非正常退出档（WER 接管）；与对局内崩溃无关 | — |

## 5 语料横账（支撑三链的公共事实，均亲读）

- 四家族计数与折叠：`RC-4=624`（折叠真 3 件 `608+10+6`）、`RC-1=16`（6 事件）、`RC-2=13`（4 事件）、`RC-3=38/18 物理件`（5 事件）+残损 22 = 713 守恒、671/671 读齐、sha_mismatch=0（a34_crash_final/A34_CRASH_FINAL.md:22,:90-95,:103-104；a22 §判词；a32 §0；a35 §0；a38 §0 五卡独立复算一致【亲读】）。
- 现势崩溃 = **RC-4**：【实跑】我亲读 `ra2youli/except.txt`（`584069ad…`/27,631 B）：`EXCEPTION_ACCESS_VIOLATION`、`Access address:00000250 was read from`、`Eip:00724737 Esp:00F9A344 Ebp:00000000` —— 与 CORPUS_PROVENANCE_20261021.md:43-50,:81（`584069ad`，2026-10-08 21:59:33）及 :15「不是 RC-1，是 RC-4」逐字吻合。
- 对局内 = 0/671、候选集为空（CRASH_CENSUS.md:32-34；crashfam_ext §0.1）。
- RC-4 触发条件结构性绕过：RC-4 的 3 份真转储全部紧贴**关窗**时刻，现行 harness 用 `TerminateProcess` 结构性绕过 RC-4 触发 ⇒ harness 趟「0 新异常」对 RC-4 **零判别力**（CORPUS_PROVENANCE_20261021.md:21【亲读】）。
- RC-4 唯一可执行最小复现 = C-1 三步（免进对局）+ 下界变体；其余 5 候选给不出逐字触发动作（crash_repro/CRASH_REPRO.md §0-2,:0-3【亲读】）；S1 窗创建 `0x77778D`→S2 窗销毁 `0x7777F3`→S3 退出前 GUI 记录更新 `0x654320` 触发 `call 0x724730`（a35 §0 靶②；a38 §0 靶③）——纸面规格，真机 0 趟。
- 预注册【仍不成立】：无内嵌时间戳、自述 SHA 缺失、0 趟真机、仅 mtime（a34 §0 靶③；a28 立六支柱新设计未执行）。
- WER 通道：对 gamemd 工作（AppHang 现场 2026-10-16 18:25:04，QC111 趟，IsFatal=1）；WER LocalDumps **从未配置**（非不生效）；harness 观测窗口在挂起判生前关闭（goal2_wer_observation_20261022/WER_OBSERVATION_REPORT.md §0【亲读】）。
- RC-4 正常退出硬门槛未达成、不收口（GOAL_THREE_TARGETS_20261018.md:1010「挂死 T204123 单例未复现、六臂 9/9 不退在案」；:5702「② RC-4 不收口」；:9507「目标② 主崩溃状态：未改变」）。
- 健康进程全生命周期零崩溃：O1 180 s / O2 255.8 s 两观察 exceptions_total=1（仅附着首断点）、O2 判据全过 exit 0——受测窗口（单机遭遇战+sf8+866–874 单位+≤4.3 min）内不复现，窗口外未证（goal2_dump_20261021/REPRO_ATTEMPT_RECEIPT.md §一、§二、§四【亲读】）。
- 横向矛盾登记在案：crashfamily_crosscheck 12 处数字不一致（8 新发现）+17 条 E 组条目，HIGH 4（contradictions.json counts【亲读】）——引用各家族数字时须带对账限定。

## 6 选择：链 1（A5 重定位）最接近可证伪根因；排除理由

**选链 1**，理由（三链中唯一同时满足四项）：
1. 有实测运行数据（132 条 L3 readings、exit 31 多义——不是纸面）；
2. 机制链静态锚定且多件互证：`0x7CFC9B` load → `0x7CFC9F` deref ← SBH freelist；分配器三函数/守卫/全局簇互证（CRASH_ADDR_ANALYSIS.md:138；crashfam_ext §2.1）；
3. 责任写者候选位点已点名（unlink `0x7CFD30/0x7CFD39`，POISON_GEN_DESIGN §1）；
4. 自证判别器已实现并经离线独立核验（P1 槽算术 k/c 自证，L3_DISAMBIG §5-P1；QC205_VERIFY 7/0/0）。其可证伪形态：**「trip 时刻候选 entry 的槽区出现 0xFE00FFFF ⇒ k/c 自证定位」**——下一真机趟即可证实或证伪。

**排除链 2（P1 毒值）**：它不是独立证据链而是链 1 的判别仪器——零捕获事件、零异常时序、零写者证据；且仪器现值已漂移出 QC205 验件锚（【实跑】`b27e870b…`/312,537 B ≠ `1355dead…`/299,887 B），判词不绑定现值。放行真机 B 臂后它才成为链 1 的证伪执行器。
**排除链 3（UAF 写者）**：其自身定位声明（WRITER_VERDICT.md:1-19，2026-10-22，依用户裁决 2）已下调为「次生崩溃分析」——对象是 csf 失败载体进程的次生崩溃，非对局内、非现势 RC-4 族；根因写者明写未定谳（§五：(a)/(b) 未分、需真机 dump 才能一锤定音，§六优先级建议 3）。

**★ 选择边界（必须随选择一起引用）**：链 1 的对象族 RC-1 本身是已停摆 22 天的历史缺陷（CORPUS_PROVENANCE:17）；**现势崩溃族 RC-4 不在三链射程内**。RC-4 的可证伪假设（关窗邻近三步触发、S1→S2→S3）在语料内已有纸面规格与时间窗证据（CRASH_REPRO §0-2；a35/a38；CORPUS_PROVENANCE:21），但其取证全部需真机——若 N-10 问「主崩溃根因最近的可证伪路径」，答案在 RC-4 关窗观察，不在三链之内。本轮仍按 N-6 原文在三链内选链 1 并如实标注此边界。

## 7 候选修改位置 / 回退方式 / 独立复核者（按所选链 1）

- **候选修改位置**：SBH freelist 读点守卫 `0x7CFC9B`（P2 守卫；规格 crashspec_v4/RC_SPEC_V4.md §3.1；交付件 goal2_sbh_guard_20261020/：`blitter_hooks_sbhguard.txt` 257,989 B 成品、`sbh_guard.diff`、assembly_report 插入点表；CL_EXIT=0、13/13 语义检查、默认 `EnableSbhGuard=0`）。
- **回退方式**：补丁为离线副本、**从未部署** ⇒ 当前回退=零动作；若未来部署，回退=按 RECEIPT「安全卸载」段卸载 cave 并复核母本指纹 `73201cc0…67476` 恢复。
- **独立复核者（角色）**：独立静态复核者（N-4 口径：逐调用点确认设计一致、API/改动面计数）+ 第二方复算者；真机验收须另有执行资格的验证任务（N-6 验收原文）；RC-4 正常退出硬门槛不放宽（GOAL_THREE_TARGETS_20261018.md:1010）。
- ★ **修复状态声明**：以上是候选与协议，**不是已实施修复**。真机禁令下 RC-4 保持未验，**不标目标②修复完成**；亦不得把 SBH 守卫的编译通过说成「已修 RC-1」（RC-1 已停摆 22 天，守卫即便部署也只覆盖历史族）。

## 8 grade 判定与最小新增证据（交 N-10）

**grade = COMPLETE**：三链各有证据与缺口，逐件登记完毕（§2–§4）。三链都有证据/缺口即交付完成（N-6 验收原文，NEXT_STEPS_20261106.md:65）。

**不是 ROOT_CAUSE_READY**，四项硬条件全缺：
1. 可信新鲜异常：无（对局内=0/671；RC-1 停摆 22 天；RC-4 硬门槛未达成 :1010；`0x7CFC9F` 单步记录系 DR0 断点伪异常，§599/§601 订正口径）；
2. 可定位责任写者/破坏路径：无（A5 多义未消歧；UAF 根因写者未定谳；RC-4 无写者证据）；
3. 可证伪假设被证实/证伪：无（P1 判别器零事件）；
4. 明确修改+回归协议齐备并验证：无（守卫未部署；预注册机制未执行；真机 0 趟）。

**最小新增证据卡（交 N-10，均需用户当轮明示授权+技术裁决，本轮禁令下不实施）**：
- N10-a（RC-4，指向主崩溃）：先配置 WER LocalDumps（WER_OBSERVATION §0 已证通道工作、从未配置——纯配置、非采样代码），再按 a35/a38 S1→S2→S3+CRASH_REPRO §2 预注册五分类协议跑一趟**关窗邻近**观察（RC-4 三份真转储全部紧贴关窗，CORPUS_PROVENANCE:21）。
- N10-b（链 1/P1）：真机 B 臂七连标定趟（台账 :38 既定排期），产生或排除首个毒值事件，同时消解 L3 多义。
- N10-c（版本钉桩，零真机可先做）：L3 引用版 readings（`9fd5ea8a`）重钉或声明不可复钉；`qc135_objloc.py` 现值（`b27e870b`）补独立核验锚。

## 9 未验项单列

1. RC-4 真机触发/修复验收——**未验**（真机禁令；:1010 硬门槛不放宽）。
2. P1 判别器在真实 gamemd 上的判别力——**未验**（零真机趟）。
3. `qc135_objloc.py` 现值（`b27e870b`）相对 QC205 锚之后改动的合规性——**未验**（本轮未做逐 hunk 审计，仅测得漂移）。
4. L3 引用版 readings `9fd5ea8a` 是否存在于 trip 目录之外——**未验**（本轮仅穷尽 trip 目录内 5 件候选+evidence_preserved 递归）。
5. boot_hang_triage_20261018 的 `gamemd_crawl.dmp`（306 MB）内容解析——**未验**（本轮零采样纪律下未解析 dump，仅登记存在性与字节数）。
6. 台账 :1010/:5702/:9507 所述「六臂 9/9 不退」「挂死 T204123」原始趟件——**未验**（本轮未回读其底层文件，仅引用台账行）。
7. W9 20 条必须改项是否已被 W9 自身修订——**未验**（§601:9505-9506 明写未代改；引用 W9 须带每项限定）。

## 10 纪律自证

- 零真机：未启动 gamemd/ra2loader/YURI，未 taskkill，未读活进程内存。
- 零采样代码：本轮新增唯一脚本 `_n6_hash_anchor.py` 仅 `open(rb)+hashlib`；无 hook/MiniDump/SuspendThread/StackWalk/ctypes/OpenProcess/ReadProcessMemory 及任何动态解析。
- 只读母本与既有件；唯一写域 `lead/crash_diag_n6_20261107/`（三件：本文件、`_n6_hash_anchor.py`、`_n6_hash_anchor_out.txt`）；未 commit、未 push。
- Python 一律 `python -I -X utf8` + 绝对路径；指纹用 hashlib（本机无 sha256sum/wc）。
- §599/§601 订正节联引：本文件 §1、§2「新鲜性可判性」行、§8.1 均按订正后口径引用 `0x7CFC9F` 单步证据链，未把订正前结论（「历史基线残件」/「唯一一次真实产生」）当作现行结论使用（GOAL_THREE_TARGETS_20261018.md:9229-9326、:9418-9508）。
