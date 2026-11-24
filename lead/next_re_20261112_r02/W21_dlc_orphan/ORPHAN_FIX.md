# ORPHAN-FIX01 · 升级孤儿文件缺陷：复现与修复（run_id NEXT_RE_20261112_R02 / W21）

日期：2026-11-13 · 执行：W21 子代理 · 仓库 `main@3872ef6` · Python 3.12.10
**真实游戏目录 `ra2youli` 全程零写操作**（仅沙箱内验证，见 §6）。

---

## 0. 结论

1. **缺陷存在，已复现**（原版代码，两种升级路径）。A→A′ 后：A 独有的 `X.MAP` 残留在游戏目录、新清单不再记录它；uninstall 漏删 X.MAP，且把「我们自己写的第一版 INI/Y/MIX」当成"原版"还原回来（另一同族表现，见 §2.3）。
2. **已修复**（补丁在 `ra2forge_patched/`，原 `ra2forge/` 逐字节未动，见 §4）：孤儿按清单+SHA-256 归属判定后移除/还原原版；新清单只记 A′ 内容；新增 `original_absent` 修复"过度还原"；写入阶段带 undo 回滚。
3. **T3 全部用例通过**（V1–V6 + 补充 V7/V1b/COMPAT-1/COMPAT-2，每条含命令、原始输出、退出码，见 §5 与 `repro_A_to_aprime/logs/`）。

---

## 1. 沙箱构造

写域：`lead/next_re_20261112_r02/W21_dlc_orphan/`。

| 项 | 内容 |
|---|---|
| 假游戏目录 `sandbox/game_golden/`（每用例复制到 `sandbox/game/`） | `gamemd.exe`(占位)、`RA2MD.INI`、`BATTLEMD.INI`(假官方，无 forge 标记)、`USERMAP1.MAP`(用户自己的文件) |
| 包 A（`sandbox/pkgs/ORPHAN PROBE`） | 原版 builder 从 `designs/pkg_A.json` 构建：`BATTLEMD98.INI` + `X.MAP` + `Y.MAP` + `expandmd98.mix`（构建 exit 0，日志 `logs/00_build_packages.txt`） |
| 包 A′（`sandbox/pkgs/ORPHAN PROBE TWO`） | 从 `designs/pkg_A2.json` 构建：只含 `Y.MAP`(修改版)、`Z.MAP`、`BATTLEMD98.INI`、`expandmd98.mix`，**不含 X** |
| 同路径变体 `sandbox/pkgs_same/ORPHAN PROBE` | A 的包目录副本，两次 install 之间**原地**变异成 A′ 内容（路径不变 ⇒ `same_install=True`，无需 conflict 旗标） |
| 快照工具 | `tools/snapshot.ps1`（每文件 SHA-256+大小+相对路径）、`tools/diffsnap.ps1`、`tools/show_state.py`、`tools/v5_fail_driver.py`（失败注入） |

包安装器视角：`package_files()` 只取 `BATTLEMD98.INI` + `*.MAP` + `expandmd98.mix`，故事/报告文件不参与安装。

## 2. T1 复现（原版代码，未打补丁）

序列（跨路径主场景）：fresh game → `install A` (exit 0) → `install A′ --allow-content-conflict` (exit 0) → `uninstall` (exit 0)。日志：`logs/t1_10_install_A.txt`、`t1_20_install_A2.txt`、`t1_30_uninstall.txt`；快照：`snaps/t1_0*.sha.txt`。

### 2.1 升级后：X.MAP 残留且清单不再记录（缺陷核心）

`install A′` 输出（原始）：备份/替换了 `BATTLEMD98.INI`、`Y.MAP`、`expandmd98.mix`，`created Z.MAP` —— **通篇没有 X.MAP**。升级后状态（`snaps/t1_21_after_install_A2.sha.txt`）：

```
f9a90db6f6beaa97…  4321  X.MAP                       ← A 的 X，仍在盘上（孤儿）
…                 4280  Y.MAP                       ← A′ 的 Y（已更新）
d0cb854487f9ca2c…  4267  Z.MAP                       ← A′ 新增
29608485366540e7…   386  BATTLEMD98.INI.ra2forge.bak ← bak 里是 A 的 INI，不是"原版"
清单 files: BATTLEMD98.INI / Y.MAP / Z.MAP / expandmd98.mix   ← X 条目消失（清单整体重写）
```

### 2.2 uninstall 后：漏删 + 残留（`snaps/t1_31_after_uninstall.sha.txt` vs 初始）

```
DIFFER（=ONLY-IN-B 表示卸载后仍残留）：
  29608485… BATTLEMD98.INI  386B   ← 被"还原"成 A 的 INI（真原版是"不存在"）
  4a472404… expandmd98.mix  8555B  ← 同上，A 的 MIX
  f9a90db6… X.MAP           4321B  ← 孤儿漏删（清单无记录，卸载器不认识）
  b1bbeb66… Y.MAP           4200B  ← 被"还原"成 A 的 Y
卸载器输出：removed expandmd98.mix / restored …ra2forge.bak -> expandmd98.mix / removed Z.MAP /
  removed Y.MAP / restored Y.MAP… / removed BATTLEMD98.INI / restored BATTLEMD98.INI… / removed 清单
```

