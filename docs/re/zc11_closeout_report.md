# ZC-11 收尾门禁与交付收口报告（CLOSEOUT）

> [META]
> task=ZC-11-CLOSEOUT · 执行方=MiMo（收尾核验/清理/记忆）· 日期 2026-09-29
> 上游交付：`out/re_work/zcode_live/RESULT_ZC11.md`（ZCode 真机批，2026-09-29 23:35）
> 本文只做：**门禁复跑、残留清理、与报告声明的差异登记、跨会话记忆要点、待裁决汇总**。不改 RESULT 本体、不改 `ra2render/**`。

---

## [0] 结论摘要

1. **收尾门禁双绿**（MiMo 独立复跑）：`verify_anchors.py` **323/323**；`bench_map_install.py --verify --game-dir ra2bench` **13/13**。
2. **战役残留存档已清**：`ra2bench` 无 `SOV01UMD.sav`；会话产生 4 份自动存档已在 `zc11/evidence/**/quarantine*` 留证；`ALL01UMD.sav`/`SOV01T.sav` 为接手前既有（9/25），按 RESULT [5] 口径**保留**。
3. **★与 RESULT [7] 声明存在差异（必读）**：收尾时 `ra2bench/except.txt` **存在**（创建 2026-09-29 22:38:24，26,830 B，EXCEPTION_ACCESS_VIOLATION @ `007CFC9F`），与报告「全程未生成 except.txt / 收尾仍不存在」**不符**。已哈希留证并隔离出游戏目录，**不得**据此宣称「零崩溃」。
4. 段 G 维持 **[待实测]**（无 dump 不伪造）；H1 分档失效与 harness ESC 缺陷升为 P0/P1 待裁决。

---

## [1] 收尾门禁（实跑原文摘要）

| 门禁 | 命令 | 结果 |
|---|---|---|
| 锚点/基线 | `python tools\verify_anchors.py` | **323/323 PASS**；`.text` sha256 `c0368a17…` 一致；`.detour` 签名未变 |
| 基准图 | `python tools\bench_map_install.py --verify --game-dir ra2bench` | **PASS=13 / FAIL=0** |
| 进程 | `Get-Process gamemd,ra2loader` | 无残留 |
| ini | `ra2bench\ra2render.ini` | RESULT 载明 sha256 `B8BB8238…` = 接手快照（本卡未再改） |

---

## [2] 残留清理台账

| 对象 | 清理前 | 动作 | 清理后 |
|---|---|---|---|
| 战役自动存档 `SOV01UMD.sav` | 已被 ZC-11 即时隔离 ×4 | 确认隔离留证 | `ra2bench` **无**该文件 |
| `ALL01UMD.sav` / `SOV01T.sav` | 9/25 既有（接手前） | **保留**（非本会话残留） | 仍在 |
| `ra2bench/except.txt` | 22:38 崩溃转储（与 [7] 冲突） | **哈希后隔离**至 `evidence/closeout/` | 游戏目录已无 |
| `ra2render.log` | 4.1MB 遥测 | 保留（诊断资产） | 仍在 |

`except.txt` SHA256 = `B42C7014C96CADCB2DA86327CA6A62E302A043283238531880325809D7D35870`

崩溃摘要（隔离件首行）：`EXCEPTION_ACCESS_VIOLATION`，Access `FE00FFFF`，EIP `007CFC9F`，`EDX=FE00FFFF`（疑似毒值/未初始化指针）。**未定位归属**（是否发生在 ZC-11 窗口内的哪一段、是否与注入件相关）——见 [5] 待办。

---

## [3] ZC-11 各段结论（引用 RESULT，收尾核对）

