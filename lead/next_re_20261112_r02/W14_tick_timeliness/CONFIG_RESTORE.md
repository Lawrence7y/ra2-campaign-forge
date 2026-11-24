# CONFIG_RESTORE · W14 RE-N04d

基线：`baseline_pre_launch\`（本轮启动前字节副本 + PRE_LAUNCH_BASELINE.tsv）

## 启动前守卫（探针实算，5/5 match）
| 文件 | bytes | sha256 | match |
|---|---|---|---|
| RA2MD.INI | 1754 | c91c6a47…cd3c27d | ✅ |
| ddraw.ini | 14782 | c983abad…6df9d52 | ✅ |
| RA2MD.INI.benchbak | 1754 | c91c6a47…cd3c27d | ✅ |
| gamemd.exe | 4825360 | 73201cc0…fcf67476 | ✅ |
| ddraw.dll | 411648 | 85e0f7d5…83b03a9 | ✅ |

载体：`[8]试验地_Pro_ProvingGrounds.yrm` 175,361 B / sha256 `3e3c874572bc02199cddce05b3633888caf968e6fbb457e763fb70b9fbfd5b19`（卡面钉定值一致）。

## 运行期变化（游戏自身，非探针）
- `written_back`（启动前 vs 关闭后清单 diff，647/647 项）：**changed=1 = RA2MD.INI**
  —— gamemd 退出时按惯例自行改写自身 INI（与历轮相同），探针未写过该文件。

## 收尾还原（探针 finally 执行 + 本报告成文时代理复算终态）
- 逐字节拷贝还原 RA2MD.INI / ddraw.ini / RA2MD.INI.benchbak：
  post_restore_sha256 三者均等于基线哈希，`byte_identical_to_baseline=True`（实算自证）。
- gamemd.exe / ddraw.dll verify-only：哈希与基线一致（未变）。
- **代理终态复算（04:09，探针退出后）**：
  `RA2MD.INI` = c91c6a47…cd3c27d match ✅；`ddraw.ini` = c983abad…6df9d52 match ✅。

## 结论
配置终态与基线**逐字节一致**；`ra2youli` 清单 0 增 0 删（changed 1 项由游戏自身产生、
已还原）；5 文件哈希守卫全过。
