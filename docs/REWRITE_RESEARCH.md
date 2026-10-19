# RA2 / 尤复：底层现代化 调研报告

> 调研时间：2026-09-25　调研者：ZCode（在 `D:\Project\ra2-campaign-forge` 会话内完成）
> 本报告只写**证据**，不写愿望。标注「实测」的数据都是本次调研在本机二进制/运行时上量出来的，
> 可复现；标注「公开」的来自各项目仓库元数据。规划见 [REWRITE_ROADMAP.md](REWRITE_ROADMAP.md)。

---

## 0. 摘要（三条结论）

1. **目标系统的可恢复信息量异常好，而且已经落地成工具与数据**：`gamemd.exe` 里有
   **988 个 C++ RTTI 类型描述符**，其中 **954 个已解析出 vtable 地址与完整继承链**
   （`ra2re rtti`，18 项自检全过）。这意味着类继承图、vtable、虚函数地址表已经**程序化恢复**——
   拿到的是"带类名和虚函数表的骨架"，不是一坨裸机器码。这决定了逆向路线从"考古"降级为"工程"。
2. **"多单位卡顿"的主因不是单线程，而是"渲染被逻辑节拍绑死 + 纯软件 blit"**：
   实测导入表里**没有 D3D、没有 OpenGL**，只有 `DDRAW.dll`；逻辑节拍只有 15Hz（每 tick 66ms 预算）。
   所以第一杠杆是**渲染解耦 + GPU 化**，而不是多线程重写模拟。
3. **"保玩法/UI/数据契约，只换实现"这个定义是可行的，且收益集中在契约之外**：
   渲染层与数据布局属于实现（改了不算改游戏），模拟层与触发器属于契约（改了就是另一个游戏）。
   **约 80% 的性能收益在契约之外，这是"最小改动最大收益"的根据。**

---

## 1. 目标系统：逆向友好度（全部实测）

### 1.1 `gamemd.exe` 二进制画像

| 项 | 实测值 | 对逆向的意义 |
|---|---|---|
| 文件大小 | 4,825,360 字节（4.60 MB） | — |
| 格式 | PE32（32 位），ImageBase `0x400000` | 需要 32 位工具链；有 2GB/4GB 天花板 |
| 时间戳 | 2001-10-31 | 官方 1.001 |
| 节表 | `.text .rdata .data .rsrc .detour`（5 节） | `.detour` = 第三方 Detours 补丁痕迹 |
| `.text` | VA `0x1000`，VS `0x3DF38D`，RAW `0x1000`，RS `0x3E0000`（4,063,232 字节 / 3.88 MB） | 代码量约 10–15 万行 C++ 量级 |
| `.text` SHA-256 | `c0368a17…14eb738` | 我用作**引擎指纹**（不含 PE 头，打补丁后仍可识别版本） |
| 整文件 SHA-256 | `db264305…e015255aa` | 原始版本记录 |
| DllCharacteristics | 原始 `0x0000` → 现 `0x0020`（LAA 已由 ra2opt 打开） | 原版**没有** 4GB 寻址 |
| CheckSum | `0`（未填） | 改 PE 头不需要重算校验和 |
| PDB 路径 | **无** | 2001 零售 exe 常态，无源码级调试信息 |

### 1.2 C++ RTTI：最大的一笔免费资产

实测扫描结果（`ra2re rtti`）：

```
装饰名（.?AV / .?AU / .?AW）  988 个 → 全部通过 TypeDescriptor 校验（0 个被拒）
拿到 CompleteObjectLocator      954
拿到 vtable 地址                954
拿到完整基类链（>1 层）         698
```

> **修正记录**：本报告初稿写的是"307 个类名"，那是我的正则 `[^\x00@]{1,64}` 把名字里
> 含 `@` 的类型（模板/嵌套类）漏掉了，属**低估**。修正后为 988 个类型描述符。

判定布局时用的不是记忆而是**自洽性检验**——对每个名字试 8/12/16 字节三种头部宽度，
看哪种能让绝大多数描述符共享同一个 `type_info` vtable：

