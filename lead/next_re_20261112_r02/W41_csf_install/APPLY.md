# W41 · APPLY（相对路径补丁 / 校验 / 回滚）

> 本卡**纯离线**：未启动游戏、未 attach、未写 `ra2youli/`、未改仓库 `ra2forge/`、
> 未动 W21–W40 任何目录（`ra2bench\langmd.mix` 只读）、git 只读。
> 所有产物只落在 `lead/next_re_20261112_r02/W41_csf_install/`。
> **本卡不写「CSF 功能可用」**——真机验证由另一张卡（W40）负责；本卡只做
> 离线实现与回归（见 `UNCOVERED.md` U1）。

---

## 1 · 交付树

```
lead/next_re_20261112_r02/W41_csf_install/
├── APPLY.md                       # 本文件（相对路径补丁 + 校验 + 回滚）
├── UNCOVERED.md                   # 未闭环 / [待运行验证] 清单
├── DISAGREE.md                    # 与 W30/W29/W38/W34 的差异与更正
├── PATCH_RELATIVE.diff            # v11 -> v12 相对路径 unified diff（a/ b/ 前缀）
├── V12_FILES.sha256.txt           # v12 每个源码/数据的 SHA-256 + 相对 v11 状态
├── ra2forge_patched_v12/
│   └── ra2forge/
│       ├── csf.py                 # MODIFIED：完整性守卫 + 官方基线加载 + require_complete
│       ├── builder.py             # MODIFIED：仅「官方基底克隆」路径 + --csf-out 归属守卫
│       ├── cli.py                 # MODIFIED：--allow-csf-out-in-game（默认关闭）
│       ├── install.py             # MODIFIED：清单/备份/卸载纳入 ra2md.csf + 永不释放冲突
│       ├── data/RA2MD.OFFICIAL.CSF        # NEW：官方 332,973 B 字节精确克隆
│       ├── data/RA2MD.OFFICIAL.LABELS.txt # NEW：5,211 个官方标签名（有序去重）
│       ├── data/MAPSELMD.OFFICIAL.INI     # IDENTICAL（W34 遗留）
│       └── (其余 9 个 .py + __init__/__main__)  # IDENTICAL，含 verify.py 逐字节未改
├── regress_dlc_v12.py             # 51 个既有用例（原样复制）+ CSF_INST1..6
├── out/
│   ├── SUMMARY.txt                # 57/57 汇总（含 assertions）
│   ├── SHA256_COMPAT.txt          # v12 无 CSF 开关 == v11 逐文件 SHA-256 对照表
│   └── <case>.log                 # 57 个用例各自的命令 + stdout + 退出码 + 判据
├── EVIDENCE/
│   ├── step1_extract_official_csf.py / .stdout.txt (EXITCODE=0) / step1_official_csf.json
│   ├── step2_file_manifest.py / .stdout.txt (EXITCODE=0)
│   ├── step2_newcases.stdout.txt (EXITCODE=0)
│   ├── step3_full_regress.stdout.txt (EXITCODE=0)
│   └── step3_make_patch.py / .stdout.txt (EXITCODE=0)
└── sandbox/                       # 自建测试目录（inert game dirs，从不执行 gamemd.exe）
```

---

## 2 · 相对路径补丁

`PATCH_RELATIVE.diff` 是 `difflib.unified_diff` 产出，路径为：

```
a/ra2forge/<file>
b/ra2forge/<file>
```

它描述的是 **W34 的 `ra2forge_patched_v11/ra2forge/` → 本卡
`ra2forge_patched_v12/ra2forge/`** 的变更，**不是**对仓库 `ra2forge/` 的改动。
两个 NEW 数据文件是二进制 / 85 KB 文本，补丁里不内联，只记录
`bytes` + `sha256`（由 `EVIDENCE/step1_extract_official_csf.py` 从
`ra2bench\langmd.mix` 只读提取产出，可复现）。