即「装了 A′，卸载后游戏目录里仍留有 4 个 A 时代的文件」。用户自己的文件（`USERMAP1.MAP`、`BATTLEMD.INI`、`RA2MD.INI`、`gamemd.exe`）全程未被误删——缺陷表现为**残留/漏删**，不是误删。

### 2.3 同路径变体（`logs/t1b_same_path.txt`）

`same_install=True`（包路径未变）时无需 `--allow-content-conflict` 即完成升级，孤儿表现**完全相同**：X.MAP 残留（sha `f9a90db6…`）、清单无 X 条目、卸载后同样残留 4 个文件。

### 2.4 根因（对应任务书 §3 RE-N10 第 6 项）

`preinstall_plan()` 只遍历**新包**的文件（`for src in files`），从不检视旧清单里有而新包没有的条目；`install_package()` 用只含新包文件的 `entries` 整体重写 `ra2forge_install.json`。旧条目连同其备份槽被静默遗弃：文件留在盘上成为孤儿，备份槽里的内容语义也随之失真（见 §3 的 `original_absent`）。

## 3. T2 修复（`ra2forge_patched/ra2forge/install.py`，仅此一个文件，+418/−67 行，PATCH.diff）

改动 6 处（均为 `ra2forge/install.py` 内的最小接线，CLI/builder/legacy 路径未动）：

1. **模块 docstring**：新增 `Safety rules (ORPHAN-FIX01)` 一节，固化本节规则。
2. **`preinstall_plan()`**：每个 step 计算 `original_absent`（若被替换文件的备份槽**在 preflight 时不存在**且旧清单记录过该文件 ⇒ 新备份槽里将是**我们自己上一版字节**而非用户原版）。步骤元数据携带该旗标。
3. **新增 `_plan_orphans()` + preinstall_plan 返回 `orphans` 计划**（只读，分类）：
   - `restore`：文件 sha == 记录 sha（⇒ 是我们的）且记录的 `.ra2forge.bak` 存在且非 `original_absent` ⇒ 先用 bak 把**真原版**还原到槽位再消费 bak；
   - `remove_absent`：bak 存在但记录证明 bak 是我们自己的旧版本 ⇒ 文件+bak 一并删除；
   - `remove`：无 bak（A 自己创建的文件）⇒ 直接删除；
   - `changed`：sha 不匹配 ⇒ **不删不改**，strict 拒绝（risk），非 strict 保留并告警；
   - `missing`：记录并提示，无写操作；
   - `invalid_name / unsafe_slot / invalid_backup / unsafe_backup`：转成**硬 blocker**（名字不规范/别名/目录/备份槽别名——沿用 `_dest_safety_error`/`_bak_safety_error` 五项判据）。
4. **新增 `_execute_orphan_plan()`**（写阶段：先完成包拷贝，再执行孤儿退出，最后写清单）；每个槽位在写/删前一刻重跑身份判据。
5. **新增 `_rollback()` + `install_package()` 写阶段 undo 日志**：任一步失败（含 Ctrl-C），已提交的拷贝回滚（created→unlink；replaced→从本次建的 bak 还原，既有 keep 槽保留），孤儿移除若已发生则**从旧清单记录的旧包路径重装**（sha 校验），报告写入异常消息；清单始终最后写，失败即不落盘。
6. **`uninstall()`**：条目带 `original_absent=true` 时删除文件+bak 而非"还原"我们的旧版本；无旗标的旧清单行为逐字节不变。清单新增审计字段 `removed_orphans`（仅记录本次过渡，不参与卸载追踪）；`TOOL_VERSION 0.4→0.5`。

**归属判定**（任务书红线）：只以「`ra2forge_install.json` 记录过该文件名 + 当前字节 sha256 == 记录 sha256」判定为我们写入；不匹配⇒视为已变更⇒拒绝/保留；清单未记载的名字⇒永不触碰；一切删除/还原都限游戏目录内的普通文件槽位。

**向后兼容**：旧格式 `ra2forge_uninstall.txt` 路径一行未改（V6d 验证 same risk 拒绝）；v0.4 清单 × 补丁代码卸载逐字节精确（COMPAT-1）；v0.5 清单 × 原版代码不崩溃，但回到旧"过度还原"行为（COMPAT-2，APPLY.md 提醒混用限制）。

## 4. 原包零改动证明

`ra2forge_patched/ORIG_BASELINE.sha256.txt` 记录了打补丁前 `ra2forge/*.py` 全部 11 个文件的 SHA-256；补丁完成后复测一致（"ORIGINAL ra2forge/ UNCHANGED"）。补丁只存在于 `ra2forge_patched/ra2forge/`。

## 5. T3 用例结果（全部原始输出见 `repro_A_to_aprime/logs/`，快照见 `snaps/`）

