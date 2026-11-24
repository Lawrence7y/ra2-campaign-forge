# RECON-UNMERGED · 只读完整性核查（P3 交叉收口）

卡号 RECON-UNMERGED｜2026-11-19｜`ra2youli\gamemd.exe` 只读，现场复算 SHA-256 `73201CC0…F67476`、ImageBase 0x400000 ✅｜Python 3.12.10 + capstone 5.0.7（skipdata=True）+ pefile 2024.8.26；未建 venv / 未 pip install / 未改游戏文件 / 未改 COVERAGE / 未改台账 / 未改 R14_COMMON.md / 未改 STATUS_BOARD / 未交 delta / 未 git commit。写域仅本目录。
## 裁定

**铁规未被破坏。违规行数 = 0。** 26 张卡：**A 类 9 张 / B 类 17 张 / C 类 0 张**。已落盘 143 行全部能追到异族审计裁决；未落盘 76 行盘上仍是原值（B 类，被挡在本卡之外）。
## 逐卡判定（详见 `CARD_VERDICTS.tsv`；逐行 `EVIDENCE\timeline_rows.tsv`）

| 卡 | 行 | 并入 | 判 | 依据 / 挡因 |
|---|---|---|---|---|
| S01_KPROVED | 0 | 0 | B | 仅表头 + 注释 `# 0 data rows` |
| S03_C8 | 0 | 0 | B | 仅表头 |
| S05_KPROVED4 | 3 | 0 | B | 3 行 grade 仍 [静态推断]、语义未落盘 |
| S05_KPROVED5 | 0 | 0 | B | 仅表头 + `# 0 data rows` |
| S05-K2 | 24 | 0 | B | 语义 0/24 落盘 |
| S07-K2 | 2 | 0 | B | 语义 0/2；00551A30 仍 [未证] |
| S09_KPROVED2 | 7 | 6 | **A** | a-S09-KPROVED2 PARTIAL（共享 `_audit\VERDICT.md`，白名单 6 行、0069DEB0 黑名单）→ M40 并 grade；语义后由 M42 落盘 |
| S10_K11 | 2 | 2 | **A** | a-S10-K8 判两行 ✔ + a-S10-K8F PASS 明令 R1/R2 改字 → M11 仅改措辞、grade 未变（见「过程瑕疵」） |
| S10_K14 | 1 | 1 | **A** | M16 并 name+语义（删编造表/幽灵被调）；M41 以 S10_KPROVED2/_audit/VERDICT.md#18 升 [已证] |
| S10_KPROVED4 | 0 | 0 | B | 仅表头 |
| S11_DIRECT | 8 | 0 | B | 语义是 delta 从盘上抄的（早于 delta mtime 11h 出现），grade 仍 [静态推断] |
| S11_K5 | 11 | 0 | B | 语义 0/11 落盘 |
| S13_DIRECT | 0 | 0 | B | 仅表头 |
| S13_K11 | 9 | 0 | B | grade 仍 [静态推断]、语义 0/9 |
| S13_KPROVED2 | 0 | 0 | B | 仅表头 |
| S15_K5 | 0 | 0 | B | 0 字节空文件 |
| S16_N2 | 0 | 0 | B | 仅表头 |
| S19-K2 | 18 | 0 | B | grade 仍 [静态推断]/[未证]、语义 0/18 |
| S21_KPROVED2 | 0 | 0 | B | 仅表头 |
| SEMFIX_6 | 6 | 6 | **A** | AUDIT_SEM_SELF/ROW_VERDICTS.tsv 6/6 判 P1 → M36 |
| SEMFIX_REST | 41 | 41 | **A** | AUDIT_SEM_SELF 41/41 判 P1 → M35（仅改语义，grade 未变） |
| SEMFIX_S10 | 25 | 25 | **A** | AUDIT_SEM_SELF 25/25 判 P1 → M35（仅改语义，grade 未变） |
| SEMFIX_SLOTS | 36 | 36 | **A** | grade：M37(a-S08-KPROVED2 6)/M40(S03_C5 3 + a-S09-KPROVED2 5)/M41(S09_KPROVED3 4 + S10_KPROVED2 8)；语义：M42。36/36 有审计出处 |
| SEMFIX_SLOTS2 | 11 | 11 | **A** | a-S03_C6 4 + a-S10_KPROVED3 7 → M44（组1并入，逐行 cite VERDICT） |
| SEMFIX_SLOTS3 | 15 | 15 | **A** | a-S05_KPROVED3 7 + a-S09_KPROVED5 8 → M45（M44 曾「组2拦下」拒绝提级，未越权） |
| W177_KA | 0 | 0 | B | 0 字节空文件 |
## 违规清单

