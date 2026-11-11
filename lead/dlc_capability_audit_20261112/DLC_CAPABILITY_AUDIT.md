# DLC 框架能力逐行实测盘点（2026-11-12）

> 受限执行方审计报告。仓库 `D:\Project\ra2-campaign-forge`（Windows / PowerShell）。
> 写域唯一：`lead\dlc_capability_audit_20261112\`。
> 规范依据：`docs/PROJECT_DIRECTION.md` §2.C 明确写「**以下是待实现目标，不表示已经具备**」（第 48 行），因此本文只做「现成实现实际具备什么」的实测盘点，不把规划当成能力。

---

## 0. 审计口径与执行约束

| 项 | 本次执行 |
|---|---|
| 零真机 | 全程未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 attach、未读活进程内存。写域沙箱内名为 `gamemd.exe` 的文件是 34 字节纯文本惰性占位（`INERT PLACEHOLDER - NEVER EXECUTED`），**从未执行**，仅用于满足 `install.py` 的 `gamemd.exe` 前置检查。 |
| 只读边界 | 未执行 `git commit / push / reset / checkout`；未改任何既有件；未改 `ra2youli\` 任何文件。所有构建产物用 `--out` 指向写域子目录。 |
| Python 调用 | 包入口一律 `$env:PYTHONPATH='D:\Project\ra2-campaign-forge'; python -X utf8 -m ra2forge ...`；自写脚本一律 `python -I -X utf8 <绝对路径>`。 |
| 指纹 | 一律 `hashlib` 实算（`python -I -X utf8`）；无估计值、无转抄哈希。 |
| 证据 | 全部实跑 stdout 落盘在 `stdout\`（46 件）；逐行结论只引用实跑输出或 `文件:行`。README / DESIGN 的**自述**只作为「文档写了什么」的证据，不作为「能力具备」的证据。 |
| 判定用语 | **实测通过** / **实测不通过** / **未测** 三态分开写。机制类、跨图普适类、因果推断类一律标 **【未证】**，不把读数升格成结论。 |

**执行时点**：2026-11-12 00:41–01:10（Asia/Shanghai，采样自会话时标）。

---

## STEP 1 · 规范清单（逐条最低交付要求 + 文件:行）

### 1.1 §2.C 表头与前提

| 出处 | 原文要点 |
|---|---|
| `docs/PROJECT_DIRECTION.md:46` | `### C. DLC 框架与工具` |
| `docs/PROJECT_DIRECTION.md:48` | 「从现有 ra2forge 战役构建、验证、安装/卸载能力出发，**先盘点实际能力，再补缺口**。以下是**待实现目标，不表示已经具备**。」 |
| `docs/PROJECT_DIRECTION.md:50` | 最小贯通样例：一个小型多关卡战役包，经过**制作、校验、构建、安装、游戏内注册、关卡推进、存读档和卸载还原**。 |
| `docs/PROJECT_DIRECTION.md:52` | 「框架需要明确：」 |
| `docs/PROJECT_DIRECTION.md:54` | 表头 `| 能力 | 最低交付要求 |` |
| `docs/PROJECT_DIRECTION.md:65` | 「阶段一不依赖新引擎或全面源码还原。单位、建筑和资源扩展在战役最小样例通过后逐项接入。**资产继续由用户自己的游戏安装提供，工具生成的包与原版资产依赖分开登记**。」 |
| `docs/PROJECT_DIRECTION.md:121` | G3 验收「一个真实补充包完成制作到卸载全流程，并**验证存读档与冲突处理**」 |

### 1.2 八行最低交付要求（逐条）

| # | 能力 | 最低交付要求（逐字） | 文件:行 |
|---|---|---|---|
| 1 | 包清单 | 稳定包 ID、版本、目标游戏/构建、内容清单、依赖、冲突及文件哈希 | `docs/PROJECT_DIRECTION.md:56` |
| 2 | 内容组织 | 地图与战役、规则、单位/建筑、美术/音频分阶段接入；明确能力限制 | `docs/PROJECT_DIRECTION.md:57` |
| 3 | 资源与注册 | 资源查找与覆盖顺序、MIX 分配、战役 ID、散装 INI 和命名冲突检查 | `docs/PROJECT_DIRECTION.md:58` |
| 4 | 构建与校验 | 输入校验、缺失引用检查、构建报告、产物读回校验及可重复构建验证 | `docs/PROJECT_DIRECTION.md:59` |
| 5 | 安装与升级 | 安装前检查、备份清单、失败恢复、依赖检查、升级迁移和卸载还原 | `docs/PROJECT_DIRECTION.md:60` |
| 6 | 内容隔离 | 明确包间冲突和可并存范围；初版允许检测并拒绝冲突，不承诺任意组合 | `docs/PROJECT_DIRECTION.md:61` |
| 7 | 兼容策略 | 标注补丁开关与规则版本、存档兼容范围、联机内容一致性；不兼容时明确拒绝或提示 | `docs/PROJECT_DIRECTION.md:62` |
| 8 | 作者入口 | 示例、内容规范、命令行工作流和诊断报告；优先复用现有模块 | `docs/PROJECT_DIRECTION.md:63` |

### 1.3 已通读的配套材料（给 文件:行）

