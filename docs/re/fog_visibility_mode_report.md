# FOG-MODE 交付报告 —— 新增「可见性模式」选择键：原版态 ↔ 现状态（用户裁决）

> 任务号：**FOG-MODE** ｜ 执行方：**DSH 子代理** ｜ 工作区：`D:/Project/ra2-campaign-forge`（Windows）
> 基线（只读）：`ra2youli/gamemd.exe` MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367` / 4,825,360 B（开工=收工复算一致）
> 交付产物：`ra2render/ra2render.dll` ≡ `ra2youli/ra2render.dll` = **140,800 B** / MD5 `455651B1C44BC5D69AF8E88189499128` / SHA-256 `1E50F72E84EE091D90618E71BC3C4F98234172C050DC09E8E5EB7ED13A68C04F`
> 旧件备份：`out/re_work/fog_mode/ra2render.dll.bak-59671E8B`（138,752 B / MD5 `59671E8BC333A999820C788D76A5B375`）、`ra2render.ini.bak-2DEB8F3B`（9,459 B = 开工时仓内件）、`ra2render.ini.deployed-2DEB8F3B`（9,459 B = 开工时部署件）
> 两份 ini 同步：**12,242 B** / MD5 `F81E3A2CD8FD98191AFC8CA423D9D31E` / SHA-256 `613A59CA359880366C0A256D93D2BBFCD84C4C20F128EB62CC936178E9AC10A0`（`fc /b` = no differences）
> 源码：`ra2render/blitter_hooks.cpp` 143,071 B / MD5 `36FD70EE5689D4C93FB6D26266CA6F6A` / **2,648 行**；`ra2render/ra2render.h` 22,386 B / MD5 `B8B9147A5B3BCAF67374B7AA13CDC0FC` / 356 行

---

## [META]

| 字段 | 值 |
|---|---|
| task | FOG-MODE（父 agent id `session-852a2193-df41-4859-b6f3-cd17f595410f` 的子代理；本任务以 FOG-MODE 作语义标识） |
| executor | DSH 子代理 |
| mode | accept-edits（仅在写作用域内） |
| scope_declared | 允许写 `ra2render/**`、`ra2youli/ra2render.{dll,ini}`、新建 `docs/re/fog_visibility_mode_report.md`、`out/re_work/fog_mode/**`；另按 **F7 明文要求**就地订正 `docs/re/fog_split_report.md`（§E3）、`docs/re/visibility_gap_spysat.md:93`、`ra2render/ra2render.h:147-153`（**保留原记**） |
| 快照时点 | 开工时 `blitter_hooks.cpp` = 132,852 B / MD5 `CB4D5E72888B08B2494C99787906EC22`；`ra2render.h` = 19,737 B；两份 ini = 9,459 B / SHA-256 `8D289390…`；DLL = 138,752 B / MD5 `59671E8B…`（与任务卡一致）。本会话内未见他人并发写入本任务文件 |
| 禁止事项遵守 | **未启动游戏、未注入、未改 exe、未伪造实测**（全部真机项一律 [待实测]，交 ZCode） |
| 产物级验收 | 反汇编取证 + claims 双文件（DLL 26/26 OK、引擎 5/5 OK），见 §[6] 与附录 B |

---

## [0] 结论摘要

1. **F1 已落地**：新增 `[FogOfWar] VisibilityMode = starcraft | vanilla`（默认 **starcraft** = 现状）。`vanilla` ⇒ **不做任何视距剔除**：`UnitClass/InfantryClass/AircraftClass/BuildingClass/BulletClass` 五个 `Draw` 钩子的**第一条分支**即短路放行到原版 Draw（产物 RVA 见附录 B），敌方单位/建筑/弹道在任何区域（含灰雾区、未探索黑区）都会绘制。
2. **优先级与零副作用**：`vanilla` 时三子键 `EnableUnitFog/EnableBuildingFog/EnableBulletFog` **被覆盖（忽略）**，启动日志与遥测行逐键标注「被 VisibilityMode 覆盖 -> 放行(不剔除)」；短路支位置在 `ShouldDraw*` 判定**之前** ⇒ `vanilla` 档三处剔除计数**结构性恒 0**（F4 机器判据），且该支**零引擎写入、不读视野网格、不调用 `ShouldDraw*`**（不改 RNG / 命令序）。
3. **日志/遥测（F3/F4）**：新增启动行 `[ra2render-visibility]`（`VisibilityMode` 生效值 + 来源 ini/默认值 + 三子键生效值 + 覆盖标注 + 非法值收敛告警）与 2 秒行 `[ra2render-telemetry-visibility]`（三处剔除计数 + 「被 mode 覆盖而放行」独立计数）；**既有行（`[ra2render]`/`[ra2render-fog]`/`-telemetry`/`-fogswitch`/`-fogsplit`/`-radar`）字段与顺序零变化**。
4. **既有键默认值零变化（F5）**：新旧 ini 键值集合对比 = **新增 1 键、删除 0 键、值变化 0 键**（总闸 1 / 三子键 1 / 小地图 0 / 灰化档 3 / 渐变 1 全保持）。产物 140,800 B 已部署到 `ra2youli/`，两份 ini 逐字节一致。
5. **F8（只诊断，未改行为）**：以 ZC-5 两档截图像素级复算 —— 「顶行近黑雾带」在**比值口径下不是顶行特异的格状态判定问题**（顶行带 0.329 ≈ 全雾区中位 0.325，且顶行带绝对亮度反而更高）；真实可量化偏差是**雾区整体压暗倍数 ≈ 1/3**，而同批截图里**引擎原生 50% 减暗（小地图通道）实测 0.494** ⇒ 显示链路线性 ⇒ 主视图雾区比设计口径（强度 256 = 50%）**深约 1.5×**（新发现，未定谳，见附录 D）。
6. **门禁全绿**：`verify_anchors.py` **323/323 PASS**；`audit_bytes.py` 产物侧 **26/26 OK**、引擎侧 **5/5 OK**。**最大风险**：真机 A/B 未跑（本任务禁止启动游戏/注入），判据交 ZCode（附录 C）。

---

## [1] 逐条必答项结论表

| # | 问题 | 结论 | 证据等级 | 证据锚点 |
|---|---|---|---|---|
| F1-1 | 是否新增 `VisibilityMode = starcraft \| vanilla`（默认 starcraft）？ | **是**。字符串键走 `GetIniStringEx`（哨兵默认值口径 ⇒ 可区分「键缺失」与「键值=默认」）；缺省 = `starcraft`；未知值/空值**收敛为 starcraft** 并打告警行 | [实证] | 源码 `blitter_hooks.cpp:348-360`（解析）、`:397-416`（日志）；产物：默认串 `starcraft` @ VA `0x10022018`、全局 `g_visibilityVanilla` @ VA `0x10022996`（初值 `00`）；claims `0x422018` / `0x422996` |
| F1-2 | `vanilla` 是否「不做任何视距剔除」（三处剔除全放行）？ | **是**。5 个 Draw 钩子各有独立短路支：`Aircraft(0x1A0E)` / `Building(0x203E)` / `Bullet(0x20AE)` / `Infantry(0x245E)` / `Unit(0x2763)`，全部 `call FogModeVanillaPassThrough`（入口 RVA `0x1850`）后直接调用原版 `g_pOrig*Draw` | [实证] | 产物 RVA `0x1A0E/0x203E/0x20AE/0x245E/0x2763`（push 0/1/2 + call `0x10001850`）；claims_dll 15 条；反汇编原文见 `out/re_work/fog_mode/evidence/F6_prod_visibility_mode.txt` |
| F1-3 | 门控是否运行期判定？ | **是**。热路径每帧直读 `g_visibilityVanilla`（5 处 `cmp byte ptr [0x10022996],0`），**恰好 5 处**运行期读取点、与 5 个短路支一一对应；运行期置位全局 ⇒ ≤1 帧生效（ini 本身仍只在 `LoadConfig` 读一次 ⇒ 改 ini 需重启，与既有键同口径） | [实证] | 产物：`cmp byte [0x10022996],0` 站点 `0x1A00/0x2030/0x20A0/0x2450/0x2758`（全库恰 5 处）；claims_dll 5 条 |
| F1-4 | `vanilla` 是否零引擎状态写入、不改 RNG/命令序？ | **是（就本模式自身而言）**。短路支只自增我方私有计数（4 个 `inc dword ptr [.data]`）+ 直接调用原版 Draw；**不调用 `ShouldDraw*`**（故不读视野网格、不调 `UpdateVisionGrid`）、不写任何引擎全局。※ 诚实边界：`Hook_CellClass_Draw` 与 `UpdateVisionGrid` 的**既有**引擎写入（Scenario FogOfWar 位清零、SpySatActive 清零、间谍卫星类型改写）与 `VisibilityMode` **无关**，属总闸/小地图既有语义，本任务未改其触发条件 | [实证] | 产物 RVA `0x1850-0x187D`（函数体：仅 4 个 inc + 分支 + ret）；源码 `blitter_hooks.cpp:273-284`、`:2348-2351` 等 |
| F2-1 | 两种规范组合是否写清（含混搭观感）？ | **是**。[现状态] `EnableStarCraftFog=1 + VisibilityMode=starcraft`；[原版态] `EnableStarCraftFog=0 + VisibilityMode=vanilla`（未探索黑幕仍保留）；另说明两种混搭观感（「看得见但很暗」/「亮着的黑箱」） | [实证] | `ra2render/ra2render.ini` §[FogOfWar] FOG-MODE 注释块（第 60-84 行）；附录 A 摘录 |
| F3-1 | 启动日志是否打印 `VisibilityMode=…(来源: ini/默认值)` + 三子键生效值 + 覆盖标注？ | **是**。新增**独立行** `[ra2render-visibility]`：`VisibilityMode=%s (来源: %s) \| 生效: … \| 子键生效值(来源): …`（vanilla 档三键各带覆盖标注）；非法值另有 `[警告/红字]` 行 | [实证] | 源码 `blitter_hooks.cpp:397-416`；产物串 `.rdata` RVA `0x18D08` / `0x18E2F` |
| F3-2 | 是否破坏既有解析口径？ | **否**。既有行的**字段与顺序零变化**，新模式信息全部落在新增行；遥测同理新增 `[ra2render-telemetry-visibility]` | [实证] | 源码改动仅新增 LogMessage 调用与注释；既有 6 条 LogMessage 格式串未改 |
| F4-1 | `vanilla` 时三处剔除计数是否恒 0？ | **是（结构性保证）**。短路支位于 `g_enableUnitFog && !ShouldDraw…` 判定**之前**并直接 `return`，故三处剔除计数在 vanilla 档不可能自增 | [实证] | 产物：`Aircraft 0x1A00-0x1A35` / `Building 0x2030-0x2057` / `Bullet 0x20A0-0x20C7` / `Infantry 0x2450-0x2485` / `Unit 0x2758-0x278A`（短路支均 `je` 跳过剔除判定） |
| F4-2 | 是否把「被 mode 覆盖而放行」单独计数？ | **是**。4 个新计数：`s_visVanillaPassed`（合计）/`…Mobile`/`…Building`/`…Bullet`，逐钩子分类；2 秒行打印之（含机器判据文字） | [实证] | 产物 `inc dword ptr [0x102E2AAC/AB0/AB4/AB8]` @ RVA `0x1850/0x185E/0x186C/0x1875`；claims_dll 4 条 |
| F5-1 | 编译/备份/部署是否完成？ | **是**。`cmd /c build.bat` = `ALL BUILDS FINISHED SUCCESSFULLY`（loader 部署按 default 跳过）；旧 DLL/旧 ini 已备份；新 DLL 由 build.bat 部署 + 手工同步 ini | [实证] | §[6] 门禁原文；`fc /b` 两处 `no differences` |
| F5-2 | 既有键默认值是否未改？ | **是**。键值集合对比：新增 1 键、删除 0、**值变化 0** | [实证] | `out/re_work/fog_mode/ini_regression.txt` |
| F6-1 | ①「被 mode 覆盖而放行」短路分支存在且可达？ | **是**。函数体 `FogModeVanillaPassThrough`（RVA `0x1850`：4 个计数 inc + 3 出口 `mov al,1; ret`）+ **5 个可达调用点**，每点前有 `cmp byte [g_visibilityVanilla],0` | [实证] | 附录 B；claims_dll `0x401850/0x401856/0x40185E/0x40186C/0x401875` + 5×（cmp + push/call） |
| F6-2 | ② 新日志/遥测串存在？ | **是**。`.rdata` 明文：`[ra2render-visibility] VisibilityMode=`（RVA `0x18D08`）、`[ra2render-telemetry-visibility] VisibilityMode=`（RVA `0x19808`）、`VisibilityMode 取值`（`0x18E2F`）、`被 VisibilityMode 覆盖`（`0x18C36`）；代码引用点 RVA `0x1722/0x3A4C/0x3A8D` 等 | [实证] | 附录 B；claims_dll 4 条串锚点 |
| F6-3 | ③ 既有挂钩点未变？ | **是**。引擎侧 5 个挂钩点原始字节逐字节比对一致（`0x655D38` 9B / `0x655D87` 7B / `0x65719A` 5B / `0x4801F0` 15B / `0x6F8DF0` 15B）；DLL 安装器里对上述 5 个地址的 `imm32` 引用仍在（各 5-6 处） | [实证] | `claims_exe.txt` 5/5 OK；claims_dll `0x402C01/0x402D48/0x402CEA/0x40286C/0x402FB7` |
| F7-1 | 三处勘误是否就地订正（保留原记）？ | **是（3/3）**。`ra2render.h:147-153`、`docs/re/fog_split_report.md` §E3（追加 E3·就地订正行）、`docs/re/visibility_gap_spysat.md:93` | [实证] | §[3] 勘误清单 |
| F8-1 | 顶行近黑雾带是「强度边界」还是「顶行格状态判定」？ | **静态定位：偏「强度边界（强度口径）」**。ZC-5 两档截图复算：顶行带比值 0.329 vs 上段 0.326 / 中段 0.315 / 全雾区 0.325（**同值**），直视对照区 1.000；**顶行带绝对亮度反而更高**（S1 中位 L=35 vs 中段 11）⇒ 无顶行特异强度异常。可量化真实偏差 = **全雾区压暗倍数 ≈1/3**，而同批截图里**引擎原生 50% 减暗（小地图通道）实测 0.494** ⇒ 显示链路线性 ⇒ 主视图雾区比设计 256(=50%) 深约 1.5×（**新发现，未定谳；本轮零行为改动**） | [推演]（量化部分 [实证]） | 附录 D；脚本 `zc5_topband_ratio.py`/`zc5_transfer_fn.py`/`f8_minimap_probe.py` |

---

## [2] 关键证据块

### 2.1 引擎侧（只读基线，`claims_exe.txt` 5/5 OK）

~~~
0x655D38 = 89 44 24 28 A1 50 35 B7 00                     # H1 Plot_Cell 9B 补丁点（未变）
0x655D87 = 8B 47 04 89 6C 24 14                           # H3 原生减暗 7B 补丁点（未变）
0x65719A = E8 91 93 00 00                                 # H2 跳帧判定 5B 补丁点（未变）
0x4801F0 = 53 55 56 8B F1 8B 0D 24 73 88 00 57 8D 7E 24   # CellClass::Draw inline hook（未变）
0x6F8DF0 = 83 EC 5C 8B 15 34 EC A8 00 53 55 56 57 33 FF   # Greatest_Threat inline hook（未变）
~~~

### 2.2 产物侧：vanilla 短路支函数体（RVA 0x1850 / VA 0x10001850）

~~~
RVA 001850  FF 05 AC 2A 2E 10   inc dword ptr [0x102E2AAC]   ; s_visVanillaPassed++
RVA 001856  8B 44 24 04         mov eax, dword ptr [esp+4]   ; kind 参数
RVA 00185A  85 C0               test eax, eax
RVA 00185C  75 09               jne 0x10001867
RVA 00185E  FF 05 B0 2A 2E 10   inc dword ptr [0x102E2AB0]   ; s_visVanillaMobilePassed++
RVA 001864  B0 01               mov al, 1
RVA 001866  C3                  ret
RVA 001867  83 F8 01            cmp eax, 1
RVA 00186A  75 09               jne 0x10001875
RVA 00186C  FF 05 B4 2A 2E 10   inc dword ptr [0x102E2AB4]   ; s_visVanillaBuildingPassed++
RVA 001872  8A C0               mov al, al
RVA 001874  C3                  ret
RVA 001875  FF 05 B8 2A 2E 10   inc dword ptr [0x102E2AB8]   ; s_visVanillaBulletPassed++
RVA 00187B  B0 01               mov al, 1
RVA 00187D  C3                  ret
~~~

### 2.3 产物侧：5 个短路支（= 5 个 Draw 钩子的第一条分支）

| 钩子 | 入口 RVA | 短路支 call RVA | kind | 要点 |
|---|---|---|---|---|
| `AircraftClass::Draw` | `0x1A00` | `0x1A0E` | 0 | `cmp byte [0x10022996],0` / `push esi` / `mov esi,ecx` / `je 0x1A35` / `push 0` / `call 0x10001850` / `test al,al` / `je 0x1A35` / `add [0x100229B8],1`（渲染单位++） |
| `BuildingClass::Draw` | `0x2030` | `0x203E` | 1 | 同构，`push 1` |
| `BulletClass::Draw` | `0x20A0` | `0x20AE` | 2 | 同构，`push 2` |
| `InfantryClass::Draw` | `0x2450` | `0x245E` | 0 | 同构，`push 0` |
| `UnitClass::Draw` | `0x2750` | `0x2763` | 0 | 入口先 `call 0x100014E0`（CheckTelemetry，与源码一致），随后 `cmp byte [0x10022996],0` @ `0x2758` / `je 0x278A` / `push 0` / `call 0x10001850` |

> 定名依据：在 InstallVTableHooks 的 inline 展开里，`push <hookAddr>` 后 0x18 字节内即 `push <vtableAddr>`；5 组配对得 `0x1A00→0x007E23B8(Aircraft)`、`0x2030→0x007E3FD0(Building)`、`0x20A0→0x007E47F8(Bullet)`、`0x2450→0x007EB16C(Infantry)`、`0x2750→0x007F5D84(Unit)`（脚本 `f6_map2.py`）。

### 2.4 产物侧：新全局与新串

| 项 | 真实 VA（RVA） | 初值/明文 | 说明 |
|---|---|---|---|
| `g_visibilityVanilla` | `0x10022996`（`0x22996`） | `00` | 默认 `false` = starcraft；全 DLL **仅 5 处**运行期读取（= 5 个短路支） |
| `g_visibilityModeRaw` | `0x10022018`（`0x22018`） | `"starcraft"` | ini 原始串（日志用） |
| 4 个新计数 | `0x102E2AAC/AB0/AB4/AB8` | `0` | 位于 `.data` 段虚拟尾（无文件数据，故不作为字节 claim，只 claim 引用它们的指令） |
| 启动行串 | `.rdata` RVA `0x18D08` | `[ra2render-visibility] VisibilityMode=%s …` | 代码引用 `push imm32` @ RVA `0x3A4C` |
| 告警串 | `.rdata` RVA `0x18E2F` | `VisibilityMode 取值 "%s" 不合法…` | `push imm32` @ RVA `0x3A8D` |
| 覆盖标注串 | `.rdata` RVA `0x18C36` | `…被 VisibilityMode 覆盖…` | 三子键标注 |
| 遥测行串 | `.rdata` RVA `0x19808` | `[ra2render-telemetry-visibility] VisibilityMode=%s …` | `push imm32` @ RVA `0x1722` |

### 2.5 机器可读断言

* `out/re_work/fog_mode/claims_dll.txt`（**26 条**，以 `0x400000+RVA` 书写）→ `audit_bytes.py --exe ra2youli/ra2render.dll`：**26 OK / 0 MISMATCH / 0 NOREAD**
* `out/re_work/fog_mode/claims_exe.txt`（**5 条**，引擎侧挂钩点）→ `audit_bytes.py`：**5 OK**
* 口径说明：DLL 真实 ImageBase = `0x10000000`；`audit_bytes.py` 的 `IMAGE_BASE` 常量为 `0x400000`（段映射口径），故 DLL 断言按其要求写作 `0x400000+RVA`（例：真实 VA `0x10001850` ⇒ claim `0x401850`）。Lead 可直接原样复跑。

---

## [3] 勘误（逐条；**保留原文 + 【原记】**）

| # | 目标文件:行 | 改前原文 | 改后文本 | 理由 | 影响面 |
|---|---|---|---|---|---|
| **E1** | `ra2render/ra2render.h:147-153`（宏 `OFF_CELL_FLAGS` 注释） | 「`+0x12C` 是 CopyFlags…其 `0x08 = cf2_NoShadow`、`0x02 = cf2_ContainsBuilding`（`ref/yrpp/GeneralDefinitions.h:557-560`）；『已探索』位 `cf_Explored = 0x08` 在 `+0x140 = CellClass::Flags`…旧注释『bit3 = 已探索』**已证伪**」 | 「**本偏移的 bit3(0x08) = `cf_Explored`（已探索）**，原始注释『bit3 = 已探索』是对的」+ 读写双向字节锚点（读 `0x005863F2 F6 81 2C 01 00 00 08 test byte ptr [ecx+0x12C],8`；写 `0x004A98E6` / `0x004A98EC or al,8` / `0x004A98F0`），原文整段以 **【原记（FOG-SPLIT 勘误 E3，★已作废，勿再引用）】** 保留 | UNIT-VIS 以二进制读写双向证据反向证伪了 FOG-SPLIT 的「证伪」；`cf2_NoShadow` 属另一族命名，不能据以否证 | 纯注释 ⇒ **零行为影响**（本版钩子仍用引擎口径 `Shroudedness(+0x120)==-2`）；影响后续任何以 `+0x12C/+0x140` 判「已探索」的实现 |
| **E2** | `docs/re/fog_split_report.md` §[3] 表（E3 行之后**追加**一行 `E3·就地订正`） | §E3 行原文完整保留在上一行 | 新增「E3·就地订正（[FOG-MODE F7①]，保留原记）」行：【原记】+ 新结论 + 双向字节锚点 + 明确 §E4 中「原实现的 `CopyFlags & 0x08` 位与『已探索』**无**对应关系」一句**同并更正**（该位就是「已探索」，改判据只为贴引擎口径，并非原判据错位） | 同 E1 | 文档级；对 `fog_split_report.md` 的行为结论无影响 |
| **E3** | `docs/re/visibility_gap_spysat.md:93` | `004680DC  jne 0x468422            ; 黑雾 → 不画（原版行为）` | 同址保留 **【原记】** 原文，追加更正：「黑雾 → 不画（**原版预留门**：谓词 `0x005865E0` 为**恒假 stub**，字节 `32 C0 C2 04 00` = `xor al,al; ret 4` ⇒ 本分支**永不生效**）」，并注明证据（UNIT-VIS 实测字节 + 全 exe 25 处调用点，含本处 `0x4680D5`）与出处 | 原表述把「预留但恒不生效的门」当成原版行为，直接影响「原版是否隐藏雾中弹道/单位」的产品判断 | 文档级；可能需同步 `bullet_particle_fog_deep_dive.md` / `fx_draw_chain.md:158`（**不在本任务作用域，交 Lead**） |

---

## [4] 未闭环清单

| # | 缺口 | 为何无法静态闭环 | 下一步取证方法（可直接执行） | 阻塞级别 |
|---|---|---|---|---|
| U1 | `vanilla` 档真机判据（原版档：灰雾区与未探索黑区都能看见敌单位/建筑/弹道；三处剔除计数 ≡0） | 本任务**明令禁止启动游戏/注入** | 按附录 C 交 ZCode 执行（3 张截图 + 两档日志 + sha256） | **P0（验收）** |
| U2 | `starcraft` 档回归（剔除计数 >0、与旧件同量级、无崩溃） | 同上 | 附录 C 现状档步骤 | **P0（验收）** |
| U3 | 混搭组合（灰雾开 + vanilla / 灰雾关 + starcraft）观感 | 属主观观感 + 需真机 | 附录 C 可选 A/B（每档 ≥10s + 1 张截图） | P2 |
| U4 | 雾区压暗倍数 ≈1/3（设计口径 256 = 50%）的**第二重压暗来源** | 需运行期计数/像素探针；静态分支已穷举（我方 1 次调用 + 引擎路径需运行期判定位） | 下一轮加「每格压暗应用次数」探针 + 纯白底单点取色（附录 D §D.4） | **P1（新发现）** |
| U5 | `vanilla` 档 `CheckTelemetry` 是否仍每帧到（只有 Unit 钩子调用它） | 属频率/性能观测，不影响行为 | `vanilla` 档跑 ≥30s，确认遥测行仍每 2 秒出现 | P2 |
| U6 | 联机（MpActive）侧可见性模式纪律 | 单机环境不便构造联机会话（任务卡许可跳过） | 若未来放开联机，需双端对拍确认各端同为 vanilla | P1（仅当放开联机） |

---

## [5] 写作用域合规声明

**改动文件清单**（路径 + 字节数；时间为沙箱本地时间）：

| 文件 | 操作 | 结果 | 时间 |
|---|---|---|---|
| `ra2render/blitter_hooks.cpp` | 编辑（新增 FOG-MODE 全局/短路支/日志/遥测/注释） | 132,852 B → **143,071 B** / 2,648 行 / MD5 `36FD70EE…` | 17:15 |
| `ra2render/ra2render.h` | 编辑（F7① 勘误注释 + 新全局 extern） | 19,737 B → **22,386 B** / 356 行 / MD5 `B8B9147A…` | 17:16 |
| `ra2render/ra2render.ini` | 编辑（新增 `VisibilityMode=starcraft` + FOG-MODE 注释块；**既有键值零变化**） | 9,459 B → **12,242 B** / 135 行 | 17:16 |
| `ra2render/ra2render.dll` | 重编译 | 138,752 B → **140,800 B** / MD5 `455651B1…` | 17:16 |
| `ra2youli/ra2render.dll` | 部署（build.bat） | **140,800 B**（与仓内件 `fc /b` 一致） | 17:16 |
| `ra2youli/ra2render.ini` | 部署（手工同步） | **12,242 B**（与仓内件 `fc /b` 一致） | 17:16 |
| `docs/re/fog_visibility_mode_report.md` | **新建**（本报告） | 见 §[8] | 17:2x |
| `docs/re/fog_split_report.md` | 勘误（§E3 后追加 `E3·就地订正` 行，原记保留） | 52,122 B → 53,518 B | 17:21 |
| `docs/re/visibility_gap_spysat.md` | 勘误（`:93` 保留原记 + 追加更正） | 44,049 B → 44,665 B | 17:22 |
| `out/re_work/fog_mode/**` | 新建（备份/脚本/证据/claims/门禁输出） | 见 §[8] | 17:0x–17:2x |

**未触碰清单**：`ra2youli/gamemd.exe`（**只读**：MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367` / 4,825,360 B，开工=收工一致）、任何 `.mix/.map/.sav`、`ra2forge/**`、`mcp/**`、`ra2opt/**`、台账（`REVERSE_ENGINEERING_AND_PATCHES.md`）、`docs/RE_COORDINATION.md`、除 §[3] 三处勘误外的其他 `docs/**`、`ra2youli/ra2loader.exe`（build.bat 默认不部署 loader，输出已确认 `skip ra2loader.exe deploy (default)`）。

**哈希证据**：`gamemd.exe` MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`（收工复算一致）；旧 DLL = 任务卡给定 `59671E8BC333A999820C788D76A5B375`（已备份留档）。

---

## [6] 门禁实跑输出（原文粘贴）

### 6.1 `python tools\verify_anchors.py`

~~~
回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！
~~~

（完整输出 `out/re_work/fog_mode/gate_verify_anchors.txt`；基线完整性审计三行亦全 PASS：`.text` 原始段哈希 `c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738`、PE 头特征 `RA2OPT_PERF_APPLIED`、`.detour` 原生签名。）

### 6.2 `python tools\audit_bytes.py out/re_work/fog_mode/claims_dll.txt --exe ra2youli\ra2render.dll`

~~~
合计 26 条：OK=26  MISMATCH/NOREAD=0
~~~

（逐条输出全文：`out/re_work/fog_mode/gate_audit_dll.txt`）

### 6.3 `python tools\audit_bytes.py out/re_work/fog_mode/claims_exe.txt`

~~~
合计 5 条：OK=5  MISMATCH/NOREAD=0
~~~

（全文：`out/re_work/fog_mode/gate_audit_exe.txt`）

### 6.4 构建与部署实跑

~~~
Building ra2render.dll...  dllmain.cpp  blitter_hooks.cpp  正在生成代码...
Building ra2loader.exe...  ra2loader.cpp
        1 file(s) copied.
[build.bat] skip ra2loader.exe deploy (default). Set RA2RENDER_DEPLOY_LOADER=1 to deploy it.
ALL BUILDS FINISHED SUCCESSFULLY
---
Comparing files RA2RENDER\ra2render.ini and RA2YOULI\RA2RENDER.INI
FC: no differences encountered          (exit 0)
Comparing files RA2RENDER\ra2render.dll and RA2YOULI\RA2RENDER.DLL
FC: no differences encountered          (exit 0)
~~~

---

## [7] 风险与红线提示

| 维度 | 是否触及 | 说明 |
|---|---|---|
| ①同步语义/命令序 | **否（静态判定）** | `vanilla` 短路支只自增我方私有计数并直调原版 Draw；不进 `ShouldDraw*`（不读视野网格、不调 `UpdateVisionGrid`）；不改任何引擎全局、不发命令、不改单位状态。**但**本键改变的是「谁可见」这一**玩法可见性**，联机各端配置不一致将造成观感不对称（非 desync：不改命令序/随机数）⇒ 若未来放开联机，**需要 MP 门控矩阵/真机对拍验收**。 |
| ②随机数消费序 | **否（静态判定）** | 短路支不调用任何随机数相关路径。 |
| ③存档结构 | **否** | 不改存档/对象结构；仅运行期布尔 + 私有计数。 |
| ④渲染像素等价性 | **否（相对旧件）** | `starcraft` 档（默认）走**与旧件完全相同的分支**（短路支仅多一次 `cmp`/条件不成立）；`vanilla` 档是**新增行为**（本任务目标）。旧件 `starcraft` 档与 FOG-SPLIT 旧件的逐像素等价性属 ZC-5 既有判据 D4，本任务未改该路径。 |
| 红线遵守 | — | 未改 `IsShrouded(0x487950)` / `IsCellShrouded(0x5865E0)` / `RevealArea*` 判定语义；未写 Scenario 状态（除既有 bit12=0 约定）；未改 `.detour` 段；未改 exe；未启动游戏/注入。 |

**明确声明**：本任务**未启动游戏、未注入、未改 exe**；所有真机观感/计数判据均标 [待实测] 并交 ZCode（附录 C）。

---

## [8] 交付物清单

| 类型 | 路径 | 规模 |
|---|---|---|
| 源码改动 | `ra2render/blitter_hooks.cpp`（+10,219 B / 2,648 行）、`ra2render/ra2render.h`（+2,649 B / 356 行） | 5 个短路支 + 1 个 noinline 放行函数 + 2 条新日志 + 4 个新计数 + 注释 |
| 配置 | `ra2render/ra2render.ini` ≡ `ra2youli/ra2render.ini`（12,242 B，新增 1 键） | 135 行 |
| 产物 | `ra2render/ra2render.dll` ≡ `ra2youli/ra2render.dll`（140,800 B / MD5 `455651B1…`） | 4 段 PE，`.text` RVA `0x1000` |
| 备份 | `out/re_work/fog_mode/ra2render.dll.bak-59671E8B`、`ra2render.ini.bak-2DEB8F3B`、`ra2render.ini.deployed-2DEB8F3B` | 138,752 B / 9,459 B / 9,459 B |
| 报告 | `docs/re/fog_visibility_mode_report.md`（本文件） | 见页脚行数 |
| claims | `out/re_work/fog_mode/claims_dll.txt`（26 条）、`claims_exe.txt`（5 条） | 31 条断言 |
| 门禁输出 | `gate_verify_anchors.txt`、`gate_audit_dll.txt`、`gate_audit_exe.txt`、`ini_regression.txt` | 4 份原文 |
| 证据 | `out/re_work/fog_mode/evidence/F6_prod_visibility_mode.txt`、`F6_prod_vanilla_shortcircuit.txt`、`F6_prod_summary.txt`、`F6_gen_out.txt`、`F8_*` | 5+ 份 |
| 复算脚本 | `snapshot_baseline.py`、`f6_discover.py`、`f6_callers.py`、`f6_inc_sites.py`、`f6_map.py`、`f6_map2.py`、`f6_final.py`、`ini_regression.py`、`zc5_topband_measure.py`、`zc5_topband_ratio.py`、`zc5_transfer_fn.py`、`f8_minimap_probe.py`、`f8_engine_dump.py`、`final_hashes.py` | 14 个 |

---

## [9] 待裁决项

| # | 分叉 | 建议方案 | 理由 |
|---|---|---|---|
| D1 | 是否新增 `Preset=vanilla\|starcraft` 复合键？ | **暂不加**，保持「一个模式键 + 两个正交表现键（总闸）」 | 两键已能表达 F2 的两种规范组合；复合键引入第三层优先级，增大真机判据复杂度 |
| D2 | `vanilla` 时是否也放行**小地图**侧敌方点隐匿？ | **本版不放行**（本键只管主视图三处绘制剔除，与 F1 范围一致） | 小地图灰化是独立子系统（ZC-3 未验收）；混进来会破坏 F4「三计数恒 0」判据边界 |
| D3 | F8 的「1/3 压暗」（U4）是否单独立任务修？ | **建议立新任务（P1）**，先加探针定谳再改 | 与「关雾才现」是两个独立问题；未定谳前改强度会污染 ZC-5 已建立的亮度判据基线 |
| D4 | 「原版态」是否连引擎黑幕渲染路径（Scenario FogOfWar 位）也还原？ | **不建议**，保持位恒 0（SHROUD.SHP 全黑黑幕） | 用户裁决明确要求「未探索黑幕保留」；还原该位会让未探索区切到 FOG.SHP 出现既知劣化 |
| D5 | 三处勘误的同类表述回填（`bullet_particle_fog_deep_dive.md` / `fx_draw_chain.md:158` 等） | **交 Lead 处置** | 超出本任务写作用域（仅授权 §[3] 三处） |

---

# 附录 A · 两种状态的规范组合（F2）

| 档位 | `EnableStarCraftFog` | `VisibilityMode` | 观感/语义 |
|---|---|---|---|
| **[现状态]（ini 默认）** | `1` | `starcraft` | 灰雾压暗（已探索非直视档）+ 视距剔除（远方敌军不可见）；三子键各自生效 |
| **[原版态]** | `0` | `vanilla` | 无灰雾压暗 + 无视距剔除 = **原版可见性**（敌方单位/建筑/弹道在任何区域都会绘制）；**未探索黑幕仍保留**（引擎 `0x47EFE0` 路径，我方零介入） |
| 混搭 ① | `1` | `vanilla` | 灰雾照压暗，但雾里的敌人/建筑/弹道照常绘制 ⇒「看得见，但画面很暗」（战术上等于给我方开图，建议仅做 A/B 对照） |
| 混搭 ② | `0` | `starcraft` | 地图明亮（已探索区不压暗），但远处敌军仍按视距隐形 ⇒「亮着的黑箱」，敌方目标会「凭空出现」 |
| 非法值 | 任意 | 其它字符串 | 收敛为 `starcraft` 并打 `[ra2render-visibility] [警告/红字]` 行 |

启动日志行格式（vanilla 档示例）：

~~~
[ra2render-visibility] VisibilityMode=vanilla (来源: ini) | 生效: 原版可见性(不做任何视距剔除; 单位/建筑/弹道三处剔除全部放行) | 子键生效值(来源): EnableUnitFog=1(ini, 被 VisibilityMode 覆盖 -> 放行(不剔除)) EnableBuildingFog=1(ini, 被 VisibilityMode 覆盖 -> 放行(不剔除)) EnableBulletFog=1(ini, 被 VisibilityMode 覆盖 -> 放行(不剔除)) | [FOG-MODE] 优先级: vanilla 覆盖三子键（三子键配置被忽略） | 机器判据([ra2render-telemetry-visibility]): vanilla 档要求：机动单位剔除 ≡0 且 建筑剔除 ≡0 且 弹道剔除 ≡0 且 被 mode 覆盖而放行 >0
~~~

2 秒遥测行格式（vanilla 档示例）：

~~~
[ra2render-telemetry-visibility] VisibilityMode=vanilla(生效=vanilla(原版可见性/不做任何视距剔除)) | 三处剔除计数: 机动单位 0, 建筑 0, 弹道 0 | 被 mode 覆盖而放行: 合计 N (机动单位 N1, 建筑 N2, 弹道 N3) | 渲染单位 N4 | 判据: vanilla ⇒ 机动单位剔除≡0 且 建筑剔除≡0 且 弹道剔除≡0 且 被 mode 覆盖而放行>0
~~~

---

# 附录 B · 产物级证据（F6）

## B.1 断言索引表（`claims_dll.txt`，26 条，`0x400000+RVA`）

| # | claim VA | 真实 VA / RVA | 字节 | 含义 |
|---|---|---|---|---|
| 1 | `0x401850` | `0x10001850` / `0x1850` | `FF 05 AC 2A 2E 10` | 放行函数入口：`inc [s_visVanillaPassed]` |
| 2 | `0x401856` | /`0x1856` | `8B 44 24 04 85` | `mov eax,[esp+4]`（kind） |
| 3-5 | `0x40185E/0x40186C/0x401875` | /`0x185E,/0x186C,/0x1875` | `FF 05 …` | kind==0/1/2 ⇒ 机动单位/建筑/弹道放行计数 |
| 6-10 | `0x401A00/0x402030/0x4020A0/0x402450/0x402758` | /`0x1A00,/0x2030,/0x20A0,/0x2450,/0x2758` | `80 3D 96 29 02 10 00` | 5 个钩子各自的 `cmp byte [g_visibilityVanilla],0`（全库恰 5 处） |
| 11-15 | `0x401A0C/0x40203C/0x4020AC/0x40245C/0x402761` | /`0x1A0C,/0x203C,/0x20AC,/0x245C,/0x2761` | `6A 0k E8 rel32 83` | 5 个短路支：`push k; call FogModeVanillaPassThrough` |
| 16-19 | `0x418D08/0x419808/0x418E2F/0x418C36` | `.rdata` | 明文串 | 新启动行 / 新遥测行 / 非法值告警 / 覆盖标注 |
| 20-21 | `0x422018`（9B）、`0x422996`（1B） | `.data` | `"starcraft"` / `00` | `g_visibilityModeRaw` 初值 = 默认档；`g_visibilityVanilla` 初值 = 0 |
| 22-26 | `0x402C01/0x402D48/0x402CEA/0x40286C/0x402FB7` | `.text` | `B8/B9 imm32` | 既有挂钩点 `0x655D38/0x655D87/0x65719A/0x4801F0/0x6F8DF0` 在安装器中的 imm32 引用（未变） |

## B.2 与既有挂钩点的差异面（F6③）

* 引擎侧 5 个挂钩点原始字节**逐字节一致**（§[2] 2.1，claims_exe 5/5 OK）；`gamemd.exe` MD5 未变。
* DLL 侧：新增 FOG-MODE 代码**只**落在 5 个 Draw 钩子函数体（RVA `0x1A00`-`0x278A` 区段）与 1 个新函数（`0x1850`-`0x187D`）；`0x655D38`/`0x655D87`/`0x65719A`/`0x4801F0`/`0x6F8DF0`/`0x47EFE0`/`0x6D3D99` 等既有补丁点的安装代码与 imm32 引用**均未改动**（各 5-6 处引用仍在）。
* `starcraft` 档下 5 个钩子第一分支条件恒假 ⇒ 控制流与旧件相同（只多一条 `cmp`/`je`）。

---

# 附录 C · 给 ZCode 的真机判据（可直接执行）

> 前置：本任务**未启动游戏/未注入**；真机步骤由 ZCode 执行。每档开跑前备份 `ra2youli/ra2render.ini`，跑完还原并贴 `sha256`。
> 公共约定：日志取 `ra2youli/ra2render.log`；每档至少跑 ≥10 秒或到能覆盖「敌方单位进入视野」的阶段；截图沿用 ZC-5 取图流程。

## C.1 【原版档】`EnableStarCraftFog=0` + `VisibilityMode=vanilla`

| 判据 | 步骤 | 通过条件 |
|---|---|---|
| V1 | 开局 → 敌方单位/建筑在**灰雾区与未探索黑区**均可见 | **3 张截图**：① 己方基地附近 ② 灰雾区敌单位/建筑 ③ 未探索黑区敌目标；三张内目标均**可见** |
| V2 | 读 2 秒遥测行 `[ra2render-telemetry-visibility]` | `机动车剔除 = 0` **且** `建筑剔除 = 0` **且** `弹道剔除 = 0` **且** `被 mode 覆盖而放行 > 0`（多行持续 ≡0） |
| V3 | 读该档启动行 `[ra2render-visibility]` | `VisibilityMode=vanilla (来源: ini)`；三子键各带「被 VisibilityMode 覆盖 -> 放行(不剔除)」标注 |
| V4 | 未探索黑幕仍在 | 未探索区截图仍为**全黑**（对标 ZC-5 判据①：核矩形 median ≈ 0） |

## C.2 【现状档】`EnableStarCraftFog=1` + `VisibilityMode=starcraft`（默认）

| 判据 | 步骤 | 通过条件 |
|---|---|---|
| S1 | 灰雾区敌方单位 | 视距外敌单位**不可见**，进入视野圈即显现（与旧件一致） |
| S2 | 读 `[ra2render-telemetry-visibility]` | 三处剔除计数**按视野圈判定增长**（>0），`被 mode 覆盖而放行 ≡0` |
| S3 | 回归 | `[ra2render-telemetry-fogsplit]` / `-fogswitch` / `-telemetry` / `-radar` 各既有行**字段数与顺序与 ZC-5 快照一致**；`EnableMinimapFog` 等行为不变 |

## C.3 两档通用

1. **无崩溃**（无 `except.txt` 新增；进程存活 ≥ 判据时长）。
2. **启动日志生效值正确**：`VisibilityMode` 与 ini 实际一致（改键后重启再验一次，确认非缓存）。
3. **跑完还原 ini** 并贴：`Get-FileHash ra2youli/ra2render.ini -Algorithm SHA256`（原值 `613A59CA359880366C0A256D93D2BBFCD84C4C20F128EB62CC936178E9AC10A0`）。
4. **可选 A/B（P2）**：混搭 ①（灰雾开 + vanilla）与 ②（灰雾关 + starcraft）各 1 张截图，核对附录 A 的观感描述。

---

# 附录 D · F8 顶行近黑雾带：静态定位与量化（只诊断，未改行为）

## D.1 复算口径

* 素材：ZC-5 真机快照对（同场景、同镜头、同脚本时点）
  `out/re_work/zcode_live/zc5/evidence/s1_master1_final.png`（总闸=1）vs `s2_master0_final.png`（总闸=0）。
* 方法：逐像素比值 `r = L_s1 / L_s2`（仅取 S2 亮度 > 阈值的像素，规避两侧皆黑的未探索块与 UI）；另做「S2 值 → S1 中位值」的传递函数反解。
* 脚本：`zc5_topband_measure.py`（行带）、`zc5_topband_ratio.py`（比值直方图）、`zc5_transfer_fn.py`（传递函数）、`f8_minimap_probe.py`（对拍标尺）。

## D.2 量化结果

| 区域 | 样本 n | 逐像素比值中位 | 结论 |
|---|---|---|---|
| 顶行带 y0-40（x250-1000） | 24,581 | **0.329** | 与全雾区同值 |
| 上段 y40-160 | 66,636 | 0.326 | — |
| 中段 y160-400 | 38,145 | 0.315 | — |
| **雾区全 y0-400** | 129,362 | **0.325**（直方图众数区间 0.30-0.35 占 79.6%） | 全域一致 ⇒ **单一机制** |
| 直视区 y440-660（设计强度 0、不压暗） | 11,273 | **1.000** | 两档截图在非雾区**逐像素一致** ⇒ 无全局亮度差异 |
| **小地图框（引擎原生 50% 减暗通道）** | 6,511 | **0.494**（传递函数实测：S2 20-39 → 16.0 ≈ 16.5 = 半值） | **显示链路线性**：真实 50% 压暗在截图里就显示 0.5 |

**关键推论**：主视图雾区在显示口径下被压暗到未压暗档的 **≈1/3**（逐通道 R/G/B 斜率 `0.324/0.335/0.316`，`S1 ≈ S2/3` 在 8-223 全域拟合），而设计口径 `s_fogBlendStrength = 256` 的公式 `final = c - ((c - c50) * s >> 8)`（s=256 ⇒ **逐通道精确半减**，可在 565 空间代数证明）应为 0.5 ⇒ **实测比单次 50% 深约 1.5×**。〔**勘误 FOG-STRENGTH2 · 2026-09-28**：此处原写「等效一次 0.5 + 一次约 0.67」，**已精确化为**「**一次 ×0.71875（=184/256=23/32）**，**发生在地表侧、在我方 FOG 桩之前**；本桩自身仍为设计值 256 ≡ 精确 0.5」⇒ 合成 **0.359375 = 23/64 ≈ 1/3**；三通道逐样本拟合吻合率 **82.5%/74.9%/75.2%**（而「单次 0.5」仅 0.29%/0.14%/4.52%，被决定性否定）。校准应针对**第一段**而非本桩。详见 `docs/re/fog_strength_rootcause.md` 与 `[v1.8.21]`。〕同批截图里引擎自身 50% 减暗（小地图）恰为 0.494 ⇒ **排除「截图伽马」解释**。

## D.3 顶行 vs 全屏：结论

* **顶行特异性：不成立**。比值口径下顶行带与上/中/全域同值（0.329 / 0.326 / 0.315 / 0.325）；**绝对亮度**口径下顶行带反而更亮（S1 中位 L=35.2 vs 中段 11.3 vs 直视区 41.3）。
* 因此 ZC-5 报的「顶行近黑雾带」在现有快照中**不是顶行格状态判定/格判据故障**，而是：**① 该带底色本身偏深**（NW 深色水面/地形）× **② 全雾区压暗倍数偏深（≈1/3 而非 1/2）** 的叠加观感。
* 代码侧唯一「行相关」的静态候选项已排除：`Hook_CellClass_Draw` 的判定只用 `MapCoords(+0x24)` 与 `Shroudedness(+0x120)`，**无任何屏幕行/视口行相关量**（源码 `blitter_hooks.cpp:1430-1500`；产物主线 RVA `0x1FC8` 起，本次未改）。

## D.4 机制候选与判别实验（未定谳，**本轮零行为改动**）

| # | 候选机制 | 静态依据 | 若成立的表现 |
|---|---|---|---|
| C1 | 存在**第二重压暗**（引擎自身 `Draw_Fog 0x47F250` 调用点 `0x480278`/`0x480290` 在 Scenario `bit0x1000` 置位时可达；其落像素同样经过**我方 B1/B2 混色桩**，故会得到第二次半减） | 引擎 `0x480251 test dh,0x10` / `0x480266 movsx eax,al`（al = **Foggedness(+0x121)**，-2⇒0xF，-1⇒0x0）/ `0x480278 call 0x47F250`；我方 `UpdateVisionGrid` 只**每逻辑帧清一次** bit12 | 雾区应为 0.5×0.5 = 0.25（实测 0.32 ⇒ 需一次约 0.67 的二次压暗，或第二次应用为部分强度） |
| C2 | **黑幕边缘帧**（`Shroudedness 0..48`）叠加：该类格被我方判为「已探索非直视」而压暗 50%，同时引擎 `0x47EFE0` 用 SHROUD.SHP 的**部分帧**再压暗一次 | 我方计数 `s_shroudEdgeDraws`（0..48 档）两档都 >0（ZC-5：166→55,182） | 只影响边界带（窄），不足以解释全域 0.32 |
| C3 | 我方恒定 `frame = 15`（引擎对 -2 用的最暗帧）使每格雾贴图**满菱形覆盖**（消除稀疏/抖动） | 我方 `push 15`；遥测比值 `混色桩介入次数/半透明层绘制次数 = 218,996,470/259,310 ≈ 844.5 像素/次` ≈ 60×30 菱形面积（900） | 解释「全域均匀压暗」，但不解释 1/3 与 1/2 之差 |
| C4 | 截图链路非线性 | **已被 D.2 小地图标尺排除**（真 50% 实测 0.494） | — |

**判别实验（建议下一轮，3 个独立观察量）**：

1. **应用次数探针**：在 `Hook_CellClass_Draw` 压暗点加「每格每逻辑帧应用次数」计数（另计 `s_cellFogDrawnToken` 命中数）⇒ 若 >1 则 C1 成立；若 ≡1 则 1/3 必有另一条不进我方计数器的路径（可查 `s_fogBlendStubHits` 与 `s_fogLayerDraws` 增量比是否恒 ≈844）。
2. **强度标尺**：临时把强度改成 128（公式 ⇒ 0.75 压暗）跑 1 档 ⇒ 若观测比值从 0.32 变到 ≈0.48（=0.75×0.67）说明存在与强度无关的固定乘子；若变到 ≈0.24 说明是两次相乘（0.75×0.32）。
3. **纯白底单点**：对已知纯白地形（雪地/白建筑外框）取样比较 S1 像素：单次半减的 RGB565 展开期望值 **≈123/126/123**，1/3 期望 **≈82/84/82** —— 一次截图即可定谳。

## D.5 与产品的关系

* 本现象与「关雾后敌人靠近才现」（UNIT-VIS 定谳 = 我方剔除造成）是**两个独立问题**；FOG-MODE 的 `vanilla` 档解决后者，**不触碰**前者。
* 因此 D3 建议：**F8 的强度偏差另立任务**（先探针定谳，再决定是否把 256 下调为观感标定值或按底色自适应）；本轮**零行为改动**，以免污染 ZC-5 已建立的亮度判据基线。

---

> 收工复算：`ra2youli/gamemd.exe` MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`（未变，只读）；`ra2render/ra2render.dll` ≡ `ra2youli/ra2render.dll` MD5 `455651B1C44BC5D69AF8E88189499128`；两份 ini MD5 `F81E3A2CD8FD98191AFC8CA423D9D31E`（`fc /b` 一致）。
