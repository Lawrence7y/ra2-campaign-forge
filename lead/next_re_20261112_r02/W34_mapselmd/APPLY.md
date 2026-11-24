# W34 · APPLY（相对路径补丁 / 校验 / 回滚）

> 本卡**纯离线**，从未写仓库 `ra2forge/`、从未写 `ra2youli/`、从未改 W21–W33 任何目录、`ra2bench` 只读、git 只读。
> 所有产物只落在 `lead/next_re_20261112_r02/W34_mapselmd/`。**本卡不宣称「已修复战役推进」**——真机验证是后续独立卡（见 `UNCOVERED.md` U1）。

---

## 1 · 交付树

```
lead/next_re_20261112_r02/W34_mapselmd/
├── MAPSELMD_SPEC.md              # 格式定谳 + 证据 + 五问逐答
├── DISAGREE.md                   # 与 W33/W29/W30 的差异与更正
├── UNCOVERED.md                  # 未闭环 / [待运行验证] 清单
├── APPLY.md                      # 本文件
├── PATCH_RELATIVE.diff           # v10 -> v11 相对路径 unified diff（a/ b/ 前缀）
├── V11_FILES.sha256.txt          # v11 每个交付源码的 SHA-256 / 状态
├── ra2forge_patched_v11/
│   └── ra2forge/
│       ├── builder.py            # MODIFIED：新增 --mapselmd 接线（默认关）
│       ├── cli.py                # MODIFIED：--mapselmd / --mapselmd-base
│       ├── install.py            # MODIFIED：清单 + 备份/卸载 + 冲突预检
│       ├── mapselmd.py           # NEW：完整克隆 + 追加生成器
│       ├── data/MAPSELMD.OFFICIAL.INI  # NEW：官方 5,573 B 字节精确克隆
│       └── (其余 10 个 .py)       # IDENTICAL，含 verify.py 逐字节未改
├── regress_dlc_v11.py            # 45 个既有用例 + MS1..MS6
├── out/
│   ├── SUMMARY.txt / RUN_SUMMARY.txt     # 51/51 汇总（含 exit）
│   ├── full_run.txt / full_run.exitcode.txt
│   ├── SHA256_V10_V11.txt        # v10/v11 逐文件 SHA-256 对照表
│   ├── compat_sha256.json        # step4 机器可读对照
│   └── <case>.log                # 51 个用例各自的命令 + stdout + 退出码 + 判据
├── EVIDENCE/
│   ├── step1_extract_mapsel.py / .stdout.txt / .exitcode.txt  (0)
│   ├── step2_disasm_mapsel.py / .stdout.txt / .exitcode.txt   (0)
│   ├── step3_disasm_stage.py / .stdout.txt / .exitcode.txt    (0)
│   ├── step4_compat_sha256.py / .stdout.txt / .exitcode.txt   (0)
│   ├── MAPSELMD.OFFICIAL.INI     # 从 ra2md.mix 解出的官方原文（5,573 B）
│   └── step1_extract.json        # id / 偏移 / 大小 / 哈希 / 行尾统计
└── sandbox/                      # 自建测试目录（inert game dirs，从不执行 gamemd.exe）
```

---

## 2 · 相对路径补丁

`PATCH_RELATIVE.diff` 是 `difflib.unified_diff` 产出，路径为：

```
a/ra2forge_patched_v10/ra2forge/<file>
b/ra2forge_patched_v11/ra2forge/<file>
```

它描述的是 **W30 的 `ra2forge_patched_v10/ra2forge/` → W34 的 `ra2forge_patched_v11/ra2forge/`** 的变更，不是对仓库 `ra2forge/` 的改动。

| 文件（相对 `ra2forge_patched_v11/ra2forge/`） | 状态 | 说明 |
|---|---|---|
| `builder.py` | MODIFIED | `build()` 增 `mapselmd=False` / `mapselmd_base=None`；新增 `_emit_mapselmd()`；`_write_build_report` / `_write_install_readme` 增可选参数（默认分支字节不变） |
| `cli.py` | MODIFIED | 增 `--mapselmd`、`--mapselmd-base`；`--mapselmd-base` 单独使用返回 2 |
| `install.py` | MODIFIED | 增 `MAPSEL_NAME`；`package_files()` 条件纳入 `MAPSELMD.INI`；`preinstall_plan()` 增 `mapsel_conflicts`；`install_package()` 对该类冲突**永不释放** |
| `mapselmd.py` | NEW | `validate_official_base` / `load_bundled_official` / `stage_names_for` / `faction_for` / `build_mapselmd` / `write_mapselmd` |
| `data/MAPSELMD.OFFICIAL.INI` | NEW | 5,573 B，SHA-256 `074ccccd9e156d586d0ed099ceab78b3d72384c808725d8b5bee2c9799691d52` |
| `csf.py`, `design.py`, `format80.py`, `lzo.py`, `maplib.py`, `mixlib.py`, `triggers.py`, `verify.py`, `__init__.py`, `__main__.py` | **IDENTICAL** | 尤其 `verify.py` 与 v10 逐字节相同（既有语义零削弱） |