| 文件（相对 `ra2forge_patched_v12/ra2forge/`） | 状态 | 说明 |
|---|---|---|
| `csf.py` | MODIFIED | 新增 `CsfIncompleteError`；`OFFICIAL_CSF_*` 常量；`official_baseline_labels()` / `load_official_csf()` / **`assert_complete_csf()`**；`write_csf()` / `append_or_set_label()` 增 `require_complete=False` 可选参数（默认关，不影响 W30 低层用例） |
| `builder.py` | MODIFIED | `_csf_out_ownership_guard()`（W38 CRITICAL）；`_emit_csf_artifacts()` 重写为「只允许官方基底克隆」；`build()` 增 `install_game_dir` / `allow_csf_out_in_game` 可选参数；守卫在**首个文件系统写之前**执行 |
| `cli.py` | MODIFIED | 新增 `--allow-csf-out-in-game`（默认 False，危险开关）；把 `args.install` 作为 `install_game_dir` 传入 `build()` |
| `install.py` | MODIFIED | 新增 `CSF_NAME`；`package_files()` 条件纳入 `ra2md.csf`；`preinstall_plan()` 增 `csf_conflicts`；`install_package()` / `_refusal_text()` 对该类冲突**永不释放** |
| `data/RA2MD.OFFICIAL.CSF` | NEW | 官方 `ra2md.csf` 字节精确克隆（332,973 B，`sha256=1b90bb07…`） |
| `data/RA2MD.OFFICIAL.LABELS.txt` | NEW | 5,211 个官方标签名（case-fold 比对基准，85,527 B） |
| `verify.py` | **IDENTICAL** | `sha256=051c2e214b0d9…`，自 v10 起逐字节未改，语义未削弱 |
| 其余 9 个 `.py` + `__init__.py` / `__main__.py` | IDENTICAL | — |

---

## 3 · 改了什么（按需求逐条）

### 3.1 完整性守卫（`csf.py`）

`assert_complete_csf(csf_or_bytes)` 是唯一强制卡口，检查（依次）：

1. `parse_csf(strict=True)`：魔数 ` FSC`、版本 {2,3}、无截断、无尾随字节、
   `num_strings` 自洽、无未知值类型尾；
2. `version == 3`（官方 `ra2md.csf` 是 v3）；
3. 头 `num_labels == 解析标签数` **且** 头 `num_strings == 解析值数`（标签数一致）；
4. 值类型只允许 `b' RTS'` / `b'WRTS'`（官方实测只有这两种），且无
   `warnings` / `unknown_records` / `has_unparsed_tail`；
5. **case-fold 后的标签名集合必须 ⊇ 官方基线标签集**（从 `langmd.mix`
   提取的 5,211 个标签名）——缺失即抛 `CsfIncompleteError`，并列出前 12 个示例。

**没有提供 `--allow-partial-csf` 危险开关**（遵循任务书「不建议」）。唯一允许的
产出路径是「基于官方基底克隆」：

- `--csf-base B`：B 必须通过守卫，克隆到 `--csf-out`；
- 无 `--csf-base` 且 `--csf-out` 已存在：该现有文件必须**已经**是完整官方克隆
  （就地更新；畸形/最小/部分文件被拒且原文件零改动）；
- 无 `--csf-base` 且 `--csf-out` 不存在：克隆**内置**的官方字节精确副本。

`create_if_missing=True` 的最小 CSF 路径在构建链路里**已不存在**。
低层 `write_csf()` / `append_or_set_label()` 保留 `require_complete=False` 默认
（W30 的 CSF1/CSF3/CSF4 故意造最小 CSF 测读写能力，语义不得削弱）；**所有
安装产物写出都走 `require_complete=True`**。

### 3.2 纳入安装清单（`install.py`）

`package_files()` 在包内存在 `ra2md.csf` 时条件纳入（与 W34 `MAPSELMD.INI`
同构）。因为官方游戏目录**没有**散装 `ra2md.csf`：

- 安装 = **CREATE**（`CSF_INST2` 日志：`created ra2md.csf`）；
- 清单记录该文件 + 精确 sha256，`verify` 逐个文件校验（**verify.py 未改**，
  它本就遍历 `manifest["files"]`）；
