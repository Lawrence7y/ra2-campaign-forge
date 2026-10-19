# HouseClass / TeamClass / AITrigger 每帧更新循环逆向

> 逆向对象：`gamemd.exe` 1.001（尤里的复仇），ImageBase=`0x400000`，文件偏移 = VA − `0x400000`
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> 目标：找出高密度局下**除寻敌外**的 AI 成本中心，供时间片 / 空间索引优化。
> 配套产物：`out/re_work/house_team_ai/`（`fn_*.txt` / `window_*.txt` / `house_team_ai_re*.py`）。
> 已有前置：`docs/re/targeting_spatial.md`（SelectAutoTarget + Greatest_Threat）、`docs/re/pathfinding_locomotion.md`（Dijkstra）。

---

## 0. 结论速览

| 问题 | 答案 |
| :--- | :--- |
| 每帧谁遍历 House 列表？ | **没有单一"全 House 循环"**。`HouseClass::Update`（`0x004F8440`，v[23]）由主循环按虚表逐 House 调用；内部自带 8 帧 / 100 帧 / Timer 三层限频。 |
| 每帧谁遍历 Team 列表？ | `TeamTypeClass::ProcessAllTaskforces`（`0x006F2040`）由场景更新 `0x00686B20` 调用，按 **TeamType** 遍历；单个 Team 的脚本步进在 `0x006E9050`（O(脚本行)）。 |
| 每帧谁遍历 AITrigger 列表？ | **不是每帧**。`0x006F0AB0`（AITrigger 评估宿主）由 `HouseClass::Update` 里的 **TeamDelayTimer**（`this+0x5798/0x57A0`）门控；另有 Team 析构 `0x006E8DE0` 反向扫全 AITrigger 做权重回写。 |
| House 决策是否 O(建筑)×O(单位)？ | **否**。生产/重建是 O(可造类型)；防御/经济扫描走 CounterClass 计数器（O(1) 查询）。真正的 O(N) 在 **8 帧一轮的建筑向量遍历**（`0x004F8F9C`）与 **TeamType 全表扫描**（招募三兄弟 `0x004FEA60/0x004FEEE0/0x004FF210`）。 |
| Team 成员扫描代价？ | `TeamClass::LiberateMember`（`0x006EA870`）39 个调用点；Team 析构时 `FirstUnit` 链循环释放。成员数 ≤ TaskForce 上限（通常 ≤ 5），**代价低**。 |
| AITrigger 权重更新频率？ | **仅在 Team 死亡/完成时**（`0x006E8DE0` → `RegisterSuccess 0x0041FD60` / `RegisterFailure 0x0041FE20`）。非每帧。 |
| AI 逻辑是否也扫全图？ | **否**。House/Team 层不碰 `Greatest_Threat`。全图扫描只在单位级 `SelectAutoTarget`/`Greatest_Threat`（见 `targeting_spatial.md`）。AI 只做列表/计数器扫描。 |
| 最大非寻敌成本中心？ | ① AITrigger 评估 `0x006F0AB0`（O(Team×Trigger)）；② 招募三兄弟（O(TeamType×可造类型)）；③ 8 帧建筑向量回调 `0x006E53A0`；④ Team 析构 O(AITrigger)。 |

---

## 1. 每帧 AI 调用树

