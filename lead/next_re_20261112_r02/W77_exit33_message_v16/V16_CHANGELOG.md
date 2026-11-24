# V16_CHANGELOG — W77: EXIT 33 message product-language rewrite (message-only)

Card: `W77_exit33_message_v16` · base: `W60_battlemd_inplace\ra2forge_patched_v15` · date: 2026-11-14
Executor: GLM-5.3-Flash · timebox 70 min · 纯离线：I launched 0 / attached 0（未启动 gamemd.exe、未 attach、未读 `.game_instance.lock`；W76 真机卡不受干扰）

## 0. 结论口径（先读这个）

**v16 的 EXIT 33 消息已改为产品语言；96 个继承用例 + 1 条新用例（W77_1）全绿。**
本卡**只改了字符串**（外加 1 条新用例与 1 篇产品文档），**没有**改任何退出码、判定分支、门槛或阈值。
**不得**表述为"多包共存已支持"——v16 依然是"一次只支持一个战役包"，只是把这句话直说了。

分级标记：`[本次实测]` = 本卡实测输出；`[本次读码]` = 本卡读 v15/v16 源码；`[静态推断]` = 未实测的推断；`[转引]` = 引自其他卡的文档。

## 1. 改了哪几处（文件:行）

### 改动 1 — `ra2forge_patched_v16\ra2forge\resolve_integration.py:963-1001`（v15 中为 963-972）
- 抛出点：`inplace_preflight()`（`resolve_integration.py:936`）里 `BI.is_official(data)` 为 False 的分支——即 **W74 实测的第二包安装落点** `[本次实测]`（W77_1e: exit 33）。
- 该分支先于 `install.py:2032` 的 PKG-IDENT01 门（`[本次读码]` `install()` 顺序：`_s3_guard_gate` → `install_resolve` → `inplace_preflight`(2026) → identity 门(2032)），所以 EXIT 3 `package_mismatch` 文案在路线 (a) 这条路径上永远到不了——这正是 W74 的发现 `[转引]` REVIEW\LEAD_VERIFY_W74.md §5。
- 改动内容：**仅 message 文本**。`exit_code=EXIT_INPLACE_OFFICIAL_MISMATCH`、`reason_code="INPLACE_OFFICIAL_MISMATCH"`、`plan=plan` 三个机器可读参数原样未动。
- 同函数的 ABSENT 分支（v15/v16 `resolve_integration.py:956-962`，"the official loose BATTLEMD.INI is ABSENT"）**未改**——W74 场景不含它，保持最小改动面。
- 渲染链未改：`ResolveIntegrationRefused.__str__`（`resolve_integration.py:226-227`）产 `[REASON exit=N] ` 前缀；`cli.py:182-188` `_w46_refusal()` 打印 `error: {exc}` 到 stderr 并返回 `exc.exit_code`。CLI 侧零改动 `[本次读码]`。

### 改动 2 — 新增 `ra2forge_patched_v16\docs\ONE_PACKAGE_AT_A_TIME.md`（53 行）
- v15 包内没有 README/INTEGRATION.md（`[本次实测]`：包树仅 `ra2forge\`），按任务书落在"否则新增"分支。
- 写明产品约束「One campaign package at a time」、用户会看到的新文案、为什么拒绝、怎么办（uninstall → 再装）、W74/LEAD 裁决溯源。

### 改动 3 — `regress_dlc_v16.py`（由 `W60_battlemd_inplace\regress_dlc_v15.py` 复制而来，3811 行 → ~3900 行）
路径级最小适配 + 1 条新用例，**96 个继承用例体逐字未动**：
| 位置 | 改动 |
|---|---|
| 文件头 docstring | 加一段 W77 说明（复制来源、重指向、+1 用例、message-only） |
| `W43_ROOT_NAME` | `"W60_battlemd_inplace"` → `"W77_exit33_message_v16"`（目录断言） |
| `V12_ROOT` | `ra2forge_patched_v15` → `ra2forge_patched_v16`（S3/S4/S5 经 `bind_*` 全部跟随，case 文件本身零改动） |
| 新增 `case_W77_1`（约 60 行） | 见 §4；复用 s5_cases 的 harness helpers（`_build/_install/_golden_official/_manifest/_fsfile/_inplace_fs/_design`） |
| `CASES` 字典 | 增 `"W77_1": case_W77_1` |
| `main()` summary 头两处字符串 | 标题改为 W77 v16；加一行 `W77 EXIT-33 message cases: 1` |
| `SANDBOX`/`OUT` | **未改**——它们从 `W43_ROOT` 派生，随目录断言自动落在本卡 `sandbox\`、`out\`，W60 卡零写入 |

`REPO_ROOT` 未改：本卡与 W60 同为 `lead\next_re_20261112_r02\` 的直接子目录（深度一致，`parents[2]` 仍解析到仓库根）。

### 改动 4 — 复制件 `s3_cases.py` / `s4_cases.py` / `s5_cases.py`
- `s3_cases.py`、`s5_cases.py`：与 W60 原件逐字节一致（`[本次实测]`），零改动。
- `s4_cases.py`：**仅 1 处文件集范围适配**（case_S4_8 内 delta 遍历从整包 `rglob("*")` 收窄到 `ra2forge/` 子树，2 行收集器改动 + W77 注释；S4_8a–g 的断言文本与判定**逐字未动**）。原因：任务书明确要求在**包内**新增 `docs\ONE_PACKAGE_AT_A_TIME.md`，整包遍历会让该文档进入 `added` 并把 S4_8e 的"v14→v15 source delta is CLOSED (3 changed + 2 added)"精确列表断言打红——文档增删不是该断言要守护的事实（源码封闭性）。这是全卡唯一一处动到用例文件正文的编辑，动机与替代方案记录在 `DISAGREE.md` §D1。
- 夹具适配（零代码）：S3_19/S3_20/S3_22 与 S4_8 还读**卡内**只读夹具，本卡没有——已从 W60 卡**只读复制**进来：`s1_revision\`（2 个 json）、`TRACK_B_gates.json`、`baseline_v14\W46_resolve_integration\ra2forge_patched_v14\`（23 个文件，SHA 与 W60 原件一致）。第一次运行在 S3_19 因缺夹具 FileNotFoundError 中断（run1 记录见 `out\`），复制后 run2 全量重跑。

## 2. 改前 / 改后原文对照

### 改前（v15，`resolve_integration.py:964-972`）
```python
    data = target.read_bytes()
    if not BI.is_official(data):
        raise ResolveIntegrationRefused(
            "INPLACE_OFFICIAL_MISMATCH: the loose BATTLEMD.INI on disk is not "
            f"the official baseline (sha={BI.sha256(data)[:16]}..., "
            f"expected {BI.official_sha256()[:16]}...). W60 rewrites ONLY the "
            "official bytes; a modified/third-party file is a content "
            "conflict and is refused BEFORE any write. Zero bytes written.",
            exit_code=EXIT_INPLACE_OFFICIAL_MISMATCH,
            reason_code="INPLACE_OFFICIAL_MISMATCH", plan=plan)