| 材料 | 关键行 | 内容 |
|---|---|---|
| `docs/DESIGN.md:9-22` | 18–22 | 战役 ID 默认 `RA2F1`；官方 ID（`ALL1`/`SOV1`/…）被显式拒绝；「多个战役包同时安装时，给每个包一个不同的 `campaign.id`」 |
| `docs/DESIGN.md:55` | 55 | 「常用代码（**rulesmd 原版 id，原版引擎直接可用**）」——只引用原版 ID，不产出规则 |
| `docs/DESIGN.md:134-156` | 150–156 | 构建期硬自检：每张 .MAP 写出后**从磁盘读回**核对 `[Basic] NextScenario`；末关 `EndOfGame=yes` |
| `docs/DESIGN.md:158-195` | 160–169、171–174、177–190、192–195 | 产物表名；散装 `BATTLEMD98.INI` 的通配机制；`[Battles] 15=RA2F1`（官方占 1–14）；`expandmd98.mix` 只放地图、0 个 INI |
| `docs/DESIGN.md:197-204` | 200–204 | 安装形态：逐文件备份 `<名字>.ra2forge.bak` + 清单 `ra2forge_install.json` + uninstall 还原 |
| `docs/DESIGN.md:206-218` | 206–218 | 「迁移须知（从旧版 ra2forge 升级）」；**L211 勘误**：删除散装 `BATTLEMD.INI` 不会回退到 MIX；应先用 `extracted/found_battlemd.ini` 恢复 |
| `README.md:20-29` | 22–28 | 快速开始命令（validate / build / build --install / uninstall / example） |
| `README.md:31-35` | 32–35 | 「安装是**清单驱动**的」+ 备份 + `ra2forge_install.json` + uninstall 还原 |
| `README.md:37-42` | 37–42 | 「老用户迁移」：称「删掉后引擎会**回退到 MIX** 里的官方同名文件」，且「**不要**用 `extracted/found_battlemd.ini` 去还原」 |
| `README.md:54-67` | 56–67 | 代码结构表；`ra2forge/cli.py` 列 validate / build / install / uninstall / example / inspect |
| `README.md:104-122` | 118–122 | ⚠️ 「本机 `ra2youli\` 仍是 FORGE-1 之前的安装」；⚠️ 「**游戏内实测**（进游戏看战役列表、通关节）需要玩家进行」 |
| `README.md:124-129` | 126–129 | 已知限制：水面无海岸线、地图预览占位图、暂不支持 CarryOver / 自定义 CSF 语音字幕 / 经济波次 AI |

> **规范内部冲突（实测读到，不下裁决）**：`README.md:38-40` 说删 `BATTLEMD.INI` 会回退到 MIX 且不要用 `found_battlemd.ini` 还原；`docs/DESIGN.md:211` 明确「【勘误 2026-09-27 · Lead 实测推翻】**删除散装 `BATTLEMD.INI` 不会回退到 MIX**」并要求用 `found_battlemd.ini` 恢复。两处对同一迁移步骤给出互斥指令。本文只登记该矛盾，不裁决谁对。

---

## STEP 2 · 逐行实跑

所有命令的 stdout/stderr 与退出码均落盘在 `stdout\`。以下每行给出**命令原文**与**关键输出**（完整输出见对应日志文件）。

### 命令总表

```
# 包入口（每条都带 $env:PYTHONPATH='D:\Project\ra2-campaign-forge'）
python -X utf8 -m ra2forge --help
python -X utf8 -m ra2forge {validate,build,install,uninstall,example,inspect} --help
python -X utf8 -m ra2forge validate examples/demo_campaign.json
python -X utf8 -m ra2forge validate <写域>\fixtures\neg_*.json            # 4 个负例
python -X utf8 -m ra2forge example <写域>\fixtures\minimal_design.json
python -X utf8 -m ra2forge build --design <写域>\fixtures\minimal_design.json --out <写域>\build_min
python -X utf8 -m ra2forge build --design examples/demo_campaign.json --out <写域>\build1
python -X utf8 -m ra2forge build --design examples/demo_campaign.json --out <写域>\build2
python -X utf8 -m ra2forge install  --package <写域>\build1\钢铁残响 --game <写域>\sandbox_*  [各种旗标]
python -X utf8 -m ra2forge uninstall --game <写域>\sandbox_*  [--legacy]
python -X utf8 -m ra2forge inspect <写域>\build1\钢铁残响\ECH01.MAP

# 自写脚本（一律 python -I -X utf8 <绝对路径>）
python -I -X utf8 <写域>\scripts\readback.py <包目录>                    # 独立产物读回
python -I -X utf8 <写域>\scripts\repeat_compare.py <build1> <build2>     # 两次构建逐件 sha256
python -I -X utf8 <写域>\scripts\fingerprint.py <baseline.json|closing.json>
python -I -X utf8 <写域>\scripts\compare_fingerprints.py <baseline> <closing>
python -I -X utf8 <写域>\scripts\make_manifest_fixture.py <包目录> <out.json>
python -I -X utf8 D:\Project\ra2-campaign-forge\tools\validate_package_manifest.py <写域>\fixtures\prototype_manifest.json
python -I -X utf8 D:\Project\ra2-campaign-forge\mcp\ra2forge_mcp.py        # stdio JSON-RPC 实跑
```

---

### 第 1 行 · 包清单 — **实测不通过**（缺独立清单，7 项要求中 5 项完全没有）

**实跑**：构造两种最小包（`build_min\Example Operation`＝1 关；`build1\钢铁残响`＝3 关），逐件列目录。

```
python -X utf8 -m ra2forge build --design examples/demo_campaign.json --out <写域>/build1
  -> built: ...\build1\钢铁残响\expandmd98.mix   (stdout\22_build1.txt, exit=0)
python -I -X utf8 <写域>\scripts\readback.py <写域>\build1\钢铁残响
  -> stdout\31_readback_build1.txt, exit=0
```

**实测读数**（`stdout\31_readback_build1.txt`）：

```
-- files in package (8) --
  BATTLEMD98.INI / BUILD_REPORT.txt / ECH01.MAP / ECH02.MAP / ECH03.MAP
  expandmd98.mix / INSTALL.txt / story.md

-- manifest-like filenames (regex) = NONE --
  key 'package_id' ... False   key 'version' ... False   key 'target' ... False
  key 'depend' ... False       key 'conflict' ... False  key 'hash' ... False
  key 'sha256' ... False       key 'content' ... False
```

`BUILD_REPORT.txt` 全文（实读，见 `stdout\31_readback_build1.txt`）实际只有：
`campaign` / `side` / `battle_file` / `battle_id=RA2F1` / `battle_id_source` / `battle_index=15` / `description` / `first_scenario` / `mix` / `NextScenario chain` / `self-checks` / `artifacts`（6 行，每行 `<名字> <字节> sha256=<16 位十六进制>`）。

逐项对表（均为实测或实读，非推测）：

| 规范要求 | 实测 | 依据 |
|---|---|---|
| 稳定包 ID | **实测不通过**。无包 ID；`battle_id=RA2F1` 是**游戏 INI 段名**，且两个不同包都用同一个 `RA2F1` / 同一个 `[Battles] 15`（`stdout\31_readback_build1.txt` 与 `stdout\32_readback_build_min.txt` 双向读到），不构成包身份 | `ra2forge/builder.py:46,52,279-291`；`ra2forge/design.py:32` |
| 版本 | **实测不通过**。产物中无版本字段。`__version__="0.3.0"`（`ra2forge/__init__.py:9`）与 `TOOL_VERSION="0.4"`（`ra2forge/install.py:262`）是**工具版本**，且后者只在安装时写入游戏目录的记录里，不在包里 | 同上 |
| 目标游戏/构建 | **实测不通过**。产物中无目标 exe / 构建指纹字段 | `stdout\31_readback_build1.txt` |
| 内容清单 | **部分**。BUILD_REPORT 的 `artifacts` 列了 6 件（3 图 + INI + mix + story.md），**未列** `BUILD_REPORT.txt` 自身与 `INSTALL.txt`（共 8 件） | `ra2forge/builder.py:603-608` |
| 依赖 | **实测不通过**。产物无依赖字段；`design.py` 无 dependency 字段；`install.py` 无包依赖解析 | `ra2forge/design.py:65-195`；`ra2forge/install.py:601-758` |
| 冲突 | **实测不通过**。产物无冲突声明；冲突只在**安装时**由 `preinstall_plan` 现场检出并写进游戏目录的 `ra2forge_install.json`，不随包分发 | `stdout\53_manifest_dump.txt`；`ra2forge/install.py:711-729,1093-1109` |
| 文件哈希 | **部分**。`sha256=` 后为 **16 位截断值**（`ra2forge/builder.py:580` `[:16]`），仅 6 件；非 64 位、非全量、非独立可校验清单。本次独立复算 6 件前缀全部 MATCH（`stdout\31_readback_build1.txt`） | `ra2forge/builder.py:574-580` |

**另有一件未接线的事实**：仓库另有离线原型 `docs/re/package_manifest_schema.md:69-88`（定义了 `schema_version` / `package_id` / `version` / `target_exe` / `target_sha256` / `files[].sha256` / `dependencies` / `conflicts`，恰好覆盖本行要求）和 `tools/validate_package_manifest.py`。本次实跑该验证器 exit=0（`stdout\72_prototype_validator.txt`），并确认 `ra2forge/**/*.py` 中 `validate_package_manifest|package_manifest|manifest.json|schema_version|package_id|target_sha256` **命中 0**（grep 实跑）。即：**有原型、无接线**；`ra2forge build` 不产出该清单。

---

### 第 2 行 · 内容组织 — **实测通过：地图/战役；实测不通过：规则/美术/音频与分阶段接入**

**实跑**：

```
python -X utf8 -m ra2forge inspect <写域>\build1\钢铁残响\ECH01.MAP
  -> ECH01.MAP: 40 sections; [Map] [Basic] [Houses] [Waypoints] [Structures]
     [Units] [Infantry] [Triggers] [Events] [Actions] [Tags] ...  (stdout\64_inspect.txt, exit=0)
