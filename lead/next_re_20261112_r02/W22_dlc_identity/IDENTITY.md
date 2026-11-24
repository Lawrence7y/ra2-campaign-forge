# IDENTITY.md · 清单接线 / 包身份（PKG-IDENT01）

run_id `NEXT_RE_20261112_R02` · W22 卡（RE-N10 第 5 项）· 2026-11-13
基线：`W21_dlc_orphan/ra2forge_patched/`（TOOL_VERSION 0.5，孤儿修复已含）演进为
`W22_dlc_identity/ra2forge_patched_v6/`（TOOL_VERSION **0.6**）。
仓库 `ra2forge/` 原版逐字节未动（对照 `W21_.../ORIG_BASELINE.sha256.txt` 复测 0 差异）；
真实游戏目录 `ra2youli/` **零写操作**（唯一接触 = 只读复制其清单，见 §6）。

---

## 1. 清单 schema 前后对照

### 1.1 v0.3（真实旧清单，`ra2youli/ra2forge_install.json`）

```
顶层键: tool, version(="0.3"), installed_at, package, game_dir, files, warnings
files[]: name, action, bytes, sha256, backup
```

### 1.2 v0.4 / v0.5（仓库现状 + W21 补丁）

```
顶层键: tool, version, installed_at, package, game_dir, files, warnings,
        precheck{strict, allowed_content_conflicts, risks, notices,
                 conflicts_seen, blockers}
        [v0.5 追加] removed_orphans[]
files[]: name, action, bytes, sha256, backup [, original_absent (v0.5)]
```

### 1.3 v0.6（本卡新增，全部向后兼容字段）

```
顶层键:  tool, version(工具版本 "0.6"),
+        package_id            ← 稳定包标识（未声明时写 "unknown"）
+        package_version       ← 包版本（与工具 version 完全分开）
+        package_digest        ← 包内容指纹（定义见 §2）
         installed_at, package(路径，保留兼容+回滚用), game_dir,
         files, warnings, precheck, removed_orphans,
+        supersedes            ← 仅审计链: {package_id, package_version,
                                  package_digest, package, adopted_legacy}
                                  （无旧清单时不存在；判定逻辑不读它）
files[]: name, action, bytes, sha256, backup [, original_absent],
+        source_package_digest ← 该条目来自哪个包版本（= 安装时 package_digest）
```

实测样例（P1 升级后清单，节选，全文见 `sandbox/P1/game/ra2forge_install.json`）：

```json
{
  "tool": "ra2forge", "version": "0.6",
  "package_id": "org.ra2forge.probe-orphan",
  "package_version": "2.0",
  "package_digest": "9d1e3babd16392fd768d859bb6ae706b4b6abad43f0e2e2fdcd51c4c3c236c8f",
  "files": [
    { "name": "Y.MAP", "action": "replaced", "sha256": "5bd20d0e…",
      "backup": "Y.MAP.ra2forge.bak", "original_absent": true,
      "source_package_digest": "9d1e3babd16392fd768d859bb6ae706b4b6abad43f0e2e2fdcd51c4c3c236c8f" }
  ],
  "supersedes": { "package_id": "org.ra2forge.probe-orphan", "package_version": "1.0",
                  "package_digest": "9ed1ca1b…", "adopted_legacy": false },
  "removed_orphans": [ { "name": "X.MAP", "action": "removed" } ]
}
```

### 1.4 身份声明的来源链（由设计决定）

```
design JSON 可选顶层 "package": {"id": "…", "version": "…"}
        │  builder._write_package_identity()（缺失 ⇒ 不写文件 = 未声明）
        ▼
<包目录>/ra2forge_package.json   {"tool":"ra2forge","package_id":"…","package_version":"…"}
        │  install._read_package_identity()（存在但损坏 ⇒ PackageIdentityError 硬错，
        │                                    绝不静默当 "unknown"）
        ▼
ra2forge_install.json 的 package_id / package_version / package_digest
```

