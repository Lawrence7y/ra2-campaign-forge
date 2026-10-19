# 战役设计 JSON 规范（AI 编写指南）

AI 按本规范写一个 JSON，交给 `python -m ra2forge build` 即可编译成红警2尤复可玩的完整战役。

## 顶层结构

```json
{
  "campaign": { "name": "...", "description": "...", "side": "soviet|allied|yuri", "id": "RA2F1" },
  "missions": [ { ... }, { ... } ]
}
```

- `campaign.name`：战役显示相关名称（中文可用）
- `campaign.description`：**战役级简介**，写进 `BATTLEMD98.INI` 的 `Description`
  （战役选择界面里显示的那句话；取自设计文件，工具不硬编码任何文案）
- `campaign.side`：玩家阵营；决定默认玩家国家（soviet=Russians, allied=Americans, yuri=YuriCountry）
- `campaign.id`（**可选**）：追加战役条目的战斗 ID，默认 `RA2F1`。合法字符集
  ASCII 字母/数字/下划线、长度 1–16、必须以字母开头（它会成为 INI 段名 `[RA2F1]`）；
  官方 ID（`ALL1`/`SOV1`/`ALL02`…`SOV07`）被显式拒绝——引擎按战斗 ID 归并多个
  `BATTLEMD*.INI`，占用官方 ID 会**覆写**官方战役而不是追加。多个战役包同时安装时，
  给每个包一个不同的 `campaign.id`。

## 每个任务（mission）

| 字段 | 说明 |
|---|---|
| `name` | 地图文件名（ASCII 字母/数字/下划线），如 `ECH01` |
| `title` | 任务标题（写入地图 Name，中文可用） |
| `briefing` | 开场简报。`@@` 表示换行段落。中文可用 |
| `theater` | `TEMPERATE` / `SNOW` / `URBAN` |
| `size` | `[宽, 高]`，偶数，建议 80–120 |
| `player` | `{"house": "Russians"}`，见下方国家表 |
| `water` | 水域矩形数组：`{"row0","col0","row1","col1"}`（含端点） |
| `structures` / `units` / `infantry` | 物件数组，见下 |
| `waypoints` | `{"0": [row, col], ...}`，id 0–98 |
| `objectives` | 目标/事件数组，见下 |
| `next` | 可选：指定下一关的关卡名（`""` = 战役在这一关结束）；不写则按数组顺序自动串链，见《关卡链与 NextScenario》 |

### 坐标系（row, col）

`row ∈ [0, 高)` 从地图"上边缘"到"下边缘"，`col ∈ [0, 宽)` 从一侧扫到另一侧。
工具会自动换算成游戏的菱形等距网格，AI 只需保证 `0 <= row < 高`、`0 <= col < 宽`。
布局思路：把地图想象成一张 `宽 × 高` 的矩形图纸，玩家基地放一侧（如 row 60–70），
敌方基地放对面（如 row 10–25），水源放边缘条带。

### 国家（house，必须精确使用）

`Americans, Alliance, French, Germans, British, Africans, Arabs, Confederation,
Russians, YuriCountry, GDI, Nod, Neutral, Special`

同盟国系：Americans/Alliance/French/Germans/British；苏维埃系：Africans/Arabs/Confederation/Russians；
YuriCountry 与双方敌对。玩家与所选敌国默认自动开战。

### 常用代码（rulesmd 原版 id，原版引擎直接可用）

- 建筑：`GACNST`(盟军基地车展开) `NACNST`(苏军) `GAPOWR` `NAPOWR` `GAWEAP` `NAWEAP`
  `GAREFN` `NAREFN` `GAPILE` `NAHAND` `GARADR` `NARADR` `GATECH` `NATECH`
  `GAPILL`(机枪塔) `NASAM`(防空炮) `NABNKR`(战斗碉堡) `ATSLA`(光棱塔) `TESLA`(磁暴线圈)
