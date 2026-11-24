Q1 | S口径: BOTH=209 COVERAGE_ONLY=220 RTTI_ONLY=779 合计=1208 全表行=1208 | 列名: class_name/bucket/note（桶名按第2列bucket取值，非文本grep） | 是否与台账一致: 否（台账口径S=397/32/383不在本文件，而在R24 reconcile_final.tsv的S_bucket列；数据行1208/过滤条件bucket列取值/脚本recount.py+recount.ps1）
Q2 | C口径: BOTH=403 COVERAGE_ONLY=26 RTTI_ONLY=377 | 实现规则: 在口径S之上，把coverage token的X_Y/X_Y_Z下划线整体替换为@，与非模板复合TD的X@Y/X@Y@Z做大小写不敏感精确相等，禁止丢段取基名，模板态@不适用；数据行429/过滤条件R24 reconcile_final.tsv的C_bucket列、RTTI_ONLY=988TD−611覆盖=377/脚本recount.py | 或: reconcile.tsv单表未取得（缺decorated_name/compound_TD列）
Q3 | 0x4264C0 @107 不同类=15 ; 全 slot 出现=15 次 / 15 类 | REPORT.md 的「15 项」= 一致（数据行42/过滤条件function_value=0x004264C0且slot=107，全slot=15次15类且仅出现在slot107/脚本recount.py+recount.ps1）
Q4 | 220 可复现? 是（方法=R17_R19_RTTI_XCHECK/reconcile.tsv按bucket列取值=COVERAGE_ONLY，1208数据行得220；脚本recount.py；R24 REPORT.md历史表亦记R19=209/220/779）
Q5 | 正控: 数 口径S BOTH 用两法分别得 397（法A=reconcile_final.tsv的S_bucket列值=BOTH的行数）与 397（法B=同表S_bucket=BOTH行的S_mechanism分组求和 exact209+prefix186+template_base2）⇒ 一致
OVERALL | 成立 — F14两断言从盘上原始数据重算均一致：220可复现；第三版双口径S=397/32/383、C=403/26/377可在R24 reconcile_final.tsv复现（口径S数不在reconcile.tsv，须用R24权威表）；0x4264C0@107实测15个不同类，非17。

## 复算脚本

两个独立实现（不同语言/不同读法）结果逐项一致；均只读源文件、不写源目录。

- `recount.py` — Python 3.12 `csv.reader(delimiter='\t')` + `collections.Counter` 按列取值计数；命令：`python recount.py`。
- `recount.ps1` — PowerShell `Get-Content` + `-split "`t"` + 哈希计数；命令：`& .\recount.ps1`。

读取的源文件（只读，未修改）：
- `R17_R19_RTTI_XCHECK/reconcile.tsv`（表头 class_name/bucket/note；1208 数据行）
- `R17_R24_RECON_FINAL/reconcile_final.tsv`（表头 token/coverage_rows/S_bucket/S_mechanism/C_bucket/C_mechanism/compound_TD；429 数据行）
- `R17_R24_RECON_FINAL/compound_names.tsv`（660 数据行）、`_stage1_compound.json`、`_stage3_buckets.json`、`REPORT.md`
- `R17_R17_SLOT73_MAP/reverse_map.tsv`（表头 function_value/class_name/vtable_va/slot；42 数据行）、`REPORT.md`
- `R17_R19_RTTI_XCHECK/_stage1_td.json`（tdNameRows=988）、`R17_LEDGER_1060/SECTION.md`、`R17_LEDGER_1062/SECTION.md`

## 复算明细（每个数字的 数据行数 / 过滤条件 / 命令或脚本）

**Q1 — reconcile.tsv 直接三桶（R19 第一版口径）**
- 表头/列名：`class_name` / `bucket` / `note`。桶名是第 2 列 `bucket` 的取值（BOTH、COVERAGE_ONLY、RTTI_ONLY），不是把这三个词当文本 grep。
- 数据行 1208（文件 1209 行含表头）；列宽异常 0（每行恰 3 列）。
- 过滤条件：`bucket == 'BOTH'` → 209；`bucket == 'COVERAGE_ONLY'` → 220；`bucket == 'RTTI_ONLY'` → 779。
- 三桶合计 209+220+779 = 1208 = 全表数据行数（相等）。
- 判定：与台账口径 S（397/32/383）**不一致**。原因：reconcile.tsv 是 R19 第一版（大小写原样精确比对），口径 S 是 R24 第三版（大小写不敏感裸名 + 前缀 + 模板基名）。台账本身已注明 R19=209/220/779 为作废旧版。

