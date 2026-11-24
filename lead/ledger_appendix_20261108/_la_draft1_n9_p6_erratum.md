# _la_draft1_n9_p6_erratum.md — 第一笔草案：N-9:205 P6 前提勘误（供 Leader 整段复制追加；本文件本身不是台账，不入台账）

- **核对结论**：成立（全部要件在现盘命中，另有本会话独立复跑坐实；证据见文末「核对记录」）。
- **建议入账位置**：`lead/GOAL_THREE_TARGETS_20261018.md` 尾部（当前尾节 = §604 @:9687，全文至 :9757 止）之后追加为新节（下文按「本笔最先追加」暂编 §605；Leader 按实际追加顺序重排编号即可）。
- **锚点**：`lead/static_spec_n9_20261107/STATIC_COUNT_SPEC.md:205`（P6 行）。注意：`lead/NEXT_STEPS_20261106.md` 不存在（MISSING）；同路径计划件实为 `lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md`（135 行，SHA256 前 16 位 c364467dea909da6，本会话实算），**与本笔无关，不得当锚点**。
- **基线指纹（追加前基线，两条）**：
  - `lead/PENDING_DECISIONS.md` SHA256 = `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7`（382 行口径；52419 B，本会话实算同值）
  - `lead/GOAL_THREE_TARGETS_20261018.md` SHA256 = `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede`（759518 B，本会话实算同值）

---

## ↓↓↓ 草案正文（从这里开始整段复制）↓↓↓

## §605 · ★ 订正登记：N-9:205「P6 静态 u64 窗口读可闭」前提半成立——[0x7E1738] 可闭、[0xB0CD48] 结构性开口，P6 改判「半闭半开」（2026-11-08）

- **勘误对象**：`lead/static_spec_n9_20261107/STATIC_COUNT_SPEC.md:205`（N-9 复核件，SHA256 = `5b933fe2fcb3cc35c5026cb57b45f29da29c90b67a618346af248744ed3ccdb9` / 32281 B，本会话实算与编排方指纹一致）P6 行原文：
  `| P6 | F8 两个 FPU 常量数值（静态 u64 窗口读可闭） | F8V:169/:222 |`
  上位节题 :198「### 6.2 搜索缺口（静态可闭、既有材料未做）」；同件 :145「静态 u64 窗口读即可闭；本任务按铁律不新增探针，未读（§6.2 P6）」；:139 将两常量并列为「两个 qword」。该前提最早载体为上游转录件 `_n9_STATIC_COUNT_SPEC.md:81/:109`（mtime 2026-11-07 22:42:13 早于 N-9 复核件 23:32:45，属转录非首创）；F8_VISIBILITY.md:169/:222 原文只写「未读出/标未验/实现阶段必读」，无静态可闭断言（本会话亲读两行命中）。
- **订正后表述（P6 由「静态可闭」改为「半闭半开」）**——前提对两常量一真一假：
  - `[0x7E1738]`：**静态可闭**。落 .rdata（VA=0x7E1000 / RAWSZ=0x31000），节内 d=0x738 → 文件偏移 0x3E1738，qword=0x3FE0000000000000，double=**0.5**；同法 0x7E1728=60.0、0x7E27F8=900.0 两校验锚全中，映射法无系统偏差。
  - `[0xB0CD48]`：**结构性静态不可闭**。RVA=0x70CD48 唯一命中 .data（VA=0x812000 / VSZ=0x367BE4 / RAWPTR=0x412000 / RAWSZ=0x6C000，ZEROINIT_TAIL 尾长 0x2FBBE4；该 PE 无独立 .bss 节），节内 d=0x2FAD48 ≥ RAWSZ ⇒ **文件镜像无字节、qword 不可读**；位于 .data 零初始化尾 VA∈[0x87E000, 0xB79BE4)。值 = `ret(0x4CACB0,[0xB0CD88],[0xB0CD8C]) × (60.0/[0xB0CD78])` 运行期算出，且输入端 0xB0CD78/88/8C 与暂存槽 0xB0CE18 同落零初始化域（文件镜像均无值）；唯一写点 0x6D1BDD = `fstp qword [0xB0CD48]`（文件字节 `dd1d48cdb000` 实读核中），全文件 disp32 `48CDB000` 恰 12 命中 = 1 写（fstp@0x6D1BDD）+ 11 读（fmul）。
