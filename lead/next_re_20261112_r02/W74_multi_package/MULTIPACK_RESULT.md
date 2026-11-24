# W74 · 多战役包共存实测（C 线路线 (a) 的产品化问题）

> 执行者 **Hy4**（W74，非 Lead）｜卡目录 `lead\next_re_20261112_r02\W74_multi_package\`
> 全部时间 `+08:00`（UTC 时间见 `out\*.ndjson` / `STARTED.txt`）
> **默认离线**：沙箱内 `install`/`uninstall`/`verify`，**未启动游戏、未取锁、未写 `ra2youli`**。git 只读。
> 分级：`[本次实测]` 本卡沙箱命令实收 stdout/退出码/哈希；`[本次读码]` 本卡读 v15 源码；`[静态推断]` 由源码语义推出、未实测；`[转引]` 已签发背景；`[待运行验证]` 未做。

---

## 0 · 结论速览

**三分判定：`互斥`**（写明拒绝方式，见 §5）。

- `[本次实测]` **第二个包被拒绝**，不是覆盖、不是合并。路线 (a) 的 `--feature-set` 路径下，**退出码 33**，reason `INPLACE_OFFICIAL_MISMATCH`。
- `[本次实测]` 还有**第二道独立闸门**：用一个非 inplace 的第二包做诊断，装 A 后再装它得到 **退出码 3**，reason `package_mismatch`（`This version does not support coexisting packages / 初版不支持并存`）。
- `[本次实测]` `--force` / `--allow-content-conflict` / `--adopt-legacy` **三种逃逸开关全部无效**（两道闸门的退出码都不变），且被拒安装 **零写入**。
- `[本次实测]` 因 B 从未被安装，**不存在"共存态"**，所以"卸载顺序"在当前实现下不可表达；两种顺序实测都能逐字节还原官方 `BATTLEMD.INI`。
- `[转引]` 结论为「互斥」→ 按卡面规定**不做真机**（没有可玩状态），**未取锁、未启动 gamemd、`0x125C` 无值可报**。

---

## 1 · 实验装置（先复制脚本、改输出路径，未直接调用别卡脚本）

`[本次实测]` 本卡把 W63 的两个 helper **复制到本卡并改了输出路径**后再用：

| 本卡文件 | 来源 | 改动 |
|---|---|---|
| `work\tools\w74_lib.py` | `W63_route_a_e2e\work\tools\w63_lib.py` | `W63`→`W74`；`OUT`/`GAME` 全部指向 `W74_multi_package`（`w74_lib.py:33-38`）；Win32 live helper 原样保留但**本卡从不调用** |
| `work\tools\w74_common.py` | 同上 `w63_common.py` | `import w74_lib`；`CARD`→`W74_multi_package`；新增 `PKG_A`/`DESIGN_A`/`FEATURE_SET_A`（只读引用 W63）与 `PKG_B`/`DESIGN_B`/`FEATURE_SET_B`（本卡） |
| `work\tools\w74_make_b.py` / `w74_make_b2.py` / `w74_multi.py` / `w74_diag.py` / `w74_realproof.py` | 本卡新写 | 全部只写本卡目录 |

`[本次实测]` 所有 v15 命令都由本卡 `v15_cmd()` 以 `cwd = W60_battlemd_inplace\ra2forge_patched_v15` 执行。首次手工构建 B 时**漏设 cwd**，`-m ra2forge` 命中了仓库根的旧版 CLI（usage 只有 `validate/build/install/uninstall/example/inspect`），报 `unrecognized arguments: --feature-set` **exit 2**；该次失败只在会话控制台出现、**未单独归档到 `out\`**（如实说明，不伪造日志）。随后以 `cwd=V15` 重跑成功，日志见 `out\cmd_build_B.log`。

### 1.1 三个包

| 包 | 目录 | `package_id` | `package_version` | `[SOV1] Scenario` | 构建方式 |
|---|---|---|---|---|---|
| **A**（转引 W63，不改） | `W63_route_a_e2e\work\pkg\W63RouteA` | `org.ra2forge.w63.routea.three` | `1.0` | `RA2F_M1.MAP` | `[转引]` W63 已签发 |
| **B**（本卡第二包，主实验） | `work\pkg_b\W74PkgB` | `org.ra2forge.w74.pkgb.one` | `2.0` | `RA2F_N1.MAP` | `[本次实测]` `ra2forge build --design work\w74_design_b.json --out work\pkg_b --feature-set work\w74_feature_set_b.json` → **exit 0**，产出 `RA2F_N1.MAP` / `RA2F_M2.MAP` / `RA2F_M3.MAP` |
| **B2**（诊断用第二包） | `work\pkg_b2\W74PkgB2` | `org.ra2forge.w74.pkgb2.append` | `3.0` | `BATTLEMD98.INI`（append 模式，不碰 `[SOV1]`） | `[本次实测]` `ra2forge build ... --feature-set work\w74_feature_set_b2.json` → **exit 0** |

`[本次实测]` B 的构造记录在 `out\PACKAGE_B_CONSTRUCTION.json`：从 W63 的 design/feature-set 出发，仅改 `package.id`/`package.version`、`campaign.id`/`campaign.name`、把首关 `RA2F_M1` 改名 `RA2F_N1`（于是 build 造出**第二张地图 `RA2F_N1.MAP`**），并让 `battlemd.scenario=RA2F_N1.MAP`、maps/chain/mix/mapselmd.stages 同步改名；其余（3 关链、trigger、inplace、repack、csf=off、clone_append）与 A 一致。**B 是一个真实可安装的包**，不是桩。

### 1.2 沙箱 prep（每个 trial 都重新 robocopy，保证独立）

`[本次实测]` 复制 W63 的 prep：`robocopy ra2youli → sandbox_game`（源只读，rc=1 属 0..7 成功码）→ `verify` → `uninstall` 掉真目录里既有的 v0.3 记录 → `verify` → 从**沙箱副本**删除无主的 241 B 孤儿 `BATTLEMD.INI.ra2forge.bak` → 断言 `BATTLEMD.INI` 逐字节等于官方 2733 B 基线。

官方基线：`7e40691a3480b1e5ffe6d1cdfccb83f67da4447157607ec3ecb5d2278acf0791`（2733 B），与卡面给定值一致（`[本次实测]` 实算 `v15\ra2forge\data\BATTLEMD.OFFICIAL.INI` 与 `ra2youli\BATTLEMD.INI` 均得此值）。

### 1.3 真目录自证

`[本次实测]` `out\REAL_DIR_PROOF.json`：对 `ra2youli` 做 647 文件全量 SHA 清单，与 W63 的 `out\real_pre.json` 全量逐行比较 → `added=0 removed=0 changed=0 mtime_diff=0`，`IDENTICAL_TREE_vs_W63 = true`；与 W44 签发 baseline（647 文件 / 1,989,215,270 B / 277 maplike / 关键哈希）全部匹配；`BATTLEMD.INI` 仍是官方值。**本卡从未写 `ra2youli`**（robocopy 只作源，所有 v15 `--game` 都指向本卡 `sandbox_game`）。

---

## 2 · 问题 1：v15 会不会拒绝第二个包？

`[本次实测]` **会拒绝**。同一沙箱内，装 A → `verify` → 装 B：

```
$ python -m ra2forge install --package <A> --game <sandbox> --feature-set <w63_feature_set.json>   → EXIT 0
$ python -m ra2forge verify  --game <sandbox> --json                                             → EXIT 0
$ python -m ra2forge install --package <B> --game <sandbox> --feature-set <w74_feature_set_b.json> → EXIT 33
```

**原始 stdout / stderr / 退出码**（逐字，`out\cmd_t1_install_B.log`）：

```
ARGV: [... "-m","ra2forge","install","--package","...\\work\\pkg_b\\W74PkgB",
       "--game","...\\W74_multi_package\\sandbox_game",
       "--feature-set","...\\work\\w74_feature_set_b.json"]