- 卸载 = **DELETE**（`removed ra2md.csf`），无 `.ra2forge.bak` 残留，游戏目录
  `sha_tree` 与安装前逐字节相同 —— 正是 W21 `original_absent` 陷阱要求的
  CREATE/DELETE 语义（见 `W21_dlc_orphan/DISAGREE.md:17-24`）。

若游戏目录**已有非我方** `ra2md.csf`：按 W34 `MAPSELMD.INI` 的既有语义判
**definite preflight conflict**，默认拒绝，且 `--allow-content-conflict`
**永不释放**（与 `MAPSEL_NAME` 并列 `csf_conflicts`）。字节相同但未登记的
「adopt」态同样拒绝。拒绝时零写入（`CSF_INST3`）。

### 3.3 路径归属守卫（补 W38 CRITICAL，`builder.py` / `cli.py`）

W38 `WRITE_ENTRY_AUDIT.tsv:11-13,18-22` 把 `builder.py:434-437` /
`cli.py:140-146` 的 `--csf-out` 直写任意路径标为 CRITICAL。本卡：

- `_csf_out_ownership_guard()` 在 `build()` **第一个文件系统写之前**运行；
- 游戏目录判定与 `install.preinstall_plan()` 一致：目录含 `gamemd.exe`；
  同时检查显式 `--install` 目录 + `--csf-out` 的所有祖先；
- **默认**：落在游戏目录内即 `BuildError` 拒绝，零写入，并指向正确通道
  `build --install` / `install --package`（该通道把 `ra2md.csf` 走完整
  preflight/备份/清单/卸载）；
- **显式确认**：仅当给出 `--allow-csf-out-in-game`（默认关闭）时允许，
  但仍做目标身份判定（纯文件名、非保留槽 manifest/seal/backup/stage、
  非符号链接别名），并在 `BUILD_REPORT.txt` 打 `[WARN]` 明示
  **绕过清单 → 该文件 uninstall 不会删除（W21 孤儿风险）**。

### 3.4 向后兼容（`CSF_INST5`）

不启用任何 CSF 相关开关时，v12 构建与 v11 **逐字节相同**：
`out/SHA256_COMPAT.txt` 给出 8 个产物文件的 `v11 sha256 / v12 sha256 /
MATCH` 对照表（8/8 MATCH，VERDICT: IDENTICAL）。`MS4` 的
v12-默认-构建 == v10 参考构建也仍成立。

### 3.5 回归（`regress_dlc_v12.py`）

51 个既有用例**原样复制**（只把根常量重指向 v12、并在
`expected_digest()` 里加一条「包内存在 `ra2md.csf` 才纳入」的镜像分支，
对 51 个用例的 shipped set 零影响）。新增 `CSF_INST1..6`：

| 用例 | 覆盖 |
|---|---|
| `CSF_INST1` | 完整克隆通过 / 最小+部分文件 API 拒绝 / `require_complete` 写零字节 / build 部分 `--csf-out` 与部分 `--csf-base` 被拒 |
| `CSF_INST2` | 安装 → verify(exit 0, ra2md.csf ok) → 卸载 → 游戏目录逐字节还原（无散装 csf） |
| `CSF_INST3` | 既有非我方 csf ⇒ preflight 拒绝 + 零写入；`--allow-content-conflict` 不释放；byte-identical 未登记态也拒；无冲突对照成功 |
| `CSF_INST4` | `--csf-out` 指向游戏目录内 ⇒ 守卫触发、零写入；显式开关路径仍产出完整克隆并打 WARN |
| `CSF_INST5` | 无 CSF 开关 ⇒ v12 == v11 逐文件 SHA-256 对照表 + `--csf-out` 只新增 2 个 CSF 产物 |
| `CSF_INST6` | 升级 / 备份 / 还原路径同样覆盖 `ra2md.csf`（镜像 W34 MS5 restore 场景，`original_absent` 旗标正确） |

