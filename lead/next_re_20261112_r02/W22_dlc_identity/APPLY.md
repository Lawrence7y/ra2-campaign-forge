# APPLY.md · W22 补丁（PKG-IDENT01，含 W21 孤儿修复）应用与回滚

- 补丁文件：`PATCH_RELATIVE.diff`（**相对路径** `a/ra2forge/*.py` / `b/ra2forge/*.py`，
  仅 3 个文件：`install.py`、`cli.py`、`builder.py`；其余 8 个 .py 零改动）
- 补丁性质：**累计补丁** = 仓库 `main@3872ef6` 现状（0.4）→ W22 v0.6（0.4→0.5 的孤儿修复
  + 0.5→0.6 的包身份接线，一次 `git apply` 全部到位）
- 基线：从 `W21_dlc_orphan/ra2forge_patched/` 复制后在副本上修改；
  仓库 `ra2forge/` 未动一字节（见 §3 复测）

## 1. 哈希（改前 / 改后）

- `BASELINE_V6_PRE.sha256.txt`：v6 包**改前**（= W21 v0.5 包 11 个 .py，逐字节同源）
- `BASELINE_V6_POST.sha256.txt`：v6 包**改后**（TOOL_VERSION 0.6）

关键文件（前 12 位）：

| 文件 | 改前 (v0.5) | 改后 (v0.6) |
|---|---|---|
| ra2forge/install.py | `d1186be13e18` | `b80421088434` |
| ra2forge/cli.py | `c1000ad243b1` | `fed2a9bb3299` |
| ra2forge/builder.py | `c58d841e986a` | `d65d6d2e5e95` |
| 其余 8 个 .py | 不变 | 不变（两表逐行可对） |

仓库原版 11 个 .py 的哈希基线见 `W21_dlc_orphan/ra2forge_patched/ORIG_BASELINE.sha256.txt`；
本卡完成后复测 **0 差异**（"原版未动"证据，§3）。

## 2. 应用（在仓库根 `D:\Project\ra2-campaign-forge` 执行）

```bash
# 预检
git apply -c core.autocrlf=false -c core.eol=lf --check lead/next_re_20261112_r02/W22_dlc_identity/PATCH_RELATIVE.diff
# 应用
git apply -c core.autocrlf=false -c core.eol=lf     lead/next_re_20261112_r02/W22_dlc_identity/PATCH_RELATIVE.diff
```

**为什么带 `-c core.autocrlf=false -c core.eol=lf`**（实测踩坑）：本机 git 是
**system 级 `core.autocrlf=true`**，裸 `git apply` 会把被补丁文件**整文件改写为 CRLF**
——能跑，但与交付的 v6 副本不逐字节一致（回放差 2196 个 \r）。带这两个 `-c` 后，
回放树与 `ra2forge_patched_v6/ra2forge/` **11/11 逐字节一致**（已实测，见 §3）。
补丁文件本身为 LF、无 BOM。

应用后自检：

```bash
python -c "import ra2forge.install as m; print(m.TOOL_VERSION)"   # 应输出 0.6
python -c "import ra2forge.install as m; print(m.PACKAGE_MANIFEST_NAME)"  # ra2forge_package.json
python -B -m py_compile ra2forge/install.py ra2forge/cli.py ra2forge/builder.py  # exit 0
python -B -X utf8 lead/next_re_20261112_r02/W22_dlc_identity/regress_dlc.py      # 14/14, exit 0
```

## 3. 回放验证（本卡已做）

1. 取仓库原版 `ra2forge/` 副本（剔除 `.mimosa/`、`__pycache__/` 非源码目录）；
2. `git apply`（带 `-c`）成功（`--check` 与 apply 均 exit 0）；
3. 与 `ra2forge_patched_v6/ra2forge/` 11 个 .py 逐一 sha256 对比：**全部一致**。

原版未动复测：以 W21 的 `ORIG_BASELINE.sha256.txt` 对当前仓库 `ra2forge/*.py` 全量比对
→ 0 mismatch（W21、W22 两卡合计零改动）。

## 4. 回滚

```bash
git checkout -- ra2forge/install.py ra2forge/cli.py ra2forge/builder.py
```

（补丁未新增文件、未删除文件，只改这 3 个文件；回滚即恢复 0.4 原状。若在副本上操作，
删除副本目录即可。）

## 5. 混用限制（沿 W21 APPLY.md 的提醒，仍然成立）

- v0.6 清单被 **0.4 原版代码**读取：不崩溃（未知键被忽略，C2 实测同类），但 0.4 没有
  孤儿清理与身份门——升级/卸载请统一用同一份代码。
- v0.6 的 `install` 对 **v0.3/v0.4/v0.5 清单**（无 `package_id`）会以 exit 4 要求
  `--adopt-legacy`：这是本卡的新语义（原行为是路径等值判定）。升级真实旧安装时命令为
  `python -m ra2forge install --package <pkg> --game <dir> --adopt-legacy`。

## 6. W22 写域内移除项说明

`ra2forge_patched_v6/` 根下曾随复制带入 W21 的三份文档（`APPLY.md`、`PATCH.diff`、
`ORIG_BASELINE.sha256.txt`），为避免与 W22 根部的同名交付混淆已从副本移除
（原件在 `W21_dlc_orphan/` 完好保留；`BASELINE_V6_PRE.sha256.txt` 只含 11 个 .py，
与该移除无关）。
