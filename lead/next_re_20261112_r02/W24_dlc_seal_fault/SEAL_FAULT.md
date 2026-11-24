# SEAL_FAULT · W24（seal 写失败回滚的故障注入实测）

日期：2026-11-13。run_id = `NEXT_RE_20261112_R02`。仓库 `main@3872ef6`。
被测断言（W23 `ra2forge_patched_v7/ra2forge/install.py` docstring，约 L353-355）：

> "a failed install rolls the record back to its exact previous bytes if the
> seal write fails, so an install never leaves a seal-era record standing
> without its seal (the refused-uninstall state) silently."

W23 UNCOVERED §5 自认此条只有代码审读、没有执行证据（`@record` 注入在清单写处
raise，天然到不了 seal 写）。本卡补上 `@seal` 注入点并实测。全程隔离沙箱：
`W24_dlc_seal_fault/sandbox/`，**未触碰真实游戏目录**（ra2youli 仅被 READ 过
`ra2forge_install.json`，与 W23 套件行为一致）。

## 1. 注入方式（T1）

**选择：外部手段（驱动级 monkeypatch + 纯文件系统障碍），`ra2forge_patched_v7i/`
与 W23 的 v7 逐字节相同**（12/12 文件 SHA-256 一致，见
[BASELINE_V7I.sha256.txt](BASELINE_V7I.sha256.txt)，与 W23
`BASELINE_V7I_POST` 逐行比对过）。依据：

1. W23 UNCOVERED §5 自己的建议就是「给 **driver** 加 `@seal` 注入点」；
2. 副本零字节差异 ⇒「默认关闭、不改变正常路径」从"信环境变量判断"升级为
   "字节级保证"——对照组跑的就是与 W23 完全相同的二进制；
3. 形态 (a)(c) 各有**零代码注入**的纯文件系统做法，命中的是 `os.replace` /
   landing-slot 门禁这些真实 OS 层失败。

注入入口：[tools/v7i_seal_fault_driver.py](tools/v7i_seal_fault_driver.py)，
显式模式参数，**不传模式即拒绝注入**（usage 退出码 3，且在 import ra2forge
之前退出，游戏目录零接触）——F0 对此有专门断言。三种模式：

| 模式 | 注入点（包代码零改动） | 模拟的失败 |
|---|---|---|
| `@seal` | `write_install_seal` 入口 raise OSError | 形态 (a)：seal 目标完全写不进 |
| `@seal_open` | `_open_staging_file` 对 seal 槽 raise | 形态 (a) 变体：staging 文件都建不出来（目录不可写） |
| `@seal_half` | 武装标志包住 seal 写，期间 `os.fdopen` 返回半写包装器：真实 staging 文件落一半字节（flush 上盘）后 raise `OSError(ENOSPC)` | 形态 (b)：磁盘满，写到一半 |

`@seal_half` 的包装只罩住 seal 这一次写（武装标志在 `write_install_seal` 前后
设置/清除），清单写与回滚恢复写都不受影响。半写发生在**生产代码路径内**
（真实 `_open_staging_file`、真实 staging 文件、真实字节落盘，生产异常分支负责
清理 staging 残留）——只截获 `write()` 这一个调用点，注入强度不放宽。

纯文件系统手段（F6/F7 用，**完全不碰代码、不用 driver**）：

- **F6（形态 a）**：在游戏目录预埋一个名为 `ra2forge_install.json.seal` 的
  **目录** → seal 写在生产的 landing-slot 门禁
  （`_refuse_aliased_landing_slot` → `_derived_slot_error` 的 "exists but is
  not a regular file"）被拒，真实 OS 层失败；
- **F7（形态 c）**：既有安装的 seal 文件置**只读**属性（`os.chmod(S_IREAD)`）
  → `os.replace` 真实抛 `[WinError 5]`。

## 2. 实测表（T2）

全部数字出自 [out/](out/) 下各用例日志（命令 + 原始输出 + 退出码 + 逐项判据）。
对照 = F0（无注入跑同一序列，全部成功）+ 原有 22 用例全过（系统性对照）。

### F1 · 形态 (a) 注入：全新安装，seal 完全写不进（driver `@seal`）

- install 退出码：**1**；消息："the install seal (ra2forge_install.json.seal)
  could not be written (simulated seal-write failure …) - the install record
  was rolled back to its previous bytes, the package files are UNCHANGED;
  nothing was left in the unsealed state"，随后
  "install aborted mid-write; best-effort rollback" 列出 3 个 created 文件被删。
