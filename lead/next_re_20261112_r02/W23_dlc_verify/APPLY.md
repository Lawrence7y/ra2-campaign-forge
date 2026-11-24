# APPLY.md · W23 补丁（SEAL-CHAIN01，含 W21 孤儿修复 + W22 包身份）应用与回滚

- 补丁文件：`PATCH_RELATIVE.diff`（**相对路径** `a/ra2forge/*.py` / `b/ra2forge/*.py`，
  共 4 个文件：`install.py`、`cli.py`、`verify.py`（**新增**）、`builder.py`；其余 8 个
  .py 零改动）
- 补丁性质：**累计补丁** = 仓库 `main@3872ef6` 现状（0.4）→ W23 v0.7
  （0.4→0.5 孤儿修复 + 0.5→0.6 包身份 + 0.6→0.7 信任链/verify，一次 `git apply` 全部
  到位，**取代** W22 的同名补丁）
- 基线：从 `W22_dlc_identity/ra2forge_patched_v6/` 复制后在副本上修改；
  仓库 `ra2forge/`、W21/W22 交付目录未动一字节（本卡完成后复测，见 §4）

## 1. 哈希（改前 / 改后）

- `BASELINE_V7_PRE.sha256.txt`：v7 包**改前**（= W22 v0.6 包 11 个 .py，逐字节同源；
  `__pycache__` 剔除）
- `BASELINE_V7_POST.sha256.txt`：v7 包**改后**（TOOL_VERSION 0.7，12 个 .py）

关键文件（完整 64 位十六进制见两份基线文件）：

| 文件 | 改前 (v0.6) | 改后 (v0.7) |
|---|---|---|
| ra2forge/install.py | `b804210884344418ddf833a312c7203c75e0ee898078da0d1bb79b139fe44ef3` | `81ffee422e068bd35d53f740a4d78f5388ee02f3cb8f07d9aaab1f68b6b97975` |
| ra2forge/cli.py | `fed2a9bb3299b76d328a508c49795ac6058cc7e986bba624b47cc15602a13f39` | `0011747b93b185855cb45a4aedb69408d8b808a116d8f79631fe363af8bc51e0` |
| ra2forge/verify.py | （不存在） | `ee852dd1207f3eb38f5dc631e37ce61482f22d05297161c8a2abaa294e3b6101`（新增） |
| ra2forge/builder.py | `d65d6d2e5e95c1ca0cf897fe6247a998629921c314199de1aa8de358d89fc783` | 不变（v0.7 未触碰） |
| 其余 8 个 .py | 不变 | 不变（两表逐行可对） |

## 2. 应用（在仓库根 `D:\Project\ra2-campaign-forge` 执行）

```bash
# 预检
git -c core.autocrlf=false -c core.eol=lf apply --check lead/next_re_20261112_r02/W23_dlc_verify/PATCH_RELATIVE.diff
# 应用
git -c core.autocrlf=false -c core.eol=lf apply     lead/next_re_20261112_r02/W23_dlc_verify/PATCH_RELATIVE.diff
```

**⚠️ 与 W22 APPLY.md 的两处差异（本卡实测踩坑，务必按此执行）：**

1. **`-c` 参数必须放在 `git` 与子命令之间**（`git -c k=v apply ...`）。W22 文档写的
   `git apply -c core.autocrlf=false ...` 在 git 2.54 上报
   `error: unknown switch 'c'`，**不会执行**。
2. **不要在仓库的子目录里跑 `git apply`**：本卡实测，在仓库子目录里对路径形如
   `ra2forge/...` 的补丁，git 会输出 `Skipped patch '...'` 并**静默退出 0**（看似成功、
   实际零改动）。必须在**仓库根**执行，且应用后必须跑 §2 的自检确认 `TOOL_VERSION`
   确实变成 0.7。
3. 本仓库 `.git/config` 已有 `core.autocrlf=false`，`-c` 属于双保险；补丁文件本身为
   LF、无 BOM。

应用后自检：

```bash
python -c "import ra2forge.install as m; print(m.TOOL_VERSION)"        # 应输出 0.7
python -c "import ra2forge.verify as v; print(v.__name__)"             # 应正常导入
python -B -m py_compile ra2forge/install.py ra2forge/cli.py ra2forge/verify.py  # exit 0
python -B -X utf8 lead/next_re_20261112_r02/W23_dlc_verify/regress_dlc_v7.py    # 22/22, exit 0
```

## 3. 回放验证（本卡已做）

1. 取仓库原版 `ra2forge/*.py` 副本到**仓库外**临时目录（剔除 `__pycache__`）；
2. `git -c core.autocrlf=false -c core.eol=lf apply` 成功（`--check` 与 apply 均 exit 0）；
3. 与 `ra2forge_patched_v7/ra2forge/` **12 个 .py 逐一 sha256 对比：全部一致**
   （`__init__/__main__/builder/cli/design/format80/install/lzo/maplib/mixlib/triggers/verify`
   = 12/12 identical）；
4. 另在**仓库根**复测 `git apply --check` → exit 0（与第 2 步互证）。

原版未动复测（§4）：仓库 `ra2forge/*.py` 当前哈希 = 0.4 原状
（`install.py 73209597…`、`cli.py c1000ad2…`、`builder.py c58d8419…`，
与 W21 `ORIG_BASELINE.sha256.txt` 同源），`git status --porcelain -- ra2forge/` 为空。

## 4. 本卡红线复测（交付时状态）

| 对象 | 结果 |
|---|---|
| 仓库 `ra2forge/` | 0.4 原状，git status 干净，**未动** |
| `W21_dlc_orphan/`、`W22_dlc_identity/` | 未动（W22 v6 `install.py` 仍为 `b8042108…`） |
| 真实游戏目录 `ra2youli/` | 只读复制其 `ra2forge_install.json`（1487 B，`fe3bdf62…`）到沙箱做 S7/C1 兼容测试，**零写入** |
| git 写操作 | 无（仅 `apply --check`/`--stat`/只读 diff） |

## 5. 回滚

```bash
git checkout -- ra2forge/install.py ra2forge/cli.py ra2forge/builder.py
# 若已应用：verify.py 是本补丁新增的文件，需要手动删除
rm ra2forge/verify.py
```

（补丁只改 `install.py` / `cli.py` / `builder.py` 并新增 `verify.py`；回滚 = 还原三个
改动文件 + 删除新文件，即恢复 0.4 原状。若在副本上操作，删除副本目录即可。）

## 6. 混用限制（沿 W21/W22 APPLY.md 的提醒，仍然成立 + 本卡新增）

- v0.7 清单被 **0.4/0.5/0.6 旧代码**读取：不崩溃（未知键被忽略，C2 实测同类），但旧工具
  **不认识 `.seal`**——v0.5 卸载后会在游戏目录留下 `ra2forge_install.json.seal` 残留
  （C2 实测并断言）。升级/卸载/校验请统一用同一份代码。
- v0.7 的 `uninstall` 对 **v0.6 及更早清单**自动降级：警告后照常卸载（C1 实测）。
- v0.7 的 `install` 对 v0.3/v0.4/v0.5 清单仍以 exit 4 要求 `--adopt-legacy`（W22 语义，
  未变）。
- **恢复路径例外**：seal 丢失后重装同一个**未盖章包**时，需要 `--adopt-legacy`
  （VERIFY.md §2.4）。
