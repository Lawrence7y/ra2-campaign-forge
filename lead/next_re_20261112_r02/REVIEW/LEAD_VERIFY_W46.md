# LEAD_VERIFY_W46 · B 线 resolve() 集成（v14）签发 + 一个被证实的 CLI 缺陷

> 签发人：Lead（本会话）｜ 时间：2026-11-13 21:22
> 卡：**W46**（Hy4）`lead\next_re_20261112_r02\W46_resolve_integration\`

---

## 1. Lead 亲自复跑

| 检查 | 我的结果 |
|---|---|
| `python -B -X utf8 regress_dlc_v14.py` | **90 cases / 90 passed / 807 assertions / 0 failed / exit 0** ✅ |
| 用例构成 | 继承 v13 的 **82 例逐例保留**（含 57 继承 + S3_1..S3_25）+ 新增 `S4_1..S4_8` |

## 2. 三项落地（我认可的核心）

- **G-7 `resolve()` 串进真实写路径**：`install` 写盘前跑 `resolve()`，三道门 = 写前包子集门 + 写前逐文件 plan/actual 对账 + **写后字节级复核**（不一致落入 v13 既有 `_rollback()`）；`build` 在 `out.mkdir()` **之前** 跑。不一致 ⇒ `PLAN_ACTUAL_MISMATCH` / **exit 24 + 零写**（`sha_tree` 前后逐字节证）。
  新增退出码 **24–31**，不占用 v13 的 0–10 与 W38-S1 的 20–23 —— 这个分配纪律是对的。
- **G-8 二次安装语义定谳**：同 `package_id` + 同 `feature_set_id` + 无 drift ⇒ **`IDEMPOTENT_REPLAY`**（允许、但游戏目录**零字节写入**，连清单/seal 都不刷新）。其余数据化为 FRESH / SUBSET_UPGRADE / LEGACY_PRE_PLAN / DIFFERENT_PACKAGE。
  orphan ⇒ **exit 27 零写**（v13 会 adopt，v14 拒绝）；legacy 无 `feature_set_id` ⇒ **exit 28**，须 `--adopt-legacy`；子集缩小时 v13 的 ORPHAN-FIX01 删除显式建模为 `ORPHAN_CLEANUP:<mode>`，**不算 LEAVE** —— 这个区分很关键（`LEAVE` 应是严格零触碰）。
- **G-9 `battlemd:inplace`（按裁决 D5.2 暂缓）**：不实现写侧；纯规划器与 `resolve` 子命令**逐字节未改**，仍能表达该 mode；`MODE_RESERVATIONS["battlemd:inplace"]` 数据化预留槽；`run_resolve()` 是唯一明确拒绝点 ⇒ `BATTLEMD_INPLACE_REFUSED` / **exit 25**，install/build 两端零写；`S4_7` 12 条断言钉死。

## 3. 向后兼容与卫生

- `[转引]` 不启用新开关时 v14 默认构建 vs v13：**8 产物 8/8 SHA-256 MATCH / VERDICT IDENTICAL**
- `[转引]` 源码 delta：**3 改 + 1 增 + 0 删**；`verify.py`/`feature_subset.py`/`csf.py`/`s3_contract.py`/`version_guard.py`/`mapselmd.py` + 两份 data 与 v13 逐字节相同；`uninstall()`/`package_files()`/`_write_step()`/`_rollback()` 函数体一致
- `[本次实测]` **无 `__pycache__` / `*.pyc`**（W43 有这个卫生问题，本卡 0 个）—— 派卡时点名要求，做到位了

## 4. 它守住的三个口径（我认可）

1. **未写「B 线已完成」**；真机行为等价性明确归 W45
2. **未沿用 W43 的「进程数 0」措辞**，改为逐次留痕「W46 launched 0 / attached 0、未触碰」，并把观察到的 W45 进程（不同 PID：32588 / 2080 / 31112）记入 `EVIDENCE\game_proc.txt` + `game_proc_history.json`
3. 分级齐全，`guard_state` 明标「仍是注入夹具、W38-S1 `classify()` 未在此运行，**不证守卫已普遍启用**」

## 5. 新登记的差距（我认可其诚实）

- **G-14**：F0 全关 plan 与 build 内建 G1 基线互斥（已显式拒绝 + 断言，未实现空游戏目录包）
- **G-15**：build 写后不一致不自动 `rmtree`（保留 package dir 供检查）
- **G-16**：`guard_state` 仍为注入夹具
- **U-W46-3**：**卸载侧（E3）未按 plan 的 delete/restore 集合做逐文件对账**（`uninstall()` 未改，仍清单驱动）—— 属下一卡

---

## 6. ★ 一个被证实的 CLI 缺陷（本卡未修，需单独立项）

`[本次实测]` 我在 v14 上直接验：
```
python -m ra2forge install --package x --game y --json
→ python -m ra2forge: error: unrecognized arguments: --json
```
而 `verify --json` **可用**（返回结构化 JSON）。

⇒ **`ra2forge` 的 `--json` 只在部分子命令上存在，`install` / `uninstall` / `build` 都不接受。**

`[代价]` 这个不一致**直接让 W45 丢掉了整个 B 臂**：它的 `install ... --json` 返回 **exit 2**，而驱动脚本没把非零退出当致命错误，继续跑了一趟"未装包"的游戏，还把 `verify exit 0`（无 manifest 时的**空过**）当成了成功。
详见 `REVIEW\LEAD_VERDICT_W45_arm_B_invalid.md`。

`[建议]` 单独立一张小卡统一 CLI：所有子命令要么都支持 `--json`，要么都不支持；并在 `install`/`uninstall` 上加「非零退出即致命」的文档说明。
`[教训]` **一个 10 分钟的 CLI 一致性修复，能省掉一整臂真机实验**。