powershell: 解析 ECH01.MAP 全部节名 -> stdout\73_map_sections.txt (40 节)
powershell: 统计包内扩展名 -> .INI 1 / .MAP 3 / .md 1 / .mix 1 / .txt 2  (stdout\73_map_sections.txt)
```

**实测结论**：

- 地图与战役：**实测通过**。3 张 .MAP + 关卡链 + 追加战役条目（`stdout\31_readback_build1.txt`：`ECH01→ECH02→ECH03→空`，末关 `EndOfGame=yes`）。
- 规则、单位/建筑、美术/音频：**实测不通过**为「内容类型」。40 个节全是地图内节（`IsoMapPack5` / `OverlayPack` / `Structures` / `Units` / `Infantry` …），包内 8 个文件后缀只有 `.MAP/.INI/.mix/.md/.txt`，**无** `rulesmd.ini`、无 SHP/VXL/CSF/WAV 等资源。`docs/DESIGN.md:55` 明写所用为「rulesmd 原版 id，原版引擎直接可用」；`README.md:128` 明写「暂不支持：…自定义 CSF 语音字幕」。单位/建筑只是**在地图上摆放原版 ID**（`ra2forge/builder.py:400-421`），不是内容扩展。
- 「分阶段接入」：**实测不通过**。代码与产物里没有阶段开关或按内容类型分批接入的机制；`docs/PROJECT_DIRECTION.md:65` 只把它列为目标。
- 「明确能力限制」：**部分有**，仅存在于文档（`README.md:124-129`、`docs/DESIGN.md:225`），**不随包分发**（包内 `INSTALL.txt` 无限制声明；`stdout\31_readback_build1.txt` 包文件清单可见）。

---

### 第 3 行 · 资源与注册 — **实测通过：MIX 分配 / 战役 ID / 散装 INI / 部分命名冲突；未证：查找与覆盖顺序**

**实跑**：`python -I -X utf8 <写域>\scripts\readback.py <写域>\build1\钢铁残响`（`stdout\31_readback_build1.txt`，exit=0）。该脚本用标准库独立重解 MIX 索引，不 import ra2forge。

```
BATTLEMD98.INI read-back:
  sections = ['Battles', 'RA2F1']
  [Battles] = {'15': 'RA2F1'}
  [RA2F1] = {CD=2, Scenario=ECH01.MAP, FinalMovie=, Description=<设计文件 description>}
  official battle-id sections = NONE

expandmd98.mix read-back (independent MIX index decode):
  flags=0 count=3 body_size=43315 data_start=46
  entry id=0x8067D343 / 0xC7C7A993 / 0xFAA78023
  expected map CRCs = ['0x8067D343','0xC7C7A993','0xFAA78023']
  id set equal? YES
  ECH01/02/03.MAP: bytes in MIX == loose MAP? YES (全部)
  known .INI names present as entry ids? NONE
  INI count in MIX (by probe) = 0