**空（0 行）**：`VIOLATIONS.tsv` 只有表头 + 一行显式无违规说明，无任何 entry 行。
## 正负对照

1. **正对照（已知 A）SEMFIX_SLOTS3**：15 行在 M45 MERGE_LOG **15/15 命中**，basis 明写 `S05_KPROVED3/_audit/VERDICT.md（白名单7行）`+`S09_KPROVED5`，7+8=15 恰等于 delta 行数；SEMFIX_SLOTS2 亦 11/11 命中 M44 ⇒ 方法能识别 A 类。
2. **负对照（已知 C 候选）S10_K11**：两行**仍在盘上**（语义与 delta 逐字符相同）。但 **grade 非本卡授予**——[已证] 在 M10_before 快照即为 [已证]。查得**确有审计**：a-S10-K8 L13-14 判 `004DFCB0 ✔` / `004DFE00 ✔`；a-S10-K8F L20-21 残留 R1/R2 明令改字，同文件裁决 **PASS** 并写「R1/R2 改字即可，无需回退或降级任何行」。时序 VERDICT 05:41 → delta 05:45 → M11.bak 05:57 ⇒ **审计指令先于并表**，非「先并入后补审」。按「行有无审计结论」判 A。
   **过程瑕疵（如实登记）**：S10_K11 自身无 `_audit\VERDICT.md`；台账 §999 已按「无审计 ⇒ 只写措辞修正、grade 未变」登记为**例外**。若铁规按「每卡自身必须有 VERDICT」读，此项应改判 C（1 卡 / 2 行）——本卡按行级口径判 A，分歧挂 `UNKNOWNS.md` U1 待 Lead 裁。
3. **反向核**：S09_KPROVED2 的审计**不在**卡目录而在共享 `_audit\VERDICT.md`（BOARD_ARCHIVE:2494 登记的写域偏离）——只查卡目录会误判为 C，本卡按内容核实为 PARTIAL。
## 方法自证（可复跑）

1. 基线（`EVIDENCE\baseline.txt`）：coverage.tsv 18,432 行/数据 18,431/字段数全 8/entry 唯一 18,431/重复 0；表头逗号、数据 TAB；grade 直方图 1460+5947+11024=18,431。atlas 12,917 行/12,916 数据行 ✅。
2. **`.bak` = 合并前备份**，在 `EVIDENCE\snapshot_map.txt` 用三条已知并表记录单点证明（0040F0A0 旧值留到 M36.bak、新值首现 M37.bak ⇒ 由 M36 并入；0047AE10 同理 M44；006F3330 同理 M45）。故「变迁首现于 M(N+1).bak ⇒ 由 M(N) 并入」。
3. 判「被并入」不靠 grade 相等，用四证据：①盘上语义/grade 与 delta 逐字符比对 ②语义串在 **41 个快照点**（`_hygiene` 备份 40 + 当前盘面）上首次出现的时点 vs delta 文件 mtime（堵反向因果：S11_DIRECT 语义早于其 delta 11 小时出现 ⇒ 判搬运、未并）③MERGE_LOG 登记 ④台账 §999/§1018。
4. 归属：扫 M22–M48 `MERGE_LOG.tsv`（8 种表头 schema，3/4/7/8 列不等）与 M2–M5 `REPORT.md`，共 48 个来源；`EVIDENCE\merge_records.txt` 给 9 张 A 类卡逐行登记。
5. 审计存在性：全树 **142 份 `VERDICT.md`** + `AUDIT_SEM_SELF\ROW_VERDICTS.tsv` 逐 entry 反查（`EVIDENCE\audit_coverage.tsv`）。关键：a-* 审计卡裁决可能落在**共享 `_audit\`**，不能只查卡内。
6. 脚本链：`work\recon.py`→`recon2.py`→`recon3.py`→`recon4.py`→`final_verdicts.py`；证据 `gen_evidence.py`/`gen_controls.py`/`gen_merge_records.py`；原始输出 `work\*.json`、`work\*_out.txt`。
## 核心数字（给审计）

- 26 卡 delta 合计 **219 行**；已落盘 **143 行**；未落盘 **76 行**；**违规 0 行**。
- A/B/C = **9 / 17 / 0**。
- 规则引用：`R14_CARDS.md` L184（M 卡输入仅限 PASS/PARTIAL 卡的 delta）、L120（正文只收审计 PASS 的结论）；`AUDIT_SEM_SELF\CARD.md`（只读测量卡，逐行 P1/P2/P3）。