- 清单：安装前**不存在** → 失败后**不存在**（fresh 安装无前版字节，回滚 = 不落盘）。
- `.seal`：**不存在**。
- 半写/残留：无（`stage_residue()==[]`，无 `*.ra2forge-stage*`、无 `*.ra2forge.bak`）。
- 目录全清单+哈希（失败后，= 安装前 golden）：

  ```
  6567904f25b5cdd2dba5c29bb19a6afb5614950f2a36e9a314b4f239b25ba7d1   46 BATTLEMD.INI
  57a99bcaf0c41b8f8681606b2300e384a654571ec8b1aa0d5b684273cea89162   35 gamemd.exe
  54811b59b3b2d5330d662e72c31c7084cad066c0a58e75aa5a15bfa1066ac43f   27 RA2MD.INI
  ff7887282c1709106446abb5099a60fd7dbd52531fb284095d84c8a5391ad8ed   35 USERMAP1.MAP
  ```
- 随后 `verify`：exit **0**（"nothing to verify"）；`uninstall`：exit **0**
  （"nothing recorded to remove"）。**非死锁态。**

### F2 · 形态 (b) 注入：全新安装，seal 半写（driver `@seal_half`）

- install 退出码：**1**；消息含真实半写字节数：
  "…could not be written ([Errno 28] simulated disk full (ENOSPC) mid seal
  write (injected; landed **171/343** bytes)) - the install record was rolled
  back to its previous bytes, the package files are UNCHANGED; …"
- 清单：**不存在**（同 F1）；`.seal`：**不存在**（无半截 seal 站着）。
- 半写 staging 文件：由**生产**异常分支 unlink 清理——`stage_residue()==[]`。
- 目录全清单+哈希：与 F1 终态完全相同（见 [out/F2.log](out/F2.log) note）。
- 随后 `verify` exit **0**、`uninstall` exit **0**。**非死锁态。**

### F3 · 形态 (c) 注入：既有 seal-era 安装之上更新，新 seal 写失败（driver `@seal`）

- install 退出码：**1**（消息同 F1 家族 + 回滚行含 "rolled back the orphan
  removal of X.MAP (re-installed from the previous package …)"）。
- 清单逐字节回滚（SHA-256）：

  | | SHA-256 |
  |---|---|
  | 更新前 `ra2forge_install.json` | `3605c21647e279958df21455787d40ae66d63702854c7d13a09128da37f0eb9f` |
  | 失败后 `ra2forge_install.json` | `3605c21647e279958df21455787d40ae66d63702854c7d13a09128da37f0eb9f`（**相同**） |

- `.seal`：更新前 `59f3edc2023224db37093df7f39e55ebfad50820b21f7f1b80967c7865d11856`
  → 失败后**相同**（旧 seal 原样，与旧清单配对完整）。
- 残留：无；目录整树哈希与更新前逐字节相同（[out/F3.log](out/F3.log) note）。
- 随后 `verify`：exit **0**，"seal: OK"（旧对立即是自洽可用状态）。

### F6 · 形态 (a) 纯文件系统：seal 槽被目录占用（零代码注入）

- install 退出码：**1**；消息："…could not be written (the install seal slot
  was refused right before the write: install seal ra2forge_install.json.seal
  **exists but is not a regular file - refusing to use it**) - the install
  record was rolled back …"——这是**生产 landing-slot 门禁**在 `os.replace`
  之前的真实拒绝，不是注入代码。
- 清单/`.seal` 文件：均不存在；包文件回滚；无 staging 残留。
- 唯一额外对象是**预埋的目录**（测试装置，安装前已存在——判据里显式区分
  "setup artefact" 与 "install residue"）。
- 随后 `verify` exit **0**、`uninstall` exit **0**。

### F7 · 形态 (c) 纯文件系统：seal 只读（零代码注入）+ 新发现

- update install 退出码：**1**；消息含**真实 OS 错误**：
  "…could not be written ([**WinError 5**] 拒绝访问。: '…seal.ra2forge-stage.…'
  -> '…ra2forge_install.json.seal') - the install record was rolled back …"
- 清单逐字节回滚（SHA-256）：`6f3b9b532a77…` → `6f3b9b532a77…`（**相同**）；
  seal：`e02fced92b2c…` → **相同**（只读挡住的是新 seal，旧 seal 完好）。
- 残留：无；整树与更新前逐字节相同。
- 随后 `verify`：exit **0**，"seal: OK"（旧对立即自洽）。
- **随后 `uninstall`：exit 1 —— 新发现（见 §4）**。
- 二次 `uninstall`：exit **0**，显式披露 "no ra2forge_install.json … nothing
  recorded to remove" + "a ra2forge_install.json.seal is present without an
  install record - left in place"——**状态被披露，非死锁**。

## 3. 失败后的可继续性（T2-3）

| 状态 | verify | uninstall | 结论 |
|---|---|---|---|
| F1/F2/F6 失败后（无清单） | exit 0（nothing to verify） | exit 0（nothing recorded） | 可继续 |
| F3 失败后（旧对完好） | exit 0（seal OK） | exit 0（F4 实测完整生命周期：卸载→重装→verify→卸载全通） | 可继续 |
| F7 失败后（旧对完好） | exit 0（seal OK） | exit 1（新发现）→ 二次 exit 0 + 披露 | 可继续，但见 §4 |