```
主逻辑帧
├─ 场景/全局更新 0x00686B20（size 0x11C0，115 call）
│    ├─ TeamTypeClass::ProcessAllTaskforces 0x006F2040
│    │    └─ 按 TeamTypeArray(0xA8ECA0) 遍历 → ProcessTaskForce 0x006F1FA0
│    └─ （其余为地图/触发器/存档同步，不在本文范围）
│
├─ HouseClass::Update 0x004F8440  ← v[23]，逐 House 虚调用（无直呼）
│    │
│    ├─ [Timer 门控] RepairTimer 一带 (+0x2A4/+0x2AC, +0x2B0/+0x2B8)
│    │    └─ 到期重置 + 置脏标志 +0x5778/+0x5779
│    │
│    ├─ UpdatePower 0x00508C30          （仅 +0x5778 置位时）
│    ├─ 0x00508DF0 / 0x00508F60         （仅 +0x5779 置位时，电力/雷达重算）
│    │
│    ├─ [每 100 帧] CurrentFrame % 100 == 0
│    │    └─ 遍历 +0x5608 向量（BaseNode 计数），逐项衰减
│    │
│    ├─ [AutoCreate 块] +0x1F3 标志 / Rules 阈值比较
│    │
│    ├─ [TeamDelayTimer 门控] +0x5798(StartTime) / +0x57A0(Duration)
│    │    ├─ 0x006F0AB0  AITrigger 评估宿主 ★热点★
│    │    │    ├─ 遍历 TeamClass::Array (0x8B40EC/0x8B40F8)
│    │    │    │    统计 IsBaseDefense(Type+0xF6) 团队数 vs Rules+0x13CC/0x13B0
│    │    │    ├─ AITriggerTypeClass::ConditionMet 0x0041E720
│    │    │    │    ├─ OwnerHouseOwns 0x0041EE90
│    │    │    │    ├─ EnemyHouseOwns 0x0041EAF0
│    │    │    │    ├─ CivilianHouseOwns 0x0041EC90
│    │    │    │    ├─ HouseCredits 0x0041F230
│    │    │    │    ├─ IronCurtainCharged 0x0041F0D0
│    │    │    │    └─ ChronoSphereCharged 0x0041F180
│    │    │    └─ 0x6F2230/0x6F25E0/0x6F26E0/0x6F2780/0x6F27F0（内部辅助）
│    │    ├─ 0x0050E830 汇总
│    │    └─ 对结果向量逐个 TeamTypeClass::CreateTeam 0x006F09C0
│    │         └─ TeamClass ctor 0x006E8A90 + ScriptClass ctor 0x006913C0
│    │
│    ├─ [每 8 帧] CurrentFrame % 8 == 0          ★热点★
│    │    └─ 遍历 +0x3C 向量（计数 +0x48）
│    │         └─ 0x006E53A0(item, args…)  单项脚本/建筑回调
│    │              └─ 0x007264C0（Script/Tag 动作）
│    │
│    ├─ [生产门控 Timer] +0x5634/+0x563C
│    │    └─ 0x004FD500  AI_TryFireSW 驱动
│    │         ├─ 0x005098F0 AI_TryFireSW
│    │         │    └─ 0x0050D170 PickTargetByType → 0x006EC3D0（扫 TeamArray）
│    │         ├─ 0x004FD9A0 基地附近建造
│    │         │    └─ FirstBuildableFromArray 0x005051E0（多次）
│    │         └─ 0x004FDD10 基地建设驱动
│    │              └─ 0x004FE3E0 AI_BaseConstructionUpdate
│    │                   └─ AllPrerequisitesAvailable 0x00505360（BFS 前置）
│    │
│    └─ [每 8 帧 + AIMode] +0x1E4
│         ├─ AIMode==1 → 0x004FE3E0 AI_BaseConstructionUpdate
│         │    └─ Factory 虚调用 v[0x94] 尝试下单
│         └─ AIMode==2 → 招募三兄弟（按类型分派）
│              ├─ 0x004FEA60  陆军/通用   ★热点★
│              ├─ 0x004FEEE0  海军        ★热点★
│              └─ 0x004FF210  空军        ★热点★
│                   共同模式：
│                   ├─ 遍历 Rules+0xB3C 可造类型（按 House 位图 +0x6CC 过滤）
│                   ├─ FirstBuildableFromArray 0x005051E0
│                   ├─ TeamClass::GetTaskForceMissingMemberTypes 0x006EF4D0
│                   └─ 内部再调 CanBuild 0x004F7870（递归重入）
│
└─ TeamClass 生命周期（事件驱动，非每帧）
     ├─ 创建：TeamTypeClass::CreateTeam 0x006F09C0
     │    └─ ctor 0x006E8A90（写入 TeamArray 0x8B40E8）
     ├─ 脚本步进：0x006E9050（O(脚本)，33 个调用点，含自递归）
     │    ├─ ScriptClass::GetCurrentAction 0x00691500 / 0x691590 / 0x6915B0 / 0x6915D0
     │    ├─ ControlledByHuman 0x0050B730
     │    └─ 0x6EC3A0/0x6EC3D0/0x6EC7D0/0x6EC9A0/0x6ECA70/0x6ECCE0（脚本动作分派）
     ├─ 招兵：TeamTypeClass::CanRecruitUnit 0x006F1320（当前 0 直呼，疑走虚表）
     ├─ 解散/完成：0x006E8DE0（TeamClass dtor）★热点★
     │    ├─ 遍历 AITriggerTypeClass::Array (0xA8B204/0xA8B210)
     │    │    匹配 Trigger.Team1(+0xDC) == this.Type(+0x24)
     │    │    ├─ AchievedGreatSuccess(+0x84) → RegisterSuccess 0x0041FD60
     │    │    └─ 否则 → RegisterFailure 0x0041FE20
     │    ├─ BaseDefense 计数回写 House+0x566C
     │    ├─ while(FirstUnit) LiberateMember 0x006EA870
     │    └─ AnnounceExpiredPointer 0x007258D0
     └─ LiberateMember 0x006EA870（39 调用点：死亡/卸载/路径失败等）
```

---

## 2. 关键地址与数据结构

### 2.1 全局数组（DynamicVectorClass）

| 对象地址 | 类型 | Items | Count | 用途 |
| :--- | :--- | :--- | :--- | :--- |
| `0x00A80228` | `HouseClass*` | `0x00A8022C` | `0x00A80238`（待复核） | 全部 House |
| `0x008B40E8` | `TeamClass*` | `0x008B40EC` | `0x008B40F8` | 活动 Team |
| `0x00A8B200` | `AITriggerTypeClass*` | `0x00A8B204` | `0x00A8B210` | 全部 AITrigger |
| `0x00A8ECA0` | `TeamTypeClass*` | `0x00A8ECA4` | `0x00A8ECA8` | 全部 TeamType |
| `0x00B0F720` | `AbstractClass*` | — | — | 全对象（析构通知用） |

> 实测 Items/Count 偏移以代码引用为准：Team 用 `0x8B40EC`/`0x8B40F8`（差 `0xC`），AITrigger 用 `0xA8B204`/`0xA8B210`（差 `0xC`）。YRpp `DynamicVectorClass` 的字段序与此一致（Items 在 +4，Count 在 +0x10）。