**Q2 — 口径 C 的实现与三数**
- 口径 S/C 权威数在 `R17_R24_RECON_FINAL/reconcile_final.tsv`（429 数据行，分母为 429 个 coverage token）与 `_stage3_buckets.json`。
- 口径 S：大小写不敏感裸名精确相等 + 保留已审过的 P/A/V 前缀 + 模板基名键，不接受下划线取段。S_bucket 列：`BOTH`=397、`COVERAGE_ONLY`=32（合计 429）。RTTI_ONLY 分母为 988 TD 条目：988−605(覆盖)=383。
- 口径 C：S 之上加显式复合名匹配——coverage token 的 `X_Y`/`X_Y_Z` 下划线整体替换为 `@`，与 `compound_names.tsv` 中非模板复合 TD 的 `X@Y`/`X@Y@Z` 做大小写不敏感精确相等，禁止丢段取基名，模板态 `@` 不适用。C_bucket 列：`BOTH`=403、`COVERAGE_ONLY`=26（合计 429）。6 条新增覆盖 TD（INIEntry@INIClass、INISection@INIClass、RTacticalClass@RadarClass、SBGadgetClass@SidebarClass、SelectClass@StripClass@SidebarClass、TacticalClass@DisplayClass）使 RTTI_ONLY 383→377（988−611=377）。
- 复合名规模：compound_names.tsv 660 条（模板 634 + 非模板 26），与台账「复合名 660」一致。
- 从 reconcile.tsv 单表无法机械实现口径 C：其列（class_name/bucket/note）既无 RTTI 装饰名（decorated_name）也无复合 TD 匹配结果列（compound_TD），缺这两列，故单表记为未取得；三数改由 R24 权威表取得。
- 判定：403/26/377 与台账口径 C 一致。

**Q3 — 0x4264C0 的类数**
- 源文件 reverse_map.tsv，42 数据行。过滤条件 `function_value == '0x004264C0'`。
- 全 slot：出现 15 次，涉及 15 个不同类；使用的 slot 集合仅 `{107}`（无 slot 73 行）。
- 再加 `slot == '107'`：15 行，15 个不同类。
- 与 `R17_R17_SLOT73_MAP/REPORT.md` Q1 的「`0x004264C0`（15 项）」分组逐条比对：15 个类名完全一致（AnimClass、BuildingLightClass、BulletClass、IsometricTileClass、MissionClass、ObjectClass、OverlayClass、ParticleClass、ParticleSystemClass、RadioClass、SmudgeClass、TechnoClass、VoxelAnimClass、VeinholeMonsterClass、WaveClass）⇒ 一致。
- 「17 vs 15」差在哪：§1060 卡面原称 17 个类，盘面 reverse_map.tsv 与报告 Q1 实测均为 15；全 slot 也只有 15 次/15 类，没有额外 2 个类可补出差额 2。台账 §1060 SELFCHECK 与 §1062 事项 5 均已把 15 列为实测值、17 列为卡面值并列。F14「实为 15」成立。

**Q4 — 220 的来源**
- 220 = R19 `reconcile.tsv` 中 `bucket == 'COVERAGE_ONLY'` 的行数（1208 数据行过滤得 220）。
- 旁证：`R17_R24_RECON_FINAL/REPORT.md` Q2 历史表「R19 | 209 | 220 | 779」；§1061/§1062 均记 220 为已被取代的旧值。
- 故 220 可复现，且确为 R19 第一版残片口径（大量 .?AV 切分残片），非现行结论。

**Q5 — 正控**
- 选数：口径 S 的 BOTH=397（Q1b 已确认可复现）。
- 法 A：`reconcile_final.tsv` 第 3 列 `S_bucket` 值等于 `BOTH` 的行数 → 397。
- 法 B：同表按 `S_mechanism` 对 `S_bucket==BOTH` 的行分组求和 → exact 209 + prefix 186 + template_base 2 = 397（换了列 + group-by，独立于法 A 的直接行数）。
- 两法结果相同（397=397）⇒ 正控通过。
- 补充正控：R19 BOTH=209 也用两读法核对——Python `csv` 按 bucket 列取值 = 209，PowerShell 原始文本 `split "`t"` 取第 2 列 = 209，一致。
