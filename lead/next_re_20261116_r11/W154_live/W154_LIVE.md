# W154 · 真机：**首次在本轮真正进局** + 实例数组的活体验证（2026-11-16）

> 用户本轮明示授权：「只读+合成输入，我自己进局」。
> 全部操作只读内存（`OpenProcess(PROCESS_VM_READ)` + `ReadProcessMemory`）+ 一次鼠标点击；
> 未注入 DLL、未 attach 调试器、未写目标进程内存、未改任何游戏文件。

## 结论摘要（5 行）

1. **进局了**：主菜单一次点击后 `mode 0→5`、`[0xA8ED84]` 由 0 起以 **31.13 帧/s** 推进，场景名 `[2]0LoadBench_U0800.yrm`。**此前所有会话都没有到过这一状态。**
2. **活体验证了三条数组口径**：`Foot = Unit+Infantry+Aircraft`（35=12+23+0）、`Techno = Unit+Infantry+Building+Aircraft`（44=12+23+9+0）、9 个 `DynamicVectorClass` 全部 `Count == 逐元素走过数`。
3. **`AbstractClass::Array` 运行期是完整注册表**：69 个对象按 vtable 逐一点名，0 个未映射；6 个类型数组的对象 **0 个缺失** ⇒ 台账 §859 的「完整性未证」**已验**。
4. **修正两处地址口径**：`UnitClass::Array` 的 `0x8B4108` 是 **vtable**（Items 在 `0x8B410C`）；子弹容器基址是 **`0xA8ED40`**（不是 `0xA8ED3C`）。
5. **0 弹基线**：60 s / 1190 样本 / bullets 恒 0 ⇒ **31.13 fps = 32.13 ms/帧**，与「0–24 发 → 32.00 ms 满帧」相容。

---

## 1. 进局的事实与界限

| 观测 | 值 | 等级 |
|---|---|---|
| 启动后（菜单） | `mode=0`、`frame=0`、可见 Win32 `Button` 数 **0** | `[已证]` |
| 一次点击后 | `mode 0→5`（同一进程内前后读数） | `[已证]` |
| 之后 60 s | `frame` 4494→6360，31.13 帧/s；`bullets` 恒 0 | `[已证]` |
| 当前场景文件 | 进程内存 `0x00A8B8E4` 处 ASCII `…[2]0LoadBench_U0800.yrm` | `[已证]` |
| 局内配置来源 | `RA2MD.INI [Skirmish] ScenIndex=166 / UnitCount=10 / Credits=10000 / GameSpeed=2` | `[已证]` |
| 画面 | 小岛地形 + 载具/步兵 + 侧边栏，`10:0x` 计时 | `[已证]`（截图 `pw_ingame.png`） |

**⚠️ 因果界限（如实登记）**：
- 我只做了「长基线（约 40 s 稳定在 mode=0/frame=0）→ 一次点击 → mode=5」的**时间序对照**，
  **没有**做「不点击是否也会进局」的对照臂 ⇒ **「点击导致进局」这一条是 `[静态推断]`，不是 `[已证]`**。
- 点击坐标按**当时的**几何读数映射（client 533×400、原点 (587,280)），而**局内**实测该窗口是
  client 910×512、原点 (398,224)、`dpi=144`（DPI-aware 视角窗口 `1366×768 @ (597,336)`）。
  ⇒ **菜单期与局内窗口几何不同**，这次点击落在哪个按钮上**我无法证明**（可能命中「單人遊戲/網絡」族的
  快速开局路径）。下一轮必须**每次动作前重测几何**，并做单变量对照。

## 2. 三处活体口径验证（本轮硬结论）

采样瞬间（同一帧内读出，全部 `[已证]`）：

| 数组 | base | Items | Cap | Count | 逐元素走过 |
|---|---|---:|---:|---:|---:|
| `AbstractClass::Array` | `0x00B0F720` | `0x15D1F650` | 80 | **69** | 69 |
| `FootClass::Array` | `0x008B3DC0` | `0x15BF7430` | 40 | **35** | 35 |
| `UnitClass::Array` | **`0x008B4108`** | **`0x008B410C`** | 20 | **12** | 12 |
| `InfantryClass::Array` | `0x00A83DE8` | `0x15BF6260` | 30 | **23** | 23 |
| `AircraftClass::Array` | `0x00A8E390` | `0x15BF5D00` | 10 | **0** | 0 |
| `BuildingClass::Array` | `0x00A8EB40` | `0x156BB030` | 10 | **9** | 9 |
| `TechnoClass::Array` | `0x00A8EC78` | `0x15BF6060` | 50 | **44** | 44 |
| `BulletClass::Array` | **`0x00A8ED40`** | `0` | 0 | **0** | 0 |
| `AnimClass::Array` | `0x00A8E9A8` | `0x15BF9F20` | 20 | **17** | 17 |

- **容器布局（字节级，9/9 一致）**：`DynamicVectorClass` 共 **0x18 B**；`+0` vtable / `+4` Items /
  `+8` Capacity / `+0xC` 两字节 `01 01`（IsInitialized/IsAllocated）/ `+0x10` **Count** / `+0x14` Incr（=10）。
  原始 dword 证据（`probe6_dump.py`）：`B0F720: 007E91EC 15BFB9C0 00000046 00000101 0000003D 0000000A`。