**应用方式（示例，全部在只读参考副本上操作）**

```bash
# 从 v10 复制一份工作副本，然后按 diff 落地（或直接使用本卡已交付的 v11 目录）
cp -r lead/next_re_20261112_r02/W30_csf_capability/ra2forge_patched_v10 \
      lead/next_re_20261112_r02/W34_mapselmd/ra2forge_patched_v11
# 用 PATCH_RELATIVE.diff 核对/重放（路径前缀 a/ b/ 需映射到实际两个目录）
git apply --no-index --unsafe-paths --directory=. PATCH_RELATIVE.diff   # 或 patch -p1
```

> 便捷做法：**直接使用交付的 `ra2forge_patched_v11/`**，它已是补丁结果；`PATCH_RELATIVE.diff` 只用于审阅/审计。切勿把补丁打到仓库根的 `ra2forge/`（本卡纪律禁止）。

**新开关用法**

```bash
# 默认（与 v10 逐字节相同，不产生 MAPSELMD.INI）
python -B -X utf8 -m ra2forge build --design design.json --out out

# 启用：产物目录多出完整克隆 + 追加的 MAPSELMD.INI（散装投放）
python -B -X utf8 -m ra2forge build --design design.json --out out --mapselmd

# 可选：指定自定义完整官方基础文件（最小/部分文件会被硬拒绝）
python -B -X utf8 -m ra2forge build --design design.json --out out \
       --mapselmd --mapselmd-base PATH/TO/MAPSELMD.OFFICIAL.INI

# 安装（自动备份 / 记录清单；已有非我方 MAPSELMD.INI 默认拒绝）
python -B -X utf8 -m ra2forge install --package out/<Campaign> --game "<game dir>"
python -B -X utf8 -m ra2forge verify --game "<game dir>"
python -B -X utf8 -m ra2forge uninstall --game "<game dir>"
```

---

## 3 · 校验（全部亲自跑通）

### 3.1 EVIDENCE 脚本

```bash
cd lead/next_re_20261112_r02/W34_mapselmd/EVIDENCE
python -B -X utf8 step1_extract_mapsel.py       # 32/32 PASS  exit 0
python -B -X utf8 step2_disasm_mapsel.py        # 六函数反汇编 exit 0
python -B -X utf8 step3_disasm_stage.py         # 34/34 PASS  exit 0
python -B -X utf8 step4_compat_sha256.py        # v10/v11 逐字节  exit 0
```

四个 `.stdout.txt` 是原始 stdout，`*.exitcode.txt` 记录退出码（全为 `0`）。

### 3.2 回归

```bash
cd lead/next_re_20261112_r02/W34_mapselmd
python -B -X utf8 regress_dlc_v11.py            # 全量
python -B -X utf8 regress_dlc_v11.py MS1 MS2 MS3 MS4 MS5 MS6   # 仅新增用例
```

**本次实测结果**（`out/full_run.txt` / `out/full_run.exitcode.txt` / `out/SUMMARY.txt`）：

| 项 | 值 |
|---|---|
| cases | **51**（45 个既有：W26 的 39 + W30 CSF1..6；新增 MS1..MS6） |
| passed | **51** |
| failed | **0** |
| exit | **0** |

逐例日志 `out/<case>.log`（命令 + 原始输出 + 退出码 + 逐项判据）。新增用例覆盖：完整克隆（MS1）、追加后官方条目零丢失（MS2）、最小文件被拒（MS3）、不启用时逐字节等同（MS4）、安装/卸载还原（MS5）、冲突预检拒绝（MS6）。

### 3.3 向后兼容硬证据

`out/SHA256_V10_V11.txt`（源：`EVIDENCE/step4_compat_sha256.stdout.txt`）：同一 design、同一 CLI、**不传 `--mapselmd`**，v10 与 v11 全部 **7/7** 输出文件 SHA-256 逐一相同：

```
Example Operation/BATTLEMD98.INI      9898db18…  == 9898db18…
Example Operation/BUILD_REPORT.txt    4d5b8684…  == 4d5b8684…
Example Operation/EX01.MAP            d5c7f3c2…  == d5c7f3c2…
Example Operation/INSTALL.txt         90cc4a48…  == 90cc4a48…
Example Operation/expandmd98.mix      022fc941…  == 022fc941…
Example Operation/ra2forge_package.json bd7b2715… == bd7b2715…
Example Operation/story.md            8e396678…  == 8e396678…
```