```

- **MIX 分配**：实测通过。`expandmd98.mix` 恰好装 3 张地图、0 个 INI；CRC 集合与独立复算一致；MIX 内字节与散装 .MAP 逐字节相同。构建器自检亦 `[PASS] expandmd98.mix: 3 entries, 0 INI`（BUILD_REPORT）。
- **战役 ID**：实测通过。`[Battles] 15=RA2F1`（索引 15 不占官方 1–14）；官方 ID 被拒（`stdout\12_validate_neg_official_id.txt`：`INVALID: campaign.id 'ALL1' is an official battle id ...`，exit=1）；产物读回断言「无 `[ALL1]/[SOV1]/[ALL02]..[SOV07]`」。
- **散装 INI**：实测通过。`BATTLEMD98.INI` 为包内独立文件，MIX 内 0 个 INI；机制说明见 `docs/DESIGN.md:171-174`、`ra2forge/builder.py:14-22`。
- **命名冲突检查**：**部分有（实测通过的部分）**。实测拒绝 `campaign.id=ALL1`（`stdout\12_...`）、重复关卡名（`stdout\13_...`：`INVALID: duplicate mission name 'NX01'`）、`next` 指向不存在关卡（`stdout\14_...`）；`_verify_battle_file` 读回断言无官方段名（`ra2forge/builder.py:224-229`）；`install.py:574-591` 把其它 `BATTLEMD*.INI` / `expandmd99.mix` / 旧清单列为 risk。`ra2forge/mixlib.py:344-356` 的 `write_mix` **没有 CRC 冲突/条目重名检查**（只对 name 排序后取 `crc_hash`），多包之间的战役 ID 冲突未在安装期检查（见第 6 行）。
- **资源查找与覆盖顺序**：**【未证】 + 无实现**。全仓库 `ra2forge/*.py` 中 `FindFirstFileA` / 覆盖顺序只出现在注释（`ra2forge/builder.py:14-22`、`ra2forge/mixlib.py:311-317`、`ra2forge/install.py:5`）与文档（`docs/DESIGN.md:171-174,192-195`）；唯一相关代码是 `install.py:574-586` 把「其它 `BATTLEMD*.INI`、`expandmd99.mix`」判为**无法判定**的 risk。工具**没有**资源查找器、没有覆盖顺序声明/控制/校验。引擎侧 `FindFirstFileA("BATTLEMD*.INI")` 与 `expandmd*.mix` 装载顺序的说法属运行期机制，本次零真机，**【未证】**，不作为能力具备的证据。

---

### 第 4 行 · 构建与校验 — **实测通过（5 个子项全通过）**

| 子项 | 实跑命令 | 实测输出 | 判定 |
|---|---|---|---|
| 输入校验 | `validate examples/demo_campaign.json` | `OK: 3 mission(s)` exit=0（`stdout\10_validate_demo.txt`）；缺文件时 `error: ... not found` exit=1（`stdout\15_...`） | 实测通过 |
| 缺失引用检查 | `validate fixtures\neg_missing_ref.json` / `neg_bad_next.json` | `INVALID: ... destroy_building references tag 'ghost_tag' but no structure carries it` exit=1；`INVALID: missions[0].next 'GHOST' does not name a mission of this campaign` exit=1（`stdout\11_...`、`stdout\14_...`） | 实测通过 |
| 构建报告 | `build ... --out build1` | 产出 `BUILD_REPORT.txt`（1707 B，sha256 `940c3055…`），含关卡链 / 自检 / 产物哈希（`stdout\31_readback_build1.txt` 全文） | 实测通过 |
| 产物读回校验 | 构建器自检 + 独立脚本 `readback.py` | BUILD_REPORT 7 条 `[PASS]`；独立复算 6 件 `sha256=<16>` 前缀全部 `MATCH`；3 张 MAP 的 `[Basic]` 读回 `NextScenario` / `EndOfGame` 与链一致；MIX 索引 CRC / 字节一致 | 实测通过 |
| 可重复构建验证 | **连跑两次** `build`（build1 / build2，不同 `--out`） | 8/8 逐件 `MATCH`，聚合树 sha256 `e88b055f…` 两侧相同，`total MISMATCH files = 0`（`stdout\30_repeat_compare.txt`） | 实测通过 |

**保留口径**：可重复构建是**本审计在外部实跑两次验证**的，`ra2forge` 自身**没有内建**可重复构建自检（grep `ra2forge/*.py` 无 reproducibility / 二次构建比对逻辑）。这不改变「产物可重复」的实测事实，但「工具自带验证」未具备。

---

### 第 5 行 · 安装与升级 — **实测通过：安装前检查/备份清单/卸载还原；实测不通过：升级迁移；部分有：失败恢复/依赖检查**

**CLI 暴露（实跑 `stdout\01_help.txt`）**：`{validate,build,install,uninstall,example,inspect}` —— **无 `upgrade` / `migrate` 子命令**。`uninstall --help` 有 `--legacy` / `--drop-legacy-battlemd`（旧版残留清理），不是升级迁移。

| 子项 | 实跑 | 实测输出 | 判定 |
|---|---|---|---|
| 安装前检查 | `install --package <包> --game <空目录>` | `error: ... does not look like a Yuri's Revenge directory (gamemd.exe not found)` exit=1；空目录**仍为空**（`stdout\40_...`、`stdout\43_post_refusal_state.txt`） | 实测通过 |
| 安装前检查 | 写入外部 `BATTLEMD98.INI` 后再 `install`（strict） | `install blocked by preflight - no file has been written: definite content conflicts ...` exit=1；目录文件列表/长度不变 | 实测通过 |
| 安装前检查 | 写入损坏 `ra2forge_install.json` 后 `install` | `hard blockers ... corrupt-manifest ... NOT bypassable` exit=1；目录不变（`stdout\42_...`） | 实测通过 |
| 备份清单 | `install --allow-content-conflict` 到写域沙箱 | `backup BATTLEMD98.INI -> BATTLEMD98.INI.ra2forge.bak` 等；`ra2forge_install.json` 里 `files[].backup` 逐件登记（`stdout\51_...`、`stdout\53_manifest_dump.txt`） | 实测通过 |
| 卸载还原 | `uninstall --game <沙箱>` | `restored ECH01.MAP.ra2forge.bak -> ECH01.MAP` 等；卸载后 3 个文件的 sha256 **与装前逐件相同**（`stdout\50_pre_install_state.txt` vs `stdout\55_post_uninstall_state.txt`） | 实测通过 |
| 失败恢复 | 3 次预检拒绝 + 装前/卸后快照 | 预检拒绝时「no file has been written」且目录指纹不变；但 `ra2forge/install.py:797` 自述「**Full write rollback stays out of scope**: see DLC_STRICT_AUDIT MEDIUM-3」 | **部分有**（零写预检 + 暂存写 + 读回校验实测通过；**跨多文件的完整事务回滚未测且代码声明不做**） |
| 依赖检查 | `install.py:615-618,670,574-592` + 实跑 | 只做**环境前置**：`gamemd.exe` 存在性、其它 `BATTLEMD*.INI`、`expandmd99.mix`、旧清单；**无包依赖声明/解析**（设计 JSON 与包内均无 dependency 字段，第 1 行已证） | **部分有** |
| 升级迁移 | `install` 包 A → 再 `install` 包 B（不同包） | `error: ... a previous ra2forge install ... would be replaced by a DIFFERENT package - **uninstall it first**` exit=1（`stdout\62_...`） | **实测不通过（无升级路径）** |
| 升级迁移 | 强推 `--allow-content-conflict` | 成功，但**旧包 A 的 `ECH01/02/03.MAP` 残留在游戏目录**，新清单只记包 B 文件（`stdout\63_...`、`stdout\66_post_forced_upgrade_state.txt`） | **实测不通过（留下孤儿文件）** |
| 重装机 | 再 `install` 同一包 A | 5 件 `unchanged (already up to date)`（`stdout\61_...`）——幂等重装，**不是版本升级** | 实测通过（但≠升级） |

`uninstall --legacy` 实跑（`stdout\65_uninstall_legacy.txt`）：空目录下输出「no `ra2forge_install.json` ... nothing recorded to remove」+「no `ra2forge_uninstall.txt`: falling back to the known legacy artefact set」。这是**旧版残留清理**，不是 v1→v2 升级迁移。

**文档矛盾（实测读到）**：`README.md:37-42` 与 `docs/DESIGN.md:206-218` 对同一旧版迁移步骤互斥（详见 STEP 1.3）。升级路径的文档本身不自洽。

---

### 第 6 行 · 内容隔离 — **部分有（检测并拒绝冲突实测通过；可并存范围/多包登记实测不通过）**

| 子项 | 实跑 | 实测输出 | 判定 |
|---|---|---|---|
| 检测并拒绝冲突（初版允许） | `install` 外部文件 / 不同包替换 | strict 预检 3 次拒绝，均 `no file has been written`（`stdout\40/41/42/62_...`） | 实测通过 |
| 释放冲突被记录 | `--allow-content-conflict` | `ALLOWED ... (recorded in the manifest)`；`ra2forge_install.json.precheck.allowed_content_conflicts` 逐条留痕（`stdout\51_...`、`stdout\53_...`） | 实测通过 |
| 明确包间冲突 | 读包内文件 | **包内无 `conflicts` 声明**；冲突只在安装时按「目标目录现场状态」判定，不随包分发（第 1 行） | 实测不通过 |
| 可并存范围 | 文档 + 实跑 | `docs/DESIGN.md:21-22` 写「多个战役包同时安装时，给每个包一个不同的 `campaign.id`」；但**构建默认两个包都用 `RA2F1` / `[Battles] 15`**（`stdout\31_` 与 `stdout\32_`），安装期**不校验**该 ID 是否已被别的包占用 | 实测不通过 |
| 多包登记 | `install` 包 B 覆盖包 A 后 | 游戏目录只有**一份** `ra2forge_install.json`，被后一次安装覆盖；`package` 字段只指向最后一个包（`stdout\53_`、`stdout\66_`） | 实测不通过 |

**具体缺口**：无随包的冲突/并存元数据；无多包安装登记（单记录、后装覆盖前装）；无跨包 `campaign.id` / `[Battles]` 索引占用检查；`docs/DESIGN.md` 的并存规则只靠作者手工遵守，工具不校验。

---

### 第 7 行 · 兼容策略 — **实测不通过（4 个子项全部没有实现）；真机维度未验**

**静态实跑**：grep `ra2forge/*.py` 中 `存档|联机|规则版本|补丁开关|save|multiplayer|rulesmd|art|audio|CSF|SHP|WAV` —— 命中项全部是「地图计时器 / 触发器 / CSF 标签注释 / 文件说明」等无关上下文，**无**兼容策略实现。设计 JSON 字段（`ra2forge/design.py:65-195`）与构建产物（8 件）里均无规则版本、补丁开关、存档兼容范围、联机一致性字段。

| 规范要求 | 实测 | 依据 |
|---|---|---|
| 标注补丁开关与规则版本 | **实测不通过**。无字段、无开关、无标注 | `ra2forge/design.py:65-195`；`stdout\31_readback_build1.txt` 包清单 |
| 存档兼容范围 | **实测不通过**。产物/代码无声明与检查 | 同上；`docs/PROJECT_DIRECTION.md:121` 把「验证存读档」列为 G3 验收，README.md:121-122 明写游戏内实测需玩家进行 |
| 联机内容一致性 | **实测不通过**。无字段、无检查 | 同上 |
| 不兼容时明确拒绝或提示 | **实测不通过（就兼容维度）**。工具唯一的拒绝是**文件系统/内容冲突**（第 5、6 行），没有任何基于规则版本 / 存档 / 联机的门禁 | `ra2forge/install.py:979-992` 三类 blockers/conflicts/risks |

**未验**：存档跨会话、联机双方一致性、规则版本兼容范围均需真机或联机样本，本次零真机 → **未验**（不补造）。

---

### 第 8 行 · 作者入口 — **实测通过（4 个子项全通过）**

| 子项 | 实跑 | 实测输出 | 判定 |
|---|---|---|---|
| 示例 | `example <写域>\fixtures\minimal_design.json` | `wrote ...\minimal_design.json` exit=0；随后 `build --design` 成功产出 1 关最小包（`stdout\20_`、`stdout\21_`） | 实测通过 |
| 内容规范 | 通读 `docs/DESIGN.md`（227 行） | 顶层结构 / 国家表 / 坐标 / 目标 / 关卡链 / 产物命名全覆盖 | 实测通过（文档存在） |
| 命令行工作流 | `--help` + 6 个子命令实跑 | `validate / build / install / uninstall / example / inspect` 全部 exit=0 或按预期 exit=1（`stdout\01_…07_`、`10_…15_`、`22/23_`、`40_…65_`、`64_`） | 实测通过 |
| 诊断报告 | `BUILD_REPORT.txt`（7 条 `[PASS]` + 产物哈希）、`inspect`（40 节 + `[Basic]` 摘要）、安装/卸载 `actions` 输出 | `stdout\31_`、`stdout\64_`、`stdout\51_`、`stdout\54_` | 实测通过 |
| 优先复用现有模块 | MCP stdio 实跑 `python -I -X utf8 <...>\mcp\ra2forge_mcp.py` | `tools/list` 返回 `validate_campaign / build_campaign / inspect_map`；`tools/call validate_campaign` 返回 `{"ok": true, "missions": 1}`（`stdout\70_mcp_probe.txt`, exit=0）；源码 `mcp/ra2forge_mcp.py:31-33` 直接 `from ra2forge import design, install; from ra2forge.builder import build` | 实测通过 |

**保留说明**：`mcp/ra2forge_mcp.py:56` 的 `out_dir` 默认 `"out"`（不在写域内），本次未以默认路径调用；`example` 子命令写用户指定路径（`ra2forge/cli.py:84-98`），本次全部指定到写域内。作者侧没有「包清单编写」入口 —— 离线原型 `tools/validate_package_manifest.py` 与 CLI 未接线（第 1 行实跑已证）。

---

## STEP 3 · 八行盘点表

> 判定口径：**实测通过**＝本次有命令+输出支撑该子项成立；**实测不通过**＝本次实跑证明该子项缺失/失败；**未测/未验**＝零真机或超出本次边界，明确写出、不补造。「有 / 部分有 / 没有」按**整行最低交付要求的达标程度**判定。

| 能力 | 规范最低要求（§2.C） | 实测结论 | 证据（命令 + 输出 / 文件:行） | 缺口（缺什么才能达标） |
|---|---|---|---|---|
| **包清单** | 稳定包 ID、版本、目标游戏/构建、内容清单、依赖、冲突及文件哈希（`PROJECT_DIRECTION.md:56`） | **部分有**（无任何 manifest 类文件；7 项要求中 5 项完全没有、2 项不完整） | `build --design examples/demo_campaign.json --out <写域>/build1`（exit=0，`stdout\22_build1.txt`）；`python -I -X utf8 scripts\readback.py`（`stdout\31_readback_build1.txt`）：`manifest-like filenames = NONE`、8 件文件；`BUILD_REPORT.txt` 全文；`ra2forge/builder.py:580` 截断 `[:16]`；`docs/re/package_manifest_schema.md:69-88` + `stdout\72_prototype_validator.txt` 原型验证器 exit=0、`ra2forge/**/*.py` grep 命中 0 | ① 产出独立 `manifest.json`（原型已有 schema，需接入 `builder.build`）；② 稳定且**每包唯一**的包 ID（现 `RA2F1` 是游戏段名且两包相同）；③ 包版本；④ 目标游戏/构建身份（target exe + sha256）；⑤ 依赖 / 冲突声明字段；⑥ 全量 64 位文件哈希（现 6 件、16 位截断、缺 BUILD_REPORT/INSTALL）；⑦ 内容清单覆盖全部 8 件 |
| **内容组织** | 地图与战役、规则、单位/建筑、美术/音频分阶段接入；明确能力限制（`:57`） | **部分有** | `inspect ECH01.MAP` → 40 节（`stdout\64_inspect.txt`）；节名清单 + 包内后缀统计（`.INI 1/.MAP 3/.md 1/.mix 1/.txt 2`，`stdout\73_map_sections.txt`）；`docs/DESIGN.md:55`「rulesmd 原版 id」；`README.md:128` 不支持自定义 CSF | ① 规则内容（rulesmd / 规则版本）接入；② 新单位/建筑定义（现仅摆放原版 ID）；③ 美术/音频（SHP/VXL/CSF/WAV）接入；④ 分阶段接入机制/开关；⑤ 能力限制随**包**分发（现只在文档） |
| **资源与注册** | 资源查找与覆盖顺序、MIX 分配、战役 ID、散装 INI 和命名冲突检查（`:58`） | **部分有** | `readback.py`（`stdout\31_readback_build1.txt`）：`[Battles]={'15':'RA2F1'}`、`official battle-id sections=NONE`、`expandmd98.mix count=3 / 0 INI / id set equal? YES / bytes in MIX == loose MAP? YES`；`stdout\12_validate_neg_official_id.txt` 官方 ID 被拒；`stdout\13_` 重名被拒；`ra2forge/mixlib.py:344-356`；`install.py:574-591` risk 扫描 | ① **资源查找与覆盖顺序**无实现（仅注释/文档；引擎机制【未证】）；② `write_mix` 无条目 CRC/重名冲突检查；③ 无跨包战役 ID / `[Battles]` 索引占用检查；④ 无覆盖顺序的声明、控制与校验 |
| **构建与校验** | 输入校验、缺失引用检查、构建报告、产物读回校验及可重复构建验证（`:59`） | **有**（5 子项全**实测通过**） | `validate` 正向 `OK: 3 mission(s)`（`stdout\10_`）；4 负例 exit=1（`stdout\11_…15_`）；`BUILD_REPORT.txt` 7 条 `[PASS]`（`stdout\31_`）；独立 `readback.py` 6 件哈希前缀全 `MATCH` + MIX 字节一致（`stdout\31_`、`stdout\32_`）；**两次 build 8/8 MATCH**（`stdout\30_repeat_compare.txt`） | 无阻断性缺口。保留：工具**未内建**可重复构建自检（本次由审计方外部实跑验证）；产物哈希为 16 位截断（与第 1 行合并整改） |
| **安装与升级** | 安装前检查、备份清单、失败恢复、依赖检查、升级迁移和卸载还原（`:60`） | **部分有** | `--help` 子命令表（`stdout\01_`，**无 upgrade**）；空目录/外部文件/损坏记录 3 次预检拒绝且目录零变化（`stdout\40_…43_`）；`ra2forge_install.json` 逐件 `backup`（`stdout\53_`）；卸载后 3 件 sha256 与装前相同（`stdout\50_` vs `stdout\55_`）；F3 `uninstall it first` 拒绝（`stdout\62_`）；F4 强推后孤儿 `ECH01/02/03.MAP`（`stdout\66_`）；`install.py:797` 完整回滚 out of scope；`README.md:37-42` vs `docs/DESIGN.md:206-218` 矛盾 | ① **升级迁移**：无 CLI 子命令、无代码路径、无版本追踪；强推会留旧包孤儿文件；迁移文档互斥；② **依赖检查**：只有环境前置，无包依赖声明/解析；③ **失败恢复**：无跨多文件完整事务回滚（代码自述不做，本次未测中途失败）；④ 安装记录只有一份且不记包版本/目标构建 |
| **内容隔离** | 明确包间冲突和可并存范围；初版允许检测并拒绝冲突，不承诺任意组合（`:61`） | **部分有** | strict 预检拒绝外部文件/不同包，均 `no file has been written`（`stdout\41_`、`stdout\62_`）；`--allow-content-conflict` 逐条留痕（`stdout\51_`、`stdout\53_`）；`docs/DESIGN.md:21-22` 并存建议；两包同为 `[Battles] 15=RA2F1`（`stdout\31_` vs `stdout\32_`）；覆盖后仅 1 份 `ra2forge_install.json`（`stdout\66_`） | ① 随包的 `conflicts` / 并存范围元数据；② 多包安装登记（现单记录、后装覆盖前装）；③ 跨包 `campaign.id` / `[Battles]` 索引占用校验；④ 卸载某包时不影响其它包的清单与文件 |
| **兼容策略** | 标注补丁开关与规则版本、存档兼容范围、联机内容一致性；不兼容时明确拒绝或提示（`:62`） | **没有** | `grep ra2forge/*.py` 兼容关键词无实现命中；`ra2forge/design.py:65-195` 与包内 8 件文件（`stdout\31_`）无相关字段；唯一拒绝来自 `install.py:979-992` 的**文件系统/内容**三类门禁；`README.md:121-122` 游戏内实测需玩家进行 | ① 规则版本标注 + 补丁开关字段；② 存档兼容范围声明与校验；③ 联机内容一致性校验；④ 基于兼容维度的明确拒绝/提示门禁。**真机存档/联机行为本次未验** |
| **作者入口** | 示例、内容规范、命令行工作流和诊断报告；优先复用现有模块（`:63`） | **有**（4 子项 + 复用全**实测通过**） | `example` 生成最小设计并成功 build（`stdout\20_`、`stdout\21_`）；`docs/DESIGN.md` 通读；6 子命令 `--help`/实跑（`stdout\01_…07_`、`64_`）；`BUILD_REPORT.txt` / `inspect` 诊断（`stdout\31_`、`stdout\64_`）；MCP stdio `tools/list` 3 工具 + `validate_campaign` 返回 `ok:true`（`stdout\70_mcp_probe.txt`）；`mcp/ra2forge_mcp.py:31-33` 复用 | 无阻断性缺口。保留：无「包清单编写」作者入口（原型未接线）；MCP `build_campaign` 的 `out_dir` 默认 `"out"` 不在写域，调用方须显式指定 |

**汇总**：`有` 2 行（构建与校验、作者入口）；`部分有` 5 行（包清单、内容组织、资源与注册、安装与升级、内容隔离）；`没有` 1 行（兼容策略）。

---

## STEP 4 · 连跑两次的产物哈希对比表（可重复构建判据）

**命令**（两次输入相同、输出目录不同，均未做归一化）：

```
$env:PYTHONPATH='D:\Project\ra2-campaign-forge'
python -X utf8 -m ra2forge build --design examples/demo_campaign.json --out <写域>\build1   # stdout\22_build1.txt, exit=0
python -X utf8 -m ra2forge build --design examples/demo_campaign.json --out <写域>\build2   # stdout\23_build2.txt, exit=0
python -I -X utf8 <写域>\scripts\repeat_compare.py <写域>\build1 <写域>\build2            # stdout\30_repeat_compare.txt, exit=0
```

| 相对文件 | build1 字节 | build2 字节 | sha256(build1) | sha256(build2) | 判定 |
|---|---:|---:|---|---|---|
| `钢铁残响/BATTLEMD98.INI` | 453 | 453 | `4e3417568924891792520ad8c3ab44f42e11fdc9934fb453d4db7210bf3d2c74` | `4e3417568924891792520ad8c3ab44f42e11fdc9934fb453d4db7210bf3d2c74` | **MATCH** |
| `钢铁残响/BUILD_REPORT.txt` | 1707 | 1707 | `940c30552dcf865d240d227546ab44ac57b10b6150ab5fef6645b42b78a8a59e` | `940c30552dcf865d240d227546ab44ac57b10b6150ab5fef6645b42b78a8a59e` | **MATCH** |
| `钢铁残响/ECH01.MAP` | 14226 | 14226 | `f363818f410d2bd5a9baec30099bb3d18ad76a4dd0e7a28956da36f97b28c66f` | `f363818f410d2bd5a9baec30099bb3d18ad76a4dd0e7a28956da36f97b28c66f` | **MATCH** |
| `钢铁残响/ECH02.MAP` | 13606 | 13606 | `723c797a7784e2040d25aea10c5484992720b09715bf9595d05f073fe40dc477` | `723c797a7784e2040d25aea10c5484992720b09715bf9595d05f073fe40dc477` | **MATCH** |
| `钢铁残响/ECH03.MAP` | 15483 | 15483 | `2f7f75afe8a4159bc1b861302a081a329bb5c76042b19d35991d531ab0141698` | `2f7f75afe8a4159bc1b861302a081a329bb5c76042b19d35991d531ab0141698` | **MATCH** |
| `钢铁残响/INSTALL.txt` | 1561 | 1561 | `05b00dfd30a64c432bd8ba4dde51205bdfd969058ba194b2445e60d0a4378cfd` | `05b00dfd30a64c432bd8ba4dde51205bdfd969058ba194b2445e60d0a4378cfd` | **MATCH** |
| `钢铁残响/expandmd98.mix` | 43361 | 43361 | `ee9e39e158eba9974b8bbeed83f62e987eb8324b440a6cd047e5788e70ac388f` | `ee9e39e158eba9974b8bbeed83f62e987eb8324b440a6cd047e5788e70ac388f` | **MATCH** |
| `钢铁残响/story.md` | 1127 | 1127 | `16e30c09391f62d27974f8ef16fda9bca572f3dff7639a62b22ee7543044522b` | `16e30c09391f62d27974f8ef16fda9bca572f3dff7639a62b22ee7543044522b` | **MATCH** |

```
file counts: build1=8 build2=8
aggregate tree sha256 build1 = e88b055ff9945029401e78b9d533d5060c90af9850f878db7205c09cda71013d
aggregate tree sha256 build2 = e88b055ff9945029401e78b9d533d5060c90af9850f878db7205c09cda71013d
aggregate verdict = MATCH
total MISMATCH files = 0
```

**MISMATCH 判定**：本轮 **0 件 MISMATCH**，因此无需判断时间戳/随机量归因；也**未做任何归一化或删除差异**，`repeat_compare.py` 对两棵树逐件做原始字节 sha256 比对。

为什么两轮一致（仅列实测/实读支撑项，不升格为普适结论）：
- `ra2forge/builder.py` 中无 `datetime` / `time` / `random` / `uuid` 调用（grep 实跑）；触发 ID 由 `_hex_id_gen(start)` 确定性递增（`builder.py:549-553`）；
- `ra2forge/maplib.py:160-161` 的树木散布用 `random.Random(seed or (row0*7919+col0*31+self.w))`，种子来自设计 JSON（`demo_campaign.json` 每个 `tree_rects` 都带 `seed`）；
- `ra2forge/mixlib.py:344-356` 的 `write_mix` 对 `names = sorted(files)` 排序后写索引，顺序确定；
- 唯一时间戳 `installed_at`（`install.py:1096`）属于**安装记录**，不是构建产物，故不影响本表。

【未证】：不同 Python 版本 / 不同系统区域设置 / 不同机器上的可重复构建未测，不把本机两轮一致外推为普遍可重复。

---

## 边界与未验

### A. 本次明确「实测通过」的项
`validate` 正负例、两次 `build` 成功、`BUILD_REPORT.txt` 自检、独立产物读回（MAP/INI/MIX 索引/字节/哈希前缀）、两次构建 8/8 sha256 MATCH、CLI 6 子命令、MCP 3 工具、预检 3 类零写拒绝、合成沙箱内备份清单与卸载还原逐字节回退、`inspect` 诊断输出、离线原型验证器可运行。

### B. 本次明确「实测不通过」的项
包清单的 5 个字段（包 ID / 版本 / 目标构建 / 依赖 / 冲突）；规则/美术/音频内容类型与分阶段接入；资源查找与覆盖顺序的**实现**（只有注释/文档）；升级迁移（无子命令、无代码路径、强推留孤儿文件）；包依赖解析；兼容策略 4 个子项；多包登记与跨包 ID 冲突校验；MIX 写入侧 CRC/重名冲突检查。

### C. 未测 / 未验（**不补造**）
1. **真机全链路未验**：未启动 `gamemd.exe`；BATTLEMD98.INI 是否真被引擎通配枚举、`expandmd98.mix` 是否真被加载、战役列表是否多出条目、关卡推进是否正确、`EndOfGame=yes` 实际效果 → **未验**（`README.md:121-122` 亦写需玩家进行）。
2. **存读档 / 联机**：存档兼容范围、跨会话保存加载、联机双方内容一致性 → **未验**（零真机，G3 验收项见 `PROJECT_DIRECTION.md:121`）。
3. **真机安装/卸载**：本次安装/卸载只在写域内的**合成沙箱**（惰性 `gamemd.exe` 文本占位）演练；`ra2youli\` 全程零读写（只做哈希取证），真实游戏目录上的安装/卸载 → **未验**。
4. **资源查找与覆盖顺序的引擎机制**：`FindFirstFileA("BATTLEMD*.INI")`（VA `0x52CBA0`）、`expandmd*.mix` 与 `ra2md.mix` 的装载先后、同 CRC 条目遮蔽 → **【未证】**（仅文档/注释转述，本次零真机，不作为能力或机制结论）。
5. **失败恢复**：只测了「预检拒绝 → 零写」；**写入开始之后**的真实中途失败（磁盘满、进程被杀、文件被占用）下的多文件事务回滚 → **未测**（且 `install.py:797` 自述完整回滚 out of scope）。
6. **内容隔离多包场景**：只做了「包 A 装完 → 强推包 B」的顺序合成演练；两个及以上包**并存**于真实游戏目录、分别卸载其中一个 → **未测**。
7. **输入面覆盖**：包清单/构建/校验只在 `examples/demo_campaign.json`（3 关）与 `example` 生成的 1 关设计上实跑；其它设计形状（分叉 `next`、多战役 ID、极大地图）→ **未测**。
8. **可重复性外部条件**：不同 Python 版本 / 时区 / 机器 / 文件系统 → **未测**（STEP 4 结论仅限本机这两轮）。
9. **指纹范围**：既有件指纹覆盖 `docs/`、`ra2forge/`、`mcp/`、`examples/`、`README.md` 共 453 件（内容 sha256）+ `ra2youli\` 顶层 425 件（内容 sha256）；**未**对仓库全树（如 `out/`、`extracted/`、`ref/`）做内容哈希，改以 ROOT 顶层条目清单作辅助。该范围限制如实声明。

### D. 零改动核验（收尾指纹，hashlib 实算）

```
python -I -X utf8 <写域>\scripts\fingerprint.py <写域>\evidence\baseline.json   # stdout\22_baseline_fingerprints.txt
python -I -X utf8 <写域>\scripts\fingerprint.py <写域>\evidence\closing.json    # stdout\23_closing_fingerprints.txt
python -I -X utf8 <写域>\scripts\compare_fingerprints.py <baseline> <closing>   # stdout\80_zero_change_compare.txt
```

| 范围 | 基线 | 收尾 | 判定 |
|---|---|---|---|
| 既有件内容聚合（453 件 / 9,189,931 B） | `1d49194d78a1dc7a2af153db4e8e442f210dd3b05fd0a49f2f461b7a14ed03c7` | 同 | **PASS**（added=NONE / removed=NONE / changed=NONE） |
| **`ra2youli\` 顶层文件清单哈希**（425 件 / 1,978,417,678 B，`name<TAB>size` 行的 sha256） | `0442594cc3282fb6620d02eb972e5534ef0db3f19ca2e187ece39ce89fd09dea` | 同 | **PASS** |
| `ra2youli\` 顶层 425 件内容聚合（name+size+sha256 行） | `8db912d6b8f0f521ca84657e61fa2b4eda1fe4eb7f4cb5596895daf3ea8caf3b` | 同 | **PASS** |
| ROOT 顶层条目清单（含 mtime_ns，**信息性**） | `ed7667395917a69a6e173f00453a8356ca7c428bcfe23b28fdac323e27170b91` | `651eb67d31a364e508ecba2e166f7d03ce35704726fabc7b10d628877efc79b3` | 差异仅 `lead` 目录的 **mtime_ns**（`stdout\81_repo_top_diff.txt`）：同一共享工作区其它会话在 `lead/` 下新建了 `round_gap_disposition_20261112`(0:57)、`re_chain_v2_xverify_20261112`(1:04) 等任务目录。去掉 mtime 后重算 `name+kind+size` 清单哈希两侧均 `37e5e3cf…`，**MATCH，无顶层条目增删/改大小**（`stdout\82_repo_top_mtime_free.txt`）。 |
| 无读取/哈希错误 | `errors = []` | `errors = []` | PASS |

> 结论：**既有文件内容与 `ra2youli\` 顶层 425 件文件的内容及清单前后逐字节一致**；唯一观测到的差异是共享工作区其它会话创建目录导致的 `lead` 父目录时间戳，非本审计写入、非文件内容变化。

### E. 铁律遵守声明
- 未启动任何游戏可执行文件；沙箱内 `gamemd.exe` 为 34 B 惰性文本占位，从未执行（`stdout\50_pre_install_state.txt` 记其 sha256 `f863e7da…`）。
- 未 attach、未读活进程内存、未写 hook/采样/MiniDump 代码。
- 未做 `git commit / push / reset / checkout`。
- 所有新建文件均在 `lead\dlc_capability_audit_20261112\` 内；所有 `--out` 均指向写域子目录。
- 所有指纹由 `hashlib` 实算；`target_sha256` 在原型 fixture 里是 `ECH01.MAP` 的真实 sha256，**仅用于满足 64 位格式规则**，不是任何游戏 exe 的身份声明（`stdout\71_make_manifest_fixture.txt` 已注明）。
- 未把读数升格成结论；所有运行期机制说法标【未证】。

---

## 收尾回执

**改了哪些文件**（全部为**新建**，位于唯一写域 `lead\dlc_capability_audit_20261112\`；既有件 0 改动、`ra2youli\` 0 改动）：

| 类别 | 件数 | 说明 |
|---|---:|---|
| `DLC_CAPABILITY_AUDIT.md` | 1 | 主交付（本文件） |
| `build1\钢铁残响\` / `build2\钢铁残响\` | 8 + 8 | 两次可重复构建产物（不同 `--out`） |
| `build_min\Example Operation\` | 6 | `example` 生成的 1 关最小包构建产物 |
| `stdout\*.txt` | 46 | 全部实跑 stdout/stderr + EXITCODE |
| `evidence\baseline.json` / `closing.json` | 2 | 前后指纹明细（各 172,469 B） |
| `fixtures\*.json` | 6 | 4 个负例设计 + 最小设计 + 原型清单 fixture |
| `scripts\*.py` | 5 | fingerprint / readback / repeat_compare / compare_fingerprints / make_manifest_fixture |
| `sandbox_*` | 5 目录 | 写域内的合成安装演练目录（`sandbox_empty` / `sandbox_conflict` / `sandbox_legacygate` / `sandbox_install` / `sandbox_upgrade`；含惰性占位与备份槽），全部在写域内 |

**跑了哪些命令**：见本报告 STEP 2「命令总表」与 `stdout\` 46 件日志；核心为 `python -X utf8 -m ra2forge {--help,validate,build,install,uninstall,example,inspect}`（配 `PYTHONPATH=D:\Project\ra2-campaign-forge`）、`python -I -X utf8 <写域>\scripts\*.py`、MCP stdio 探针、离线原型验证器、前后两次指纹与比对。**未执行任何 git 写操作，未启动任何游戏可执行文件。**

**结论一句话**：§2.C 八行能力实测盘点为「有 2 / 部分有 5 / 没有 1」——构建与校验、作者入口达标，包清单/内容组织/资源与注册/安装与升级/内容隔离均为部分具备（升级迁移与兼容策略是最大缺口），两次独立构建 8/8 产物 sha256 全 MATCH，既有 453 件与 `ra2youli\` 顶层 425 件指纹前后一致、零改动。

**遗留未验项**：真机战役注册/关卡推进/存读档/联机一致性；真实游戏目录上的安装与卸载；引擎资源查找与覆盖顺序机制【未证】；写入开始后的多文件事务回滚；多包并存与分别卸载；其它设计形状与跨机器可重复性；仓库全树（`out/`、`extracted/` 等）内容哈希未覆盖。详见「边界与未验」C 节。
