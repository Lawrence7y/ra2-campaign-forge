# CONFIG_RESTORE.md —— 配置逐字节还原与残留进程核对

- run_id: `NEXT_RE_20261112_R02`；生成时刻(UTC): `2026-11-12T16:06:45.279096+00:00`

## 1. 启动前守卫（实算 SHA-256）

| 文件 | bytes | 实算 SHA-256 | 期望(守卫/基线) | 一致 |
|---|---|---|---|---|
| RA2MD.INI | 1754 | `c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d` | `c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d` | True |
| ddraw.ini | 14782 | `c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52` | `c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52` | True |
| RA2MD.INI.benchbak | 1754 | `c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d` | `c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d` | True |
| gamemd.exe | 4825360 | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | True |
| ddraw.dll | 411648 | `85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9` | `85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9` | True |

- `RA2MD.INI` 守卫值 `c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d`（任务卡）→ 实算一致 = **True**。

## 2. 残留进程核对

- 启动前 `gamemd.exe` 残留：**0** 个 `[]`
- 收尾后 `gamemd.exe` 残留：**0** 个 `[]`
- 关闭步骤（只针对自己启动的 pid，优雅优先）：
  - WM_CLOSE(hwnd=23268762) -> True
  - taskkill /PID 4856 (无 /F) rc=0 out='SUCCESS: Sent termination signal to the process with PID 4856.'
  - taskkill /F /PID 4856 rc=0 out='SUCCESS: The process with PID 4856 has been terminated.'
  - 最终存活=False

## 3. 配置逐字节还原（baseline_pre_launch\ → ra2youli\，实算 SHA-256 自证）

| 文件 | 还原前 SHA | 基线副本 SHA | 还原后 SHA | 逐字节一致 | 哈希一致 |
|---|---|---|---|---|---|
| RA2MD.INI | `099904d9345053383e53aa091d3475e14d56b3880695094a4967b9ac337a05c9` | `c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d` | `c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d` | True | True |
| ddraw.ini | `c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52` | `c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52` | `c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52` | True | True |
| RA2MD.INI.benchbak | `c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d` | `c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d` | `c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d` | True | True |
| gamemd.exe | (仅校验，无字节副本) | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | — | 未改动=True |
| ddraw.dll | (仅校验，无字节副本) | `85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9` | `85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9` | — | 未改动=True |

本卡额外独立复核（`Path.read_bytes()` 逐字节比对 + 实算 SHA-256）：

| 文件 | 基线 SHA | 目标 SHA | 字节相同 | 与任务卡守卫/TSV 一致 |
|---|---|---|---|---|
| RA2MD.INI | `c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d` | `c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d` | True | True |
| ddraw.ini | `c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52` | `c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52` | True | True |

**配置逐字节还原 = True**

## 4. 游戏写回了哪些文件（与启动前清单比对）

- 清单范围：`ra2youli\` 有上限递归扫描；启动前 647 项，收尾 647 项。
- 新增 0 / 删除 0 / 变化 1
- added (0): （无）
- removed (0): （无）
- changed (1): `RA2MD.INI`

> 清单比对发生在还原**之前**，故记录的是游戏真实写回；还原本身会再次改写配置文件。

