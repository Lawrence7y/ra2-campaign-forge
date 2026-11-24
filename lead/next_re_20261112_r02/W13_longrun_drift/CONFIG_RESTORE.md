# W13 · CONFIG_RESTORE.md（RE-N04b attempt 3 配置还原自证）

## 基线
- 来源：`lead/next_re_20261112_r02/baseline_pre_launch/`（RA2MD.INI / ddraw.ini / RA2MD.INI.benchbak 字节副本 + PRE_LAUNCH_BASELINE.tsv）。

## 启动前守卫（5 文件全 match=True）
| 文件 | bytes | sha256 | match |
|---|---|---|---|
| RA2MD.INI | 1754 | c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d | True |
| ddraw.ini | 14782 | c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52 | True |
| RA2MD.INI.benchbak | 1754 | c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d | True |
| gamemd.exe | 4825360 | 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476 | True |
| ddraw.dll | 411648 | 85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9 | True |

## 收尾还原（探针 finally，逐字节 copyfile + 实算自证）
| 文件 | 还原前 sha256 | 还原后 sha256 | byte_identical_to_baseline | sha_match | tsv_matches_copy |
|---|---|---|---|---|---|
| RA2MD.INI | 099904d9345053383e53aa091d3475e14d56b3880695094a4967b9ac337a05c9（游戏运行改写） | c91c6a47…c3c27d | **True** | **True** | True |
| ddraw.ini | c983abad…f9d52（未变） | c983abad…f9d52 | True | True | True |
| RA2MD.INI.benchbak | c91c6a47…c3c27d（未变） | c91c6a47…c3c27d | True | True | True |
| gamemd.exe（verify_only） | — | 73201cc0…67476 | — | unchanged=True | — |
| ddraw.dll（verify_only） | — | 85e0f7d5…b03a9 | — | unchanged=True | — |

## 文件清单 diff（ra2youli，启动前 647 项 vs 收尾后 647 项）
- added=[] · removed=[] · **changed=[RA2MD.INI]**（仅游戏运行期改写，已还原自证如上）。

## 结论
`ra2youli` 现场 = 基线逐字节一致；进程残留 0；锁已恢复 owner=lead。meta.json 对应字段：
`restore_rows`（全部 sha_match=true 且 byte_identical=true）、`residual_after=[]`、`written_back.changed=[RA2MD.INI]`、`lock_restored=true`。