CWD: D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W60_battlemd_inplace\ra2forge_patched_v15
EXIT: 33

--- STDOUT ---
(空)

--- STDERR ---
error: [INPLACE_OFFICIAL_MISMATCH exit=33] INPLACE_OFFICIAL_MISMATCH: the loose
BATTLEMD.INI on disk is not the official baseline (sha=8fb51769216d36af...,
expected 7e40691a3480b1e5...). W60 rewrites ONLY the official bytes; a
modified/third-party file is a content conflict and is refused BEFORE any
write. Zero bytes written.
```

`[本次实测]` 装 A 后 `BATTLEMD.INI` 已变成 A 的 `[SOV1]` 改写（sha `8fb51769…`，2732 B，`Scenario=RA2F_M1.MAP`），不再是官方 `7e40691a…`，W60 的 `inplace_preflight` 因此拒绝。

**逃逸开关全测**（各 4 个变体，t1/t2 各跑一遍，共 8 次，日志 `out\cmd_t*_install_B_*.log`）：

| 变体 | t1 EXIT | t2 EXIT | 之后状态与装 A 后是否逐字节相同 |
|---|---|---|---|
| 裸 `install --feature-set` | **33** | **33** | ✅ 相同 |
| `+ --allow-content-conflict` | **33** | **33** | ✅ 相同 |
| `+ --adopt-legacy` | **33** | **33** | ✅ 相同 |
| `+ --force` | **33** | **33** | ✅ 相同 |

`[本次实测]` 四次被拒后 `verify --game <sandbox> --json` 仍 **EXIT 0**（A 完好）。`[SOV1]` 一直是 `RA2F_M1.MAP`（A 的），B 的 `RA2F_N1.MAP` 从未落盘 → **不是覆盖、不是合并、是零写入拒绝**。

### 2.1 对照组：B 本身能不能装？

`[本次实测]` `out\TRIAL_control.json`：全新沙箱（无 A）里单独装 B → **EXIT 0**；`[SOV1] Scenario=RA2F_N1.MAP`，manifest `package_id=org.ra2forge.w74.pkgb.one`，`.bak` 为官方 2733 B；卸载后 `BATTLEMD.INI` 还原为官方 SHA。**证明 B 是有效包，t1/t2 的拒绝完全由"A 已占用 `[SOV1]`"引起**，不是 B 自身构造失败。

### 2.2 诊断：还有一道更通用的身份闸门（exit 3）

`[本次实测]` 为了回答"就算绕过 inplace 闸门，两个包能共存吗"，本卡用 **append 模式的第二包 B2**（同样不同 `package_id`，但 `battlemd.mode=append` → `inplace_preflight` 不适用）在"装 A 之后"再装 → **EXIT 3**：

```
EXIT: 3
--- STDERR ---
error: install blocked by package identity - no file has been written:
  - package identity mismatch: ra2forge_install.json records package_id
    'org.ra2forge.w63.routea.three', but this package declares package_id
    'org.ra2forge.w74.pkgb2.append'. This version does not support coexisting
    packages (初版不支持并存) - uninstall the recorded package first
    ('python -m ra2forge uninstall --game <dir>'). This refusal is NOT
    bypassable: not by --force, not by --allow-content-conflict, not by
    --adopt-legacy.
