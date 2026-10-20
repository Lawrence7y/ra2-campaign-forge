# P2 部署 + 冷启冒烟结果（2026-10-20 08:53）

## 结论

**P2 冒烟 PASS（六条判据全过）**。按 D2 条件⑤，P2 可勾 [x]；T2–T4（老用户迁移/联机门控/卸载对称）本次未跑，另行排期。

## 部署

| 项 | 值 |
|:--|:--|
| 部署时间 | 2026-10-20 08:52:27 |
| 部署前备份 | `deploy/backup_20261020_085227/`（旧 DLL `626f98b6`、旧 ini `a28122dd`） |
| 目标 DLL | `39cbd665501416109368174394613c9608876728a3b57ca386aee8bdfd60cce3`（165,376B） |
| 目标 ini | `27c9a60c55a8a1b422d3ef06b90e3d343a93eb523a600286c937198b363ecee4`（16,496B） |
| ddraw.ini | `windowed=false`（D2 条件④；原值 true 已备份到 `deploy/backup_ddraw/ddraw.ini.pre_p2`，hash `6d86e1ef…`） |
| 部署前进程 | gamemd/ra2loader/YURI 均未运行 |
| 启动方式 | `ra2youli\ra2loader.exe` 冷启动（gamemd pid 8448 / ra2loader pid 57820） |
| 日志 | `ra2youli\ra2render.log`（8,689B；副本 `smoke_evidence/ra2render.log`） |
| except.txt | mtime 仍为 2026-10-08 21:59，未新增 |

## 六条判据（D2 条件⑤）

| # | 判据 | 结果 | 日志证据（节选） |
|:--|:--|:--|:--|
| 1 | 配置加载完成目标值全关且来源=默认值 | **PASS** | `[ra2render] 配置加载完成: TargetScanInterval=1, … EnableStarCraftFog=false, EnableSpySatRadarSweep=false (CD=600, Radius=16), EnableBuildingFog=false, EnableBulletFog=false, FadeFogTransition=true, EnableMinimapFog=false, EnableUnitFog=false`；`配置来源: … TargetScanInterval=1 (来源: 默认值) …` |
| 2 | 灰雾总闸=0 来源默认值 | **PASS** | `[ra2render-fog] 灰雾总闸: EnableStarCraftFog=0 (来源: 默认值, 生效: 关(已探索非直视档强度归零; 未探索黑幕保留))` |
| 3 | VisibilityMode=vanilla 来源默认值 | **PASS** | `[ra2render-visibility] VisibilityMode=vanilla (来源: 默认值) | 生效: 原版可见性(不做任何视距剔除…)` |
| 4 | 旧节迁移命中 0 项 | **PASS** | `[ra2render-gameplay] [G3-SPLIT] 玩法配置拆分: 旧节只读迁移命中 0 项` |
| 5 | 门控 TargetScanInterval=配置(1)->生效(1) | **PASS** | `[ra2render] 门控: MpActive=false, … TargetScanInterval=配置(1)->生效(1), …` |
| 6 | 无间谍卫星重构行 | **PASS** | 全文无 `间谍卫星…重构` 行 |

## 备注

- 部署包内 `deploy.cmd` 复制后不校验目标文件；本轮已手工复核目标 DLL/ini 哈希（见上表）。
- `ra2youli/ra2render.ini` 现行 `a28122dd` 与母本 `fd9ebb32` 的差异已预录：`deploy/PRE_DEPLOY_INI_DIFF.md`（只记录，不移植）。
- 冷启动后游戏停留在主菜单；T55k 前需关闭当前 gamemd/ra2loader。
