# LEAD_VERIFY_W43 · B 线 S3（实现 + 回归）签发

> 签发人：Lead（本会话）｜ 日期：2026-11-13 20:25
> 卡：**W43**（Hy4）`lead\next_re_20261112_r02\W43_b_line_s3\`（892 文件；`S3_IMPLEMENTATION.md` 24,881 B / `APPLY.md` / `DISAGREE.md` 12,394 B / `UNCOVERED.md` 8,189 B）

---

## 1. Lead 亲自复跑（不采信其汇总）

| 检查 | 我跑出来的结果 |
|---|---|
| `python -B -X utf8 regress_dlc_v13.py` | **82 cases / 82 passed / 714 assertions / 0 failed / exit 0** ✅ |
| 用例构成 | **继承 v12 的 57 例逐例保留**（`P0/V1-6/P1-4/C1-2/T4/S1-8/F0-7/U1-6/R0-2/CSF1-6/MS1-6/CSF_INST1-6`）+ 新增 `S3_1..S3_25` |

`[说明]` 我中途两次读到 `cases: 1`/`cases: 25`、`inherited v12 cases: 0`、以及 `22/25 3 失败` —— 那是它**迭代过程中瞬时刷新的 SUMMARY**，不是最终态。最终态与我的复跑一致：**82/82**。
`[教训]` 监控在跑卡的 `SUMMARY.txt` 这类**每例覆写**的文件会读到假状态。判断完成度要看「有没有完成通知」+「文件 mtime 是否停止」，而不是读一个会被覆盖的汇总文件。

## 2. 五项裁决的落地（逐条核对交付声明）

| 裁决 | 落地 | 我认可 |
|---|---|---|
| **D1** 修 S1 的 E1 允许清单，加入 `ra2md.csf` | `data/E1_KNOWN_GOOD.json` + `data/guard_decision_table.json` 新增 | ✅ |
| **csf 完整性门禁 + 理由改口** | `csf.py` 改 `assert_complete_csf` 的理由串（保留 `PARTIAL` 关键字以兼容 57 例）；封死 `append_or_set_label(create_if_missing=True, require_complete=False)` 造最小 CSF 的真实缺口 | ✅ **且明确写了「理由中不含『最小 CSF 会启动失败』」** |
| **D2** 版本守卫显式 opt-in | `--version-guard <fixture.json>`，默认路径零改动 | ✅ |
| **D3** K2 硬拒绝 / G3 只警告 | K2 保留硬拒绝，G3 走 `warnings[]` | ✅ |
| **D4** `TRACK_B_gates.json` 独立工件 | 已产出；`is_clean_retail_gold: false` | ✅（我未逐字段核） |

`[新增模块]` `feature_subset.py` / `version_guard.py` / `s3_contract.py` + `data/E1_KNOWN_GOOD.json` + `data/guard_decision_table.json`；改 `builder.py` / `cli.py` / `csf.py` / `install.py` 四个。

## 3. 三条它自己指出、我认可的关键事实

1. **`[本次读码]` v12 其实已有完整性门禁**（`assert_complete_csf` + `require_complete=True`），W42 签发里「v11 无完整克隆门禁」这句**只对 v11 成立、对 v12 不成立**。真实仍开的缺口是低层原语 `append_or_set_label(create_if_missing=True, require_complete=False)` 能从零造最小 CSF —— S3 封死它。这条更正我采纳（我在 `LEAD_SIGNOFF_BATCH` 里引用了 W42 的那句，需按此修正）。
2. **`[静态推断]` 版本守卫必须 opt-in**：S1 规定「无已定谳 `BASELINE.json` ⇒ UNKNOWN ⇒ 零写拒绝」，而 v12 的 57 例沙箱里 `gamemd.exe` 是 `INERT PLACEHOLDER - NEVER EXECUTED` 文本、**非 PE** ⇒ 默认启用会让 57 例全落拒绝，且破坏「不开开关时逐字节相同」。
   ⇒ `[我要记住的结构性限制]` **测试夹具用假 `gamemd.exe`，所以身份守卫在标准夹具里永远无法正向通过**。守卫"能拒绝"可用负例证，"能放行"只能用 `--version-guard` 指向合成 fixture 证。**不得写成「守卫已验证」**。
3. **G3 与 K2 的可达性张力**（它先发现、我随后澄清）：在 `battlemd.mode=off` 时 K2 已硬拒绝，G3 的警告不可达。我已在 `LEAD_DECISIONS_W42.md` D3-补 裁决：K2 硬拒绝保留，G3 活例子收窄为「maps + mapselmd 开、battlemd 关、csf 关」。

## 4. 我自己要改口的一处

`LEAD_SIGNOFF_BATCH_W38_W41_W42.md` §3 里我引用了 W42 的「**v11 的 CSF 侧没有完整克隆门禁**」。按 W43 的读码：这句**对 v11 成立、对 v12 不成立**（v12 已有 `assert_complete_csf`+`require_complete=True`）。我在此更正——**W41 已经做了门禁，只是理由写错**。

## 5. B 线现在的真实位置

`[签发]` **B 线已有实现，但仍不是"能力具备"**：
- ✅ 版本守卫**已接线但 opt-in**（`--version-guard`），默认路径零改动
- ✅ feature-set → 文件子集 `resolve()` 已实现，S2 的三个负例（B8/B9/B10）可拒
- ✅ csf 完整性门禁已封死底层原语
- ✅ G3 警告通道
- ✅ `TRACK_B_gates.json` 独立工件
- ❌ **行为等价性验证（RE-N09 第 2 项）仍未做** —— 这是 B 线的核心承诺，需要真机双轨对照
- ❌ `BASELINE.json` 未实算（W42 只给了判定程序）
- ❌ 守卫在真实镜像上的**正向通过**未验证（夹具是假 exe）
- ❌ `TRACK_B_gates.json` 我未逐字段核

`[红线]` **82/82 全绿只证明"文件层 plan/guard 行为"，不证明真机行为、也不证明守卫已普遍启用**（它自己在 SUMMARY 里就这么写的，我认可这个自我限定）。

## 6. 未复核项

- `TRACK_B_gates.json` 字段
- `DISAGREE.md` 12 KB / `UNCOVERED.md` 8 KB 我只读了被引用处
- `SHA256_COMPAT_V13_V12.txt` 我未逐行核（它在 S3_COMPAT 用例里，而该用例在我复跑中 PASS）
- `__pycache__/*.pyc` 出现在 `V13_SOURCE_DELTA.json` 的 `added` 列表里 —— 属打包卫生问题，**不影响功能**，但交付时应清理