```

`[本次实测]` B2 的 4 个变体（裸 / `--allow-content-conflict` / `--adopt-legacy` / `--force`）**全部 EXIT 3**，全部零写入（`out\cmd_diag_install_B2*.log`、`out\DIAG.json`）。卸载后仍还原官方 SHA。

`[本次读码]` 两道闸门的位置与触发顺序（v15 = `W60_battlemd_inplace\ra2forge_patched_v15`）：

- `ra2forge\install.py:2020-2027`：`preinstall_plan` 先算身份 verdict；**随后** `RI.inplace_preflight(feature_plan, game, plan["manifest"])` 先执行。
- `ra2forge\resolve_integration.py:936-972`（`inplace_preflight`）：磁盘上的 loose `BATTLEMD.INI` 不是官方基线 → `ResolveIntegrationRefused(INPLACE_OFFICIAL_MISMATCH, exit_code=33)`；`resolve_integration.py:66` `EXIT_INPLACE_OFFICIAL_MISMATCH = 33`。CLI `cli.py:508-510` 把它映射为退出码。
- `ra2forge\install.py:2029-2043`：身份 verdict 为 `reject_mismatch` 时抛 `PackageIdentityBlocked(kind="package_mismatch")`；`cli.py:501-507` 映射 `EXIT_PACKAGE_MISMATCH = 3`（`cli.py:28`）。
- `ra2forge\install.py:1291-1316`：`new_pkg_id != old_pkg_id` → `reject_mismatch`，消息含"初版不支持并存"，并声明 `--force`/`--allow-content-conflict`/`--adopt-legacy` 全部不可放行。
- `ra2forge\resolve_integration.py:187-191` 的 `SECOND_INSTALL_SEMANTICS["DIFFERENT_PACKAGE"]` 也明写"different package_id => v13 PKG-IDENT01 exit 3 stands"。

`[本次实测]` 因此在**路线 (a) 的 `--feature-set` 路径**里，先撞到的是 **33**（inplace 基线闸门），**3 到不了**；但 3 作为通用身份闸门是真实存在且同样不可放行的（用 B2 实测证实）。**两道闸门，任一都足以互斥。**

---

## 3 · 问题 2：清单与备份会怎样？

`[本次实测]` 第二次安装（B）**被零写入拒绝后**，`ra2forge_install.json` 内容（`out\manifest_t1_after_B_final.json` / `snap_t1_after_B_final.json`，t2 相同）：

| 项 | 实测值 | 含义 |
|---|---|---|
| 文件 | 存在，7715 B，sha `b8ab909f…` | **仍是 A 的清单，与装 A 后逐字节相同**（`manifest_unchanged_vs_after_A=true`） |
| `package_id` | `org.ra2forge.w63.routea.three` | A 的 id；**没有 B 的任何记录** |
| `package_version` | `1.0` | A 的 |
| `version` | `1.0` | tool 版本 |
| `files[]` | `BATTLEMD.INI`, `MAPSELMD.INI`, `RA2F_M1.MAP`, `RA2F_M2.MAP`, `RA2F_M3.MAP`, `expandmd98.mix` | 全 A 的文件 |
| **`original_sha256`** | `7e40691a3480b1e5ffe6d1cdfccb83f67da4447157607ec3ecb5d2278acf0791` | **仍是官方原值**，不是 A 改写后的 `8fb51769…` |
| `BATTLEMD.INI.ra2forge.bak` | **在**，2733 B，sha = 官方原值 | A 的备份完好 |
| `ra2forge_install.json.seal` | 在（A 的），未被改 | |
| 磁盘 `BATTLEMD.INI` | sha `8fb51769…`，`[SOV1]=RA2F_M1.MAP` | 仍是 A 的改写，未变 |
| `RA2F_N1.MAP` | **不存在** | B 的地图从未落盘 |

`[本次实测]` 清单前后快照哈希（`out\manifest_t1_*.json`）：装 A 后与 4 次 B 尝试后的清单 sha **全部相同**（`b8ab909f…`）；pre 与卸载后为 `<ABSENT>`。

**对卸载可逆性的含义**：`[本次实测]` 因为 B 从未写入，`original_sha256` 与 `.bak` 都保持官方原值 → 卸载能正确还原（§4 实测证实）。`[静态推断]` 反过来说：若未来某个实现允许 B **就地覆盖** `[SOV1]` 而不重新做备份，按 `install.py:14-19,37` 的语义（"existing backup slot is never overwritten / oldest original wins" + `original_sha256` 记的是**本次安装前**磁盘上的字节），第二次安装会把 `original_sha256` 记成 **A 改写后的 `8fb51769…`**，且 `.bak` 仍是官方 2733 B（因为已存在、不会被覆盖）→ 数字对不上、还原语义错乱；如果它先删旧 `.bak` 再新建，则 `.bak` 变成 A 的字节，卸载会还原成 A 而不是官方。**这是 `[静态推断]`，本卡未实测**（v15 根本不允许走到这一步）。

---

## 4 · 问题 3：卸载顺序的可逆性

### 4.1 先说一个实现事实（决定了"顺序"能不能表达）

`[本次读码]` `cli.py:272-307`：`uninstall` 只有 `--game` / `--legacy` / `--drop-legacy-battlemd` / `--force` / `--json`，**没有 `--package`**。它只作用于**单一全局** `ra2forge_install.json`。`[本次实测]` 由于 B 被拒（零写入），这个全局清单始终是 A 的。

因此卡面要求的两种"顺序"在 CLI 层面其实是**同一对调用**，本卡按语义分别标注并各跑一趟（每趟都用全新 robocopy 沙箱，互不污染）：

| 趟 | 序列 | 第 1 次 uninstall | 第 2 次 uninstall |
|---|---|---|---|
| **t1**（卸 B → 卸 A） | 装A → 装B(拒) → uninstall → uninstall | 标 `call1_B`，**实际卸载的是 A**（清单是 A 的），exit 0，逐字节还原 | 标 `call2_A`，已无清单，exit 0，`actions: []` + warning "no ra2forge_install.json" |
| **t2**（卸 A → 卸 B） | 同上 | 标 `call1_A`，同样卸载 A，exit 0，逐字节还原 | 标 `call2_B`，同样空操作，exit 0 |

### 4.2 逐字节还原结果

`[本次实测]` 两趟最终 `BATTLEMD.INI`：

| 趟 | 最终 SHA256 | 大小 | == `7e40691a…0791`？ | `verify` 最终 |
|---|---|---|---|---|
| t1 | `7e40691a3480b1e5ffe6d1cdfccb83f67da4447157607ec3ecb5d2278acf0791` | 2733 B | ✅ **是** | EXIT 0 |
| t2 | `7e40691a3480b1e5ffe6d1cdfccb83f67da4447157607ec3ecb5d2278acf0791` | 2733 B | ✅ **是** | EXIT 0 |

`[本次实测]` 两趟收尾状态：`manifest_present=false`、`seal_present=false`、`BATTLEMD.INI.ra2forge.bak` 已消失、`RA2F_*.MAP` 全部清空、`[SOV1] Scenario=SOV01umd.MAP`（官方）。见 `out\TRIAL_t1.json` / `TRIAL_t2.json` 的 `Q3_final`，及 `out\snap_t*_after_uninstall_call2.json`。

`[本次实测]` 唯一残留 `expandmd98.mix.ra2forge.bak` 是**真目录里原本就存在的孤儿**（36347 B，sha `dda88f30…`），与 W63 `real_pre.json` 中的条目逐字节相同，**不是本卡创建**；`verify` 把它列为 orphan 但按文档 orphan 不改退出码（仍 0）。

### 4.3 产品上这意味着什么

- `[本次实测]` **"必须按 LIFO 顺序卸载"在当前实现下不是一个可表达的要求**：v15 的 manifest 是**单记录**（一个 `package_id`、一份 `files[]`、一个 `.bak` 集合），`uninstall` 无包标识。两种"顺序"实测等价且**都能还原**。
- `[本次实测]` **单包生命周期是可逆的**：装 A →（B 被拒）→ uninstall ⇒ 官方逐字节还原；control 里装 B → uninstall 同样还原。这是 W63/W70 已签发结论在多包尝试下的延续。
- `[本次实测]` **多包共存没有发生，因此也谈不上"多包共存破坏可逆性"**——破坏点不存在，因为 v15 直接不允许两个包同时存在。
- `[静态推断]` **如果产品将来真的允许两个包都写 `[SOV1]`**：单个 `.bak` + 单个 `original_sha256` 只能记住"最老的原值"或"上一次的字节"二者之一，无法同时表达两层还原点；那时**必须按 LIFO 卸载**（先卸后装的），否则先把 `.bak` 还原成官方、后装包的文件就失去可还原的字节。这是从 `install.py:37` "oldest original wins" 推出的推断，**本卡未实测**（v15 不允许该状态）。

---

## 5 · 问题 4：三分判定

> **判定：`互斥`（写明拒绝方式）**

| 候选 | 是否成立 | 依据 |
|---|---|---|
| `可共存（写明机制）` | ❌ | `[本次实测]` 无覆盖、无合并；退出码 33 / 3，零写入 |
| `互斥（写明拒绝方式）` | ✅ **本卡判定** | 见下 |
| `共存但不可逆（写明破坏点）` | ❌ | `[本次实测]` 不存在共存态，故无可破坏的可逆性 |

**拒绝方式（两层，均为 `[本次实测]` + `[本次读码]`）**：

1. **路线 (a) 专属闸门（先命中）**：`RI.inplace_preflight`（`resolve_integration.py:936-972`）要求磁盘 loose `BATTLEMD.INI` 必须逐字节是官方 2733 B 基线；A 已把它改写成 `8fb51769…` → `ResolveIntegrationRefused(INPLACE_OFFICIAL_MISMATCH)` → **CLI EXIT 33**，stderr 明写 "Zero bytes written"。`--force` / `--allow-content-conflict` / `--adopt-legacy` 均不改变 33。
2. **通用身份闸门（更深一层）**：PKG-IDENT01 `preinstall_plan` 的 `reject_mismatch`（`install.py:1291-1316` + `2032-2043`）→ `PackageIdentityBlocked(kind="package_mismatch")` → **CLI EXIT 3**，消息 "This version does not support coexisting packages (初版不支持并存) … NOT bypassable"。用 append 模式的 B2 实测证实（4 变体全 3，零写入）。

`[转引]` 根因与卡面背景一致：路线 (a) 靠**占用唯一官方入口 `[SOV1]`**，而 `[SOV1]` 在 `BATTLEMD.INI` 里只有一个 section；`ra2forge_install.json` 是**单包覆盖写**的记录（`install.py:375` `MANIFEST_NAME` 单文件、`cli.py` 无 `--package` 卸载）。**v15 本身就没有"两个包"的概念**。

`[本次实测]` 结论为互斥 → 按卡面规定 **不做真机**（没有可玩状态）：未取锁（`owner=lead` 未变）、`gamemd.exe` 启动 0 / 残留 0、`Scen+0x125C` **无值**。

---

## 6 · 对产品的影响

1. `[本次实测]` **路线 (a) 一次只能装一个战役包**。用户想换包，唯一合法流程是 `uninstall` 现有包 → 再 `install` 新包（错误消息本身也这么建议）。这不影响 W63/W70 已签发的"三关链贯通 + 卸载后官方战役可用"，但**把"多战役包并存"排除在 v15 能力之外**。
2. `[本次实测]` **没有清单栈、没有按包卸载**：安装器只有一份全局 `ra2forge_install.json` + 一份 `.bak`。产品经理若预期"装两个包、在游戏里选一个"，当前实现不支持，且不是加个开关能解决的。
3. `[本次实测]` **好消息：拒绝是干净且安全的**（零写入、`verify` 仍 0、两趟卸载都逐字节还原官方、真目录 `IDENTICAL_TREE=true`）。即"用户试着装第二个包"不会把环境搞坏。
4. `[本次实测]` **坏消息：错误提示不面向用户**。路线 (a) 路径下用户看到的是 exit 33 `INPLACE_OFFICIAL_MISMATCH`（"loose BATTLEMD.INI 不是官方基线"）——这是内部不变量术语，没告诉他"请先卸载当前战役包"。真正的 `初版不支持并存` 文案（exit 3）在这一路径下**到不了**。
5. `[静态推断]` **若未来放开共存**：`[SOV1]` 只有一个 campaign entry，两个包不可能同时从它进入；就算用"启动时改写 `[SOV1]` 指向所选包首关"的选择器方案，也必须解决备份栈与 LIFO 卸载（§4.3），否则会破坏 W63/W70 已签发的可逆性。

---

## 7 · 最小改动建议（**不动手实现**）

按"改动量从小到大"给三条，供 Lead 决策；本卡**未修改 `ra2forge` / `ra2opt` / `ra2bench` 任何源码**。

- **A（最小、推荐先做，纯提示/文档，0 逻辑改动）**：把 EXIT 33 的拒绝文案升级成产品语言——当 `inplace_preflight` 因"非官方基线"拒绝且 `ra2forge_install.json` 里已有 `package_id` 时，明确输出「当前已安装战役包 `<id>`；本版本一次只支持一个战役包，请先 `python -m ra2forge uninstall --game <dir>`」。同时把"一次只能装一个战役包"写进 `INSTALL.txt` / 产品文档。改动面：`resolve_integration.py` 的一条消息 + builder 的 INSTALL.txt 模板；**不改任何判定逻辑、不破坏 W63/W70 已签发行为**。
- **B（若产品坚持"切换包"更顺手）**：提供一条显式 `switch` 命令 = `uninstall` + `install` 的原子封装（仍单包），带 `--yes` 确认；不引入共存，可逆性不变。改动面：`cli.py` 增加子命令，复用现有 `uninstall()`/`install_package()`。
- **C（若产品真的要求多包共存，属重新设计，非小补丁）**：必须同时改 4 处，缺一不可——
  1. `ra2forge_install.json` 从**单对象**改为**已安装包列表/栈**（每包独立 `package_id`、`files[]`、`original_sha256`、`.bak` 命名空间）；
  2. 备份槽从单一 `<name>.ra2forge.bak`（`install.py:37` "oldest original wins"）改为**按包分层**，并保证 LIFO 还原；
  3. 放开 `inplace_preflight` 的"必须是官方基线"（改为"必须是本栈上一层的字节"）**和** PKG-IDENT01 的 `reject_mismatch`（`install.py:1305-1306`）；
  4. `uninstall` 增加 `--package <id>` 并定义卸载顺序（LIFO），或直接拒绝非栈顶卸载。
  另需解决 `[SOV1]` 只有一个入口的**语义**问题：两个包不能同时"占用"它，得有选择器或改用 route (b) 多 battle id（后者已被 `LEAD_RULING_C_line_route_a_first.md` 冻结）。**`[转引]` 该裁决已定 (a) 上真机、(c) 冻结，故本卡建议 A/B，不建议 C。**

---

## 8 · 纪律自检

| 项 | 结果 |
|---|---|
| `STARTED.txt` 先于读任何文件 | ✅ `STARTED.txt` 写在读码之前（ISO + `Hy4` + "lock per trip"） |
| HEARTBEAT 每 10 分钟 | ✅ 3 次（18:09Z / 18:14Z 及起始 17:59Z），覆盖 01:58–02:14 本地 |
| **先复制脚本到本卡、改输出路径再用** | ✅ `w74_lib.py` / `w74_common.py` 为 W63 副本并重指到本卡；未 import 别卡脚本 |
| 默认离线 / 不启动游戏 / 不取锁 | ✅ 全程 `gamemd_residual=[]`，锁始终 `owner=lead`（未取 `w74` 锁） |
| 不写 `ra2youli` | ✅ `IDENTICAL_TREE_vs_W63=true`（647 文件全量逐字节相同），`REAL_DIR_PROOF.json` |
| 不改 `ra2forge`/`ra2opt`/`ra2bench`；不动 W21–W73 | ✅ 只读引用 W63 包 A 与 v15；v15 目录只作 cwd |
| 只写本卡目录；git 只读 | ✅ 所有产物在 `W74_multi_package\` |
| 结论分级 | ✅ 全篇 `[本次实测]` / `[本次读码]` / `[静态推断]` / `[转引]` 标注；**未写"多包共存已支持"** |
| 互斥 → 不做真机 | ✅ 未启动游戏、无 `0x125C`、无锁状态变更 |

---

## 9 · `out\` 产物索引

- **命令日志（argv / cwd / EXIT / 完整 stdout / stderr）**：`cmd_t1_install_B.log`（**EXIT 33 原文**）、`cmd_diag_install_B2.log`（**EXIT 3 原文**）、`cmd_t*_install_B_*.log`（4 逃逸变体 ×2 趟）、`cmd_diag_install_B2_*.log`、`cmd_*_install_A.log`、`cmd_*_uninstall_*.log`、`cmd_*_verify_*.log`、`cmd_build_B.log` / `cmd_build_B2.log`（build exit 0）、`cmd_make_b*.log`。
- **判定 JSON**：`TRIAL_t1.json` / `TRIAL_t2.json`（四问结构化事实）、`TRIAL_control.json`、`DIAG.json`、`PACKAGE_B_CONSTRUCTION.json` / `PACKAGE_B2_CONSTRUCTION.json`、`PREP_*.json`、`REAL_DIR_PROOF.json`。
- **NDJSON 逐步采样**：`w74_control.ndjson` / `w74_trial1.ndjson` / `w74_trial2.ndjson` / `w74_diag.ndjson` / `w74_realproof.ndjson`。
- **清单前后快照**：`manifest_t1_pre_official.json`（`<ABSENT>`）/ `manifest_t1_after_A.json` / `manifest_t1_after_B*.json` / `manifest_t1_after_uninstall_call*.json`（`<ABSENT>`），t2 同套；`snap_*.json` 含每个时点的全部文件 SHA。
- **`BATTLEMD.INI` 前后哈希**：见 `out\BATTLEMD_HASHES.md`（本卡另归档的速查表）与各 `snap_*.json` 的 `battlemd` 字段。
- **全树清单**：`real_post.json`、`*_sandbox_pre.json`；`console_*.log` 为 5 次脚本运行的完整控制台输出。
