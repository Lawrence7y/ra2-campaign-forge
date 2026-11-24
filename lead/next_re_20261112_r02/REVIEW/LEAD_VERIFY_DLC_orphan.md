# C 线（DLC）W21 复核：孤儿文件缺陷已复现并修复

> run_id `NEXT_RE_20261112_R02`｜Lead 独立复核｜2026-11-13
> 被复核对象：`W21_dlc_orphan/`（执行方 GLM-5.3-Flash）

## 1 · Lead 复核结果（逐项实算，不采信汇报）

| 检查 | 结果 |
|---|---|
| 原 `ra2forge/` 是否零改动 | ✅ `git status --porcelain ra2forge` 空；`install.py` = `732095978b5ed64377e120656f10e7ce78f31772d8ad588906216e7cc08bc562`（85,379 B） |
| 补丁全量副本是否存在 | ✅ **`ra2forge_patched/ra2forge/install.py`**（104,358 B，`d1186be1…`），且同目录下 `__init__/builder/cli/design/format80/lzo/maplib/mixlib/triggers` 全在 ⇒ **完整可运行包** |
| 补丁副本可编译 | ✅ `py_compile` **exit=0** |
| 新增能力存在 | ✅ `TOOL_VERSION = 0.5`；`_plan_orphans` / `_execute_orphan_plan` / `_rollback` 三函数均在 |
| 规模 | 原版 1,574 行 → 补丁 1,925 行（+351 行） |
| 真实游戏目录 | ✅ 未被写：`RA2MD.INI` `c91c6a47…`、`ddraw.ini` `c983abad…`、地图类 **277/277 = 基线** |
| 用例证据 | ✅ `repro_A_to_aprime/`：14 份日志 + 24 份 SHA-256 快照，可重放 |

### 1.1 我自己的一处误判（留痕）

我第一次检查时断言「补丁全量副本缺失」——**错的**。我只看了 `ra2forge_patched/install.py`（上一层），
而副本实际在其**子目录** `ra2forge_patched/ra2forge/install.py`。执行方的描述是准确的，是我查错层级。

### 1.2 `PATCH.diff` 不可直接 `git apply`（已由执行方预先披露）

diff 头用了**绝对 Windows 路径**（`a/D:\Project\...`），`git apply --check` 报
`error: invalid path 'D:\...'`。**`APPLY.md` 已事先写明**这一点并给出替代：
整文件替换 `copy /Y ... ra2forge\install.py`。⇒ 不构成隐瞒，但**今后补丁应生成相对路径**。

## 2 · 缺陷与修复的实质（采纳执行方结论，含其对任务书的纠正）

### 2.1 任务书对缺陷的描述不准确（`DISAGREE.md` 三处，Lead 采纳）

| 任务书原话 | 实测事实 |
|---|---|
| 「旧地图…**仍被旧清单记录**」 | **清单被整体重写、条目直接丢失**（不是"仍记录"） |
| 「卸载时可能**删错**」 | 实为**错还原**：把 A 自己写过的 INI/Y/MIX 当成"原版"还原回来，卸载后残留 4 个 A 时代文件 |
| 需不需要 `--force` 才复现 | **不需要**，跨路径与同路径两种升级形态**都复现** |

### 2.2 修复的关键设计（我认可）

- **归属判定 = 「清单记录过该名字」且「当前 sha256 == 记录 sha」**；非匹配 ⇒ 硬拒绝（strict）；
  **清单未记载的文件永不触碰**。这条是安全核心，避免了"按文件名猜归属"的危险做法。
- 新增清单字段 `original_absent`（修复"过度还原我们自己写的旧版本"）、`removed_orphans`（审计）。
- `_rollback` 用 undo 日志：`created→unlink`、`replaced→从本次 bak 还原`、`孤儿移除→从旧包路径重装`。

### 2.3 用例覆盖（执行方报告全部通过，含退出码）

V1 正常升级 / V1b 同路径 / V2 卸载还原 / V3 升级后卸载（**IDENTICAL**）/ V4a–c 用户同名文件
（拒绝 + 零写入，用户文件 sha 全程不变）/ V5a–c 中途失败回滚（精确回到 post-A）/
V6a–d 非游戏目录、目录槽、`..\evil.MAP` 穿越（**沙箱外金丝雀不变**）/ V7 备份型孤儿精确还原 /
COMPAT-1 跨版本卸载 IDENTICAL；COMPAT-2（v0.5 清单被 0.4 代码读）不崩溃但回到旧过度还原，**已注明混用限制**。

## 3 · ★ 本轮另一项独立发现：真实游戏目录**并非干净状态**

复核时发现 `ra2youli\ra2forge_install.json` **早就存在**（创建/修改 **2026-10-22 07:48:39**，非本轮写入）：

```json
{ "tool": "ra2forge", "version": "0.3",
  "package": "D:\\Project\\ra2-campaign-forge\\out\\forge2_verify\\build\\钢铁残响",
  "game_dir": "...\\ra2youli",
  "files": [ { "name": "BATTLEMD98.INI", "action": "created", ... },
             { "name": "ECH01.MAP", "action": "replaced", ... } ] }
```

⇒ **`ra2youli` 当前装着一个旧会话留下的 ra2forge 包（v0.3，"钢铁残响"）**，含 1 个新建 BATTLEMD98.INI
与若干被替换的地图（`ECH01.MAP` 等）。

**这件事的影响**：
1. 本会话 A 线的所有"基线"读数（地图清单 277、`frame` 速率、CPU）**都是在这个已装包的状态下测的**。
   此前从未声明这一点 —— 现在补上。
2. 地图清单 277 的基线**已经包含**该包写入的文件，所以 A 线的**对照一致性**不受影响（前后同状态）。
3. 但 **C 线的干净起点不成立**：任何"安装/卸载还原"实验都必须在**隔离沙箱**做（W21 正是这么做的），
   不能拿 `ra2youli` 当"未安装"的参照。

**未做**：我没有卸载这个旧包。理由：它属于旧会话的产物，卸载会改变 A 线已建立的基线状态；
且 `uninstall` 会删散装文件与还原 bak，属不可逆且影响面未知。**这留给用户裁决**。

## 4 · 下一步（采纳执行方建议，与我先前的判断一致）

**RE-N10 第 5 项：清单接线 / 包身份**。理由（执行方给出，我认可）：
本卡的 `original_absent`/`removed_orphans` 只是**单活动包内**的最小修复；
而 **「A→B 并存显式拒绝」「伪造清单的信任问题」「多代升级与完整事务回滚」三件事都卡在同一个缺口**——
清单没有 `package_id` / version / 每条目来源包哈希，任何并存与信任判定都只能靠猜。

建议的具体交付：
1. 清单 schema 加 `package_id` + `version` + 每条目 `source_package_sha256`；
2. install 时校验：**同 id ⇒ 升级路径；异 id ⇒ 明确拒绝**（初版不支持并存，这与项目「初版允许检测并拒绝冲突」一致）；
3. 把 W21 的沙箱序列**收编为回归脚本**（输入已在 `sandbox/`，可直接复用）；
4. **包身份与 battle ID 分开**（任务书原文要求）。
