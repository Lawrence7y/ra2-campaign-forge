你是 RA2 Campaign Forge 的**真机验证卡 W35**。任务：**用真机实测判定「把 DLC 地图登记进 `MAPSELMD.INI` 后，战役能否从第 1 关推进到第 2 关」**。

工作目录：`D:\Project\ra2-campaign-forge`

---

## 一、必须是真机的原因

静态分析已把失败点收窄到 `MapSelect::Init` 的 `MAPSELMD.INI` 阶段登记表分支，但**没有任何一次运行时观测**证明该分支就是实际触发的那条（`MapSelect::Init` 内共有 4 条失败分支）。本卡就是补这一次观测。

## 二、已确立的事实（可直接引用）

**阻塞机制**（`REVIEW\LEAD_VERDICT_map_start_root_cause.md`，两卡互证）：
- 结算屏点 `GUI:Continue` → `0x00685A38` 读 `[Scen+0x34B0]`(`SkipMapSelect`) 分派
  - `=no` → `0x005ADD10` → `0x005AE100` → `0x005AE220` 载入 `MAPSELMD.INI`，用**当前地图名** `[Scen+0x125C]` 经 `0x005CF760` 反查阶段
  - `=yes` → `0x005ADF20` 载入 `MAPSELMD.INI`，取当前阶段 `[Scen+0x35A0]`，遍历候选子项 `0x005CF6B0`，用子项 `Scenario=` 与 `NextScenario`（归一化后）比较
  - 两条路径都要求 `MAPSELMD.INI` 认识我方地图；未命中 → `"MapSelect: Invalid stage!"` → 弹 CSF 标签 `MSG:UnableMapSelect`（**文本是「無法啟始選取地圖！」，是「啟始」不是「啟動」**）
- `Scenario=` 直接指向能进，因为走 `Start_Scenario 0x00683AB0` → `CCFileClass`（**磁盘优先**），完全不经过 MapSelect

**`MAPSELMD.INI` 实体**（Lead 已用哈希反查钉死）：
- 在 `ra2bench\ra2md.mix` 内，**文件偏移 `0x71D050`**，长度 **5,573 B**，**CRLF**，SHA-256 `074ccccd9e156d586d0ed099ceab78b3d72384c808725d8b5bee2c9799691d52`
- 结构：`[GDI] 1=ALL01..7=ALL07` / `[Nod] 1=Sov01..7=Sov07`；每个阶段段如 `[ALL01] Scenario=ALL01umd.MAP` + `2=ALL02`
- 从 mixlib 的 `get()` 取不到（条目表加密且在嵌套容器内）；**直接用上面的文件偏移切片**最省事