- 车辆：`MTNK`(灰熊/犀牛) `HTNK`(天启) `TTNK`(磁能) `APOC` `V3` `MGTK`(幻影)
  `HTK`(防空车) `HARV`(矿车) `SMCV` `MCV` `DTRUCK`
- 步兵：`E1`(动员兵/大兵) `GI` `E2`(防空兵/火箭飞行兵用 `JUMPJET`) `ENGINEER` `SPY`
  `TANY` `BORIS` `IVAN` `DESO`(辐射工兵) `FLAKT`

### 目标（objectives）

胜利型（多目标时按顺序串联：完成第 1 个解锁第 2 个……最后 1 个达成即胜利）：

```json
{ "type": "destroy_all_forces", "enemy": "Americans" }
{ "type": "destroy_all_buildings", "enemy": "Americans" }
{ "type": "destroy_building", "structure_tag": "war_center" }   // 该 tag 必须挂在某个建筑上
{ "type": "survive", "seconds": 600 }
```

事件型（只是剧情演出，不影响胜负；`at_second` 为触发时刻，单位秒）：

```json
{ "type": "text", "text": "增援还有 4 分钟抵达！", "at_second": 30 }
{ "type": "speech", "eva": "EVA_ReinforcementsHaveArrived", "at_second": 362 }
{ "type": "timer", "seconds": 600 }                              // 显示并启动任务计时器
{ "type": "reveal_map", "at_second": 1 }                          // 全图侦察（调试/剧情用）
{ "type": "reveal_waypoint", "waypoint": 1, "at_second": 14 }     // 点亮某航点周边（故事化侦察）
{ "type": "hunt_wave", "house": "Americans", "at_second": 240 }   // 敌军全体进攻波次
{ "type": "reinforce", "at_second": 240, "at_waypoint": "A",
  "team": { "id": "0A110001", "house": "Russians",
            "units": [ { "count": 2, "type": "APOC" } ],
            "row": 45, "col": 6 } }
```

- `reinforce.team.id`：8 位十六进制字符串，全战役唯一（如 `0A110001`、`0A220002`）
- `at_waypoint`：字母 A/B/C…（对应 waypoint 0/1/2…，工具自动创建）；省略则从地图边缘增援
- `hunt_wave` 是让敌军"活起来"的关键：每隔几分钟一次 `AllToHunt`，敌军会倾巢进攻
- 常用 EVA 语音：`EVA_NewConstructionOptions` `EVA_ReinforcementsHaveArrived`
  `EVA_LowPower` `EVA_BaseUnderAttack` `EVA_UnitLost` `EVA_ObjectiveAchieved`
  `EVA_ObjectiveNotMet` `EVA_MissionAccomplished` `EVA_MissionFailed`

### 场景叙事（scenery，学习官方战役的关键）

官方战役的画面感来自大量中立元素：平民建筑群（含受损状态）、街上废置的汽车、树林、
弹坑与烧痕。设计 JSON 用 `scenery` 描述：

```json
"scenery": {
  "tree_rects": [ { "row0": 8, "col0": 0, "row1": 38, "col1": 20, "density": 0.10, "seed": 11 } ],
  "civilians":  [ { "type": "CASANF01", "row": 30, "col": 38, "health": 200 } ],
  "cars":       [ { "type": "CAR", "row": 32, "col": 41 } ],
  "smudges":    [ { "type": "CRATER02", "row": 28, "col": 40 } ]
}
```

- 温带城市建筑 id：`CASANF01/02/03` `CACHIG01/02` `CAMISC03/05/06` `CASTRT05` `CANEWY12`，
  技术建筑 `CAOILD`(油井)。`health` 低于 256 表现"受损的城市"
- 平民汽车：`CAR` `EUROC` `JEEP` `PTRUCK`（自动为 Neutral 阵营 + Sleep 状态）
- 弹坑烧痕：`CRATER02/10` `BURNT02/08/10`
- 树林自动撒布（跳过水面），`density` 0.05~0.15，`seed` 保证可复现