> **[task-11 最小勘误标记 · v1.5.35]** 对 §2.1 表逐行给出的**最小勘误补充**（**不修改上表任何单元格与尾注**，仅在此并列）[实证]：
> 1. **`0x00A8ECA0` TeamType 行**：Count 标注更正 —— 正确三元组 = `Items 0x00A8ECA4`（26 次引用）/ `Capacity 0x00A8ECA8`（3 次）/ **`Count 0x00A8ECB0`**（30 次）。
>    证据（`0x6F085C`）：`89 0D B0 EC A8 00`（`mov [0xA8ECB0],ecx` = Count 写回）→ `8B 0D A4 EC A8 00`（`mov ecx,[0xA8ECA4]` = Items 基址）→ `89 34 81`（`mov [ecx+eax*4],esi` = 数组写入）；
>    结构自证：ctor `0x4E70E0` 依次置 `[0xA8ECA4]=0`(Items) / `[0xA8ECA8]=0`(Capacity) / `[0xA8ECB0]=0`(Count)，dtor `0x4E7120` 只对 `[0xA8ECA4]` 调 `operator delete 0x7C8B3D`。
> 2. **`0x00A80228` House 行（原带「待复核」）**：`0xA8022C / 0xA80238` 按 `Count − Items = 0xC` 的结构约束**确为 DynamicVectorClass 形状**（`[实证]` `0x67D4C2 = 8B 15 38 02 A8 00` 作 Count、`0x67D4EC = 8B 15 2C 02 A8 00` 作 Items 基址）；
>    但**类归属仍有 Aircraft / House 二义**（S21 判 `AircraftClass::Array`，引用 217/146 次），**该行「待复核」标记继续有效**，不得被任何一方当已定论引用。
> 3. 其余行（`0x8B40E8`/`0xA8B200`）与上文一致，无需更正。
> 详见 `docs/re/savegame_block_manifest.md §8.4-bis`。

### 2.2 HouseClass 关键偏移（AI 相关）

| 偏移 | 含义 | 证据 |
| :--- | :--- | :--- |
| `+0x1E4` | `AIMode`（0=无 / 1=基地建设 / 2=招募） | `0x4F908B` 读取后 `cmp 1/2` 分派 |
| `+0x1EC/+0x1ED` | Defeated / IsLoser | `0x4F8564` 内联 `0x50B730` 同款逻辑 |
| `+0x1F2` | `AITriggersActive` | `0x6F0B12` 门控 |
| `+0x1F3` | AutoBaseBuilding 触发位 | `0x4F858B` |
| `+0x2A4/+0x2AC` | RepairTimer 一带 | `0x4F844B` |
| `+0x2B0/+0x2B8` | unknown_timer | `0x4F8490` |
| `+0x3C/+0x48` | 建筑/对象向量 + 计数 | `0x4F8F9C` 8 帧遍历 |
| `+0x5608/+0x5614` | BaseNode 计数向量 + 长度 | `0x4F8522` 100 帧衰减 |
| `+0x5634/+0x563C` | AI_TryFireSW 定时器 | `0x4F8FBE` |
| `+0x5650` | 招募锁（-1 表示空闲） | `0x4FEA70` |
| `+0x566C` | BaseDefenseTeamCount | `0x6E8E58` |
| `+0x5778/+0x5779` | Power/Radar 脏标志 | `0x4F84D2` |
| `+0x5788` | `Allies` 位图 | `targeting_spatial.md` 已证 |
| `+0x5798/+0x57A0` | **TeamDelayTimer**（AITrigger 评估门控） | `0x4F8A00` |
| `+0x57E0` | 某 COM 接口指针 | `0x4F854B` 虚调用 +0x10 |

### 2.3 TeamClass 关键偏移

| 偏移 | 含义 | 证据 |
| :--- | :--- | :--- |
| `+0x24` | `Type`（TeamTypeClass*） | `0x6E8E13` |
| `+0x28` | `CurrentScript` | `0x6E53E2` |
| `+0x2C` | `Owner`（HouseClass*） | `0x6E8E40` |
| `+0x54` | `FirstUnit`（FootClass*） | `0x6E8E6E` |
| `+0x70` | `Tag` | `0x6E8E98` |
| `+0x84` | `AchievedGreatSuccess` | `0x6E8E20` |
| `+0xDC`（TeamType 内） | `cntInstances` | `0x6E8E92` |

### 2.4 AITriggerTypeClass 关键偏移

| 偏移 | 含义 | 证据 |
| :--- | :--- | :--- |
| `+0xB8` | `Weight_Current` | `0x41FDAB` |
| `+0xC0` | `Weight_Minimum` | `0x41FDB9` 下限夹紧 |
| `+0xC8` | `Weight_Maximum` | `0x41FDE4` 上限夹紧 |
| `+0xDC` | `Team1` 指针 | `0x6E8E16` |
| `+0x104` | `TimesExecuted` | `0x41FD7B` |
| `+0x108` | `TimesCompleted` | `0x41FD61` |

Rules（`RulesClass::Instance = 0x008871E0`）相关：

| 偏移 | 含义 |
| :--- | :--- |
| `+0xC0` | `AITriggerSuccessWeightDelta` |
| `+0xC8` | `AITriggerFailureWeightDelta` |
| `+0xD0` | `AITriggerTrackRecordCoefficient` |
| `+0xB3C` | AI 可造类型列表（招募用） |
| `+0x13B0/+0x13CC` | BaseDefense 团队阈值表 |

---

## 3. 热点函数表

