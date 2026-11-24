# APPLY.md · W26 补丁（UNSEAL-FIX02，含 W21–W25 累计演进）应用与回滚

> 状态：**已生成并完成沙箱逐字节回放验证（12/12 文件 SHA-256 100% 一致）**
> 日期：2026-11-13 ｜ run_id = `NEXT_RE_20261112_R02` ｜ 仓库基线 `main@3872ef6`

- 补丁文件：[PATCH_RELATIVE.diff](PATCH_RELATIVE.diff)（119,339 字节，纯相对路径 `a/ra2forge/*.py` → `b/ra2forge/*.py`，由仓库 0.4 `ra2forge/` → `ra2forge_patched_v9/ra2forge/` 0.9 累计生成，已过滤 `__pycache__` 与 `.mimosa`）。
- 演进隔离说明：由 `W25_dlc_unseal/ra2forge_patched_v8/` 复制至 `W26_dlc_unseal_fix/ra2forge_patched_v9/` 后修改；仓库 `ra2forge/`、`W21–W25`、`ra2youli/` 全程零写入。

---

## 1. 哈希对照（改前 v8 实态 → 改后 v9 终态）

详细清单见 [BASELINE_V9_PRE.sha256.txt](BASELINE_V9_PRE.sha256.txt) 与 [BASELINE_V9_POST.sha256.txt](BASELINE_V9_POST.sha256.txt)。W25 → W26 本卡实质改动 2 个文件（其余 10 个文件 SHA-256 保持不变）：

| 文件 | 改前 SHA-256（W25 `v8` 盘上实态） | 改后 SHA-256（W26 `v9` 终态） | 说明 |
|---|---|---|---|
| `ra2forge/install.py` | `64e2936ea968471baaa309bc59c61fe7686effea728991908fdf1246489bcc1d` | `d55a22179a109314c8d20a7030d136c5669660c3b21315d85630ba163e7c0edd` | `TOOL_VERSION="0.9"`、双回滚隔离与复合报错、uninstall actions/unlink 容错 |
| `ra2forge/cli.py` | `a7b221f2b6717de8f2373d335707dbbfc6bdbe594ce9585ef3a146bf2f07919d` | `4f3a76fbf15e2ed337ed2f193cf60c5ad9e515973b5cca21e577b514036470bb` | `_uninstall_exit_code` 处理 `failed_step` 返回 exit 1；对齐 exit 1 / `failed` 帮助与 JSON 说明 |
| `ra2forge/verify.py` | `051c2e214b0d9862358c5732eaa91f70346231050b82df9f48419d64012e5e85` | 同左（未改动） | 累计 diff 中为新建文件 |
| `ra2forge/builder.py` | `d65d6d2e5e95c1ca0cf897fe6247a998629921c314199de1aa8de358d89fc783` | 同左（未改动） | 来自 W22 累计演进 |
| 其余 8 个 `.py` | 见 PRE/POST 哈希表 | 完全一致 | 无变动 |

---

## 2. 应用步骤（在仓库根 `D:\Project\ra2-campaign-forge` 执行）

```bash
git -c core.autocrlf=false -c core.eol=lf apply --check lead/next_re_20261112_r02/W26_dlc_unseal_fix/PATCH_RELATIVE.diff
git -c core.autocrlf=false -c core.eol=lf apply     lead/next_re_20261112_r02/W26_dlc_unseal_fix/PATCH_RELATIVE.diff
```

（若受限于非仓库目录验证，可通过 [tools/make_patch.py](tools/make_patch.py) 重新生成并验证；`python -B -m py_compile` 已通过全部目标模块。）

---

## 3. 回放验证与红线核验记录

- 运行 `python -B -X utf8 lead/next_re_20261112_r02/W26_dlc_unseal_fix/tools/make_patch.py`：
  1. `OK: 12 files hashed -> BASELINE_V9_POST.sha256.txt`
  2. `OK: cumulative diff -> PATCH_RELATIVE.diff (119339 bytes)`
  3. 在 `W26_dlc_unseal_fix/sandbox/_replay_check/tree/ra2forge` 复制原始 `ra2forge/`，执行 `--check --verbose` 与实际 `git apply`，回放后 **12/12 文件 SHA-256 与 `ra2forge_patched_v9/ra2forge/` 完全一致**（临时回放目录随后清除）。
  4. 在仓库根执行只读 `git -c core.autocrlf=false apply --check .../PATCH_RELATIVE.diff` 退出码 `0`。
  5. 验证 `PATCH_RELATIVE.diff` 文件头仅含 `a/ra2forge/{builder,cli,install,verify}.py` 与 `/dev/null`，无绝对路径、无 `.pyc`、无 `.mimosa` 污染。

---

## 4. 回滚步骤

若需要撤销对工作区 `ra2forge/` 应用后的改动，在仓库根执行：

```bash
git checkout -- ra2forge/install.py ra2forge/cli.py ra2forge/builder.py
rm -f ra2forge/verify.py
```