### 敌军要"活"，必须给它经济

敌人基地请放置 `GAREFN`+`HARV`（采矿经济），并在 `player` 里给
`"enemy_credits": 4000`（AI 启动资金），再用若干 `hunt_wave` 让它按时进攻——
否则敌军基地只是静态布景，玩家也永远遇不到战斗。

### 玩家与敌方配置（player）

```json
"player": { "house": "Russians", "credits": 5000, "enemy_credits": 4000 }
```

工具会为地图上所有 14 个标准阵营自动生成完整的 house 配置节
（PlayerControl/Credits/IQ/Edge/Color/Allies——游戏靠 `PlayerControl=yes`
识别玩家；漏写会导致玩家身份错乱、触发器失效甚至崩溃）。

## 关卡链与 `NextScenario`（战役怎么串起来）

关卡链写在每张地图的 `[Basic] NextScenario` 里：通关后引擎读这一项决定下一关。

- **默认（多数战役用这个）**：按 `missions` 数组顺序自动串，末关留空 = 打完回主菜单。
  示例三关即 `ECH01.MAP -> ECH02.MAP -> ECH03.MAP -> 空`。
- **分叉/跳关**：给单关加可选字段 `next`：

  ```json
  { "name": "ECH01", "title": "血色黎明", "next": "ECH03" }   // 跳到第三关
  { "name": "ECH03", "title": "终结之火", "next": "" }        // 在这一关结束战役
  ```

  - `next` 必须命名本战役里的某一关（工具会校验：不存在 → 构建失败）；
    不允许指向自己；`next: ""` 会让后面剩下的关卡不可达（只给 warning）。
  - 不写 `next` = 用默认顺序。
- **构建期硬自检**：每张 .MAP 写出后都会**从磁盘读回**并核对 `[Basic] NextScenario`；
  非末关留空（断链）会直接构建失败，不会产出"看着装好了、通关却卡住"的包。
- **末关结束语义**：链尾那一关（`NextScenario` 为空）同时写 `EndOfGame=yes`，
  其余关写 `EndOfGame=no`，与官方末关一致
  （依据：`extracted/yr_maps/map_133A0CB2.map:267` 官方末关 `EndOfGame=yes`）。
  真机验证后若发现通关后行为异常，可回退为 `no`。
- `AltNextScenario` 由建图器写成空值（官方战役用它做分支，本项目不使用）。

## 产物命名与安装形态（散装 `BATTLEMD98.INI` + `expandmd98.mix`）

一次 `build` 产出 `<out>/<战役名>/`：

| 文件 | 作用 |
|---|---|
| `ECH01.MAP`、`ECH02.MAP`… | 各关地图（`[Basic] NextScenario` 串链，单张也能独立试玩） |
| `BATTLEMD98.INI` | **散装**追加战役条目（注册文件；删掉即注销） |
| `expandmd98.mix` | 地图归档（**只放地图，0 个 INI**） |
| `story.md` | 剧情文档（给人看） |
| `BUILD_REPORT.txt` | 构建日志：关卡链、产物 sha256、自检结果 |
| `INSTALL.txt` | 手工安装/卸载说明 |

**注册文件必须散装**：引擎用 `FindFirstFileA("BATTLEMD*.INI")` 扫**游戏目录**
（VA `0x52CBA0`；找不到时回退同名 `BATTLEMD.INI`，`0x52CCCD`），只认文件系统里的
散装文件，**MIX 内部的同名文件永远不会被这条通配命中**。所以注册文件不能塞进 mix。

`BATTLEMD98.INI` 的内容形态：

```ini
[Battles]
15=RA2F1

[RA2F1]
CD=2
Scenario=ECH01.MAP
FinalMovie=
Description=<设计文件的 campaign.description>
```