| 头部宽度 | 有效描述符 | 共享 type_info vtable 占比 | 不同值 |
|---|---|---|---|
| **8 字节** | **988** | **100.0%** | **1** ← 自洽，选中 |
| 12 字节 | 125 | 41.6% | 29 |
| 16 字节 | 105 | 43.8% | 35 |

结论：该 exe 用 **8 字节 TypeDescriptor 头**（`[pVFTable][spare][name]`），
`type_info` vftable 位于 **VA `0x007F9594`**（`.rdata`），指针字段是**绝对地址**（VC6 方案）。

样本（按字母序前 24 个）：

```
AITriggerTypeClass, AbstractClass, AbstractTypeClass, AddTeamCommandClass,
AircraftClass, AircraftTypeClass, AirstrikeClass, AllToCheerCommandClass,
AllianceCommandClass, AlphaShapeClass, AnimClass, AnimFile, AnimTypeClass,
Animate, ApplicationClass, BSurface, Base64Pipe, Base64Straw, BaseClass,
BeaconPlacementCommandClass, BinkMovieHandle, BitFont, BitText, Blitter
```

**为什么这决定了可行性**：MSVC 的 RTTI 结构里带有基类指针，而每个多态类的 vtable
第 `-1` 槽指回自己的 `CompleteObjectLocator`。于是可以**程序化**恢复：

1. **完整类继承图**——已恢复 698 条完整链，且与公开已知层次逐字一致：
   ```
   UnitClass     → FootClass → TechnoClass → RadioClass → MissionClass → ObjectClass → AbstractClass
   BuildingClass → TechnoClass → RadioClass → MissionClass → ObjectClass → AbstractClass
   AnimClass     → ObjectClass → AbstractClass
   BSurface      → XSurface → Surface
   ```
2. **每个类的 vtable 地址** → 虚函数地址列表（例：`TechnoClass` vtable `0x007F4960`，
   309 个槽；`FootClass` `0x007E8C94`，341 个）
3. **跨类比对 vtable** → 哪些槽位是 override

**独立验证**（`python -m ra2re selftest`，18 项全过）中有一条与 RA2 无关的硬约束：
**所有父子对的 vtable 长度必须单调不减**（C++ 语义）。954 个类全部满足——
这比"看着像"强得多。

### 1.3 源码模块锚点

从字符串里恢复出 **38 个 `.cpp` 文件名 + 4 个 `.h`**，例如：

```
AbsType.cpp  CampScor.cpp  Dropship.cpp  GDlgSupp.cpp  Init.cpp  Ion.cpp
LdPrgMgr.cpp  MPCoop.cpp  MPObserver.cpp  MPScore.cpp  MPSiege.cpp  MPSiegeTeam.cpp
```

这些来自 `__FILE__`（断言/日志）。数量不多，但它们是**地区锚点**：能把二进制里某些区域
映射回源模块（例如 `Dropship.cpp` 对应空投/伞兵逻辑）。

### 1.4 导入表：渲染与依赖的硬证据

**只有 16 个 DLL**：

```
ADVAPI32  COMCTL32  DDRAW  DSOUND  GDI32  IMM32  KERNEL32  OLEAUT32
SHELL32   USER32    VERSION  WINMM  WSOCK32  binkw32  ole32  xyr.dll
```

三条关键推论：

- **没有 `D3D9.dll` / `d3d8.dll` / `opengl32.dll`** → 渲染**完全**是 DirectDraw + CPU 软件 blit。
  这是"卡顿"的第一病因，也是最大的可优化空间。
- **没有 CRT DLL**（无 `msvcrt.dll`）→ CRT 静态链接，除了这 16 个 DLL 的导入符号外
  **没有现成符号可借**，函数边界只能靠 RTTI/vtable 与手工标注。
- **`xyr.dll` 是第三方文件**，加上 `.detour` 段 → 这份 exe 被整合包改过。
  **做 oracle 必须另备一份干净的零售 1.001**（EA 官方渠道可购），否则会把补丁行为当成原版行为。

---

## 2. 数据层：契约的边界在哪里（实测）

### 2.1 内容规模