```
用户实际看到（W74 实测口径）：
```
error: [INPLACE_OFFICIAL_MISMATCH exit=33] INPLACE_OFFICIAL_MISMATCH: the loose
BATTLEMD.INI on disk is not the official baseline (sha=..., expected ...). W60
rewrites ONLY the official bytes; a modified/third-party file is a content
conflict and is refused BEFORE any write. Zero bytes written.
```

### 改后（v16，同分支；完整 diff 见 `out\diff_v15_v16.patch`）
```python
    data = target.read_bytes()
    if not BI.is_official(data):
        # W77 (message-only change, no verdict/logic change): ... 注释 13 行 ...
        mid = manifest if isinstance(manifest, dict) else {}
        pid = mid.get("package_id")
        pver = mid.get("package_version")
        pid = pid.strip() if isinstance(pid, str) and pid.strip() else None
        pver = pver.strip() if isinstance(pver, str) and pver.strip() else None
        if pid and pver and pver != "unknown":
            installed = f"campaign package '{pid}' (version {pver})"
        elif pid:
            installed = f"campaign package '{pid}'"
        else:
            installed = None
        if installed:
            cause = (f"{installed} is already installed in {game}: its "
                     "install rewrote the official loose BATTLEMD.INI, and "
                     "this version supports ONE campaign package at a "
                     "time, so installing another package here is refused "
                     "BEFORE any write ")
        else:
            cause = ("a campaign package is installed here whose record "
                     "carries no readable identity, or the official loose "
                     "BATTLEMD.INI was changed outside this tool; this "
                     "version supports ONE campaign package at a time, so "
                     "installing a package over a changed official file is "
                     "refused BEFORE any write ")
        raise ResolveIntegrationRefused(
            "INPLACE_OFFICIAL_MISMATCH: " + cause +
            "(the loose BATTLEMD.INI on disk is no longer the official "
            f"baseline, sha={BI.sha256(data)[:16]}..., expected "
            f"{BI.official_sha256()[:16]}...). To install the new package, "
            f"first run: ra2forge uninstall --game {game}. Zero bytes "
            "written.",
            exit_code=EXIT_INPLACE_OFFICIAL_MISMATCH,
            reason_code="INPLACE_OFFICIAL_MISMATCH", plan=plan)
