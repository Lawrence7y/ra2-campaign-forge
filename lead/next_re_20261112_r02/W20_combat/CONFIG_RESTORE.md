# W20 · CONFIG_RESTORE.md — 配置还原自证

## 基线
基线目录 `baseline_pre_launch/`（W12 建立后未动）：RA2MD.INI = ddraw.ini 基线 =
PRE_LAUNCH_BASELINE.tsv。开工前（attempt=1 与 attempt=2 两次 S0）实算五文件哈希全部与
TSV/钉定值一致（RA2MD.INI/RA2MD.INI.benchbak = c91c6a47…3c27d、ddraw.ini =
c983abad…9d52、gamemd.exe = 73201cc0…7476、ddraw.dll = 85e0f7d5…03a9）。

## attempt=1（探针缺陷早期退出）
收尾 restore_configs 全链执行，post_restore 哈希全部 = 基线，byte_identical=true，
锁恢复 owner=lead，gamemd 残留 0。

## attempt=2（正式趟）
游戏运行期自行改写了 `RA2MD.INI`（局内选项/槽位回写）：

| 文件 | 还原前 sha256 | 还原后 sha256 | 与基线逐字节一致 | sha_match |
|---|---|---|---|---|
| RA2MD.INI | 099904d9…a05c9（游戏回写） | c91c6a47…3c27d | **true** | true |
| ddraw.ini | c983abad…9d52（未变） | c983abad…9d52 | true | true |
| RA2MD.INI.benchbak | c91c6a47…3c27d（未变） | c91c6a47…3c27d | true | true |
| gamemd.exe（仅核对） | — | 73201cc0…7476 | unchanged=true | — |
| ddraw.dll（仅核对） | — | 85e0f7d5…03a9 | unchanged=true | — |

- 还原方式：从 `baseline_pre_launch/` 逐字节 `shutil.copyfile`，随后实算 sha256 +
  逐字节比对双自证（`out/meta.json` → restore_rows）。
- 收尾文件清单差分：added=0 / removed=0 / changed=0（探针自身仅写 W20_combat 写域）。
- gamemd 残留核对：0。观察者（watcher3）经 stop_file 退出（watcher_done.txt
  reason=stop_file）。实例锁恢复 owner=lead。
- 结论：**`ra2youli/` 现状与开工前逐字节一致；本卡零净副作用。**