**未声明（无 `ra2forge_package.json`）的包**：`package_id="unknown"`。全新目录可装；
但覆盖任何已有清单都需要 `--adopt-legacy`（§3）——这是"身份未声明 ⇒ 不猜"的统一保守规则，
对本卡自写的 `unknown` 清单与真正的旧版清单一视同仁。

## 2. `package_digest` 精确定义

```
package_digest = SHA-256( UTF-8( "\n".join(lines) ) )
lines          = 按 name 升序（Python sorted()，码点序）排列的
                 "<file_name> <SHA-256(文件字节)>" 每散装文件一行，无尾随换行
散装文件集合   = package_files()（install.py 既有定义）= BATTLEMD98.INI +
                 全部 *.MAP（升序） + expandmd98.mix（存在时）
```

实现为 `install.package_digest_from_steps(steps)`：**从计划步骤的 `new_sha` 计算**，
因此清单里的 `package_digest` 与实际拷贝的字节永远一致（不存在"指纹与货不符"的窗口）。

**为何只取安装集**（任务书例句是"构建产物中所有散装文件"，此处收窄并说明理由）：
`BUILD_REPORT.txt` / `INSTALL.txt` / `story.md` 不落游戏目录；若计入指纹，仅改文档
不改内容也会翻指纹（无意义噪声），且报告含构建路径使指纹不可复现。指纹的用途是
"多代升级判定 + 条目溯源"（`files[].source_package_digest`），必须恰好指纹化
**真正进入游戏目录的字节**。回归 P1 用例断言了"内容变 ⇒ 指纹变"（dg1 != dg2）。

`files[].source_package_digest`：本次安装写入的每一条都携带当时包的 `package_digest`。
多代追溯示例：v1 装入 → 条目来源 dg1；升 v2 → 新清单全部条目来源 dg2，同时
`supersedes.package_digest = dg1` 串起链条。判定逻辑仍只信"记录 + sha256"（W21 红线），
supersedes 只是审计，不是信任来源。

## 3. T2 四种判定（install 身份语义，核心）

判定在 `preinstall_plan()`（只读）算出 `plan["identity"]["verdict"]`，
`install_package()` 在**任何写之前**抛 `PackageIdentityBlocked(InstallBlocked)`。
CLI 退出码（`cli.py`）：**0 成功 / 3 package_mismatch / 4 legacy_adopt_required /
1 其他 OSError / 2 argparse**。

| # | 目标目录状态 | 新包身份 | 行为 | 退出码 |
|---|---|---|---|---|
| ① | 无清单 | 任意 | 全新安装，写全部新字段 | 0 |
| ② | 有清单且 `package_id` 相同（双方已声明） | 同 id | **升级路径**（W21 孤儿退出计划 + 回滚照常运行） | 0 |
| ③ | 有清单且 `package_id` 不同（双方已声明） | 异 id | **明确拒绝**："This version does not support coexisting packages (初版不支持并存)"，附双方 id、指明唯一出路（先 uninstall）。**零写入**。`--force` / `--allow-content-conflict` / `--adopt-legacy` **都不能**越过 | **3** |
| ④ | 有清单但 `package_id` 为 `unknown`（旧清单/未声明包写的清单），**或**新包未声明而清单已声明 | 一侧 unknown | **不猜**：拒绝并说明原因，要求显式 `--adopt-legacy`（语义 = 用户断言"本次安装是既录记录的指定后继"）；采纳后仅把**清单记录过的文件**视为"我们的"，其余门禁（路径安全/损坏清单/备份槽保护/strict risk）照旧 | 无 flag：**4**；带 `--adopt-legacy`：0 |

