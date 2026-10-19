---
name: ra2-campaign-forge
description: 为《红色警戒2：尤里的复仇》生成一套由 AI 编写的完整故事线战役（多张任务地图 + 战役注册 + 一键安装包）。当用户想要"生成红警2战役 / 做 RA2 任务包 / AI 写红警剧情战役"时使用。
---

# RA2 Campaign Forge

把 AI 设计的故事线编译成尤复可玩的战役。核心工具在 `D:\Project\ra2-campaign-forge`。

## 工作流

1. **收集设定**（用户没说就按建议默认）：阵营（soviet/allied/yuri）、关数（建议 3–5）、
   主题/时代背景、想要的著名兵种。然后**自己写完整的故事线**：背景 → 每关剧情 → 结局。
2. **写设计 JSON**：严格按照 `D:\Project\ra2-campaign-forge\docs\DESIGN.md` 的规范写
   （先读它！里面有国家表、建筑/单位代码、目标类型、坐标系说明）。要点：
   - 每关：`name`（ASCII）、`title`/`briefing`（中文可用，`@@` 为换行）、`theater`、`size`
   - 物件坐标用 `(row, col)` 图纸思维；玩家基地与敌基地之间留足空间
   - 目标用 `objectives`：胜利型（destroy_all_forces / destroy_building / survive）按顺序串联
   - 剧情演出用 `text` / `speech` / `timer` / `reinforce`（team.id 用 8 位十六进制，全战役唯一）
3. **校验 + 构建**（在 `D:\Project\ra2-campaign-forge` 下运行）：
   ```
   python -m ra2forge validate <design.json>
   python -m ra2forge build --design <design.json> --out out
   ```
   修复所有报错；warning 酌情处理（例如"no win objective"必须修）。
4. **安装**（用户给出游戏目录时，目录须含 gamemd.exe）：
   ```
   python -m ra2forge build --design <design.json> --out out --install "<游戏目录>"
   ```
   安装 = 复制 expandmd98.mix + BATTLEMD.INI + 散装地图进游戏目录（同名文件先备份）。
5. **交付说明**（重要，机制如下）：
   - 原版尤复的"新战役"界面是**固定的盟军/苏军两个图标**，不显示自定义列表；
     工具通过覆盖 BATTLEMD.INI 把 `campaign.side` 对应的阵营入口指向战役第一关，
     胜利后经 [Basic] NextScenario 自动接续下一关。
   - 告诉用户：启动 gamemd.exe → 单人游戏 → 新战役 → **点与 campaign.side 一致的
     阵营图标**（soviet=苏军锤子图标，allied=盟军鹰图标）→ 开始第 1 关。
     点错阵营图标会黑屏（阵营错配）。
   - 卸载：删除游戏目录里的 expandmd98.mix、BATTLEMD.INI、ECH*.MAP（清单在
     ra2forge_uninstall.txt）。
   - 存档：.sav 是引擎运行时生成的二进制状态，工具无法凭空合成；玩家可在任务中
     随时用 ESC → 储存游戏 存档、用 载入游戏 读档。

## 注意

- 生成的地图是原版引擎格式（[Basic] NextScenario 关卡链 + BATTLEMD98.INI 战役注册），
  不需要 Ares/Phobos；但**最终可玩性需要用户进游戏验证**，主动请用户试玩并反馈。
- 若用户报"进游戏看不到战役/地图加载失败"，先 `python -m ra2forge inspect <map>` 检查，
  再检查设计 JSON 是否违反 DESIGN.md（国家名、目标类型、坐标越界是最常见问题）。
- 一个目录只能装一个 expandmd98.mix（会覆盖！）；不同战役放不同游戏目录或先卸载。
- MCP 备选：`D:\Project\ra2-campaign-forge\mcp\ra2forge_mcp.py` 提供
  validate_campaign / build_campaign / inspect_map 三个工具，配置见该文件头部注释。

## 已验证的引擎行为（2026-09 真机实测）

- 原版"新战役"= 固定两图标 UI；战役入口 = 覆盖 BATTLEMD.INI 的 [SOV1]/[ALL1] Scenario。
- 地图里每个 [Houses] 成员都必须有完整 house 配置节（PlayerControl/Credits/IQ/Edge/Color/
  Allies），漏写 Neutral 等会导致：玩家身份错乱（盟军侧边栏+空建造栏）、触发器全部失效、
  平民建筑渲染崩溃（except.txt: ACCESS_VIOLATION 004482FC）。工具已自动生成，勿删。
- 触发器格式与官方完全一致时可正常触发（已用"官方地图+注入触发器"对照实验证明）。
- 中立车辆用 `Mission=Sleep`（官方写法），不要用 Stop。
- objective 类型若拼错会被静默丢弃——构建输出出现 "objectives were not compiled" 警告时必须修。

## 真机实测补充（2026-10-03）

- **`except.txt` 会被每次运行整体覆盖**：`ra2youli/except.txt` 实测从 26650 B（2026-09-30 的 RC-2 现场）
  被一次新运行覆盖为 27586 B。⇒ **试玩/采样前先复制留存**，否则现场证据不可逆丢失
  （RC-2 现场另有同源副本 `out/re_work/zcode_live/gap_p21_a3/instr/except_crash_r1off_nr.txt` 才没丢）。
- **直启 vs 注入**：直接启动 `gamemd.exe`（不经 `ra2loader.exe`）时，进程模块表里**不应出现 `ra2render.dll`**。
  实测 98 个模块中命中 0。若出现，说明有注入，则"原版/补丁关闭"的对照前提不成立。
- **新发现的启动期崩溃点（第 4 处）**：从 `ra2youli` 直启时出现过
  `EXCEPTION_ACCESS_VIOLATION`，`Eip=0x00724737`，`Bytes: 8B 85 50 02 00 00`（`mov eax,[ebp+0x250]`），
  **`EBP=0`** ⇒ 访问地址恰为 `0x250`（与 `Access address:00000250` 吻合），发生在**菜单/启动阶段**。
  若玩家报"一进游戏就崩"，先查这一处（与已知 RC-1 `0x7CFC9C`/RC-2 `0x7C9B92`/RC-3 `0x5450202F` 均不同）。
- **遭遇战可自动导航**：主菜单 → 遭遇战 → 开始，可用**像素语义校验**确认
  （`red_buttons` 签名如 `[72,220,262,304,556]`、`tactical_colors` 阈值 600），实测能自动进入战斗。
- **数组 Count 口径（运行态定死）**：`Items=+0x04`、`Capacity=+0x08`、**`Count=+0x10`**、`GrowthStep=+0x14`（恒 10）。
  菜单态 Count=0；战斗态实测 Unit=11–12、Infantry=19–23、Building=**402**、TechnoArray=36–44、机动单位 30–35。
- **实际负载远小于名义**：实测机动单位仅 **30–35**（旧文档"U0800 名义 800"不成立）；
  而 `BuildingClass::Array` 达 **402** ⇒ 对象层全表扫描的放大源可能是**建筑数**而非坦克数。
