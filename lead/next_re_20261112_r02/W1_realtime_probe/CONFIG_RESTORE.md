# CONFIG_RESTORE.md —— 配置还原与残留进程核对

- run_id: `NEXT_RE_20261112_R02`
- 生成时刻(UTC): `2026-11-12T14:36:41.551342+00:00`
- NDJSON: `D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W1_realtime_probe\out\gate_probe_R02b.ndjson`

## 1. 残留进程核对

- 启动前 `gamemd.exe` 残留：**0** 个 []
- 收尾后 `gamemd.exe` 残留：**0** 个 []
- 关闭步骤（只针对自己启动的 pid）：
  - WM_CLOSE(hwnd=30084836) -> True
  - taskkill /PID 42372 (无 /F) rc=0 out='SUCCESS: Sent termination signal to the process with PID 42372.'
  - taskkill /F /PID 42372 rc=0 out='SUCCESS: The process with PID 42372 has been terminated.'
  - 最终存活=False

## 2. 配置逐字节还原（基线 → 还原后）

| 文件 | 收尾时(还原前) SHA-256 | 基线 SHA-256 | 还原后 SHA-256 | 结论 |
| --- | --- | --- | --- | --- |
| RA2MD.INI | 099904d9345053383e53aa091d3475e14d56b3880695094a4967b9ac337a05c9 | c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d | c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d | 逐字节一致=True / 哈希一致=True |
| ddraw.ini | c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52 | c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52 | c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52 | 逐字节一致=True / 哈希一致=True |
| RA2MD.INI.benchbak | c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d | c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d | c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d | 逐字节一致=True / 哈希一致=True |
| gamemd.exe | (无字节副本，仅校验) | 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476 | 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476 | 未改动=True |
| ddraw.dll | (无字节副本，仅校验) | 85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9 | 85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9 | 未改动=True |

**结论：`RA2MD.INI` / `ddraw.ini` 是否逐字节还原 = True**

## 3. 游戏写回了哪些文件（与启动前清单比对）

- 清单范围：`ra2youli\` 有上限递归扫描（上限 6000 文件）；启动前 647 个，收尾 647 个。
- 新增 0 / 删除 0 / 变化 1
- added (0): （无）
- removed (0): （无）
- changed (1): `RA2MD.INI`

> 注：配置还原发生在清单比对 **之后**，因此上表记录的是游戏真实写回结果；还原本身会再次改写 `RA2MD.INI` / `ddraw.ini`。

## 4. 两趟汇总（Run 1 原件见 `out\run1\CONFIG_RESTORE.md`）

| 项 | Run 1 (300 s) | Run 2 (180 s) |
| --- | --- | --- |
| 启动前残留 | 0 | 0 |
| 自启动 pid | 41052 | 42372 |
| 关闭方式 | WM_CLOSE → `taskkill /PID` → `taskkill /F /PID`（仅本 pid） | 同左 |
| 收尾后残留 | **0** | **0** |
| `RA2MD.INI` 还原前哈希 | `099904d9345053383e53aa091d3475e14d56b3880695094a4967b9ac337a05c9` | 同左 |
| `RA2MD.INI` 还原后哈希 | `c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d` | 同左 |
| `ddraw.ini` 还原后哈希 | `c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52` | 同左 |
| 逐字节一致 | **是** | **是** |
| 游戏写回的文件 | 仅 `RA2MD.INI`（新增 0 / 删除 0 / 变化 1） | 仅 `RA2MD.INI`（新增 0 / 删除 0 / 变化 1） |
| `gamemd.exe` / `ddraw.dll` | 未改动（哈希与基线一致） | 未改动 |

**最终实算自证（收尾后再次独立计算，2026-11-12T14:36Z 之后）**：
`RA2MD.INI = c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d`、
`ddraw.ini = c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52`、
`RA2MD.INI.benchbak = c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d`、
`gamemd.exe = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`、
`ddraw.dll = 85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9`，
全部与 `PRE_LAUNCH_BASELINE.tsv` 一致；`Get-Process -Name gamemd` 返回空。