| 段 | 结论 | 收尾核对 |
|---|---|---|
| 0 | 分离生效；官方菜单版式 | 门禁/manifest 一致 ✔ |
| A | 默认档静态矩形 diff=0；动态相位 RNG 与 DLL 无关 | 口径已写明 ✔ |
| B | vision-dirty 生效；静态 md5 全等；回雾 ≤9 帧；ramp 计数恒 0 用像素补证 | ini 已还原 ✔ |
| C | 运行期镜像生效；**M1 最优、常数 k 再否决**；g≈67–72 | ini 已还原 ✔ |
| D | **H1 分档不成立**（units_seen [21,723] 国家主导） | 图已 restore + verify ✔ |
| E | **键盘等时闭环复位可用**（RIGHT 1.0s / LEFT 1.0s，MAD 0.13，NCC 0.996，×3） | 建议固化 ✔ |
| G | [待实测]；静态钉死 `0x4201C7` 表写入口 | 不伪造 ✔ |

---

## [4] 跨会话记忆要点（已写入 MEMORY / session notes）

### 4.1 机位复位方法（可用）
- **禁用**：小地图点击（ZC-10A：点击无效的空洞 MAD=0）。
- **可用**：键盘等时闭环 — `RIGHT 1.0s` 挪走（MAD≈13.4 ≫ 噪声）⇄ `LEFT 1.0s` 复位；验收 **MAD≤2.0 且 NCC≥0.99**（ROADS 静态 ROI 逐字节 0 差），×3 重复。
- 边缘滚屏无效；复位后若镜头被战斗拽走须重做对齐校验。

### 4.2 H1 负载发现（P0）
- units_seen 由**对阵国家**主导：随机敌国 713–723；美 vs 蘇 22–30；与图内条目 350/1400/5600、档位 50/200/800 **无标度关系**。
- **拆明 fanout 前，一切 H1 性能 ROI 数字不可用**（V3 口径 U200∈[100,320] 不成立）。
- 下一步：静态拆 `[TaskForces]/[TeamTypes]`/触发器 + 多国家矩阵实测。

### 4.3 Harness 陷阱
- `bench_replay.py enter_battle` fallback：地图加载中 **ESC×2 会打断开局**（units_seen 恒 0）；须「帧推进 + 战术区色数」双校验，进对局确认前禁 ESC。
- 官方最小采样兵力门禁与 H1 实测 713 不兼容（>320 上限）。
- `FogStrengthPct` 镜像已可局内换挡（≤0.45s），但 `L4DirtyMode` 仍启动读。
- 段 D 用「U0200 槽位置换」测 U0050/U0800 时必须 finally 还原并断言 sha。
- 水纹相位按局 RNG：全帧严格 D≡0 原理不可达，对拍用**静态矩形**口径。

---

## [5] 待裁决 / 下一步

| # | 项 | 级 | 说明 |
|---|---|---|---|
| 1 | **except.txt 归因** | P0 | 22:38 崩溃是否注入件相关；对 RESULT [7] 做勘误登记 |
| 2 | **H1 分档失效专项** | P0 | 性能 ROI 前提 |
| 3 | enter_battle ESC 缺陷修复授权 | P1 | harness |
| 4 | 箭头键复位三件套固化进 harness | P1 | segE3 可移植 |
| 5 | vision-dirty 默认切换 | P2 | 建议维持 force-full，先要帧率 A/B |
| 6 | 非线性混色桩 | P2 | 先做 G dump + 雾格分层 |
| 7 | E-1～E-9 + 46 标签写回冻结文档 | P2 | `out/re_work/errata_patches/by_file/` 已备 |
| 8 | Gap NOP 3×6B 落地 | P0 | 动 `ra2render`，待代码轨授权 |

---

## [6] 产物索引

- 真机主报告：`out/re_work/zcode_live/RESULT_ZC11.md`
- 证据树：`out/re_work/zcode_live/zc11/evidence/`（seg0–G + quarantine + closeout）
- 本文：`docs/re/zc11_closeout_report.md`
- 离线辅证：`docs/re/fog_gray_mix_offline_verify.md`、`landing_pack_preflight_audit.md`、`va_claims_p1.md`、`fog_firststage_site_locate.md`、`errata_patch_blocks_E1E2.md`
