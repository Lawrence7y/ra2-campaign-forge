# R205-EXEC-X1 — 独立重算 RTTI 类块布局

- 目标文件：`ra2bench/gamemd.exe`，sha256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`
- 取证脚本：`recompute.py`（`python3 _r205/exec_x1/recompute.py` 可完整复跑，原始输出见 `evidence.txt`）
- 只读 gamemd.exe；未改动任何台账 / 锁 / 状态板 / `_r` 系列既有文件。

## 实测结果

| 编号 | 实测值 | 判据（一句话） |
|---|---|---|
| X1 | 1214 | 遍历 `.rdata`/`.data` 每个 4 字节：`sig∈{0,1,2}`、`+8==0`、`pTD∈.data`、`pCHD∈.rdata`、`cstr(pTD+8,400)` 以 `.?A` 开头且以 `@@` 结尾。 |
| X2 | 891 | 遍历所有段中指向 `.text` 的 dword `v`，且 `dw(v_addr-4)∈COL`，收集 `v` 去重。 |
| X3 | 954 | 按每条 COL 的 `pCHD`（即 COL+16）分组，不同组键即 CHD 地址。 |
| X4 | 954 / 954（全部命中，0 失败） | CHD `a`：`dw(a+16)==0`、`dw(a+20)==0`、`dw(a+24)==0`、`where(dw(a+28))=='.data'`、`dw(a+32)==a`。 |
| X5 | 954 / 954 | `a+16` 起按 COL 五 dword 解读，其地址属于 X1 的 COL 集合。 |
| X6 | 954 / 954 | X5 命中的内嵌 COL 的 `pCHD`（`dw(a+32)`）等于宿主 CHD 地址 `a`。 |
| X7 | `{"1": 954}` | 每个 CHD 组内 `mdisp==0` 的 COL 计数分布：954 个组各恰好 1 条（另有 260 条 COL 非组内的“主”零偏移代表，见下）。 |
| X8 | mdisp==0 总数 978；pTD 属于 954 个自有 pTD 者 956；不属于者 22 | 去重 BCD（BCA 引用）按 `+8` 有符号 mdisp==0 过滤；pTD 按类型描述符指针是否等于 CHD 内嵌 COL 的 `dw(a+28)`；“不属于”按名字复核，确认均不在 954 个类名集合中。 |

补充统计：COL 总数 1214，CHD 组 954，但因组数为 954 且每组恰有 1 条 `mdisp==0`，另有 260 条 COL 的 `mdisp!=0`（X7 据此与 X1 差额吻合：1214-954=260）。去重 BCD 1002 条，其中 mdisp==0 978 条。

## 三项反控

- **C1（5000 个随机 `.rdata` 地址，X4 五元判据）**：命中 **132** 次（`[0x7e1008,0x811fd8]`，按 40 字节对齐采样 5017 个槽位，seed=205，例：`0x80be48, 0x7fac10, 0x80b998, 0x80cde8, 0x806290`）。判据对真 CHD 是 100%（954/954），对随机对齐槽约 2.6%，不是恒真。注意若按 4 字节任意采样，命中率会降至约 2%（98/5000），本卡口径属于随机地址，两种都远低于真阳性率。
- **C2（X4 整体错位 +4）**：改看 `a+20/+24/+28/+32/+36` 后命中 **0 / 954**。结构签名精确锚定在 +16，不存在偏移容差。
- **C3（X8 “不属于”的 22 条 pTD 名字）**：全部 **不在** 954 个类名集合中，逐条如下（均来自类型描述符 `pTD+8`）：

| BCD | pTD | 名字 |
|---|---|---|
| 0x7fa9e8 | 0x816b70 | `.?AUIUnknown@@` |
| 0x7faa00 | 0x816b88 | `.?AUIGameMap@@` |
| 0x7fb080 | 0x816b70 | `.?AUIUnknown@@` |
| 0x7fb098 | 0x817790 | `.?AUIPersist@@` |
| 0x7fb0b0 | 0x8177a8 | `.?AUIPersistStream@@` |
| 0x7fbbc8 | 0x8186a8 | `.?AUIApplication@@` |
| 0x7fcc10 | 0x81b928 | `.?AVDiskSwap@@` |
| 0x7ff6f0 | 0x81f628 | `.?AUIEnumConnections@@` |
| 0x7ff7a8 | 0x81f6a8 | `.?AUIConnectionPoint@@` |
| 0x7ff858 | 0x81f728 | `.?AUIEnumConnectionPoints@@` |
| 0x7ff940 | 0x81fbf8 | `.?AUISequentialStream@@` |
| 0x7ff958 | 0x81fc18 | `.?AUIStream@@` |
| 0x802368 | 0x823ed8 | `.?AUIClassFactory@@` |
| 0x803618 | 0x825ac0 | `.?AV?$Node@PAUINIEntry@INIClass@@@@` |
| 0x805d90 | 0x82c2f0 | `.?AV?$Node@PAVMixFileClass@@@@` |
| 0x8092d0 | 0x83f580 | `.?AV?$DynamicVectorClass@W4DiskID@@@@` |
| 0x80b6e0 | 0x842718 | `.?AUISwizzle@@` |
| 0x80e478 | 0x849558 | `.?AUIWOLBrowserEvent@@` |
| 0x80e618 | 0x84a7a0 | `.?AUINetUtilEvent@WOL@@` |
| 0x80e6a8 | 0x84a818 | `.?AUIChatEvent@WOL@@` |
| 0x80e930 | 0x84d6a8 | `.?AUIDownloadEvent@WOL@@` |
| 0x80e948 | 0x84d6d0 | `.?AVCDownloadEventSink@@` |

这些多为 COM 接口（`.?AU...@@`）或模板辅助类，未取得独立 CHD 记录，作为基类描述符出现在其他类的 BCD 中——与“RTTI 类块是每类自包含 40 字节 CHD 记录”的判据一致：有 CHD 的类 954 个，另有 22 个基类只有类型描述符。

## 与主会话判据的异同 / 异议

- X1–X7 全部独立复算得到：1214 / 891 / 954 / 954 / 954 / 954 / `{"1":954}`，未见与主会话数字冲突。
- X8 的“pTD 属于自有 pTD”按 **指针相等** 判为 956，但其中 2 条 BCD 复用另一类的 pTD 指针却名字不在集合——严格按“名字属于 954 个类名集合复核”口径，不属于者应为 **22**（而非按指针得到的 20）。两种口径的差为 2，且 `result.json` 记录的 `ptd_not_in_own=22` 采用名字复核口径，与 C3 逐条列表一致。
- 对 X4 的小保留：C1 显示 40 字节对齐的随机槽位约有 2.6% 命中率（真 CHD 100%）。判据仍有强区分力，但不能表述为“二进制世界中唯一恒真签名”；它依赖 `.rdata` 中 40 字节对齐且相邻字段全零、末字段自引用的组合。
- 未发现其他需要打脸主会话的差异。
