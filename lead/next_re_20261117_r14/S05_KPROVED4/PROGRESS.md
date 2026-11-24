# S05-KPROVED4 · PROGRESS

卡号 S05-KPROVED4（agent-41）。目标 `ra2youli\gamemd.exe` 只读，SHA-256 `73201CC0…F67476` 现场复核一致。
写域仅 `lead\next_re_20261117_r14\S05_KPROVED4\` 与 `lead\next_re_20261117_r14\_ghidra\S05_KPROVED4\`（-noanalysis）。
未写 COVERAGE/台账/R14_COMMON/STATUS_BOARD/ra2youli/其它卡目录/_audit；未建 venv、未 pip install、未改 coverage.tsv、未 git commit。

## 开工必读（已读）
R14_COMMON §1/§6/§7/§8.1/§8.5/§8.6 六条/§8.7 九条；D-40/41/42（PENDING_DECISIONS + §8.6）；SURVEY_RING24\PROGRESS.md；
a-S05-KPROVED3\VERDICT.md（00704350 回退理由）。

## 行源与排除
S05 A 集合 A=41（q8_pool.json A_list，SURVEY_RING24 主口径 S05 A=41）。
排除集 16 行 = S05_KPROVED2(8)：00413F80/006F4AB0/006F6AC0/0070C270/007077C0/00716DC0/007162F0/00700600；
S05_KPROVED3(8)：006F3330/006F8DF0/006FC0B0/006FFEC0/00704350/0070BF50/00712170/00716150。
剩 25 行 + 回退行 00704350 = 26 候选，选 8 行处理（00704350 必做）。

## 8 行处理结果
| entry | name | ②持有表/⑯ | ③b | ④站点 | delta |
|---|---|---|---|---|---|
| 00704350 | TechnoClass::slot187 | 1 表 TechnoClass | 未成立（回退链，维持[静态推断]） | 004DB08C | 否 |
| 006FFBE0 | TechnoClass::slot222 | 5 表同槽→基类 TechnoClass | ③b① 互斥闸异 callee | 00417CB4 | 是 |
| 00703860 | TechnoClass::slot26 | 1 表 TechnoClass | ③b② 返回码{0..5} | 004545C3,004DA519 | 是 |
| 005F9950 | ObjectTypeClass::slot6 | 1 表 ObjectTypeClass | ③b② 负返回透传 | 10 站点 | 是 |
| 006F3F40 | TechnoClass::slot9 | 2 表→基类 TechnoClass | ③a 顺序惰性构造 | 5 站点 | 否 |
| 005F9720 | ObjectTypeClass::slot5 | 1 表 ObjectTypeClass | ③a 析构清零 | 10 站点 | 否 |
| 007171A0 | TechnoTypeClass::slot13 | 1 表 TechnoTypeClass | ③a 线性序列化 | 4 站点 | 否 |
| 006F6CA0 | TechnoClass::slot54 | 1 表 TechnoClass | ③a 线性初始化 | 2 站点 | 否 |

## 核心数字
- 8 行中四环齐全数 = **3**；自报并入 = **3**；delta 行数 = **3**（判据7 ✓）。
- S05 A 集合总行数 = **41**。
- ③b 基率（seed 20261119 / 2000 次 / 池=S05 `[静态推断]` 387 行）：
  strict **0.235142 (91/387)**、loose **0.379845 (147/387)**；MC 均值 1.8365 / 2.9975。
  审计独立更严口径 strict 0.188630 / loose 0.291990，已在 DISAGREE D2 并列。
  K=N·p、E[8]=8·p 为恒等式非校验（M3）。

## 纪律自检
① 16B 对齐 + 前驱 ret/nop 全 8/8；② 全表枚举 1214 表，持有表逐字 COL→TD+8 与 name 类一致；
③b 入口相对偏移已逐条与 EVIDENCE 核对（M5 全通过）；④ 68253 指令边界 E8 全扫，站点体外/非自环；
one_line_semantics 无自陈未证（M8）；②栏类名=name类（M2）；多表同槽归基类级（错源⑯/M1）。
00704350 维持 [静态推断] 不凑（D1）。

## 交付
PROGRESS.md / UNKNOWNS.md / DISAGREE.md / coverage_delta.tsv(3 行) / EVIDENCE(ROW_00704350/006FFBE0/00703860/005F9950/006F3F40/005F9720/007171A0/006F6CA0.txt + ROW_SUMMARY.json + baselines.json) / work(可复跑脚本)。