---

## 4 · 校验（亲自跑通）

```
cd lead/next_re_20261112_r02/W41_csf_install
python -B -X utf8 regress_dlc_v12.py
```

`[本次实测]` 结果（`EVIDENCE/step3_full_regress.stdout.txt`，
`out/SUMMARY.txt`）：

```
cases: 57  passed: 57  failed: 0
assertions: 516 passed / 0 failed
exit: 0
```

其它可复跑校验脚本（均为离线、只读外部文件）：

| 脚本 | stdout | exit |
|---|---|---|
| `EVIDENCE/step1_extract_official_csf.py` | `step1.stdout.txt` | 0 |
| `EVIDENCE/step2_file_manifest.py` | `step2_file_manifest.stdout.txt` | 0 |
| `EVIDENCE/step3_make_patch.py` | `step3_make_patch.stdout.txt` | 0 |

关键不变量（脚本内断言 + 人工复核）：

- `verify.py` `sha256 = 051c2e214b0d9862358c5732eaa91f70346231050b82df9f48419d64012e5e85`
  （= v10/v11 的 `051C2E21…`，逐字节未改）；
- `TOOL_VERSION = "1.0"` 未动；14 个 `.py`（未新增模块文件）+ 2 个 NEW 数据文件；
- 官方 `ra2md.csf`：332,973 B、v3、5,211 标签、语言码 9、值类型仅
  `b' RTS'`/`b'WRTS'`、`MSG:UnableMapSelect = 「無法啟始選取地圖！」`
  （`EVIDENCE/step1_official_csf.json`）。

---

## 5 · 回滚

v12 是**独立目录**，不覆盖 v11、不写仓库 `ra2forge/`：

1. **停用**：把调用方指向的包根从
   `.../W41_csf_install/ra2forge_patched_v12/` 改回
   `.../W34_mapselmd/ra2forge_patched_v11/` 即可，v11 目录逐字节未动。
2. **撤销补丁**：以 `PATCH_RELATIVE.diff` 反向 `patch -R`（基为 v11 的
   `ra2forge/`），再删除 2 个 NEW 数据文件；或直接删除整个
   `ra2forge_patched_v12/` 目录（无共享状态）。
3. **已安装到某游戏目录的 `ra2md.csf`**：用 v12 的
   `python -m ra2forge uninstall --game <dir>` 卸载 —— 清单记录了它，
   卸载会 DELETE（回到无散装 csf 的初始态，`CSF_INST2` 已逐字节证明）。
   ⚠ 例外：若当初是用 `--allow-csf-out-in-game` **直写**进游戏目录（绕过
   install 清单），该 `ra2md.csf` 是未登记文件，uninstall 不会删除，需手工
   移除 —— 这正是 `BUILD_REPORT.txt` `[WARN]` 与 `UNCOVERED.md` U3
   明示的风险。
4. **无全局副作用**：未改 git、未写注册表、未写游戏进程/内存、未写
   `ra2youli/`、未写 W21–W40。

---

## 6 · 纪律自检

| 约束 | 状态 |
|---|---|
| 纯离线 / 不启动游戏 / 不 attach | ✅ 全程 `python -B` 子进程 + 文件 I/O |
| 不写 `ra2youli` | ✅ 仅 READ（继承用例读其 manifest / langmd.mix，均字节拷进 sandbox） |
| 不改仓库 `ra2forge/` | ✅ |
| 不动 W21–W40 | ✅ 仅 READ 引用 |
| git 只读 | ✅ 未执行任何写 git 命令 |
| 只读 `ra2bench\langmd.mix` | ✅ `step1` 以 `MixFile` 只读打开 |
| 只写 `W41_csf_install/` | ✅ |
| 不写「CSF 功能可用」 | ✅ 全文未出现该结论；真机归 W40 |
| 不削弱 51 例 / `verify.py` 语义 | ✅ 51 个既有用例 51/51 全过（总 57/57），`verify.py` 逐字节未改 |