## 4. 新发现（F7 实测，超出 T1 断言范围）

uninstall 在**全部记录文件已删、清单已 unlink 之后**才删 seal；此时撞上只读
seal 会 `PermissionError`（WinError 5）逸出，CLI exit 1，actions 报告丢失。
终态（[out/F7.log](out/F7.log) note "after the rough uninstall"）：

```
6567904f…  46 BATTLEMD.INI          ← golden，未动
57a99bca…  35 gamemd.exe            ← golden，未动
e02fced9… 343 ra2forge_install.json.seal   ← 游离只读 seal（旧字节）
54811b59…  27 RA2MD.INI             ← golden，未动
ff788728…  35 USERMAP1.MAP          ← golden，未动
```

即「清单已删 + seal 残留」。这**不否证 T1 断言**（该断言只约束 install；
install 的回滚是字节精确的），但它是 uninstall 收尾容错缺口：install 对
seal 写失败做了"记录回滚 + 报告"，uninstall 对 seal 删除失败没有任何同等
处理。该状态可恢复且被二次 uninstall 显式披露（exit 0）。

**恢复路径实测（F7 末段 + F5）**：
- 不清障碍直接重装同包 → seal 写再次失败（同一 WinError 5）——障碍持续到被清除为止（诚实结果，未放宽）；
- 清除只读属性 → 重装同包 A1：exit 0，"written ra2forge_install.json.seal"，
  且 **`seal.manifest_sha256 == 当前清单规范化哈希`**（自证重盖 seal 保护的是
  站立的这份记录）→ verify exit 0 "seal: OK" → uninstall exit 0 → 目录回 golden。
- F5（docstring 自带的恢复配方 "re-run the install of the SAME package … then
  uninstall"）在形态 (b) 失败后的状态上独立实测：配方三步全通，终态回 golden。

## 5. T1 断言判定（T3）

**逐形态：**

| 形态 | 注入手段 | 判定 | 依据 |
|---|---|---|---|
| (a) seal 完全写不进 | driver `@seal`（F1）+ 纯 FS 目录占槽（F6） | **[已证]** | 退出码 1；清单未落盘/不残留；无半写、无 staging 残留；verify/uninstall exit 0 |
| (b) seal 半写（磁盘满） | driver `@seal_half`，真实 171/343 字节落盘（F2） | **[已证]** | 半截 staging 由生产分支清理；无半截 seal 站立；清单不存在；可继续 |
| (c) 有旧 seal、新 seal 写失败 | driver `@seal`（F3）+ 纯 FS 只读（F7） | **[已证]** | 清单 SHA-256 逐字节回到更新前；旧 seal 原样（旧对自洽）；随后 verify exit 0 / uninstall 正常（F3/F4） |

**总判定：[已证]**——三种形态下 install 均未留下「seal-era 清单站着但没 seal」
的状态；「逐字节回到上一版/未落盘 + 包文件回滚 + 无残留」全部有 SHA-256 与
目录全清单证据。对照组（F0 + 原有 22 用例全过）证明注入未改变正常路径。

**边界与未证部分**：
- 断言说的是 install 这一侧。F7 揭示 **uninstall 侧无同等保护**（§4）——
  属新缺陷记录，不是本断言的否证。
- 回滚自身失败的兜底（`except OSError: pass`，install.py L1965-1966）未注入
  测试：即「清单回滚写也失败」的二次故障形态未覆盖（见 UNCOVERED.md）。
- 断言中的 "silently"：失败信息走 CLI error 通道（stderr）+ exit 1，不静默——
  与断言语义一致。

## 6. 回归（T3）

[regress_dlc_v7i.py](regress_dlc_v7i.py)：W23 的 22 用例（P0、V1-V6、P1-P4、
C1、C2、T4、S1-S8）**原样复制、仅重指向本卡的逐字节 v7i 副本**（无一削弱），
新增 F0-F7。最终轮：

```
cases: 30  passed: 30  failed: 0
assertions: 286 passed / 0 failed
SUITE EXIT CODE: 0
```

F 系列每用例的「命令 + 原始输出 + 退出码 + 逐项判据」在
[out/F0.log](out/F0.log) … [out/F7.log](out/F7.log)；
汇总在 [out/SUMMARY.txt](out/SUMMARY.txt)。

## 7. 能力边界

- 注入走驱动级 monkeypatch + 文件系统障碍，包代码零改动 ⇒ 无法测「包自身
  内嵌故障开关」这种东西（本卡断言也不需要它）。
- 形态 (b) 的"磁盘满"是 `write()` 层 ENOSPC 模拟（真实字节落盘后抛错），
  不是真实卷配额耗尽；对 `_stage_text_and_replace` 的单次 `write` 语义等价。
- 全部实验在 Windows（NTFS）+ Python 3.12.10；沿用 W23 UNCOVERED §7 的
  非 Windows 未复核提醒。
- 清单回滚写自身失败的二次故障形态未覆盖（UNCOVERED.md §2）。