| 文件 | 实测大小 |
|---|---|
| `ra2.mix` | 281,888,480 字节（269 MB） |
| `langmd.mix` | 84,643,206 字节（81 MB） |
| `theme.mix` | 76,862,662 字节（73 MB） |
| `language.mix` | 52,913,656 字节（50 MB） |
| `multimd.mix` | 31,264,268 字节（30 MB） |

规则类 INI 的规模（从官方 MIX 内提取实测）：单份文件 **500–1582 个 section**；
`artmd.ini` 336,535 字节；另一份规则文件 471,258 字节 / 306 section；官方任务图内嵌
132–163 section；含触发器的地图 629 section。

### 2.2 "契约"与"实现"的划分（本报告最重要的一张表）

| 层 | 属于 | 改动的后果 | 可复用性 |
|---|---|---|---|
| `.MIX` 资产（SHP/VXL/PAL/CSF/AUD） | **契约** | — | **直接复用** |
| `rulesmd.ini` / `artmd.ini` / `aimd.ini` | **契约** | 改了就变平衡 | **直接复用** |
| `.MAP` 地图 + 触发器语义 | **契约** | 改了就变玩法 | **直接复用** |
| UI 布局与美术（侧边栏/cameo/图标） | **契约（呈现）** | — | **直接复用**（美术是现成位图） |
| 存档 / 回放 / 联机同步 | **契约** | 破坏兼容 | 需重新实现，但语义明确 |
| **渲染管线（blit → 呈现）** | **实现** | 画面像素可以做到一致 | 应替换 |
| **数据布局 / 空间索引 / 寻路实现** | **实现** | 行为可对拍 | 应替换 |
| **内存模型 / 位宽（32→64 位）** | **实现** | 无行为影响 | 应替换 |
| **线程模型** | **实现** | 仅在并行顺序敏感处影响行为 | 最后再动 |

**结论**：性能与稳定性的收益绝大部分落在"实现"行里，而"实现"行可以替换而不触碰契约。
这就是"最小改动最大收益"的结构性依据。

---

## 3. 卡顿与闪退的机理（基于实测推导）

### 3.1 逻辑节拍与渲染绑死

原版逻辑节拍 **15 Hz → 每 tick 66 ms 预算**。渲染与逻辑节拍 1:1 绑定，且渲染是自己的软件 blit。

**实测修正（采样剖析，500 Hz × 60 s × 3 个场景）**：

| 场景 | 进程占用 | 空闲占比 | blit 族占忙时 | 单体最大热点 |
|---|---|---|---|---|
| 遭遇战开局（10 起始单位） | 0.24 个核 | 82.6% | 11.55% | `BlitTransXlatAlphaZRead@G` 7.82% |
| 同一局稍后 | 0.23 个核 | 81.5% | 12.08% | 同上 6.74% |
| 冷酷(Brutal) AI 对局数分钟后 | **0.21 个核** | **84.7%** | **16.55%** | 同上 **15.64%** |

**结论有两面，必须一起说**：

- ✅ **渲染确实是最大的单一热点群**：blit 族 + `DisplayClass` + `LayerClass` + `DSurface`
  合计约 **19–20% 忙时**；且随场面复杂度上升（11.6% → 16.6%）。
  其中 `?$BlitTransXlatAlphaZRead@G::v1`（透明 + 阵营色 + alpha + 深度 = 单位绘制主路径）
  在复杂场景下独占 15.64%，是第二名的两倍多。
- ❌ **但在正常对局里游戏远未满载**：只占 0.21–0.24 个核，**4–5 倍 CPU 余量**，
  空闲 81–85%。也就是说"渲染拖垮 tick"这个机制在**这些单位量级上并不成立**。

**本报告初稿只依据导入表推断"渲染绑死是病根"，实测把这个判断收紧了**：
机制方向对（blit 是最大热点群、且随物件增长），但触发阈值比初稿暗示的高得多——
要让 66 ms 预算真的被吃掉，需要在当前基础上再翻 4–5 倍工作量，即
**"多单位"指的是数百个单位，而不是几十个**。

