# APPLY.md · W30 补丁（CSF 读写能力与最小构建接线，含 W21–W26 累计演进）应用与回滚

> 状态：**已生成并完成沙箱逐字节回放验证（13/13 文件 SHA-256 100% 一致）**
> 日期：2026-11-13 ｜ run_id = `NEXT_RE_20261112_R02` ｜ 仓库基线 `main@3872ef6`

- 补丁文件：[PATCH_RELATIVE.diff](PATCH_RELATIVE.diff)（153,046 字节，纯相对路径 `a/ra2forge/*.py` → `b/ra2forge/*.py`，由仓库 0.4 `ra2forge/` → `ra2forge_patched_v10/ra2forge/` 1.0 累计生成，已过滤 `__pycache__` 与 `.pyc`）。
- 演进隔离说明：由 `W26_dlc_unseal_fix/ra2forge_patched_v9/` 复制至 `W30_csf_capability/ra2forge_patched_v10/` 后修改；仓库 `ra2forge/`、`W21–W29`、`ra2youli/` 全程零写入。

---

## 1. 哈希对照（改前 v9 实态 → 改后 v10 终态）

详细清单见 [BASELINE_V10_PRE.sha256.txt](BASELINE_V10_PRE.sha256.txt) 与 [BASELINE_V10_POST.sha256.txt](BASELINE_V10_POST.sha256.txt)。W26 → W30 本卡新增 1 个模块并实质改动 5 个文件（其余 7 个 `.py` 文件 SHA-256 与 v9 保持 100% 一致）：

| 文件 | 改前 SHA-256（W26 `v9` 盘上实态） | 改后 SHA-256（W30 `v10` 终态） | 说明 |
|---|---|---|---|
| `ra2forge/csf.py` | *（不存在）* | `c90603fa442fe91c40f00af1ba2229654bca61b114cee911991c8e7cedc6cece` | **新增**：纯标准库 CSF v2/v3 读写、`append_or_set_label`（写后必做磁盘读回校验）、未知值类型保留与如实报告 |
| `ra2forge/mixlib.py` | `b320e89b4cba4f75a4ebab39b50f9b68c6404f4fde6ec1588fc2532ec9a34418` | `7f10d044ccc9ac72461acdc68308c23afee596d7b70b248b63ba9ddc2653ba0a` | 新增 `ts_crc_hash`（Westwood 4 字节尾部填充 CRC-32）供 `MixFile.get()` 查找 `ra2md.csf`/`ra2.csf`；保留原 `crc_hash` 与 `write_mix` 不变以保证构建产物向后兼容 |
| `ra2forge/builder.py` | `d65d6d2e5e95c1ca0cf897fe6247a998629921c314199de1aa8de358d89fc783` | `117bd62e0b0031e0221b0694faa9611aa5ccc410e1b02bc3ce5ebc51e1823eec` | 新增可选 `csf_out`/`csf_base` 参数、`csf_label_for()`（`RA2F:<8位SHA256>`）、生成 `ra2md.csf` 与 `csf_patch.json` 及报告记录；默认 `csf_out=None` 时与 v9 逐字节一致 |
| `ra2forge/cli.py` | `4f3a76fbf15e2ed337ed2f193cf60c5ad9e515973b5cca21e577b514036470bb` | `95865319b2bed7e20f0c00839fedb5e837fdd11b80c6b0a591881f7860cbce12` | `build` 子命令新增可选 `--csf-out PATH` 与 `--csf-base CSF_PATH` |
| `ra2forge/install.py` | `d55a22179a109314c8d20a7030d136c5669660c3b21315d85630ba163e7c0edd` | `413a14547ab8f82d963e7c50bb18b3839d984ccaebbdc3b8f199c0e70f3a3275` | `TOOL_VERSION` 演进为 `"1.0"`（其余安全门与卸载语义零改动） |
| `ra2forge/__init__.py` | `21c4ac3eacf6585a492e7c66072d78da86777e3ec9a4e48b0c65802872c5cb5a` | `e66714859a0ab264ae885dc82768d50ce410f1a026512ebdcae43b758a43591c` | docstring 补充 `csf` 模块 |
| `ra2forge/verify.py` | `051c2e214b0d9862358c5732eaa91f70346231050b82df9f48419d64012e5e85` | 同左（未改动） | 累计 diff 中为新建文件 |
| 其余 6 个 `.py` | 见 PRE/POST 哈希表 | 完全一致 | 无变动 |

---

## 2. 应用步骤（在仓库根 `D:\Project\ra2-campaign-forge` 执行）

```bash
git -c core.autocrlf=false -c core.eol=lf apply --check lead/next_re_20261112_r02/W30_csf_capability/PATCH_RELATIVE.diff
git -c core.autocrlf=false -c core.eol=lf apply     lead/next_re_20261112_r02/W30_csf_capability/PATCH_RELATIVE.diff
```

可通过 [tools/make_patch.py](tools/make_patch.py) 重新生成并验证沙箱回放与仓库根目录 `git apply --check`。

---

## 3. 回放验证记录

- 运行 `python -B -X utf8 lead/next_re_20261112_r02/W30_csf_capability/tools/make_patch.py`：
  1. `OK: 12 pre-files hashed -> BASELINE_V10_PRE.sha256.txt`
  2. `OK: 13 post-files hashed -> BASELINE_V10_POST.sha256.txt`
  3. `OK: cumulative diff -> PATCH_RELATIVE.diff (153046 bytes)`
  4. `OK: sandbox replay + repo-root git apply --check matched 100%`（13/13 文件 SHA-256 与 `ra2forge_patched_v10/ra2forge/` 完全一致）。

---

## 4. 回滚步骤

若需要撤销对工作区 `ra2forge/` 应用后的改动，在仓库根执行：

```bash
git checkout -- ra2forge/__init__.py ra2forge/builder.py ra2forge/cli.py ra2forge/install.py ra2forge/mixlib.py
rm -f ra2forge/csf.py ra2forge/verify.py
```