- `15` 是 `[Battles]` 索引：官方占 1–14，本项目**只追加**，从不改写官方条目。
- `RA2F1` 是自有战斗 ID（可用 `campaign.id` 改），**绝不占用官方 ID**（`ALL1`/`SOV1`/…）。
- `Description` 取自设计文件的 `campaign.description`（纯文本，不是 `DESC:ALL1` 这种 CSF 标签）。

**`expandmd98.mix` 只放资源（本项目=地图）**：通配看不到 MIX 内 INI；而且
`expandmd##.mix` 在 `ra2md.mix` **之前**装载，同 CRC 条目会遮蔽官方件
（例如 `local mix database.dat`，外部工具要用）。构建期会断言「mix 内条目 == 地图 CRC 集合、
且没有任何 `.INI`」，违者构建失败。

**安装形态**（`python -m ra2forge install --package <包目录> --game <游戏目录>`，或
`build --install`；MCP 的 `build_campaign` 传 `install_dir` 走同一条路径）：

1. 逐文件复制 `BATTLEMD98.INI` → `*.MAP` → `expandmd98.mix`；
2. 每个被替换的文件先备份为 `<名字>.ra2forge.bak`（已有备份槽时不覆盖：最早的原件优先），
   并写清单 `ra2forge_install.json`；
3. `uninstall` 按清单删除自己写的散装文件、还原备份（文件被外部改动过则保留 + 告警，
   除非 `--force`）。官方 `BATTLEMD.INI` 全程不被写入。

**迁移须知（从旧版 ra2forge 升级）**：

- 旧版安装会在游戏目录留下**被改写的官方 `BATTLEMD.INI`**（首行带
  `; Generated by RA2 Campaign Forge` 标记，把官方 `[SOV1]` 等指到了我们的地图上）。
- 正确处理：**先备份**（重命名为 `BATTLEMD.INI.ra2forge.bak`），**再用 `extracted/found_battlemd.ini`（2,733 B，留存的官方原文：`[Battles] 1=ALL1 … 14=SOV07`）恢复该文件**。
  【勘误 2026-09-27 · Lead 实测推翻】**删除散装 `BATTLEMD.INI` 不会回退到 MIX** —— Lead 用 mixlib 扫过游戏目录全部 17 个 MIX（`ra2/ra2md/langmd/language/expandmd01/expandmd98/maps01/maps02/mapsmd03/movies01/movies02/movmd03/multi/multimd/theme/thememd/wdt`），**无任何 MIX 含官方 `BATTLEMD.INI`**（唯一命中的是 ra2forge 自己的 `expandmd98.mix`）。官方该文件原本是**散装件**、被旧版就地覆盖 ⇒ **删除它会让官方战役列表彻底消失**。
  该官方文件的注释本身即为通配机制背书：「Additional files that begin with BATTLE will augment this list」。
  若嫌其中的调试占位条目（`ALL02..SOV07`）多余，可只保留 `1=ALL1 / 2=SOV1` 两行，但**不能**删除文件本身。
- 工具路径：`python -m ra2forge uninstall --game <游戏目录> --legacy`
  （有备份则还原；无备份时只告警不删，加 `--drop-legacy-battlemd` 才把它改名移开）；
  然后再装新版。
- 升级后**不要**同时留着旧 `BATTLEMD.INI` 覆盖件：两个文件会被引擎一起归并，
  本战役仍能启动，但官方列表会继续被旧文件改写。

## 好的战役设计建议（给 AI）

1. 每关一个清晰目的：首关建家+清剿，中关守/伏击/限时，末关攻坚标志性建筑。
2. 简报要有剧情推进与具体指令；用 `text`/`speech` 在关键时刻演出。
3. 敌方基地要有梯次（电厂→防御→生产→核心），数量与玩家兵力匹配。
4. 水域只放边缘条带或小块湖泊（当前版本水面无海岸线过渡，避免大面积）。
5. 每关给 1–2 个增援点（`at_waypoint`），让玩家感到节奏。
6. `size` 90–100 时，玩家基地 row 与敌方 row 之间留 20+ 行空间。