这也解释了为什么 `cnc-ddraw` 的帧率/呈现侧调优（`ra2opt` 那一层）能改善观感却治不了根：
观感来自 15 Hz 的节拍本身与呈现路径，而 CPU 侧的堵塞门槛很高。

详见 `out/reverse/perf-profile.md`（含三次采样的完整对照、未归因热点地址桶、局限说明）。

### 3.2 其它已知结构性负担

- **无空间索引**：多个系统每 tick 对全域物件做 O(n) 扫描（AI/属性重算/渲染排序）。
- **32 位地址空间**：2 GB 硬顶（本次调研已用 ra2opt 打开 LAA，抬到 4 GB，实测生效），
  但**只有换成 64 位才能真正消除**——这是"重写底层"独有的、与性能无关的稳定性收益。
- **软件 blit 的每帧像素量**：视口越大 → 可见精灵越多 → blit 越多。所以分辨率是性能杠杆
  （这也是"高分辨率反而更卡"的原因）。

### 3.3 可定位的渲染接管点（已落地为清单）

RTTI 里 `Blitter` 是抽象基类（vtable `0x007E5B88`，5 个槽中 4 个是 `_purecall`（地址
`0x004C9150`）占位），它下面挂着 **57 个具体 blit 实现**，模板名把语义编码得很清楚：

```
?$BlitPlain@G               007F7BC4   007BC660 007BC7F0 007BC840 007BC820 007BC870
?$BlitTrans@G               007F7BF4   007BC6A0 007BC890 007BC8F0 007BC8C0 007BC920
?$BlitPlainXlat@G           007E5A38   00499F20 004924C0 00492530 00492500 00492560
?$BlitTransDarken@G         007E59F0   00499F60 00492670 004926E0 004926B0 00492710
?$BlitTransLucent25@G       007E59A8   00499FC0 00492920 004929B0 00492980 004929E0
?$BlitPlainXlatZReadWrite@G 007E58A0   0049A120 00493500 004935A0 00493570 004935D0
```

关键结论（`out/reverse/m1_blit_targets.txt` 是完整清单）：

- **57 个实现里 50 个是 16 位 RGB（`@G`）**，7 个是 8 位调色板（`@E`）
  → RA2 确实是 16 位色渲染，`@G` 那一批才是热点。
- **57 个模板名已全部解码**，语义词汇表（可组合）：
  `Plain`（不透明）/ `Trans`（跳色键）/ `Xlat`（阵营颜色重映射）/ `Darken`（阴影）/
  `Lucent25|50|75` + `Alpha`（半透明混合）/ `ZRead`·`ZReadWrite`（深度缓冲）/
  `ZRemap`（深度重映射）/ `Warp`（超时空扭曲）/ `WriteAlpha`·`MultWriteAlpha`（alpha 写回）/
  `Dest`（目标混合）/ `Remap`。
- 地址高度集中：`Plain`/`Trans` 落在 **`0x007BC6xx`** 一簇，`Xlat`/`Darken`/`Lucent`/`ZRead`
  落在 **`0x004924xx`–`0x004935xx`** 一簇。**这两个区段就是性能测量的靶子，
  也是 L1 拦截/替换的落点。**

据此，§3.3 原先只是"理论可行"的渲染接管路线，现在是**有地址清单可执行**的：
拦 `0x007BC6xx` 簇（最常见的 Plain/Trans）即可覆盖绝大多数精灵绘制。

---

## 4. 先例与竞品实测对照

### 4.1 形态先例（保资产、保契约、换引擎）

| 项目 | 形态 | 参考价值 |
|---|---|---|
| **OpenTTD**（运输大亨） | 读原版资产与数据，引擎全换 | 证明"保契约换引擎"可长期维护 |
| **OpenRCT2**（过山车大亨2） | 同上，且**能加载原版存档** | 存档兼容是可行目标 |
| **DevilutionX**（暗黑1） | 源码泄露后成为移植 | 对照：有源码的成本远低于纯 RE |
| **OpenMW**（晨风） | 干净重实现，15 年级投入 | 纯 RE 的时间尺度参照 |