| # | 用例 | 结果 | 关键证据（日志/快照） |
|---|---|---|---|
| V1 | install A → install A′（跨路径+flag） | **通过** (exit 0/0) | `removed X.MAP (orphan…)`；`X.MAP present? False`；Y=4280B(A′)、Z 新增；清单 files 仅 INI/Y/Z/MIX + `removed_orphans:[X.MAP]`；original_absent=True → `t3_V1_orphan_cleanup.txt` |
| V1b | 同路径升级（无 flag） | **通过** (exit 0/0) | 同上全部判据 → `t3_V1b_compat.txt` |
| V2 | install A′ → uninstall | **通过** (exit 0/0) | diff vs 初始 **IDENTICAL**，exit 0 → `t3_V3_full_cycle.txt`(V2 段) |
| V3 | install A → install A′ → uninstall | **通过** (exit 0/0/0) | 卸载输出含 `removed …ra2forge.bak (original absent…)`×3；diff vs 初始 **IDENTICAL**，exit 0 → `t3_V3_full_cycle.txt` |
| V4a | 用户同名 X.MAP，无 flag 安装 | **通过** (拒绝 exit 1) | content-conflict 拒绝；diff vs 初始 IDENTICAL（零写入）→ `t3_V4_user_files.txt` |
| V4b | 同场景带 flag | **通过** (exit 0) | 用户原版进 bak、`ALLOWED` 记录进清单（显式释放路径） |
| V4c | USERMAP1.MAP 全程保护 | **通过** | sha `59057b73…` 在 V1/V2/V3 快照中逐字节不变 |
| V5a | fresh 安装中途失败（注入 Z.MAP 拷贝异常） | **通过** (exit 1) | 异常消息含回滚报告；manifest 未写；diff vs 初始 **IDENTICAL** → `t3_V5_midfail_rollback.txt` |
| V5b | 升级中途失败（MIX 拷贝异常） | **通过** (exit 1) | 回滚到精确 post-A 态（IDENTICAL）；旧清单仍有效，再 uninstall 回到初始（IDENTICAL） |
| V5c | 清单写盘失败（孤儿已移除后） | **通过** (exit 1) | 回滚报告 `rolled back the orphan removal of X.MAP (re-installed from the previous package…)`；diff vs post-A **IDENTICAL** → `t3_V5c_record_fail.txt` |
| V6a | 非游戏目录（无 gamemd.exe） | **通过** (拒绝 exit 1) | "does not look like a Yuri's Revenge directory"；目录仍空 |
| V6b | 目标槽是目录（game\Z.MAP 为目录） | **通过** (拒绝 exit 1) | path-safety 硬 blocker；目录未被动 |
| V6c | 手造清单含 `..\evil.MAP` 穿越 | **通过** (拒绝该条目, exit 0) | warning `refusing to touch it`；清单保留；**沙箱外金丝雀 evil.MAP sha 不变**；注意：清单声称的 USERMAP1.MAP（sha 匹配）被删——原版既有行为，见 UNCOVERED §3 |
| V6d | legacy `ra2forge_uninstall.txt` 存在 | **通过** (拒绝 exit 1) | 与原版相同的 unresolvable-risk 拒绝文案，零写入（未静默改行为） |
| V7 | 备份型孤儿：用户原版从 bak 还原 | **通过** (exit 0/0/0) | 升级输出 `restored X.MAP.ra2forge.bak -> X.MAP (orphan…)`；X.MAP sha=用户原版 `96e5664f…`；bak 消费；uninstall 后 diff vs 用户初始 **IDENTICAL** → `t3_V7_backup_orphan_retry.txt` |
| COMPAT-1 | v0.4 清单 × 补丁卸载 | **通过** | IDENTICAL → `t3_V1b_compat.txt` |
| COMPAT-2 | v0.5 清单 × 原版卸载 | 不崩溃（记录性） | 回到旧过度还原行为，无孤儿残留（X 已被补丁升级清掉） |

「没复现」项：无（主缺陷两路径均复现）。

## 6. 安全边界自证

- 全部命令的 `--game` 都指向 `lead/next_re_20261112_r02/W21_dlc_orphan/sandbox/game`；真实目录 `D:\Project\ra2-campaign-forge\ra2youli` **零写操作**（本卡未对其执行过任何写命令，只在本报告引用其路径名）。
- 唯一的写域外操作：只读读取 `ra2forge/*.py`、`docs/re/NEXT_RE_TASKS_20261112.md`、`README.md`、`test_preinstall.py`。
- 未执行任何 `git` 写操作（仅 `git diff --no-index` 生成补丁文本）。

## 7. 未覆盖与不确定项

见 `UNCOVERED.md`。要点：引擎侧行为未验证（本卡只做文件层）；`changed` 孤儿非 strict 放行态未单测；多活动包并存策略未触碰；伪造清单可删 sha 已知文件的既有威胁面；回滚对 `bak-keep` 槽的语义限制。