| 地址 | 名称 | 复杂度 | 调用频率 | 成本定性 |
| :--- | :--- | :--- | :--- | :--- |
| `0x004F8440` | **HouseClass::Update**（v[23]） | 汇聚体 | 每帧 × House 数 | **调度中枢**，内部限频 |
| `0x006F0AB0` | **AITrigger 评估宿主** | O(Team × Trigger) | TeamDelayTimer 门控（秒级） | **★★★ 高**：高密度局 Team/Trigger 多时最重 |
| `0x0041E720` | AITriggerTypeClass::ConditionMet | O(1) 条件 | 被 0x6F0AB0 循环调 | 中：循环内 |
| `0x004FEA60` | 招募-通用 | O(可造类型 + TeamType) | 每 8 帧 × House（AIMode==2） | **★★ 高** |
| `0x004FEEE0` | 招募-海军 | 同上 | 同上 | **★★ 高** |
| `0x004FF210` | 招募-空军 | 同上 | 同上 | **★★ 高** |
| `0x004FE3E0` | AI_BaseConstructionUpdate | O(前置 BFS) | 每 8 帧 × House（AIMode==1） | 中 |
| `0x004FD500` | AI_TryFireSW 驱动 | O(超级武器数) | Timer 门控 | 低-中 |
| `0x004FDD10` | 基地建设驱动 | O(BaseNode) | 被 0x4FD500 调 | 中 |
| `0x004F7870` | HouseClass::CanBuild | O(前置递归) | 13 个调用点（UI+AI 递归） | 中：**会被招募路径递归重入** |
| `0x004F9F90` | MakeEnemy / 关系变更 | O(1) + 触发 AITrigger 重估 | 事件驱动 | 低（但会拉起 0x6F0AB0） |
| `0x006E9050` | TeamClass 脚本步进 | O(脚本行) | 每 Team 每逻辑 tick | **★★ 中高**：33 调用点，含自递归 |
| `0x006E53A0` | 单项 8 帧回调 | O(1) | 每 8 帧 × 向量长度 | 中：随建筑数线性 |
| `0x006E8DE0` | TeamClass dtor / 完成 | **O(AITrigger)** | Team 死亡时 | **★★ 中**：权重回写全表扫描 |
| `0x0041FD60` | RegisterSuccess（权重） | O(1) | 被 dtor 调 | 低 |
| `0x0041FE20` | RegisterFailure（权重） | O(1) | 被 dtor 调 | 低 |
| `0x006EA870` | LiberateMember | O(1) | 39 事件点 | 低 |
| `0x006F09C0` | TeamTypeClass::CreateTeam | O(1) 构造 | AITrigger 命中时 | 低 |
| `0x006F2040` | ProcessAllTaskforces | O(TeamType) | 场景更新 0x686B20 | 中 |
| `0x005051E0` | FirstBuildableFromArray | O(候选数) | 招募/建造多次 | 中 |
| `0x00505360` | AllPrerequisitesAvailable | O(前置 BFS) | BaseCons 内 | 中 |
| `0x0050B730` | ControlledByHuman | O(1) | **139 个调用点** | 低单次、高频次 |

### 3.1 AITrigger 权重更新（`0x0041FD60` / `0x0041FE20`）伪码

```cpp
// RegisterSuccess (0x41FD60)
double track = TimesCompleted / (double)TimesExecuted;   // +0x108 / +0x104
double delta = track - 1.0;                               // 与常量 0x7E1738 比较
Weight_Current += Rules.AITriggerSuccessWeightDelta * max(delta, 0);
Weight_Current  = clamp(Weight_Current, Weight_Minimum, Weight_Maximum);
TimesExecuted++; TimesCompleted++;

// RegisterFailure (0x41FE20)
double track = TimesCompleted / (double)TimesExecuted;
double delta = track - 1.0;
Weight_Current += Rules.AITriggerFailureWeightDelta * delta * Rules.AITriggerTrackRecordCoefficient;
Weight_Current  = clamp(Weight_Current, Weight_Minimum, Weight_Maximum);
TimesExecuted++;
```

**触发点唯一**：`0x006E8DE0`（Team 析构）按 `Trigger.Team1 == Team.Type` 匹配后调用。**不存在每帧权重漂移**。

---

## 4. 与 Greatest_Threat 的关系

| 层级 | 是否扫全图 | 说明 |
| :--- | :--- | :--- |
| House AI（Update / 招募 / 建造） | **否** | 只碰 House/Team/TeamType/AITrigger 列表与 CounterClass |
| Team 脚本步进（0x6E9050） | **否** | 走 ScriptAction，下发 Mission/目标；不直接枚举全图对象 |
| AITrigger 评估（0x6F0AB0） | **否** | O(Team + Trigger) 列表扫描 |
| 单位级 SelectAutoTarget / Greatest_Threat | **是** | 三路枚举（空间桶 0x887888 / 螺旋 Cell 链 / 数组），见 `targeting_spatial.md` |

**结论**：AI 逻辑与 Greatest_Threat **解耦**。House/Team 层的优化不需要动空间索引；空间哈希只作用于单位寻敌。二者唯一的间接耦合是：Team 脚本下发攻击指令后，单位侧才进入 Greatest_Threat。

---

## 5. 优化插入点（2～3 个）

### 插入点 A：AITrigger 评估结果缓存（限频 + 脏标记）

**位置**：`0x006F0AB0` 入口（`0x006F0AB0`–`0x006F0B20` 前置段）。

**做法**：
1. 在 House 上挂脏标记 `aiTriggerDirty`，置位条件：
   - `OwnedXxxTypes1` CounterClass 变更（`RegisterGain 0x00502A80` / `RegisterLoss 0x005025F0` 已有钩子点）；
   - `Credits` 跨阈值（HouseCredits 条件）；
   - SuperWeapon 充能状态翻转（IronCurtain / ChronoSphere）；
   - TeamDelayTimer 到期（保留原周期作为兜底）。
2. 未置位时短接 `0x006F0AB0` 直接返回空向量。
3. 可选：对 `ConditionMet` 结果按 Trigger 做 1 帧缓存（同帧多 House 共享时）。

**收益**：高密度局（Trigger 数百、Team 数十）下，未发生军力/经济变化的帧直接跳过 O(Team×Trigger)。

**确定性风险**：**中高**。
- 条件涉及计数器与金钱，若脏标记漏置（例如间谍/心灵控制导致的计数变更未走 RegisterGain），会推迟建队 → **改变出兵时序**。
- 若缓存跨帧复用，必须保证多机同步（所有客户端同帧同结果）。**建议只做"跳过整帧"而非"复用旧结果"**，且脏标记在 `RegisterGain/Loss`、`TransactMoney`、SW 充能完成处强制置位。
- **不可改变 Trigger 遍历顺序**（AITriggerArray 顺序决定同权重下的优先级）。