### 4.2 RA2 直接竞品（元数据实测，2026-09-25）

| 项目 | 语言/许可 | 体量（实测） | 状态 | 可抄什么 |
|---|---|---|---|---|
| `OpenRA/OpenRA` | C# / GPL-3.0 | 351 MB，17,433★，1,598 未闭 issue | 2010 至今 | 引擎层成熟度的天花板；其内容层不是你的目标 |
| `OpenRA/ra2` | C# / GPL-3.0 | **1,162 提交 / 33 人**，2015-12→2025-11 | **无战役**（`mods/ra2` 下无 missions，仅 27 张遭遇战图） | `ImportRA2MapCommand`（原版地图导入）、installer yaml（素材定位） |
| `Romanovs-Vengeance` | C# / GPL-3.0 | 28 人（1 人 3,282 提交），2018→2025-07 | 联机可用，自定义战役几乎没动 | 平衡与联机的调法 |
| `cookgreen/Yuris-Revenge` | C# / GPL-3.0 | 8 人，2018→2024-11 | 钉在旧引擎版本 | 尤复方向的尝试 |
| **`YuriPlanet/vera20k`** | Rust / GPL-3.0 | **3,530 提交 / 6 个月 / 2 人（1 人主导）**，仍活跃 | pre-alpha：遭遇战可玩 + **占位 AI** | **方法论**（见 §4.3）；**不要**抄它的进度预期 |
| `cookgreen/ChronoStorm` | Python+Pygame / MIT | **82 KB / 21 提交 / 1 人**，停更 5 个月 | 路线图 Phase 1 打了勾但体量不支持 | 阶段划分的思路；**反例**：Python 做运行时不可行 |
| `harshilmathur/openra2`（Vanguard） | TypeScript / GPL-3.0 | 169 提交，**活跃 4 天后停更 2 个月** | 双资产模式（自带 AI 生成素材） | **"双资产模式"**是版权问题的正解 |
| `SolidFaker/RA2R` | C / MIT | 62 提交，**建库 1–2 天** | README 像成品，代码是雏形 | 文档组织（formats/PLAN/REFERENCE/DEBUGGING） |
| `Fincer/openra-tibsunra2`、`Icenowy/oramod-yr` | Shell / — | — | 均已死（2018 / 2016） | 反面样本 |

### 4.3 `vera20k` 的方法论（本次调研最有价值的单点发现）

其 README 原文：

> The original `gamemd.exe` is the reference. Newer gameplay code **cites the original function
> it was ported from**, and **native harnesses run the original code to check the Rust results**.
> Most code is written by AI coding assistants that the maintainer directs, following the rules in
> `AGENTS.md`.

这解决了逆向重写最致命的死结——**"像不像"没有裁判**。做法是把原版当 **oracle**：
写原生 harness **直接调用 gamemd 里的函数**，用同样输入比对输出，把"手感"变成"可回归测试"。

同一份 README 的 Status 表（原文），是**AI 主导 6 个月**的现实边界：

| Works | Partial | **Not yet** |
|---|---|---|
| 零售/随机地图、原版菜单与侧边栏、建造电力科技树出售维修、战争/超时空/奴隶矿车、陆海空与防御战斗、警犬与恐怖机器人、驻防运输工程师隐形、闪电风暴与铁幕、存读档 | 飞机攻击航线、航母舰载机、心灵控制、箱子、死亡特效 | **联机（有 lockstep 无网络）**、**原版 AI（占位）**、**战役与大多数地图触发器**、超时空军团兵/疯狂伊文/磁电坦克等、光棱折射/磁暴充能/盖特转管、核弹/超时空传送仪/心灵控制器/侦察机、影片、30 人 2 万单位 |

**注意"Not yet"里的第二、三项**：`战役与大多数地图触发器` 与 `原版 AI`——
这恰好是 `ra2forge` 的产出形态，也是所有重写项目的共同盲区。

### 4.4 `OpenRA/ra2` 实机实测结论（本机跑过）

**能跑的部分**（本机实测）：