启用 `--mapselmd` 时只**新增** `MAPSELMD.INI`（本例 5,826 B，sha256 `b371eadc…`），`BUILD_REPORT.txt` / `INSTALL.txt` 按设计增行，其余游戏产物字节不变。

### 3.4 交付物完整性

```bash
# 逐文件哈希见 V11_FILES.sha256.txt；官方克隆资源自校验：
sha256sum ra2forge_patched_v11/ra2forge/data/MAPSELMD.OFFICIAL.INI
# 074ccccd9e156d586d0ed099ceab78b3d72384c808725d8b5bee2c9799691d52
```

`mapselmd.load_bundled_official()` 在**每次**构建时都会断言该 size/sha256，不符即 `MapselmdError` 硬失败。

---

## 4 · 回滚

### 4.1 回滚代码（构建工具）

本卡**从未修改仓库 `ra2forge/` 或 W21–W33**，因此代码层面回滚只需：

1. 不使用 `--mapselmd` ⇒ 行为与 v10 逐字节相同（§3.3 已证），无需任何改代码动作。
2. 需要彻底移除 v11 时：**删除整个 `lead/next_re_20261112_r02/W34_mapselmd/` 目录**即可；W30 的 `ra2forge_patched_v10/` 仍是原始只读基线（本卡未写）。
3. 若曾按 `PATCH_RELATIVE.diff` 把变更重放到某个 v10 副本：用 `git apply -R` / `patch -R -p1` 反向应用该 diff；`V11_FILES.sha256.txt` 标为 `IDENTICAL` 的 10 个 `.py` 无需还原，`MODIFIED` 的三个用 v10 原件覆盖、`NEW` 的两个删除即可。

### 4.2 回滚一次已执行的安装（游戏目录）

```bash
python -B -X utf8 -m ra2forge uninstall --game "<game dir>"
```

- `MAPSELMD.INI` 与其它包内文件一起在 `ra2forge_install.json` 清单内；uninstall 按记录的 sha256 删除我方版本，并把 `.ra2forge.bak` 里的**原文件逐字节还原**（MS5l 实测：`restored MAPSELMD.INI.ra2forge.bak -> MAPSELMD.INI`）。
- 若安装前游戏目录**没有** `MAPSELMD.INI`，uninstall 会直接删除我方文件、不留残骸（MS5g/MS5h 实测）。
- 安装前已存在**非我方** `MAPSELMD.INI` 时，preflight 会直接拒绝、零写入（MS6e 实测），因此不存在「需要回滚的静默覆盖」。

### 4.3 不要做的事

- 不要把「只含我方条目」的最小 `MAPSELMD.INI` 投放到游戏目录：它是 whole-file 覆盖，会让官方 14 关全部失效（W29 CSF 同类警告；`mapselmd.validate_official_base()` 已硬拒）。
- 不要用 `--allow-content-conflict` 去强行覆盖第三方 `MAPSELMD.INI`：v11 对该冲突**永不释放**（设计如此，见 `UNCOVERED.md` U6）。

---

## 5 · 纪律自检

| 约束 | 状态 |
|---|---|
| 不启动 `gamemd.exe` / 不 attach | ✅ 沙箱内 `gamemd.exe` 是 inert 占位文本，从未执行 |
| 不写 `ra2youli` | ✅ 仅继承回归用例如 W30 那样**只读** `ra2forge_install.json` 与 `langmd.mix` |
| 不写仓库 `ra2forge/` | ✅ 只在 `W34_mapselmd/ra2forge_patched_v11/` 内工作 |
| 不动 W21–W33 | ✅ 全部只读引用（反汇编/回归驱动/证据） |
| git 只读 | ✅ 未执行任何 git 写操作 |
| `ra2bench/ra2md.mix` 只读 | ✅ EVIDENCE 仅 `open("rb")` |
| 结论分级 | ✅ 五档标注见 `MAPSELMD_SPEC.md` §0 / `UNCOVERED.md` |
| 未写「已修复战役推进」 | ✅ 全文及代码注释均声明纯离线、真机验证属后续卡 |
| `.text` `FOFF = VA − 0x400000` | ✅ step2/step3 开头断言 PASS |
| `ret` 不当函数结束判据 / 等距指针表不当 vtable | ✅ 反汇编从已知函数起点/vtable 字面量出发；vtable `0x7E16B0` 槽位单独实测 |