### 插入点 B：Team 析构权重回写反向索引（邻域/索引）

**位置**：`0x006E8DE0` 的 `0x6E8E0B`–`0x6E8E3E` 循环（遍历 AITriggerArray 匹配 Team1）。

**做法**：
1. 建立 `TeamType* → vector<AITriggerTypeClass*>` 反向索引（TeamType 创建 / AITrigger 加载时维护，`0x41F2E0` LoadFromINIList、`0x6F06E0` TeamType ctor 处挂钩）。
2. dtor 只遍历该 TeamType 关联的 Trigger 子集，仍按 **原 AITriggerArray 下标顺序** 调 `RegisterSuccess/Failure`。
3. 索引在 Trigger 删除（`0x0041FEE0`）时同步清理。

**收益**：Team 高频死亡时（高密度局常态），从 O(全 AITrigger) 降为 O(关联 Trigger)。Trigger 数百 × Team 死亡频繁时收益明显。

**确定性风险**：**低**。
- 权重计算本身是逐 Trigger 独立的；只要**调用顺序不变**（按原数组下标排序），结果 bit 级一致。
- 索引若漏项会导致权重漏更新 → 后续 Trigger 选中概率偏移。需在 dtor 前断言 `索引大小 == 线性扫描命中数`（debug 模式）。
- **不可改**：`RegisterSuccess/Failure` 的浮点运算顺序与夹紧逻辑。

### 插入点 C：招募三兄弟时间片（限频 + 轮转）

**位置**：`0x004F90E7`–`0x004F9260`（HouseClass::Update 内 AIMode==2 分支），及 `0x004FEA60/0x004FEEE0/0x004FF210` 入口。

**做法**：
1. 将"每 8 帧跑全三类"改为"每 8 帧只跑一类，3 轮一循环"（用 House 上的 2 bit 轮转计数）。
2. 或在 `0x004FEA60` 内部对 `Rules+0xB3C` 类型列表做游标续扫（每帧最多 N 个类型），游标存 House+0x5654。
3. 保留：当 `+0x5650 == -1`（招募锁空闲）时可立即全量跑一轮（快速路径）。

**收益**：每 8 帧的 O(3×可造类型×TeamType) 降为 1/3 或 O(N)。

**确定性风险**：**高**。
- 招募顺序决定**哪个 TeamType 先被创建**，直接影响出兵组合与攻击波次。
- 轮转会改变"同帧内三类的相对优先级"（原版固定 陆军→海军→空军 的尝试顺序）。
- **必须保持同类内部的类型遍历顺序不变**；只允许跨类轮转，且需验证与 `CanBuild` 递归的交互（`0x4FEA60` 内部会再调 `0x4F7870`）。
- 联机下所有客户端必须同规则轮转（用 `CurrentFrame % 3` 而非本地计数器，保证同步）。

---

## 6. 确定性风险总表

| 优化 | 风险 | 原因 | 缓解 |
| :--- | :--- | :--- | :--- |
| A. AITrigger 短接 | **中高** | 漏脏 → 建队推迟 → 出兵时序变 | 脏标记覆盖所有 Counter/金钱/SW 路径；保留 Timer 兜底；只跳帧不复用 |
| B. dtor 反向索引 | **低** | 只要顺序不变则 bit 级一致 | 按原下标排序调用；debug 断言索引完整 |
| C. 招募轮转 | **高** | 改变建队优先级 | 仅跨类轮转；类内顺序不动；用 `CurrentFrame` 保证同步 |

**全局禁改**（会破坏建造/攻击决策顺序）：
- `AITriggerArray` / `TeamTypeArray` / `HouseArray` 的**遍历顺序**；
- `ConditionMet` 各子条件的**求值顺序与短路**；
- `Weight_Current` 的**浮点运算顺序**；
- `CanBuild 0x004F7870` 的**递归返回值语义**（招募路径依赖）。

---

## 7. 未决问题

1. **`HouseClass::Update` 的调用方**：`0x004F8440` 无 E8 直呼，必走虚表 v[23]。主循环中"逐 House 调 Update"的具体循环体未钉死（可能在 `0x00686B20` 深处或 `0x00599650` 链上）。需用硬件断点或插桩确认每帧 House 数与调用序。
2. **`0x006E53A0` 的 this 类型**：偏移特征（`+0x24/+0x28`）与 TeamClass 布局部分吻合，但 `+0x34/+0x35` 当 bool 用存疑——可能是 Building/Team 联合回调。需对照 YRpp 完整 `sizeof(TeamClass)` 与实机对象验证。
3. **`HouseClass+0x3C/+0x48` 向量的真实类型**：8 帧遍历调用 `0x006E53A0` 时传 5 个栈参，未确认是 Buildings、Teams 还是 Tag 列表。
4. **`0x004FEA60` 与 `0x004FEEE0/0x004FF210` 的类型分派依据**：三者结构几乎相同，差异在 `Rules+0xB3C` 子表过滤位（`+0x6CC`）。具体位定义（陆军/海军/空军）未逐位验证。
5. **`TeamTypeClass::CanRecruitUnit 0x006F1320` 当前 0 直呼**：疑似虚表调用或被 inline，招兵路径的实际入口需补扫。
6. **`0x006F0AB0` 内部 5 个辅助函数**（`0x6F2230/0x6F25E0/0x6F26E0/0x6F2780/0x6F27F0`）仅被它调用，命名与精确语义未展开。
7. **HouseClass 数组 Count 偏移**：Items=`0xA8022C` 已证，Count 疑为 `0xA80238`（差 0xC，与 Team/AITrigger 一致），但 `0xA80230` 也有 3 处引用，需复核是 Capacity 还是 Count。
8. **高密度局实测占比**：本文复杂度为静态推导。建议在 `0x6F0AB0`、`0x4FEA60`、`0x6E9050`、`0x6E8DE0` 入口插 `rdtsc` 采样，对照 `out/loadbench` 的 U0800 场景给出实测百分比。
> **【勘误 2026-09-28 · MIMO-H1VOID + Lead】该建议中的「U0800 场景」已不可用**：旧 `U0800` 基准图真机仅 21/22 单位（非 800 负载）⇒ 高密度局占比须改在 **H1 图**（`[2]0LoadBench_U0800_H1.yrm`，2 槽 × 800/2）上测，步骤见 `out/loadbench/H1_REMEASURE_RUNBOOK.md`；任何引用旧 `U0800` 的实测百分比**不得再作为高密度证据**。

