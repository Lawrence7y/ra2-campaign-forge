# LEAD_SIGNOFF_BATCH · W38 + W41 + W42（B 线与 CSF 三卡合并签发）

> 签发人：Lead（本会话）｜ 日期：2026-11-13 19:32
> 三卡互相咬合：W38（B 线 S1 契约）→ W42（B 线 S2 契约，消费 S1）→ W41（CSF 接入安装，独立实现）

---

## 1. W41 · CSF 纳入安装/卸载（v12）—— **签发**

`lead\next_re_20261112_r02\W41_csf_install\`（765 文件）

| 检查 | 我的结果 |
|---|---|
| `python -B -X utf8 regress_dlc_v12.py` | **57 cases / 57 passed / 516 assertions / 0 failed / exit 0**（**Lead 亲自复跑**） |
| 用例构成 | 既有 51（含 W26 的 39 + W30 的 CSF1–6 + W34 的 MS1–6）全保留，新增 `CSF_INST1..6` |
| 向后兼容 | `out\SHA256_COMPAT.txt`：不启用 CSF 开关时 v11 vs v12 的 8 个产物**全部 MATCH**（BATTLEMD98.INI / BUILD_REPORT.txt / CP1.MAP / CP2.MAP / INSTALL.txt / expandmd98.mix / ra2forge_package.json / story.md） |
| `verify.py` | `[转引]` 未改（v12 起始自 v11，v11 的 verify 与 v10 逐字节相同，我此前已验） |

`[签发]` v12 的 CSF 接线成立：纳入 `package_files()`/清单/备份/卸载还原、`original_absent` ⇒ CREATE→DELETE、完整性门禁、`--csf-out` 落游戏目录的守卫。

**文件级事实（W41 收尾消息，`[转引]` 我未逐个哈希复核）**
- `ra2forge_patched_v12\ra2forge\`：**14 个 `.py`，无新增模块**；仅 4 个 MODIFIED（`csf.py` / `builder.py` / `cli.py` / `install.py`）；其余 9 个 IDENTICAL；`TOOL_VERSION="1.0"` 未动
- `verify.py` **逐字节未改**（`051C2E21…`）——与我此前从 v10 起的观察一致
- 新增数据：`data\RA2MD.OFFICIAL.CSF`（332,973 B、`1b90bb07…`、从 `langmd.mix` 只读提取）+ `data\RA2MD.OFFICIAL.LABELS.txt`（5,211 官方标签名）
- 守卫实体：`CsfIncompleteError` / `official_baseline_labels()` / `load_official_csf()` / **`assert_complete_csf()`**（strict parse、version==3、头部计数自洽、值类型仅 ` RTS`/`WRTS`、无 warnings/unknown/尾余、**标签名集合 ⊇ 5,211 官方基线**）
- **未加** `--allow-partial-csf`（遵循我的「不建议」）；最小 CSF 路径已从构建链路删除
- `--allow-csf-out-in-game` 为显式逃生口，**默认关闭**，且仍做身份判定并在 BUILD_REPORT 打 `[WARN]` 明示「绕过清单 ⇒ uninstall 不删（W21 孤儿风险）」

`[必须改口一处]` 我给 W41 的任务卡里写的理由是「最小 CSF **会启动失败**」——**该理由已被 W40 真机推翻**（A 臂：115 B 最小 CSF → 正常启动 19.34 s）。守卫**本身正确**（该拒最小 CSF），但**理由要改成**「防止官方 UI 文本全变 `MISSING:'…'`」。
`[已发生]` W41 在其 `DISAGREE.md` 里把理由写成「散装部分 csf 会启动失败」——**沿用了我给错的理由**。⇒ 后续任何引用都要按本条改口；W41 的实现不需要改，**只有措辞要改**。

`[我认可的一个取舍]` 「安装时发现非我方 `ra2md.csf` ⇒ **never-releasable**（连 `--allow-content-conflict` 也不释放）」。
理由：CSF 是**整文件注册**（与 `MAPSELMD.INI` 同构），静默合并会打断别人的文案；代价是多包共存不可用（已在其 `UNCOVERED` 列出）。这与 W34 对 `MAPSELMD.INI` 的处理一致，**口径统一**。

---

## 2. W38 · B 线 S1（版本守卫契约 + 写入口盘点）—— **签发，附一条改动授权**

`lead\next_re_20261112_r02\W38_version_guard_s1\`（31 文件，6 主件）

| 交付 | 我的评价 |
|---|---|
| `VERSION_GUARD_CONTRACT.md` 37 KB | 13 条判据 + L0–L3 分层 + 三态×7 写入口决策表 + R1–R12 降级 + JSON Schema + 21 格机器决策表。**结构可用** |
| `WRITE_ENTRY_AUDIT.tsv` **80 行** | 43 个 v11 直接写点 + 25 个 `[CALLER]` 间接 + 9 个 `XCHAIN:` ra2opt 补充 + 2 说明行。**这是 S1 最硬的产出** |
| `ACCEPTANCE.md` 12 条 | A1–A12，全部 `[待运行验证]`，未实现（正确） |
| EVIDENCE 8 脚本 | 只读审计，exit 全 0；`gen_write_audit.py` 首跑 exit 1 后修正并留档 |

**三条我采纳的硬事实**
1. `[本次实测]` **v11 全包 0 处构建身份判定**；唯一守卫是 `install.py:1140` 的 `gamemd.exe` 存在性；`uninstall` 只有 `is_dir()`（`install.py:2184`）；`verify` 明写不需 `gamemd.exe`。
2. `[本次实测]` `_read_package_identity()` / `_write_package_identity()` 是 **PKG-IDENT01 包身份**，不是构建身份 —— 这个区分很重要，我此前差点混淆。
3. `[本次实测]` **最高风险写入口**：`build --csf-out PATH`（`builder.py:434-437` + `cli.py:140-146` 原样传参）**直写任意用户路径、零守卫**。若落在游戏目录内即等价 install 级写入。另 `cli.py:283` 的 `example` 同样无守卫。

**改动授权（回应 W42 D1）**：我授权 **S3 在同一个补丁内修订 S1 的 `E1 KNOWN_GOOD` 允许清单，加入 `ra2md.csf`**，并同步 `guard_decision_table.json`。理由见 `LEAD_DECISIONS_W42.md` D1（W40 已证散装 CSF 覆盖成立、合法即启动、只有坏魔数才不启动）。

---

## 3. W42 · B 线 S2（feature-set → 文件子集契约）—— **签发**

`lead\next_re_20261112_r02\W42_b_line_s2\`（18 文件，6 主件 + 12 EVIDENCE）

| 交付 | 我的评价 |
|---|---|
| `FEATURE_SUBSET_CONTRACT.md` 30 KB | 5-feature 模型 + `shipped()` 纯函数 + CREATE/REPLACE/LEAVE + `original_absent` + 确定性组合表 F0–F6/N1–N6 + K1–K12 耦合 + 与 S1 组合规则 + G4 公式 + **§9「契约完备≠能力已具备」差距表** |
| `FEATURE_SUBSET.schema.json` | 23 个 `$defs`、root `oneOf` 5 类。**分工正确**：schema 只校验形状，语义拒绝放 `coupling_rules.json` —— 否则 3 个负例无法作为输入被表达 |
| `ACCEPTANCE_S2.md` **17 条** | B1–B17，三个题面负例齐备（B8 最小 CSF 拒绝 / B9 非完整 MAPSELMD 拒绝 / B10 开 CSF 未开耦合项拒绝），B14/B15 覆盖与 S1 三态组合 |
| `BASELINE_ADJUDICATION.md` | **判定程序而非结论**：R-A/R-B 两轨、P0–P6、`.detour` D1–D5 字节判据、G1–G6 六门；未实算任何哈希（正确） |
| 自检 | `s2_shape_check.py` **64 PASS / 0 failures / exit 0**，只证规格自洽，未跑 build/install/regress |

**我采纳的两条关键读码事实**
1. `[本次实测]` **v11 的 CSF 侧没有完整克隆门禁**：`append_or_set_label(create_if_missing=True)`（`csf.py:442-466`）+ `builder.py:431-437` 会生成只含 1 个标签的最小 CSF；全包 grep `5211` 零命中。⇒ B8 是**契约新增门禁**，S3 之前必然 FAIL，**不得写成「v11 已拒绝最小 CSF」**。
   > **【2026-11-13 22:33 更正，来源=`LEAD_VERIFY_W43.md:32,39` + 本节 §1】范围限定：这条只对 v11 成立，对 v12 不成立。** W41 交付的 v12 已实现 `assert_complete_csf()` + `require_complete=True`（见本节 §1「守卫实体」），即**门禁已落地，只是当时我引用的理由写错了**。引用本条时必须带 v11/v12 版本限定。
2. `[本次实测]` MAPSELMD 侧 `validate_official_base()`（`mapselmd.py:142-184`）**已实现**（14 阶段 / 5573 B / `074ccccd…` / 1..7 键 / `Scenario=`）—— 两侧能力**不对等**，S3 要把 CSF 侧补齐。
3. `[本次实测]` `LEAVE` ≠ v11 `action="unchanged"`（`install.py:1290-1301` 会 adopt 未登记同字节文件、后续卸载删）。

**4 项待裁已全部裁决** → `REVIEW\LEAD_DECISIONS_W42.md`（D1 修 S1 允许清单 / D2 `.detour` = `westwood_native` / D3 G3 不补硬拒绝改警告 / D4 维持 `is_clean_retail_gold: const false`）。

`[附：我实测复核的一条]` `.detour` 段：VAddr `0x00793000`、VSize `0x2718`、RawOff `0x00497000`、`Characteristics = 0xC0000040` = MEM_READ|MEM_WRITE|CNT_INITIALIZED_DATA，**无 `MEM_EXECUTE`**（对比 `.text` = `0x60000020`）。与 `westwood_native` 裁决一致。

---

## 4. B 线的真实状态（别把三份契约读成能力）

`[签发]` **B 线零实现。** 现有：S1 契约 + 80 行写入口盘点 + S2 契约 + 17 条验收断言 + BASELINE 判定程序。
`[未达成]` 版本守卫未接线、`resolve()` 未实现、G3 警告通道未实现、`TRACK_B_gates.json` 未产出、`BASELINE.json` 未实算。
> **【2026-11-13 22:33 更正】原句里「csf 完整性门禁未实现」一项删除**：W41 的 v12 **已实现**（`assert_complete_csf()` + `require_complete=True`，见 §1）。与本节 §3 第 1 条的更正同源。
`[红线]` 三卡的"自检全绿"（W41 57/57、W38 shape、W42 64 PASS）**都不等于**行为正确或守卫已具备。