- 用**本机中文版尤复安装的 `ra2.mix` / `language.mix` / `theme.mix` 直接加载成功**
  （哈希校验一致），27 张官方地图、3 个剧场全部通过 `--check-yaml`
- 遭遇战完整链路可用：基地车展开 → 建造厂 → 发电厂 → 兵营（带 `00:08` 倒计时）→ 9 个建筑
  cameo 可造；**数值与原版一致**（矿石精炼厂 $2000、耗电 -50）；世界加载 702 ms
- 建造图标上的中文来自安装包内**烤进位图的 cameo 美术**——OpenRA 原样读出

**缺的部分**：单人菜单 `Missions` **灰掉**（无战役）；对手是引擎通用 AI `Test AI`；
主菜单标题是 `OpenRA`、按钮用引擎默认 chrome；加载提示是引擎自带冷笑话；迷雾揭开形状与原版不同。

**顺带定位到一个上游 bug（可复现、根因已确认）**：

- 28 张官方图里 2 张（`the-alamo`、`wild-animal-park`）一进即崩：
  `ArgumentException: This frozen actor has no footprint`，actor `cafncp` @ `27,-27`
- 实测崩溃与地图 **100% 相关**：The Alamo 2/2 崩、Dustbowl 2/2 正常（连续运行 5 分钟以上零异常）
- 根因链（读引擎源码确认）：
  1. 地图 `map.yaml` 里有 **233 个坐标为负的 actor**（如 `Location: 27,-27`），位于地图外
  2. `BuildingInfo.FrozenUnderFogTiles(loc)`（`Building.cs:117`）把 1 格 footprint 加到越界坐标上
  3. `map.ProjectedCellsCovering(c.ToMPos(map))`（`Map.cs:1028`）对不在 `cellProjection` 里的格子
     返回 `NoProjectedCells`（**空数组**）
  4. `FrozenActor..ctor`（`FrozenActorLayer.cs:99`）发现 `Footprint.Length == 0` → 抛异常 → 地图加载致命失败
- 性质：**引擎健壮性缺陷 + 导入原版地图的数据**共同触发。修法有两条
  （引擎侧容忍空 footprint；或导入/加载时丢弃越界 actor），属可提交上游的明确 bug

---

## 5. 已有资产盘点（本仓库已在手的东西）

### 5.1 `ra2forge`：数据层已经做了一半

| 能力 | 验证状态 |
|---|---|
| MIX 读写（含官方加密头：Westwood RSA 公钥推导 blowfish 密钥） | 已解密本机 7 个官方 MIX 并提取文件 |
| LZO1X-1（IsoMapPack5）、Format80（OverlayPack） | 30+50 组随机往返 + 官方地图真数据比对通过 |
| 地图构建（菱形坐标、11 字节地形记录、触发器/队伍全节输出） | 与官方地图逐节比对一致 |
| 触发器生成、BATTLEMD98.INI 战役注册、expandmd98.mix 打包 | 已安装并在游戏内可见 |
| 设计 JSON 校验、命令行、MCP 三个工具 | 已有 |

> 【W3 勘误 · Forge P-5 / P-7 编解码实测注】改前：30+50 组随机往返 + 官方地图真数据比对通过；改后：
> 1. Format80 50/50 通过，但官方 OverlayPack 载荷采用 Format5 分包（`[u16 comp][u16 raw]`），`maplib` 现为单条无框流，直喂官方载荷会 IndexError；
> 2. LZO 单块路径 ≤49152 B 及 8192 分块全通过，但单次调用 >49152 B 时 12/16 失败（最小复现 65,537 B、首错偏移 49,153，因 dict_ 相对下标与绝对下标混用）；
> 3. 官方 12 张地图 IsoMapPack5 解码重编再解逐字节一致，但不含压缩流逐字节相同；
> 4. `extracted/all_inis/*.ini` 落地件首行被提取工具写坏，不得用作官方还原模板；依据：`out/re_work/qc/W2_20261001/forge/PATCH_SUGGESTIONS.md` P-5, C-1, C-2；分级：[实证]

**意义**：这类重写项目"阶段一（资产管线）"的内容，本仓库已具备相当部分。