- **依据件**：`lead/n9_erratum_20261108/N9_SPEC_ERRATUM.md`（SHA256 = `61446db581a273725010e9b09cf3ebeba0d1412fc8666c0c6b8c660e4f7d22b4` / 20630 B，本会话实算同值；其自身状态 **unconfirmed**——独立复核 verdict=partial，partial 仅因下游影响清单漏登记 3 件，已由其 §4.2 补全为九行；反驳主结论本身复核判 confirmed）+ 勘误登记件 `lead/n9_erratum_20261108/_er_N9_205_P6_B0CD48_ERRATUM.md`（SHA256 = `414795407eef7f000baad213db075899513c86c2ee71fbeb3a72e1c5ff95ae73` / 15794 B，本会话实算同值）。
- **本会话独立复跑**（零真机、纯磁盘只读 + struct 解析）：`python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/n9_erratum_20261108/_er_report_pe.py"` EXIT=0，输出与该件存档**逐字节同哈希**（`ac2d247600ab098c98e042359353e29978cf711f4c83a85881ec472c2bcb1a58` / 6908 B）；镜像同一性：ra2youli/gamemd.exe 与 ra2bench/gamemd.exe SHA256 = `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` / 4825360 B 同值。
- **下游影响（九行清单，N9_SPEC_ERRATUM.md §4.2/§6.1）**：凡引用 P6 处须带「P6 半闭半开」限定——①STATIC_COUNT_SPEC.md :205/:145/:139/:198（勘误主对象）；②_n9_STATIC_COUNT_SPEC.md :81/:109（同语最早载体）；③PERF_REPAIR_HANDOFF.md :139/:161；④_n11_PERF_REPAIR_HANDOFF.md :108/:146；⑤DECISION_QUESTIONS.md :102（Q3 问题原文逐字载体，proposed 待裁）；⑥_n10_D13D14_CARDS_20261108.md :157；⑦F8_VISIBILITY.md :169/:222（引用限定，非疵点）；⑧W8_STATIC_LOCATE.md :162（无需勘误）；⑨STATIC_GAP_CLOSURE/_sc_CLOSURE（反驳承载件，无需加注）。其中 ③④⑤⑥ 为 Q3 授权卡一链四件，涉 N10-C04「静态检索任务的顺序与新写域」——**该待裁状态不变**（PENDING_DECISIONS.md:25），不得以本勘误冒充已裁任务顺序或写域。F8 实现阶段取 [0xB0CD48] 须**改道**：运行期读取，或先闭输入链（0xB0CD78/88/8C 写者与 0x4CACB0 语义，GAP_CLOSURE:101 未做项）。
- **处置**：原件一律不改，保留原表述加勘误注记（N9_SPEC_ERRATUM.md §5.2 E-1 建议处置）；本节即该勘误（erratumCount=1，E-1）的台账入账登记。
- **未验（如实）**：[0xB0CD48] 运行期实际数值（零真机铁律，永久缺口）；0x4CACB0 语义与 0xB0CD78/88/8C 写者未追；capstone 全量反汇编未重演（以原始字节 disp32 扫描替代，12 命中独立证实）。
- 本节**零真机、零采样代码、零上游件改动、未 commit、未 push**。

## ↑↑↑ 草案正文结束 ↑↑↑

---

## 核对记录（不入台账）

- **事实基础**：成立。
- **逐项证据**（本会话实读/实跑）：
  1. P6 行原文 = `lead/static_spec_n9_20261107/STATIC_COUNT_SPEC.md:205`，:198 节题、:139、:145 三处原文均亲读命中（Read 工具，本轮）。
  2. F8V 依据行 = `lead/re_line_20261105/W8_STATIC_LOCATE/F8_VISIBILITY.md:169/:222` 逐字命中（sed 抽行）。
  3. 勘误汇总件全文亲读（N9_SPEC_ERRATUM.md，123 行 + 尾行），其 §3 证据表、§4.1 判定（:63）、§5.2 E-1（:98）、§6.1（:105）与本草案转述一致。
  4. **独立复跑**：`python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/n9_erratum_20261108/_er_report_pe.py" > …\_la_er_pe_rerun_out.txt`，EXIT=0；输出 SHA256 = ac2d247600ab098c98e042359353e29978cf711f4c83a85881ec472c2bcb1a58 / 6908 B，与存档 `_er_report_pe_out.txt` **同哈希**；关键行亲读：`[0x7E1738] double=0.5`、`[0xB0CD48] sec=.data d=0x2FAD48 d>=RAWSZ(0x06C000) -> 文件镜像无字节`、`.data ZEROINIT_TAIL=YES tail_len=0x2FBBE4`、`HAS_INDEPENDENT_.bss_SECTION=False`、`BYT 0x006D1BDD … OK`、`CALL … target=0x004CACB0 OK`、`SCAN raw hits=12`。
  5. 指纹：N9_SPEC_ERRATUM.md、_er_N9_205_P6_B0CD48_ERRATUM.md、STATIC_COUNT_SPEC.md 三件本会话 hashlib 实算与编排方指纹逐位一致（`_la_fpcheck.py` / `_la_fpcheck2.py` 输出）。
  6. 锚点辨析：`lead/NEXT_STEPS_20261106.md` 实测不存在；`lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md` = 27225 B / 135 行（实算），与本笔无关。
- **被核对象绑定**：STATIC_COUNT_SPEC.md SHA256 = 5b933fe2fcb3cc35c5026cb57b45f29da29c90b67a618346af248744ed3ccdb9，字节数 = 32281。