> **[task-11 最小勘误标记 · v1.5.35]**（不改写上文第 7 项正文）**第 7 项已定谳**：`0xA80230` = **Capacity**、`0xA80238` = **Count**（差额恰为 `+4` / `+0xC`）；
> 该布局与 `0xA8ECA4`(Items)/`0xA8ECA8`(Capacity)/`0xA8ECB0`(Count) 完全同构，一并由 `0x6F085C` 指令链与 ctor `0x4E70E0` 定谳（见 `docs/re/savegame_block_manifest.md §8.4-bis`）。

---

## 8. 附：验证脚本

```text
out/re_work/house_team_ai/house_team_ai_re.py    # 全局数组 xref + 已知函数调用者
out/re_work/house_team_ai/house_team_ai_re2.py   # 调用链收敛
out/re_work/house_team_ai/house_team_ai_re3.py   # Update 虚函数 / 顶层数组遍历
out/re_work/house_team_ai/house_team_ai_re4.py   # 热点函数画像
out/re_work/house_team_ai/house_team_ai_re5.py   # 函数边界 / 频率
out/re_work/house_team_ai/house_team_ai_re6.py   # 收敛确认
```

反汇编全文见同目录 `fn_*.txt` / `window_*.txt`。

---

## 9. 冲刺结论（S6）

> 依据 S6 专项反汇编取证，针对前文未决问题与优化插入点补充实证闭环结论。  
> 证据等级：[实证]（给出具体 VA、文件偏移、机器码、汇编指令）× [推演] × [待实测]。

### 9.1 §7 AITrigger 权重回写时机全链路闭环

1. **全二进制写引用唯一性 [实证]**：
   - 对 `gamemd.exe` 全代码段扫描 `[reg + 0xB8]`（`AITriggerTypeClass::Weight_Current`），仅存在 4 处写操作：
     - `0x0041E374`（FileOffset `0x01E374`）：构造函数默认初始化。
     - `0x0041F8AC`（FileOffset `0x01F8AC`）：`LoadFromINI` 浮点解析回写。
     - `0x0041FDB3` / `0x0041FDCC` / `0x0041FDF7`（FileOffset `0x01FDB3`）：`RegisterSuccess`（`0x0041FD60`）。
     - `0x0041FE7C` / `0x0041FE95` / `0x0041FEC0`（FileOffset `0x01FE7C`）：`RegisterFailure`（`0x0041FE20`）。
   - **结论**：不存在任何每帧或周期性的 AITrigger 权重浮动逻辑；动态权重变更**完全依赖** `RegisterSuccess` 与 `RegisterFailure`。

2. **调用宿主唯一性 [实证]**：
   - 交叉引用检索显示：`RegisterSuccess`（`0x0041FD60`）与 `RegisterFailure`（`0x0041FE20`）在全程序中**各自仅有唯一调用点**：
     - `0x006E8E2A`（FileOffset `0x2E8E2A`, `E8 31 6F D3 FF`）：`call 0x0041FD60`
     - `0x006E8E31`（FileOffset `0x2E8E31`, `E8 EA 6F D3 FF`）：`call 0x0041FE20`
   - 两调用点均位于 `TeamClass::~TeamClass`（`0x006E8DE0`）析构循环体内。
   - 析构时遍历 `AITriggerTypeClass::Array`（`0x00A8B204`，计数 `0x00A8B210`），当且仅当 `Trigger->Team1 (+0xDC) == this->Type (+0x24)` 时触发。

3. **成败判定标志与脚本动作分派 [实证]**：
   - `TeamClass::ctor`（`0x006E8A90`）在 `0x006E8B2C`（`88 9E 84 00 00 00`）将 `this+0x84`（`AchievedGreatSuccess`）初始化为 0。
   - 全二进制中向 `this+0x84` 写 1 的有效指令**仅有 1 处**：`0x006E9CE8`（`C6 86 84 00 00 00 01`）。
   - 该指令位于 `TeamClass::AI`（`0x006E9050`）的脚本动作跳转表（`0x006E9F74`）**Action 49（0x31，Success）**分派分支内。
   - 若 Team 在执行完脚本 Action 49 之前死亡、被解散、或路径阻塞，`this+0x84` 保持为 0，析构时一律走 `RegisterFailure`；只有成功走完 Action 49 的队伍在析构时走 `RegisterSuccess`。