**我方地图**（`W27_campaign_live\pkg\W27 Live Campaign\`）：`ECH01.MAP`（4,671 B，`SkipMapSelect=no`/`EndOfGame=no`/`NextScenario=ECH02.MAP`，目标 `survive(8)`）、`ECH02.MAP`（`survive(1800)`）

**先读这两份规格，再动手**：
- `lead\next_re_20261112_r02\W34_mapselmd\MAPSELMD_SPEC.md`（17,390 B，格式定谳）
- `lead\next_re_20261112_r02\W27_campaign_live\CAMPAIGN_LIVE.md`（§setup：如何装包、如何用 WMI 启动、如何观测）

## 三、实验设计

1. **沙箱**：从 `D:\Project\ra2-campaign-forge\ra2youli` **只读复制**一份到 `W35_mapselmd_live\sandbox_game\`（`robocopy` 只读源）。**绝不修改真 `ra2youli`。**
   注意：`ra2youli` 里有一个**既存旧包 v0.3**（`ra2forge_install.json`=`fe3bdf62…`，"钢铁残响"，带 `BATTLEMD98.INI` 与被替换过的 `ECH01.MAP`）。沙箱里先按 W27 的做法处理（卸载旧包，或按既定语义用 `--allow-content-conflict`），**记录你选了哪种以及原因**。
2. **装包**：装 `W27 Live Campaign`，`verify` 通过。
3. **构造 `MAPSELMD.INI`**：官方 5,573 字节**完整克隆**后，按 `MAPSELMD_SPEC.md` **追加**我方两个阶段的登记（对应借用的阵营段与阶段序号）。
   - **硬性规则**：必须是完整文件，**绝不**生成只含我方条目的最小文件（那会让官方 14 关全挂）
   - 散装投放到沙箱游戏目录（散装优先于 MIX，已被字节级证实）
   - 把你追加的**具体行**原样贴进报告，并明确标注哪些写法是**代码依据**、哪些是**推断**
4. **跑测试**：进战役 → 开始第 1 关 → 等 `survive(8)` 自然判胜（必要时按两次 Enter 跳过影片，属正常 UI 输入）→ 点 `GUI:Continue` → **观测第 2 关是否加载**
5. **观测手段**（至少用三种，别只看一个）：
   - 枚举控件文本（`EnumChildWindows`）
   - 读游戏定时器 `[0xA8ED84]`（32 ms 定时器，31.25 计数/秒）判断是否真的在推进
   - 内存标记检索：找 `ECH02.MAP` ASCII/UTF-16LE 命中
   - 截图（关键节点各一张）
6. **判据**：
   - **成功**：进入第 2 关局内（定时器递增 + 截图有雪地图/基地 + `ECH02.MAP` 内存命中）
   - **失败**：仍弹「無法啟始選取地圖！」→ 记录，并**立即做一次区分实验**：把沙箱里我方地图的 `SkipMapSelect` 改成 `yes` 重试一次（`SkipMapSelect=yes` 走另一条分支），看是否变成另一种失败或成功。这能把 4 条失败分支进一步收窄。
   - **部分成功/异常**：游戏崩溃、卡在加载、菜单异常 —— 如实记录，不要美化

## 四、真机纪律（硬性，违反即视为失败）

- **单实例**：一次只跑一个 `gamemd.exe`。开工取 `lead\next_re_20261112_r02\.game_instance.lock`，收尾还原为 `owner=lead`
- **启动方式**：必须用 WMI `Invoke-CimMethod Win32_Process Create` 启动，使游戏脱离代理进程树
- **禁止注入 / attach / 写内存 / 改 exe**：只允许只读读取（`ReadProcessMemory` 只读取证可以）
- **`finally` 自愈**：关闭游戏 → 检查无 `gamemd.exe` 残留 → 逐字节还原沙箱里的 `RA2MD.INI` / `ddraw.ini` → 写 `kind=meta_end` → 还原锁
- **真目录零改动自证**：开工前后各做一次 `ra2youli` 全量清单（文件数 + 每个文件 SHA-256），收尾给出 `added/removed/changed` 与 `IDENTICAL_TREE` 布尔值。基线参考值：647 个文件、`RA2MD.INI`=`c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d`、`gamemd.exe`=`73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`、`ddraw.dll`=`85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9`
- 时间预算：单次进游戏到判定 ≤ 6 分钟；总时长 ≤ 70 分钟。超时就如实报告「未完成」，不要为了出结论而放宽判据

## 五、报告口径（关键）

- 分级：`[本次实测]`/`[本次读码]`/`[静态推断]`/`[转引]`/`[待运行验证]`
- **不许把「游戏没崩」当「功能正常」**；不许把「截图看着像」当证据——必须有定时器/内存/控件至少两项硬指标
- 若结论是「仍未解决」，那也是有价值的结论，**照实写**
- 若你在构造 `MAPSELMD.INI` 时对格式拿不准，**先写清你的假设再测**，并在报告里把「假设 + 若假设错误则结论怎么变」写出来

## 六、交付（只写这个目录）

`lead\next_re_20261112_r02\W35_mapselmd_live\`
- `LIVE_RESULT.md`：结论、实验步骤、追加的 `MAPSELMD.INI` 行、观测原始证据摘要、失败时的分支区分结果
- `out\`：ndjson 事件流、截图、`MAPSELMD.INI` 变体、`verify` 日志
- `tools\`：驱动脚本（须可复跑）
- `UNKNOWNS.md`、`DISAGREE.md`
- `REAL_DIR_PROOF.txt`：真目录零改动自证
