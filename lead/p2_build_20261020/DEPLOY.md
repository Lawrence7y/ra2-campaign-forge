# P2 部署包（离线阶段 4-5 的载体，尚未部署）

生成：2026-10-20 08:14（GOAL-3T 驱动器，离线阶段 0-3）
来源：`lead/goal3_configsplit_20261019/`（R1 重交补丁副本，R2 核验 CONFIRMED）

## 包内清单与哈希（SHA-256）

| 文件 | 角色 | SHA-256 | 大小 |
|:--|:--|:--|--:|
| `ra2render.dll` | 新编译产物（P2 源码） | `39cbd665501416109368174394613c9608876728a3b57ca386aee8bdfd60cce3` | 165,376 B |
| `ra2render.ini` | P2 出厂配置（[Gameplay] 活动节头、键全注释） | `27c9a60c55a8a1b422d3ef06b90e3d343a93eb523a600286c937198b363ecee4` | 16,496 B |
| `rollback/ra2render.dll.pre_p2` | 部署前 DLL（回滚用） | `626f98b6d6327b10dd4c2c68e2d295870ff50f1073fd48756d02000f10c596c1` | 163,328 B |
| `rollback/ra2render.ini.pre_p2` | 部署前 ini（回滚用） | `fd9ebb32dcb6cda7952381baa10d24183ee98a7ea3e8e71fd8953a3a8d17b696` | 24,028 B |

## 部署（需用户在场；脚本不启动游戏）

```bat
deploy.cmd "D:\Project\ra2-campaign-forge\ra2youli"
```

- 脚本先校验包内 DLL/ini 哈希，再把目标目录现有 DLL/ini 备份到 `backup_<时间戳>\`，最后复制新件。
- 目标目录必须含 `gamemd.exe`；否则脚本拒绝执行。
- 脚本**不运行 build.bat、不启动 gamemd、不写 ra2bench/ra2youli 之外的任何位置**。

## 启动冒烟判据（RECEIPT T1；冷启动后读 `ra2youli\ra2render.log`）

必须同时满足（默认配置、不看 ini 文本）：

1. `[ra2render] 配置加载完成:` 行含 `TargetScanInterval=1`、`EnableStarCraftFog=false`、`EnableSpySatRadarSweep=false`、`EnableBuildingFog=false`、`EnableBulletFog=false`、`EnableUnitFog=false`，且对应来源为「默认值」。
2. `[ra2render-fog] 灰雾总闸: EnableStarCraftFog=0 (来源: 默认值`。
3. `[ra2render-visibility] VisibilityMode=vanilla (来源: 默认值) | 生效: 原版可见性`。
4. `[ra2render-gameplay] [G3-SPLIT] 玩法配置拆分: 旧节只读迁移命中 0 项`。
5. `[ra2render] 门控:` 行含 `TargetScanInterval=配置(1)->生效(1)`。
6. **不得出现** `[ra2render-fog] 成功将间谍卫星建筑` 重构行（SpySat 默认零改写）。

## 回滚

```bat
rollback.cmd "D:\Project\ra2-campaign-forge\ra2youli" "backup_<时间戳>"
```

不带第二参数时自动选最新的 `backup_*` 目录。回滚后以 `backup_<时间戳>\` 内实际备份文件的哈希复核；`rollback/` 内的 `pre_p2` 仅代表母本 pre-P2 态（`ra2youli\ra2render.ini` 现行版本可能与母本 pre-P2 版本不同，回滚以 `backup_*` 为准）。

## D2 裁决附加条件（Notion 2026-10-20，日志 §282）

1. 用户在场，由主会话执行；部署前确认 `gamemd`、`ra2loader`、`YURI` 均未运行。
2. 部署前先记录 `ra2youli\ra2render.ini`（现行 `a28122dd`）与母本 `fd9ebb32` 的差异，**只记录、不移植**；部署时必须用 P2 出厂 ini **整件覆盖**，不得把旧的 `=1` 带进去。部署后判据 4「迁移命中 0 项」即对此的直接验证。
3. `deploy.cmd` 复制后不校验目标文件：复制完须手工复核 `ra2youli` 下 DLL=`39cbd665`、ini=`27c9a60c`，并记录 `backup_*` 的实际哈希。
4. 冷启动时 `ddraw.ini` 必须保持 `windowed=false`（boot hang 修复）；若卡片头，先查此项再判断是否 P2 问题。
5. 六条判据全部满足并把日志原文摘录回执；任一不满足即执行 `rollback.cmd` 并核对回滚后哈希= `backup_*` 实际备份。**冒烟通过后 P2 才可勾 [x]。**

## 边界

- 本包只覆盖 `ra2youli\ra2render.dll` 与 `ra2youli\ra2render.ini`，不触碰 gamemd.exe、地图、存档或其他目录。
- 真机冷启动、日志读回、玩法键行为验收由主会话在用户在场时执行；驱动器未执行任何真机动作。