### 5.2 `ra2opt`：稳定性层的实测结果

| 项 | 结果 |
|---|---|
| 自检 | **36 项全过**（越界写盘拒绝、PE 补丁后代码段字节不变、INI 注释/顺序/GBK/CRLF/BOM 往返、备份→回滚字节级、apply 幂等、战役产物零改动） |
| 已应用于真实安装 | cnc-ddraw **4.4.7 → 7.1.0**、`gamemd.exe`/`Ra2md.exe`/`Ra2.exe` **LAA 开 + 栈 4MB**、`DetailLevel` 2→1、清理有害兼容性标记、生成高优先级启动器 |
| 体检 | **0 严重 / 0 警告**（应用前为 4 警告 8 建议） |
| 回滚 | `restore` 后与原始安装**逐字节相同**（7 个文件 + 注册表标记），已验证 |
| 启动冒烟测试 | 改动后启动 `gamemd.exe` 存活 8 秒未退出；重复验证 3 次 |

附带产出：`ra2opt budget` 能量化"同屏物件预算"，实测示例战役三关峰值仅 18–28 个物件。

### 5.3 `ra2re`：逆向工具与已恢复的符号数据（本次新建）

| 项 | 状态 |
|---|---|
| `python -m ra2re rtti` | 解析 MSVC RTTI → 类继承图 + vtable + 虚函数地址 |
| `python -m ra2re selftest` | **18 项全过**（布局自洽性 + 8 条已知类层次 + 全类 vtable 单调性 + 确定性） |
| `out/reverse/symbols.json` | 531 KB：**988 个类**的 name / type_descriptor / COL / vtable / 每个虚函数地址 / 完整基类链 |
| `out/reverse/hierarchy.txt` | 继承树（人看） |
| `out/reverse/m1_blit_targets.txt` | **M1 接管点清单**：57 个软件 blit 实现 + 位深 + 语义 + 5 个虚函数地址 |

工具设计上的一条经验：**不靠记忆猜二进制布局**。脚本对 TypeDescriptor 头部宽度试 8/12/16
三种假设，用"哪种能让全部描述符共享同一个 `type_info` vtable"来选——初始版本因为一个
RVA/VA 混淆（`off2rva()` 返回的是 RVA 却被当 VA 用）导致三种假设全部不自洽，
**是自洽性检验把错误暴露出来的**，而不是等到下游产出垃圾才发现。

---

## 6. 结论

| 问题 | 结论 | 依据 |
|---|---|---|
| 逆向是否可行？ | **可行**，且属于"友好"的一类 | **988 个 RTTI 描述符 / 954 个 vtable / 698 条完整继承链**（§1.2）+ 38 个源文件锚点（§1.3） |
| 目标该定义成什么？ | **读原版资产与 INI，保玩法/UI/契约，只换实现** | §2.2 的契约/实现划分 |
| 卡顿的正解是什么？ | **渲染解耦 + GPU 化 + 数据布局现代化**；多线程最后 | 实测无 D3D/GL 导入、15Hz/66ms 预算（§1.4、§3.1） |
| 花多大力气？ | 见 ROADMAP 的 ROI 阶梯；**先测量再动手** | §3 的机理需要现场量化才能定 L1 还是 L3 |
| 最大的风险？ | **等价性验收**，不是写代码 | §4.3：`vera20k` 6 个月 AI 主导后 AI/触发器仍在 Not yet |
| 有没有现成裁判？ | **有**：把原版当 oracle，native harness 对拍 | §4.3 的方法论（已被验证可行） |
| 第一优先工程动作的落点找到了吗？ | **找到了**：`0x007BC6xx` 与 `0x004924xx–0x004935xx` 两簇软件 blit | §3.3 的 57 个 blit 实现清单 |

**一句话**：这条路走得通的关键不在"能不能重写"，而在**能不能把改动全部压在"实现"层、
不碰"契约"层**——而 `ra2opt` 已经实测证明，光是不碰契约的那些改动就已经能把体检从
「4 警告 / 8 建议」清到「0 严重 / 0 警告」。