4. **YRpp 命名颠倒与精确数学公式纠偏 [实证]**：
   - 汇编实证：`0x0041FD61` 读取 `[ecx + 0x108]` 并用于 `0x0041FD81`（`fdiv st(1)`）的分母；在 `RegisterFailure` 中仅递增 `[ecx + 0x108]`，而在 `RegisterSuccess` 中同时递增 `[ecx + 0x104]` 与 `[ecx + 0x108]`。
   - **纠偏**：YRpp 头文件命名颠倒！真实语义为：
     - `+0x104` = **成功次数**（`TimesSuccess` / 完成次数）
     - `+0x108` = **总执行次数**（`TimesExecuted` / 总运行批次）
   - 提取双精度常数：`0x007E2800 = 0.0`，`0x007E1738 = 0.5`。
   - **精确回写算式**：
     - 成功率：$R = \frac{\text{TimesSuccess}}{\text{TimesExecuted}} \in [0.0, 1.0]$。
     - 成功时（`0x0041FD60`）：
       $$\Delta_{success} = \max\Big(\text{TimesExecuted} \times (R - 0.5), \; 0.0\Big)$$
       $$\text{Weight} \leftarrow \text{clamp}\Big(\text{Weight} + \text{Rules.AITriggerSuccessWeightDelta}(+0\text{xC0}) + \Delta_{success}, \; \text{Weight\_Min}, \; \text{Weight\_Max}\Big)$$
       $$\text{TimesSuccess}\text{++}, \quad \text{TimesExecuted}\text{++}$$
     - 失败时（`0x0041FE20`）：
       $$\Delta_{failure} = \min\Big(\text{TimesExecuted} \times (R - 0.5) \times \text{Rules.AITriggerTrackRecordCoefficient}(+0\text{xD0}), \; 0.0\Big)$$
       $$\text{Weight} \leftarrow \text{clamp}\Big(\text{Weight} + \text{Rules.AITriggerFailureWeightDelta}(+0\text{xC8}) + \Delta_{failure}, \; \text{Weight\_Min}, \; \text{Weight\_Max}\Big)$$
       $$\text{TimesExecuted}\text{++}$$

5. **评估宿主（`0x006F0AB0`）只读实证 [实证]**：
   - 反汇编显示：`0x006F0AB0` 在 `0x006F0C61`（`fld qword ptr [esi + 0xb8]`）读取当前权重并调用 `0x007C5F00`（`__ftol`）转为整型，用于多分支累加总权重并调用 `0x0065C7E0` 进行轮盘赌随机选择（权重 5000 特权短路清空候选列表除外）。
   - 评估过程**完全没有**任何写入 `+0xB8` 的指令。

---

### 9.2 招募三兄弟轮转时序与生命周期全景

1. **三兄弟真实兵种分工澄清 [实证]**：
   - 对照其向 House 写入的订单槽位与后续工厂下单分派指令：
     - 兄一 `0x004FEA60`（FileOffset `0x0FEA60`）：门控 `[esi+0x5650] == -1`，Missing 类型过滤 `WhatAmI == 0x28`（`UnitType`），对应 **战车/装甲工厂（War Factory）**。
     - 兄二 `0x004FEEE0`（FileOffset `0x0FEEE0`）：门控 `[esi+0x5654] == -1`，Missing 类型过滤 `WhatAmI == 0x10`（`InfantryType`），对应 **兵营/步兵（Barracks）**。
     - 兄三 `0x004FF210`（FileOffset `0x0FF210`）：门控 `[esi+0x5658] == -1`，Missing 类型过滤 `WhatAmI == 0x03`（`AircraftType`），对应 **停机坪/战机（Airfield/Helipad）**。
   - 前文猜测的“陆军/海军/空军”在此正式更正为：**战车 / 步兵 / 战机**。

2. **调用时序与执行链路 [实证]**：
   - 在 `HouseClass::Update`（`0x004F8440`）内，当满足 `CurrentFrame % 8 == 0` 且 `House->AIMode == 2`（`+0x1E4`）时：
     - `0x004F90F2`：`call 0x004FEA60`（战车招募决策）
     - `0x004F9198`：`call 0x004FEEE0`（步兵招募决策）
     - `0x004F919F`：`call 0x004FF210`（战机招募决策）
   - 随后紧跟工厂下单分派逻辑（`0x004F91A4`–`0x004F9238`）：
     - 若 `House+0x5650 != -1`：取 `0x00A83CE4`（`UnitTypeClass::Array`），调 War Factory 虚表 `v[0x94]`（`StartProduction`）。
     - 若 `House+0x5654 != -1`：取 `0x00A8E34C`（`InfantryTypeClass::Array`），调 Barracks 虚表 `v[0x94]`（`StartProduction`）。
     - 若 `House+0x5658 != -1`：取 `0x00A8B21C`（`AircraftTypeClass::Array`），调 Airfield 虚表 `v[0x94]`（`StartProduction`）。

3. **队伍与单位招募结合的双通道机制 [实证]**：
   - **主动通道（Team 侧拉取）**：`TeamClass::AI`（`0x006E9050`）在 `0x006E9281` 调用 `TeamClass::Recruit`（`0x006EAA90`），遍历地图全量闲置单位，经 `TeamClass::CanAddMember`（`0x006EA610`）检查所有者、血量、Limbo、TaskForce 配额后，调 `TeamClass::AddMember`（`0x006EA500`）将单位链入 `TeamClass+0x54`（`FirstUnit`）。
   - **被动通道（Factory 侧推送）**：单位下线出厂阶段（`UnitClass::Init` / `InfantryClass::Init`，调用点 `0x0073DC19` / `0x0073815F`），新单位主动检索全 Team 列表，优先认领等待该兵种的队伍并调用 `0x006EA500`。