```
实际渲染（有安装记录时，`<package_id>`/`<version>` 取自既有 `ra2forge_install.json` 的 `package_id`/`package_version`）：
```
error: [INPLACE_OFFICIAL_MISMATCH exit=33] INPLACE_OFFICIAL_MISMATCH: campaign
package 'org.ra2forge.w77.alpha' (version 1.0) is already installed in
<game>: its install rewrote the official loose BATTLEMD.INI, and this version
supports ONE campaign package at a time, so installing another package here is
refused BEFORE any write (the loose BATTLEMD.INI on disk is no longer the
official baseline, sha=..., expected ...). To install the new package, first
run: ra2forge uninstall --game <game>. Zero bytes written.
```

### 措辞决策（为什么这样写）
1. **先原因后动作**：用户最先需要知道"为什么装不进去"——因为已有一个包改写过官方 BATTLEMD.INI，且本版本一次只支持一个。任务书原文措辞被逐句落实（`[转引]` 任务书 §任务 3）。
2. **删掉 "content conflict"**：v15 的说法让用户以为"我的文件坏了"。v16 里该短语 0 出现（W77_1h 断言）。"modified/third-party" 归因也从主路径移除——W74 场景里文件是**上一个包改的**，不是用户弄坏的。
3. **删掉内部术语 "W60"**：卡片编号对用户无意义。
4. **机器可读部分逐字保留**：reason code `INPLACE_OFFICIAL_MISMATCH`（`__str__` 前缀 + 正文开头，双重保留兼容任何 grep stderr 的脚本）、`exit=33`（`__str__` + `exit_code`）、sha 对比（on-disk vs expected）、`Zero bytes written.`（安全承诺）。
5. **`<package_id>`/`<version>` 的取值**：从 `plan["manifest"]`（既有安装记录）取，取不到时降级为"记录里没有可读身份（或文件在工具外被改过）"的诚实变体——拒绝行为不变，只是文案分两档。这个降级分支只在无记录/未声明身份时出现，不在 W74 主路径上。
6. **ABSENT 分支未动**：同一 reason code 的另一条消息（文件不存在）不是 W74 场景，保持最小 diff。`[静态推断]` 它的措辞产品化可以作为后续小卡。

## 3. v15 vs v16 diff 统计
- 包目录（`ra2forge_patched_v15` ↔ `ra2forge_patched_v16`）：**2 个文件变更，+93 行 / -5 行**（`docs\ONE_PACKAGE_AT_A_TIME.md` +53 全新增；`resolve_integration.py` +40/-5）。
- 逐字节确认：v16 其余 22 个文件与 v15 完全一致（diff --stat 仅列出上述两处）。
- 回归脚本侧（复制件）：96 个继承用例体 0 改动；脚本级改动为 docstring 段、`W43_ROOT_NAME`、`V12_ROOT`、新用例块、`CASES` 注册、summary 标题 2 处字符串。

## 4. 新用例 W77_1 断言了什么（9 条 check）
1. **W77_1a/1d** 包 A、包 B inplace 构建 exit 0（不同 `package_id`，同 feature 形状）。
2. **W77_1b** 包 A 安装进 golden 游戏目录 exit 0（路线 (a) 正常装上）。
3. **W77_1c** 安装记录记录 A 的 id/版本（v16 文案引用的数据源）。
4. **W77_1e** 包 B 装同一目录：**退出码 33** 且 stderr/stdout 含 `INPLACE_OFFICIAL_MISMATCH`（W74 路径复现 + reason code 保留）。
5. **W77_1f** 产品语言关键词齐备：已装包 id（`org.ra2forge.w77.alpha`）+ `version 1.0` + `ONE campaign package at a time`（"一次只支持一个"的英文等价）+ `uninstall`。
6. **W77_1g** 救济命令具体到本目录：`ra2forge uninstall --game <该游戏目录>`。
7. **W77_1h** 机器可读件保留：`sha=`、`expected `、`Zero bytes written`，且 `content conflict` **不再出现**。
8. **W77_1i** 拒绝的第二次安装零写入：游戏目录字节不变，安装记录仍属包 A。
（a–i 共 9 条 check → 套件总断言 835 + 9 = 844，与实测一致。）

## 5. 回归结果（硬验收，`[本次实测]` run2 = `out\regress_full_stdout.txt` + `out\SUMMARY.txt`）
- **cases: 97 passed: 97 failed: 0**（96 个继承用例逐字未动 + 1 条 W77_1）
- **assertions: 844 passed / 0 failed**（继承 835 + W77_1 9；与 v15 的 835 基线逐条对应）
- **退出码 0**（REGRESS_EXIT=0）
- 逐例日志：`out\<case>.log` 共 97 份；全量 stdout：`out\regress_full_stdout.txt`；摘要：`out\SUMMARY.txt`
- run1 曾在 S3_19 因缺卡内夹具 FileNotFoundError 中断（夹具复制后 run2 全量重跑），run1 记录保留在 git 历史外的本卡 `out\regress_full_stdout.txt`（被 run2 覆盖；中断点为 S3_19，S3_1–S3_18 及之前 88 例已 PASS——恢复自 stdout 摘要 `[本次实测]`）

## 6. 纪律核对
- 只写本卡目录（`W77_exit33_message_v16\`）；v15 源包只读（复制产生 v16）；`ra2forge/ra2opt/ra2bench` 未动；W21–W76 未动；git 仅 `diff --no-index`（读）。
- 未写 `ra2youli`；回归只读其 `ra2forge_install.json` 与 `langmd.mix`（v15 套件既有行为 `[本次读码]` regress 头注释）。
- 纯离线：**I launched 0 / attached 0**。