补充边界：
- **损坏清单**优先于身份判定（清单形状都不可信时谈何身份）——blockers 先抛（exit 1）。
- **路径判定已死**：v0.4 的 `manifest["package"] == 本目录` 路径等值判定被 ②③④ 取代
  ——这正是本卡补的缺口："从同一路径先后装两个不同包无法区分"。
  P1 用例显式断言：A1/A2 构建于**不同路径**、同 id ⇒ 升级成立（路径不是身份）。

### `--force` 语义（写清能/不能）

| | 能 | 不能 |
|---|---|---|
| install | 什么都不能（v0.4 起从未生效，本卡也不给它行为）；`--help` 明示 | **身份拒绝（exit 3/4）**、路径安全、损坏清单、备份槽保护、strict risk |
| uninstall | 删除"记录过但字节已变"的文件（原有语义，不变） | 其余一切 |

P2 用例实测：`--force`、`--allow-content-conflict`、`--adopt-legacy` 三种尝试对异 id
拒绝全部仍是 exit 3，且每次尝试后快照逐字节不变（零写入）。

## 4. T4 · `package_id` 与 battle ID 是两个独立概念

**battle ID** = `BATTLEMD*.INI` 里 `[Battles] 15=<id>` 指向的战役节名（design 的
`campaign.id`，默认 `RA2F1`）。它是**引擎侧**概念：游戏用 `FindFirstFileA("BATTLEMD*.INI")`
枚举 + 按 battle id 合并战役项（install.py 顶部注释，VA 0x52CBA0/0x46CE10）。
**package_id** = **安装器侧**概念：判定目标目录是否属于同一个包的演进线。

两者命名空间独立，互不派生（builder 的 `_write_package_identity` docstring 固化了这条规则；
BUILD_REPORT 同时打 `battle_id=RA2F1` 与 `package_id=…` 两行，P0 实测）。

回归中的 T4 用例（`out/T4.log`）构造了三个包：

| 包 | package_id | battle ID（从其 BATTLEMD98.INI 实测解析） | 判定 |
|---|---|---|---|
| A1 (v1.0) | org.ra2forge.probe-orphan | RA2F1 | — |
| A2 (v2.0) | **同上** | **RA2F1（同）** | **同 id 升级 ⇒ exit 0**（battle ID 跨版本保持稳定正是正确做法；若改 battle id，战役菜单里旧条目会成孤儿） |
| B | org.ra2forge.other-campaign（**异**） | **RA2F1（同，蓄意碰撞）** | **异 id ⇒ exit 3 拒绝**：安装器层先拦下；即便有人手拷绕过安装器，两个包的 `[RA2F1]` 节在引擎里按 battle id 合并，后者覆盖前者——两层检查两层字段，缺一不可 |

结论一句话：**"同 package_id 不同版本"走升级（battle ID 应跨版本不变）；"不同
package_id 相同 battle ID"在安装层被身份门拒绝**——初版不支持并存，自然也挡住了
battle ID 合并冲突；将来若放开并存，battle ID 唯一性检查是另一张卡的事（见 UNCOVERED）。

## 5. T3 回归（`regress_dlc.py`，一条命令）

```
python -B -X utf8 regress_dlc.py        # 全量；exit 0=全过, 1=有失败
python -B -X utf8 regress_dlc.py P1 V5  # 调试可挑用例
```

**最终结果：14 组用例 / 125 条断言，全部 PASS，脚本 exit 0。**
每组用例的 命令 + 原始输出 + 退出码 + 逐项判据 落盘 `out/<用例>.log`；
汇总在 `out/SUMMARY.txt`。用例映射：