4. **时间片轮转（Round-Robin）的确定性风险评估 [推演]**：
   - **原版固定行为**：三兄弟在同逻辑帧内严格按 战车 $\rightarrow$ 步兵 $\rightarrow$ 战机 依次检查并向工厂下单。
   - **时间片改造风险**：若改为“每 8 帧只跑 1 类、3 轮一循环”：
     - 步兵首次下单推迟 8 帧，战机首次下单推迟 16 帧，改变混编兵种成型时序。
     - **资金竞态破坏**：工厂下单会检查 House 资金；原版战车具有天然资金优先权，轮转会使得步兵或战机在低资金局面下抢先扣款，导致战车停产。
     - **联机同步纪律**：轮转相位必须使用全局确定性帧号 `(CurrentFrame / 8) % 3`，严禁使用本机构造的内部静态变量。

---

### 9.3 空间哈希替换枚举序等效性证明

> 针对 `docs/re/targeting_spatial.md` 中 `Greatest_Threat` 空间哈希优化的核心疑虑：“在严格大于（`>`）择优下，空间哈希打乱枚举顺序是否会导致同分敌人选择漂移？”本小节给出数学证明与零排序 $O(1)$ 等效实现方案。

1. **原版择优机制的偏序与全序特征 [实证]**：
   - 汇编依据：`0x006F9363`–`0x006F9377`（及全图枚举分支 `0x006F9C3C`、`0x006F9D87`）：
     ```asm
     0x006F9363: 8B 44 24 74      mov eax, [esp+0x74]   ; 本候选威胁分 S(c)
     0x006F9367: 8B 4C 24 1C      mov ecx, [esp+0x1C]   ; 当前最高威胁分 S_best
     0x006F936B: 3B C1            cmp eax, ecx          ; ★ 评分比较指令点 (FileOff: 0x2F936B)
     0x006F936D: 7E 08            jle 0x006F9377        ; ★ 严格大于才更新：S(c) <= S_best 则直接跳过
     0x006F936F: 89 6C 24 20      mov [esp+0x20], ebp   ; 更新最优目标 Target_best = c
     0x006F9373: 89 44 24 1C      mov [esp+0x1C], eax   ; 更新最高分 S_best = S(c)
     ```
     注：全图对象枚举另有两处同构更新点（步兵/战车循环）：`0x006F9C3C`（`cmp eax, ecx`）+ `0x006F9C3E`（`jle 0x006F9C48`）与 `0x006F9D87`（`cmp eax, ecx`）+ `0x006F9D89`（`jle 0x006F9D93`），其前置调用打分函数均为 `0x006F7CA0`。全逻辑统一遵循“严格大于择优”。
   - 设候选序列为 $\pi = (c_1, c_2, \dots, c_N)$，威胁评分为 $S(c)$。
   - 选出目标必为：
     $$T^* = c_{k^*}, \quad k^* = \min \left\{ k \in \{1, \dots, N\} \;\middle|\; S(c_k) = \max_{1 \le j \le N} S(c_j) \right\}$$
   - 即：**在所有取得全局最大威胁分的候选者中，原版枚举序中最先出现的候选者必胜**。

2. **等效性定理（Lexicographical Tuple Equivalence） [推演]**：
   - **定义**：设原版枚举中各候选对象的规范发现序号为 $\text{ord}(c) \in \mathbb{N}$。
     - 对于全局数组路（Aircraft/Unit/Infantry），$\text{ord}(c) = c\text{->ArrayIndex}$（或 $(c\text{->WhatAmI} \ll 16) \mid c\text{->ArrayIndex}$）。
     - 对于地图格子链表，$\text{ord}(c)$ 为其全局唯一创建序标 `c->UniqueID`（`ScenarioClass::Instance->UniqueID` 严格自增）。
   - **构造元组评分**：
     $$\mathbf{V}(c) = \Big( S(c), \; -\text{ord}(c) \Big)$$
     定义字典序全序关系 $\succ$：
     $$\mathbf{V}(A) \succ \mathbf{V}(B) \iff \Big( S(A) > S(B) \Big) \;\lor\; \Big( S(A) == S(B) \;\land\; \text{ord}(A) < \text{ord}(B) \Big)$$
   - **定理证明**：
     由于 $\text{ord}(c)$ 在任意时刻均为互不相同的良序整数，对于任意候选子集 $\mathcal{H} \subseteq \Omega$，$\mathbf{V}(c)$ 在 $\mathcal{H}$ 上具有**唯一最大元**。无论空间哈希以何种几何桶序、哈希碰撞桶序遍历 $\mathcal{H}$ 的任意排列 $\sigma(\mathcal{H})$：
     $$\arg\max_{c \in \sigma(\mathcal{H})}^{\succ} \mathbf{V}(c) \equiv T^*$$
     目标选择结果与遍历顺序**完全解耦**，100% 恒等于原版枚举序。

3. **工程实现规范（零额外排序，$O(1)$ 时间复杂度） [推演]**：
   - 优化落地时，空间哈希查询循环无需对候选做 `std::sort`，仅需在维护最优目标时增加平分决胜比较：
     ```cpp
     AbstractClass* best_target = nullptr;
     int best_score = -1;
     uint32_t best_ord = 0xFFFFFFFF;

     spatial_hash.Query(center, radius, [&](AbstractClass* candidate) {
         int score = EvaluateCandidateThreat(candidate); // 调 0x006F7CA0
         if (score <= 0) return;
         uint32_t ord = candidate->Fetch_ID(); // 或 (WhatAmI << 16) | ArrayIndex
         if (score > best_score || (score == best_score && ord < best_ord)) {
             best_score = score;
             best_ord = ord;
             best_target = candidate;
         }
     });
     ```
   - **重入与重叠天然幂等**：当空间哈希扩圈导致同一对象被多次探测时，第二次访问将满足 `score == best_score && ord == best_ord`，条件判定失败自动跳过，无需维护 `visited` 去重集合。