- **两处台账口径修正**（`[已证]`）：
  1. `0x008B4108` 是 `UnitClass::Array` 的 **vtable**，不是 Items；Items = `0x008B410C`，
     Capacity = `0x008B4110`，Count = `0x008B4118`（Count 那条原本就对）。
  2. 子弹容器基址 = **`0xA8ED40`**（vtable 处），台账/底座写的 `0xA8ED3C` 偏 4 字节；
     `Count = 0xA8ED50` 原本就对（`A8ED3C` 处那个 `0x0A` 是**前一个变量**的尾字）。
- **加法口径（`[已证]`）**：`Foot = Unit + Infantry + Aircraft` = 35 = 12+23+0；
  `Techno = Unit + Infantry + Building + Aircraft` = 44 = 12+23+9+0。

## 3. `AbstractClass::Array` 的完整性——**已验**（台账 §859 的未证项）

按对象 `+0` 的 vtable 反查 `W130_atlas\vtables_canonical.json` 得到类名（**69/69 全部命中，0 个未映射**）：

| 类 | 个数 |
|---|---:|
| `InfantryClass` | 23 |
| `AnimClass` | 17 |
| `UnitClass` | 12 |
| `BuildingClass` | 9 |
| `HouseClass` | 4 |
| `ParticleSystemClass` | 2 |
| `TeamClass` | 1 |
| `FactoryClass` | 1 |
| **合计** | **69** |

- **成员归属检验**：`FootClass`(35)、`UnitClass`(12)、`InfantryClass`(23)、`BuildingClass`(9)、
  `TechnoClass`(44)、`AnimClass`(17) 数组里的对象**全部**能在 `AbstractClass::Array` 里找到，
  **missing = 0（6/6 数组）**。
- ⇒ **运行期 `AbstractClass::Array` 是覆盖全部游戏对象的完整注册表**，且它同时收纳
  **非 ObjectClass 派生的抽象对象**（House / Team / Factory / ParticleSystem）。
- ⚠️ **与 §868 不矛盾**：§868 证的是「`FootClass` 构造器**自己不登记**、对 `0xB0F720` 0 引用」，
  登记发生在基类构造器（§877 的 `0x00410170`）。**"某个子类构造器不登记"推不出"表不完整"**——
  这正是本轮用一条真机读数关掉的推理跳跃。
- 限制：**单次读数、单场景**（U0800 图 / 33 个可见作战对象）。跨场景/高负载下是否仍 0 缺失**未验**。

## 4. 0 弹基线（对 ① 的相容性）

- 60 s、1190 个样本（50 ms 采样）、1,190 条 NDJSON：`EVIDENCE\ingame_run1.ndjson`。
- `bullets`(=`[0xA8ED50]`) **恒 0**；`frame` 每 50 ms 增 0/1/2/3；最大帧间隔 **0.056 s**。
- 平均 **31.13 帧/s ⇒ 32.13 ms/帧**，与台账「0–24 发 → 32.00 ms（1.00×满帧）」的行星**相容**。
- `mode` 全程恒 5 ⇒ **`[0xA8B238]=5 对应"局内"**、`=0` 对应主菜单（这条对照是本轮新增的 `[已证]`）。

## 5. 工具（可复跑）

| 脚本 | 用途 |
|---|---|
| `w146_nav.py` | 不重启游戏地驱动已运行实例：`--state` / `--list` / `--click LX LY` / `--click-ctrl ID` / `--key VK`，含 ClientToScreen 映射 |
| `probe1.py` | 顶层窗口族 + 计数器时间序列 |
| `probe2.py` | 精确几何（含 `GetDpiForWindow`）、子窗口树、全局量一览 |
| `probe3.py` + `probe4_measure.py` | 内存串扫描（`VirtualQueryEx` 枚举）／50 ms 计数器采样 |
| `probe5_arrays.py` | 9 个实例数组的布局、Count 与逐元素、vtable 点名、成员归属 |
| `probe6_dump.py` | 原始 dword 转储（布局证据） |
| `cap2.ps1` | `PrintWindow(PW_RENDERFULLCONTENT)` 抓图（**CopyFromScreen 会抓到覆盖窗口**，教训） |

## 6. 卫生（`[已证]`）

| 项 | 结果 |
|---|---|
| `gamemd.exe` SHA-256 | `73201CC0…CF67476` **未变** |
| `ddraw.dll` SHA-256 | `85E0F7D5…B03A9` **未变** |
| `expandmd01.mix` | 4,813,968 B **未变** |
| `except.txt` | 26,794 B / mtime **未变** ⇒ **全程零新崩溃** |
| 残留进程 | 无 |
| 唯一被写的文件 | `RA2MD.INI`（游戏自身持久化 `[Skirmish]` 设置，属正常行为） |

## 7. 未证 / 下一步

1. **「点击 → 进局」的因果**：需「不点击」对照臂 + 单变量（点哪个控件）。
2. **菜单期与局内窗口几何不同**：必须每次动作前用 DPI-aware 读数重测（本轮两种读数各自都对，
   **混用就错**）——这很可能就是 §884–§886 反复失败的真因。
3. **W150 的静态判据与本轮的真机对照**：`mode 0=菜单 / 5=局内` 已证；其余取值与"暂停/记分板"未验。
4. **高负载与战斗**：本轮 33 个作战对象、0 子弹；子弹-帧时间关系**未在本次重测**（前 45–71 趟数据由 W153 复核）。