| 卡片要求 | 回归实现 | 结果 |
|---|---|---|
| V1 升级 | V1a 无 flag 未声明升级 ⇒ exit 4 零写入；V1b `--adopt-legacy` ⇒ W21 升级流程照旧（X.MAP 孤儿退出） | PASS (10) |
| V2 卸载还原 | A1 → uninstall → 快照与初始逐字节同 | PASS (3) |
| V3 升级后卸载 | A1 → A2 → uninstall → 逐字节同初始 | PASS (4) |
| V4 用户同名文件 | V4a 冲突拒绝 exit 1 零写入；V4b 显式释放 ⇒ 用户原件进 .bak，卸载还原 | PASS (7) |
| V5 中途失败回滚 | V5a 全新失败 / V5b 升级失败回滚至精确 post-A1 / V5c 清单写失败含孤儿回滚（"re-installed from the previous package"） | PASS (12) |
| V6 路径穿越/非游戏目录 | V6a 非 gamemd 目录；V6b 槽位是目录；V6c 伪造清单 `..\evil.MAP` 穿越条目（沙箱外金丝雀不动、清单保留）；V6d legacy 清单 risk 拒绝零写入 | PASS (14) |
| P1 同 id 升级 | 免 flag 升级 + 全部新字段断言 + 来源指纹 + supersedes 链 + removed_orphans | PASS (13) |
| P2 异 id 拒绝（零写入） | exit 3 + 双 id 可见 + 零写入 + 三种 flag 不可越过 | PASS (9) |
| P3 旧清单无 id | P3-main 仿真 v0.3 态 ⇒ exit 4 零写入；P3-real 真实清单副本 ⇒ 同门 | PASS (5) |
| P4 --adopt-legacy 后升级 | ECH 原版从 .bak 还原、槽消费、original_absent、supersedes.adopted_legacy、卸载归零 | PASS (11) |
| P0 构建链 | design 声明 ⇒ build 写 ra2forge_package.json ⇒ 装入清单（battle_id/package_id 两行报告） | PASS (13) |
| C1/C2 向后兼容 | §6 | PASS (6+6) |
| T4 演示 | §4 表格的三包实测 | PASS (3) |

## 6. 向后兼容实测（旧清单 = 真实 `ra2youli/ra2forge_install.json` 的**副本**）

真实清单 SHA-256 `fe3bdf62f4e871b61bf0d1b1d451b090af1c0b1804440c093089436253cc3914`
（2026-10-22 之后未变，本卡只读复制，未回写）。

| 用例 | 状态 | 实测结论 |
|---|---|---|
| **C1** 真实清单副本 × uninstall（v0.6 vs W21 v0.5 同输入） | v0.6 清单无新字段 ⇒ 缺失字段按 `unknown` 处理 | v0.5/v0.6 输出**逐字节一致**（仅头部游戏目录路径按用例目录名归一，其余全同）、退出码同为 0、终态快照逐字节一致；行为 = 字节不匹配的条目告警保留、清单保留（既有行为，未被本卡改变） |
| **C2** v0.6 新清单 × v0.5 工具卸载 | 旧工具读新字段（忽略未知键） | 输出/退出码/终态与 v0.6 卸载一致，双方都精确还原 golden 态 |
| **P3-real** 真实清单副本 × install（无 flag） | 身份门对真实旧清单生效 | exit 4、零写入、文案点名 `--adopt-legacy` |
| uninstall 对新字段的读取 | `files[]` 新键被忽略、顶层新键不进任何分支 | uninstall 代码**零改动**（diff 可证），C1/C2 是"没改坏"的执行证据 |

注：真实清单记录的 ECH01-03 sha256 对应原字节已不可得，沙箱以"伪造字节 + 真清单"
组合做**兼容性**验证（行为等价），以**合成 v0.3 态**（字节与记录一致）做**功能升级**
验证（P4）——两者互补，都不美化。

## 7. 判定次序（代码事实，`install_package`）

1. `preinstall_plan`：gamemd.exe / 包可用性（FileNotFoundError，零写）→ 包身份声明读取
   （损坏 ⇒ PackageIdentityError，零写）→ 清单形状与槽位门 → 步骤/孤儿只读计划 →
   身份 verdict。
2. `install_package`：blockers（损坏清单/路径安全）→ **身份 verdict（exit 3/4）** →
   conflicts → risks → 复核 → 写（带 undo 回滚）→ 清单最后写。
