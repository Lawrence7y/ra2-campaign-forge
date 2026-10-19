# FOG-SWITCH 交付报告 —— 把 `EnableStarCraftFog` 做成真正干净的「半透明黑」总闸

> 任务号：**FOG-SWITCH** ｜ 执行方：**DSH 子代理** ｜ 工作区：`D:\Project\ra2-campaign-forge`（Windows）
> 基线（只读）：`ra2youli\gamemd.exe` MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367` / SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`
> 交付产物：`ra2render/ra2render.dll` ≡ `ra2youli/ra2render.dll` = **135,680 B** / MD5 `491C25F9DE72E6A5EB3484E4CF154DA3` / SHA-256 `C0C357383FB2BCAF9306642B8D6B6C1A437D4C3B9B9789781E40122187B529BF`
> 旧件备份：`out/re_work/fog_switch/ra2render.dll.bak-961E4B6C`（134,144 B / MD5 `961E4B6C883E4D18C48B293CF5D53122`）、`ra2render.ini.bak-07321883`
> 两份 ini 同步后：7,001 B / SHA-256 `0DAD9A41B2032EB7E61910C5E7DE4234F72BD646313CFB96A0C4130307E4A8C0`（ra2render/ 与 ra2youli/ Compare-Object 无差异）

---

## [META]

| 字段 | 值 |
|---|---|
| task | FOG-SWITCH |
| executor | DSH 子代理（父 agent id `session-852a2193-df41-4859-b6f3-cd17f595410f` 的子代理；本任务以 FOG-SWITCH 作语义标识） |
| mode | accept-edits（写作用域内） |
| scope_declared | 允许写 `ra2render/**`、`ra2youli/ra2render.{dll,ini}`、`docs/re/fog_switch_report.md`、`out/re_work/fog_switch/**` |
| 快照时点 | 改动前 `blitter_hooks.cpp` = 106,676 B（2200 行）；改动后见 §[8]。源码/头/ini/DLL 均在本会话内改动，未见他人对本任务文件的并发写入 |

---

## [0] 结论摘要

1. **总闸已做成真正完整的门**：`EnableStarCraftFog=0` 时 ① 我们的 FOG.SHP 半透明层不绘制；② 混色桩 B1/B2（`0x0047F40F` / `0x0047F4AE`）直接跳过后继、**保持原像素**（既不落回引擎原版混色、也不做任何 50% 压暗）；③ 小地图完全不驱动引擎减暗判定位（`[esp+0x13]` 保持引擎自身判定）；④ L4 视口全量刷（`0x006D3D99`）恢复原版 `jge` 语义；⑤ 自绘灰化 / 跳帧强驱等其它服务「半透明黑」的路径全部不介入。
2. **不新增任何 ini 键**；总闸与 5 个子键默认值**一律未变**（1 / 1 / 1 / 1 / 0 / 3），ini 仅新增注释明确「表现层子键需总闸=1」「逻辑可见性子键不受总闸影响」。
3. **F1 关键新证据**：引擎自身也会调用 FOG.SHP 层（`0x00480278`/`0x00480290` 两条 call，受 Scenario FogOfWar 位门控），但**全 exe 的半透明压降落像素点只有 3 处**（`0x47F43D`、`0x47F4BB`、`0x47F4DE`），**全部位于 B1/B2 补丁区**，且混色循环签名全库仅 2 处 ⇒ 短路这两处即「彻底没有压暗」。
4. **三条短路点全部是运行期判定**（`cmp [总闸] / je`），可被产物级反汇编逐条确认，且**计数器位于短路之后**（关闸时无绘制也无计数）。
5. 自证门禁全绿：`verify_anchors.py` **323/323 PASS**、引擎侧 claims **28/28 OK**、产物侧 claims **36/36 OK**。最大风险：真机 A/B 与像素等价性未跑（本任务禁止启动游戏/注入），需 ZCode 按 §附录 B 验收。

---

## [1] 逐条必答项结论表

| # | 问题 | 结论 | 证据等级 | 证据锚点 |
|---|---|---|---|---|
| F1-1 | 我们的 FOG.SHP 绘制点 | `CellClass::Draw` inline hook（`0x004801F0` 5B E9）内**追加**调用 `Draw_Fog 0x0047F250`，仅一处：产物 VA `0x100020B4`（`B8 50 F2 47 00` / `FF D0`）；源码 `blitter_hooks.cpp:1282-1289`（改前行号） | [实证] | `0x004801F0` = `53 55 56 8B F1 8B 0D 24 73 88 00 57 8D 7E 24`；`0x0047F250` = `A0 C6 E7 89 00 83 EC 2C` |
| F1-2 | 两处混色桩 | B1 `0x0047F40F`（49B）、B2 `0x0047F4AE`（51B）；原版语义 = **FOG.SHP 逐像素 alpha 插值混色**（`8D 4C 11 81` = `lea ecx,[ecx+edx-0x7f]`），**不是** 50% 减法（见 §[3] 勘误 E1） | [实证] | claims_exe.txt 头部 49B/51B 原字节 |
| F1-3 | 两桩的落像素点（穷举） | 全 exe 仅 **3 处**：`0x47F43D` `66 89 08`（B1）、`0x47F4BB` `66 89 10` 与 `0x47F4DE` `66 89 08`（B2），全部在被补丁覆盖的字节区内 | [实证] | evidence/F1_drawfog_stores.txt |
| F1-4 | 混色签名唯一性 | 全 .text（1,394,120 条指令）混色签名 `0F 9E C2 4A 23 CA` 仅 2 处：`0x0047F437` / `0x0047F4D8` ⇒ 无第三条引擎压暗路径 | [实证] | evidence/F1_candidates.txt「模式搜索 A」 |
| F1-5 | L4 全量刷耦合 | 原版 `0x006D3D99` 6B `0F 8D 98 00 00 00` = `jge 0x6D3E37`（滚动量绝对值≥阈值才全量重绘）；旧补丁无条件 `jmp` 该目标，只为灰雾即时刷新 | [实证] | `0x006D3D99`/`0x006D3D9F`/`0x006D3E37` 字节 + F1_disasm.txt |
| F1-6 | mode-3 减暗驱动位 | `0x00655D87` 7B 后挂钩；驱动位 = `[esp+0x13]`（写 `0x655D7B`/`0x655D82`，消费 `0x655E7E`）；引擎自身判定 = `(hWnd!=0) && MapClass::IsLocationFogged(0x5864A0)` | [实证] | F1_disasm.txt 0x655D30 窗口 |
| F1-7 | 其它候选（先排除） | ① 引擎自身两条 `call 0x47F250`（`0x00480278`/`0x00480290`）仅在 `*(Scenario)&0x1000` 且 `Player+0x1F5==0` 时可达，门在 `0x00480251`（`F6 C6 10 74 3F`）；② `0x0047EFE0`（SHROUD.SHP/FOG.SHP 二选一）的 FOG 分支同为该位选择（`0x0047F01F` `F6 C5 10 74 0B`），其像素循环是**透明索引拷贝、无混色**（`8A 06 / 3B 05 B8 4E 7E 00 / 74 03 / 66 89 07`）⇒ 半透明压降可达点仍只有 B1/B2 | [实证] | evidence/F1_xref.txt（`0x0047F250` 仅 2 处引用，均在 CellClass::Draw 内） |
| F2-1 | 总闸完备（①–⑤） | ①✓②✓③✓④✓⑤✓（见 §2.3 映射表） | [实证] | 产物 VA `0x10001FC9`/`0x10002120`/`0x100021C0`/`0x100022C1`/`0x10002350`/`0x10002390` |
| F2-2 | 三条短路点在总闸判定之后 | 是。均为「先 cmp 总闸 → je 短路」，计数器在短路点之后 | [实证] | §2.3 与 §附录 C |
| F2-3 | 运行期立即生效 | C++ 热路径直读 `g_enableStarCraftFog`（VA `0x1002100B`）；汇编短路由镜像 `s_fogMasterGate`（VA `0x10021023`），在 `CheckTelemetry` 节拍同步（产物 `setne` @ RVA `0x13E8`/`0x14EF`/`0x34C3`）⇒ ≤1 帧生效；无任何路径在安装期固化 | [实证] 机制 / [待实测] 帧延迟观感 | §2.3、§附录 C |
| F3-1 | 启动日志一行 | 已加 `[ra2render-fog] 灰雾总闸: EnableStarCraftFog=… (来源, 生效) \| 子键生效值(来源): …` | [实证] | 产物字符串 RVA **`0x187F0`**（VA `0x100187F0`；引用点 RVA `0x15FE`）<br>【原记】RVA `0x18D28` —— **该锚点有误，见 §[3] E5** |
| F3-2 | 三计数并入 2 秒遥测 | 已加 `[ra2render-telemetry-fogswitch]` 行：半透明层绘制次数 / 混色桩介入次数 / 小地图减暗驱动次数（另打印汇编侧镜像值） | [实证] | 产物字符串 RVA `0x18E58`（引用点 RVA `0x162E`）；计数 VA `0x102E1A38`/`0x102E1A3C`/`0x102E1A40` |
| F3-3 | 关闸三计数恒 0 | 结构性成立：三计数各自只在总闸门同段的可达分支内自增（产物 RVA `0x20A3`、`0x212D`/`0x21CD`、`0x46E4`/`0x48F6`） | [实证] 静态 / [待实测] 真机读数 | §附录 C |
| F4-1 | 编译 | `cmd /c ra2render\build.bat` → `ALL BUILDS FINISHED SUCCESSFULLY`（无 error/warning） | [实证] | §[6] |
| F4-2 | 备份 / 部署 | 旧 DLL 备份至 out/re_work/fog_switch/；新件已部署 `ra2youli/`（与 `ra2render/` 同 MD5） | [实证] | §[0] |
| F4-3 | 两份 ini 同步 / 单 [Logic] | 已同步（SHA-256 相同、Compare-Object 无差异）；[Logic] 仍单一节；默认值零变化 | [实证] | §[5] |
| F4-4 | build.bat loader 可选 | 保持可选（默认 skip，未回退） | [实证] | §[6] 末三行 |
| F5-1 | 三条短路分支存在且可达 | 存在且可达；关闸出口目标逐条给出（`0x47F440`/`0x47F4E1`/`0x6D3D9F`/跳板） | [实证] | §附录 C.1–C.3 |
| F5-2 | 三个新遥测符号齐备 | obj 符号表 `_s_fogLayerDraws` / `_s_fogBlendStubHits` / `_s_radarDarkenDriven`（另 `_s_fogMasterGate`）；产物地址经「遥测字符串 push 链」交叉确认 | [实证] | F5_obj_symbols.txt + §附录 C.4 |
| F5-3 | 既有挂钩点未变 | `0x00655D38`(E9/9B)、`0x0065719A`(E8/5B)、`0x00655D87`(E9/7B) 补丁点与形状均未变（另 `0x004801F0`、`0x47F40F`、`0x47F4AE` 未变） | [实证] | F5_patch_bytes_construct.txt |
| F5-4 | 关闸不落回引擎原生 50% | 关闸出口 = `B9 40 F4 47 00; FF E1`（B1）/ `B9 E1 F4 47 00; FF E1`（B2）：无像素写、无 `0x7BEF`、无插值；且引擎 .text **全库 0 处** `and reg,0x7BEF` | [实证] | §附录 C.2 + F1_candidates.txt「模式搜索 B」 |
| F6 | 真机验收清单 | 已产出（A/B 单变量、三项判据、截图与像素口径） | [纸面规格] | §附录 B + out/re_work/fog_switch/ZCODE_ACCEPTANCE_FOG_SWITCH.md |

---

## [2] 关键证据块

### 2.1 F1：引擎侧「半透明黑」实现路径全清单

| 路径 | VA / 字节 | DLL 源码（改前行号） | 被谁调用（xref 证据） | 总闸=0 处置 |
|---|---|---|---|---|
| **P1 我们的 FOG.SHP 层** | `0x0047F250` `A0 C6 E7 89 00`；调用点产物 VA `0x100020B4`（`B8 50 F2 47 00` / `FF D0`） | `Hook_CellClass_Draw`（改前 :1218-1295） | 仅 `Hook_CellClass_Draw` | **短路点①**：整段不执行 |
| **P2 混色桩 B1** | `0x0047F40F`（49B；唯一落像素 `0x47F43D` `66 89 08`） | `Hook_FogBlendB1_Stub`（改前 :1326-1380） | `0x0047F250` 第 1 条像素循环（含我们的 P1 调用与引擎 `0x00480278`） | **短路点②**：直达 `0x47F440`，无像素写 |
| **P3 混色桩 B2** | `0x0047F4AE`（51B；落像素 `0x47F4BB`/`0x47F4DE`） | `Hook_FogBlendB2_Stub`（改前 :1382-1436） | 同上第 2 条循环 / 引擎 `0x00480290` | **短路点②**：直达 `0x47F4E1`，无像素写 |
| **P4 引擎自身两条 FOG.SHP 调用** | `0x00480278` `E8 D3 EF FF FF` / `0x00480290` `E8 BB EF FF FF`；门 `0x00480251` + `0x00480262`（`Player+0x1F5`） | 无（引擎原生；我方 `UpdateVisionGrid` 每逻辑帧执行 &= 0x1000 的按位清除（压制）） | 引擎 `CellClass::Draw` 自身 | 不主动关闭；其压降必经 P2/P3 ⇒ 无像素被改（见 §[4] U2） |
| **P5 L4 视口全量重绘** | `0x006D3D99` `0F 8D 98 00 00 00` | `Hook_L4FullRedraw_Stub`（新增 naked 桩；安装点改前 :1442-1510） | 引擎战术重绘路径（`0x6D3D80` 区） | **短路点④**：`pushfd/popfd` 还原 flags 后原样 `jge` |
| **P6 小地图 mode-3 减暗驱动** | `0x00655D87` 7B 区；驱动位 `[esp+0x13]` | `Hook_RadarNativeDecide_Proxy` + `RadarHook_NativeDecide`（改前 :1717-1817） | `RadarClass::Plot_Cell` 内部 | **短路点③**：je 直通跳板，不读不写 |
| **P7 小地图自绘灰化** | 我方 `setPixel`（`(c>>1)&0x7BEF`） | `RadarHook_SelfDrawn`（改前 :1645-1708） | `Hook_RadarPlot_Cell_Proxy`（`0x00655D38`） | 短路点③-补充：整段不执行（也不进入函数尾声 ⇒ 保留引擎红点循环） |
| **P8 小地图跳帧强驱** | `0x0065719A` `E8 91 93 00 00`（`call 0x660530`） | `Hook_RadarPending_Proxy`（改前 :1821-1836） | `0x656EC0` 主循环 | **短路点⑤**：逐位走原版逻辑 |
| **P9（排除）`0x47EFE0` 的 FOG 分支** | `0x0047EFE0`；选择位 `0x0047F01F`；像素循环 `8A 06 / 3B 05 B8 4E 7E 00 / 74 03 / 66 89 07`（透明索引拷贝，无混色） | 无（引擎原生） | 引擎 `CellClass::Draw`（`0x480223`） | 非「半透明」压降路径（无混色/无 alpha），同受 Scenario 位压制；见 §[4] U2 |

**xref 方法与证据文件**（均在 `out/re_work/fog_switch/evidence/`）：

* `F1_xref.txt`：抗非法字节线性反汇编扫描（1,394,120 条指令 / 66 处非法字节跳过）。结果：`0x0047F250` 仅 2 处引用（`0x00480278`、`0x00480290`，均在 CellClass::Draw 内）；`0x004801F0` 被 `0x6D3716`/`0x6D751A` 调用；`0x00655D38`、`0x006D3D99` 无静态引用（函数中部 / 条件跳转目标）；`0x00660530` 仅 `0x65719A` 一处调用。
* `F1_disasm.txt`：各关键窗口原始字节 + Capstone 反汇编原文。
* `F1_drawfog_stores.txt`：`0x47F250`（两路径，`ret 0xc` @ `0x47F47B` / `0x47F4FE`）全部 store 穷举 ⇒ 像素写只有 3 处。
* `F1_candidates.txt`：① `0x47EFE0` 全 624B 反汇编 ② 混色签名全库搜索（2 处）③ `0x7BEF` 掩码全库搜索（0 处）④ FOG.SHP / SHROUD.SHP 字符串（.data `0x81CE10` / `0x81CE18`）。
* `F1_flag_writers.txt`：Scenario FogOfWar 位读取点（`test ch,0x10` @ `0x47F01F`、`test dh,0x10` @ `0x480251`）与 `FogOfWar` 字符串（.data `0x83CF78`、printf 模板 `0x82C3D4`）。
* 取证脚本（可复跑）：`f1_paths.py`、`f1_xref.py`、`f1_candidates.py`、`f1_cellclass.py`、`f1_fogfn.py`、`f1_flagw.py`。

### 2.2 引擎侧决定性原始字节（机器可读断言见 `out/re_work/fog_switch/claims_exe.txt`，28 条全 OK）

```text
0x0047F40F = 66 8B 08 66 83 F9 7F 75 07 66 33 C9 8A CB EB 1E 8B 54 24 48 81 E1 FF FF 00 00
             81 E2 FF 00 00 00 8D 4C 11 81 33 D2 85 C9 0F 9E C2 4A 23 CA 66 89 08   # B1 原版 49B
0x0047F4AE = 66 8B 08 66 83 F9 7F 75 09 66 0F B6 D2 66 89 10 EB 21 8B 54 24 48 81 E1 FF FF
             00 00 81 E2 FF 00 00 00 8D 4C 11 81 33 D2 85 C9 0F 9E C2 4A 23 CA 66 89 08   # B2 原版 51B
0x0047F440 = 8B 15 A4 E8 87 00 8B 4A          # B1 后继（关闸目标；此点之前无像素写）
0x0047F4E1 = 83 C0 02 4F 75 BB 8B 4C          # B2 后继（关闸目标；此点之前无像素写）
0x0047F437 = 0F 9E C2 4A 23 CA                # 混色签名 #1（全 exe 仅 2 处）
0x0047F4D8 = 0F 9E C2 4A 23 CA                # 混色签名 #2
0x006D3D99 = 0F 8D 98 00 00 00                # 原版 jge 0x6D3E37
0x006D3D9F = 8B C6 99 33 C2 2B C2             # 原版 fallthrough
0x006D3E37 = C6 84 24 0C 01 00 00 01          # 全量重绘目标
0x0081CE10 = 46 4F 47 2E 53 48 50 00          # "FOG.SHP"
0x0081CE18 = 53 48 52 4F 55 44 2E 53 48 50 00 # "SHROUD.SHP"
0x00480251 = F6 C6 10 74 3F                   # CellClass::Draw 内 FogOfWar 位门（==0 ⇒ 不走 0x47F250）
0x00480278 = E8 D3 EF FF FF                   # 引擎自身 call 0x47F250（仅 FogOfWar=1 可达）
0x00480290 = E8 BB EF FF FF                   # 同上（第二条）
0x00655D38 = 89 44 24 28 A1 50 35 B7 00       # H1 挂钩点 9B
0x00655D87 = 8B 47 04 89 6C 24 14             # H3 挂钩点 7B
0x0065719A = E8 91 93 00 00                   # H2 挂钩点（call 0x660530）
```

### 2.3 F2：总闸实现映射（短路点 ↔ 判据 ↔ 产物地址 ↔ 计数）

| 需求 | 实现位置 | 判定形态（产物可验证） | 计数（关闸恒 0） |
|---|---|---|---|
| ① 不绘制我们的 FOG.SHP 层 | `Hook_CellClass_Draw`（原版调用之后） | `VA 0x10001FC9: 80 3D 0B 10 02 10 00`（cmp [g_enableStarCraftFog],0）→ `0F 84 …`（je 函数尾声 `0x100020E6`） | `s_fogLayerDraws`(0x102E1A38)：`inc` @ VA `0x100020A3`（门后、调 0x47F250 前） |
| ② 混色桩不介入（且不落回 50%） | `Hook_FogBlendB1_Stub` / `Hook_FogBlendB2_Stub` | B1：`VA 0x10002120` cmp → `je 0x100021B1`；出口 `B9 40 F4 47 00; FF E1`（→0x47F440）。B2：`VA 0x100021C0` → `je 0x10002251`；出口 `B9 E1 F4 47 00; FF E1`（→0x47F4E1） | `s_fogBlendStubHits`(0x102E1A3C)：inc @ VA `0x1000212D` / `0x100021CD`（仅开闸路径） |
| ③ 小地图不驱动引擎减暗 | `Hook_RadarNativeDecide_Proxy`（汇编短路）+ `RadarHook_NativeDecide`/`RadarHook_SelfDrawn`（C++ 兜底） | `VA 0x10002350` cmp → `je 0x10002382`（= `jmp [s_pRadarNativeTrampoline]` 直通跳板）；C++ 侧 `VA 0x10004623`/`0x10004769` cmp | `s_radarDarkenDriven`(0x102E1A40)：inc @ VA `0x100046E4`（紧随 `if(ours)`，其下一条即 `*pFlag=ours`）、`0x100048F6`（自绘档） |
| ④ L4 不再因灰雾触发 | `Hook_L4FullRedraw_Stub`（新 naked 桩；`0x006D3D99` 补丁改指桩入口） | `VA 0x100022C1` cmp → `je 0x100022D2`；开闸 `popfd; mov ecx,0x6D3E37; jmp ecx`；关闸 `popfd; jge 0x100022DC; mov ecx,0x6D3D9F; jmp ecx` | —（可观测判据：静止单位离场后主视图不再整屏重绘，见 §附录 B） |
| ⑤ 其它服务半透明黑的路径 | `Hook_RadarPending_Proxy`（跳帧强驱）；`RadarHook_SelfDrawn`（自绘灰化） | `VA 0x10002390` cmp → `je 0x100023AE`（原版逻辑）；自绘档 `VA 0x10004769` cmp 后早退 | `s_radarGuardRejects[0]` 早退桶「总开关关闭」 |

**运行期判定口径（F2 明文要求）**：`g_enableStarCraftFog`（bool，VA `0x1002100B`）在 C++ 热路径每次调用直读（产物 `0x10001FC9`、`0x10004623`、`0x10004769`）；内联汇编短路由 `s_fogMasterGate`（VA `0x10021023`）镜像读取，镜像在 `LoadConfig` / `CheckMpGateTransition` / `CheckTelemetry` 三处 `setne`（VA `0x100013E8`/`0x100014EF`/`0x100034C3`）。`CheckTelemetry` 由单位绘制（每帧）与小地图绘制（每帧）触发 ⇒ 运行期改总闸 **≤1 帧**生效；**没有路径把开关固化在初始化期**（旧补丁字节仍在，但关闸出口不经过任何混色/绘制/状态写）。

---

## [3] 勘误（对既有文档/结论的更正）

| # | 目标文件:行 | 改前原文 | 改后文本 | 理由 | 影响面 |
|---|---|---|---|---|---|
| **E1** | `docs/re/hook_gate_gap_table.md:92-93`（#17/#18）、`docs/re/MP_SAFETY_REVIEW.md:241`、旧源码注释 | 「两桩替代了**引擎原生 50% 减法**」 | 「两桩替代的是引擎原版 **FOG.SHP alpha 插值混色**（`lea ecx,[ecx+edx-0x7f]` / `and …0xFF` 段）；「50%」是我方桩 `(c - c50)*s>>8` 在 `s=256` 时的等效表现」 | 引擎 .text 中 `0x47F40F` 49B / `0x47F4AE` 51B 原字节逐条反汇编为插值混色；**全库找不到** `and reg,0x7BEF`（0 处） | 影响产品决策（关闸语义）：**「不得落回引擎原生 50%」被更强地满足** —— 关闸分支既不经过原版混色、也不经过任何 50% 掩码。`RadarFogGuardMode=3` 的「像素精确 50% 减暗」描述仍成立（那是引擎 `0x655E8A–0x655F43` 的 `>>1` 减暗体，另一处机制，与 B1/B2 无关） |
| **E2** | `docs/re/hook_gate_gap_table.md:179`（G-04 建议） | 「或 `EnableStarCraftFog=0` 时不写对应补丁字节」 | 「改为**运行期门控**（本版已落地）：补丁字节照常安装，由桩内 `cmp [总闸] / je` 决定是否混色 / 是否驱动；关闸出口不再经过任何写像素或写状态指令」 | 安装期条件化无法满足「开关切换运行期立即生效」，且卸载路径仍需原字节备份 | 否（实施方式更新）；G-04 的验收判据由「读 `0x47F40F`/`0x6D3D99` 原字节恢复」改为「关闸时三计数恒 0 + 关闸出口反汇编证据」 |
| **E3** | `docs/re/hook_gate_gap_table.md:114`（S2 行） | 「`UpdateVisionGrid` 写 Scenario 标志（&= 0x1000 的按位清除）（每逻辑帧）」 | 「仅在 `UpdateVisionGrid` 被调用时才写；调用者 = Hook_CellClass_Draw（受总闸门）+ ShouldDrawMobileObject/Building/Bullet（受各自子键）。**总闸=0 时**：只要 `EnableBuildingFog` 或 `EnableBulletFog` 任一为 1（默认），该写仍执行；三者全 0 时我方不再写该位」 | 改后源码 4 个调用点 | 影响「关总闸是否零干预」的表述；产品决策不变（像素级判据由 P2/P3 短路保证） |
| **E4** | `docs/re/hook_gate_gap_table.md` 全文行号 | 以「`blitter_hooks.cpp` 1788 行 / 82,259 B」为快照 | 现文件已 2,280+ 行（改动后），所有 `:行号` 引用失效 | 文件已多次演进 | 文档可维护性；本报告一律以 **VA / 产物 RVA** 为锚点 |
| **E5** | 本文件 §[1] F3-1 行、§附录 C.4 末段 | 「F3① 启动行 = `.rdata RVA `0x18D28`（引用点 `0x15FE`）」 | 「F3① 启动行 = **RVA `0x187F0`**（VA `0x100187F0`）；RVA `0x18D28` 实为**常规遥测行** `[ra2render-telemetry] BlitCalls: %llu, …`」 | 【FOG-SPLIT】对 135,680 B / MD5 `491C25F9DE72E6A5EB3484E4CF154DA3` 部署件按 UTF-8 文本搜索独立复算：`[ra2render-fog] ` @ fileoff `0x16FF0` = RVA `0x187F0`；`[ra2render-telemetry]` @ fileoff `0x17528` = RVA `0x18D28`（ZC-4 亦实测同结论） | 仅文档锚点；行为结论不变（启动行本身完好且真机日志已见）。订正后原文以【原记】保留 |
| **E6** | 本文件 §2.3①/③、§附录 C.1/C.4 的 `inc` 地址、§附录 C.1 的 `RVA 0020A3` 等 | 以「指令起点」记 `inc` 地址（如 `0x100020A3` / `0x1000212D` / `0x100046E4`） | 补口径说明：**同一指令的两种口径** —— 指令起点（本报告口径）与 `FF 05` 之后的 **imm32 起点 = 指令起点 +2**（4 字节立即数扫描口径，ZC-4 `counter_addr_verify.txt` 采用）。逐条反汇编可证为同一条 `inc dword ptr [imm32]` | 【FOG-SPLIT】复核时两种口径都命中同一指令，易被误读为「地址差 2 字节 = 两条不同 inc」 | 无（同指令）；后续锚点一律写明口径（本文档与 `fog_split_report.md` 均以**指令起点**为准） |

> 另：本报告 §[1] 表格与 §2.1 中标注的「改前行号」仅为溯源，**不作为验收依据**（验收依据 = VA/RVA + 字节）。
>
> 【FOG-SPLIT 勘误追加】本报告 §[9] D1 的取舍前提（「总闸=0 时不写引擎 Scenario 位、不保留引擎原版黑幕」）已被用户裁决推翻：新的总闸语义要求
> **未探索黑幕必须保留**、玩法可见性与总闸解耦。相应实现与判据见 `docs/re/fog_split_report.md`（本报告的原语义描述在 E5/E6 之外的正文中**保持原样**，仅此追加说明指向新版）。

---

## [4] 未闭环清单

| # | 缺口 | 为何无法静态闭环 | 下一步取证方法 | 阻塞级别 |
|---|---|---|---|---|
| **U1** | 真机 A/B 像素验收（主视图 + 小地图无半透明黑、三计数恒 0、像素一致） | 本任务**明令禁止启动游戏/注入**（真机交 ZCode） | 按 §附录 B 执行；产出两张截图 + 两段 `ra2render.log`（含 `[ra2render-telemetry-fogswitch]` 行）+ 像素对比 | **P0**（验收） |
| **U2** | 引擎原生 FOG.SHP 路径（P4/P9）在「总闸=0 且 `EnableBuildingFog=0` 且 `EnableBulletFog=0` 且 rules `FogOfWar=yes`」下的可见性 | 需真机 + 特定 rules 组合；静态只能证明其压降必经 B1/B2（已被短路）且 `0x47EFE0` 的 FOG 分支无混色 | 真机：`rules.ini` 置 `[General] FogOfWar=yes`，三键（总闸/建筑/弹道）全 0，观察已探索非直视区是否出现压暗/异色；探针：断点 `0x0047F250` 记调用次数（此时应仅来自引擎 `0x480278`/`0x480290`，而像素应无任何变化） | **P2** |
| **U3** | `s_fogBlendStubHits` 为 uint32、按像素递增，长局可能回绕（4.29e9 像素） | 与既有 `s_minimapFogPixels` 同口径；改 64 位需在混色内循环加约 2 条指令/像素 | 若需绝对计数：`add dword ptr [x],1` + `adc dword ptr [x+4],0`；或改为只统计「介入的格子数」 | **P2** |
| **U4** | 自绘档（mode 0/1/2）在总闸=0 时同时不再「隐匿敌点」（跳过红点循环的能力失效） | 该副作用只能真机确认观感；静态已确定（`radar_selfdrawn_epilogue` 不再进入） | 真机 `RadarFogGuardMode=1` + 总闸 0/1 各截一张小地图：总闸=0 应看到敌点，总闸=1 应看不到 | **P2**（非默认 mode） |
| **U5** | 总闸=1 时像素级等价性（相对旧 DLL） | 需双 DLL 对拍 | 真机：旧备份 `ra2render.dll.bak-961E4B6C` 与新件同场景各截一帧做逐像素 diff（应完全一致） | **P1** |

---

## [5] 写作用域合规声明

**改动文件清单**

| 文件 | 性质 | 说明 |
|---|---|---|
| `ra2render/blitter_hooks.cpp` | 编辑 | 总闸 5 条实现 + 1 启动日志 + 1 遥测行 + 3 计数 + 1 新 naked 桩（L4） |
| `ra2render/ra2render.h` | 编辑（仅新增 2 常量 + 注释） | `ADDR_TACTICAL_FULL_REDRAW_TARGET 0x006D3E37`、`ADDR_TACTICAL_FULL_REDRAW_FALLTHROUGH 0x006D3D9F` |
| `ra2render/ra2render.ini` | 编辑（**仅注释**，键与默认值零变化） | 7,001 B / SHA-256 `0DAD9A41…A8C0` |
| `ra2youli/ra2render.ini` | 与上者逐字节同源 | Compare-Object 无差异 |
| `ra2render/ra2render.dll`、`ra2youli/ra2render.dll` | 构建产物 | 135,680 B / MD5 `491C25F9DE72E6A5EB3484E4CF154DA3` |
| `docs/re/fog_switch_report.md` | 新建（本文件） | — |
| `out/re_work/fog_switch/**` | 新建 | 见 §[8] |

**未触碰清单（逐项声明）**

* `ra2youli/gamemd.exe` —— **只读**；MD5/SHA-256 与任务卡一致（§[0]），且 `verify_anchors.py` 复核了 .text raw 段哈希与 .detour 原生签名。
* `.mix` / `.map` / `.sav` —— 未读写（含工作区根部的 `temp*.mix`、`scratch_*.shp`）。
* `ra2forge/**`、`mcp/**`、`ra2opt/**` —— 未触碰。
* 台账 `REVERSE_ENGINEERING_AND_PATCHES.md`、`docs/RE_COORDINATION.md`、`docs/re/radar_fix2_report.md`、其它 `docs/**` —— 未触碰（需订正内容写在 §[3] 勘误，交 Lead 处置）。
* `docs/re/anchor_claims.txt` —— 未触碰（仅运行 `verify_anchors.py` 复核）。
* `ra2render/build.bat` —— 未修改（loader 部署保持可选）。

---

## [6] 门禁实跑输出（原文粘贴）

### 6.1 构建（F4）

```text
> cmd /c ra2render\build.bat
**********************************************************************
** Visual Studio 2022 Developer Command Prompt v17.14.33
**********************************************************************
[vcvarsall.bat] Environment initialized for: 'x86'
Building ra2render.dll...
dllmain.cpp
blitter_hooks.cpp
正在生成代码...
Building ra2loader.exe...
ra2loader.cpp
        1 file(s) copied.
[build.bat] skip ra2loader.exe deploy (default). Set RA2RENDER_DEPLOY_LOADER=1 to deploy it.
ALL BUILDS FINISHED SUCCESSFULLY
```

### 6.2 全库锚点回归（必须 323/323 PASS）

```text
> python tools\verify_anchors.py
目标文件 : D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe (大小: 4,825,360 字节, ImageBase: 0x400000)
断言文件 : D:\Project\ra2-campaign-forge\docs\re\anchor_claims.txt
反汇编器 : Capstone x86-32 引擎已就绪
-------------------------------------------------------------------------------------------------------------------
[基线完整性审计]
  [PASS] .text 原始段哈希: c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738 (口径: raw(SizeOfRawData=0x3E0000))
  [INFO] PE头特征判定 : RA2OPT_PERF_APPLIED (0xAE=0x20, Stack=4MB, .text未变) (DllChar: 0x20, StackReserve: 0x400000)
  [PASS] .detour 原生签名: 40 00 00 00 44 74 72 00 ('@\0\0\0Dtr\0' @ VA 0xb93000) -> 严禁写入/注入原则确立
-------------------------------------------------------------------------------------------------------------------
回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！
===================================================================================================================
```

### 6.3 引擎侧 claims（`out/re_work/fog_switch/claims_exe.txt`，28 条）

```text
> python tools\audit_bytes.py out\re_work\fog_switch\claims_exe.txt      （尾部原文）
0x6d3d99   0f 8d 98 00 00 00          0f 8d 98 00 00 00      OK     L4 原版 jge 0x6D3E37（6B） | jge 0x6d3e37
0x6d3d9f   8b c6 99 33 c2 2b c2       8b c6 99 33 c2 2b c2   OK     L4 原版 fallthrough | mov eax, esi
0x6d3e37   c6 84 24 0c 01 00 00 01   c6 84 24 0c 01 00 00 01 OK     L4 全量重绘目标 | mov byte ptr [esp + 0x10c], 1
0x655d38   89 44 24 28 a1 50 35 b7 00 89 44 24 28 a1 50 35 b7 00 OK   H1 挂钩点 9B 头
0x655d41   3b c5 74 18 8d 4c 24 20    3b c5 74 18 8d 4c 24 20 OK     H1 回跳点
0x655d87   8b 47 04 89 6c 24 14       8b 47 04 89 6c 24 14   OK     H3 挂钩点 7B 头
0x655d8e   8d 04 80 8b c8 8b 07 2b    8d 04 80 8b c8 8b 07 2b OK     H3 回跳点
0x65719a   e8 91 93 00 00             e8 91 93 00 00         OK     H2 挂钩点（call 0x660530 5B）
0x65719f   84 c0 74 26                84 c0 74 26            OK     H2 返回值消费点
0x660530   a1 b8 4d b0 00 85 c0 0f 94 c0 c3 a1 b8 4d b0 00 85 c0 0f 94 c0 c3 OK  H2 被替换的原函数
--------------------------------------------------------------------------------------------------------------
合计 28 条：OK=28  MISMATCH/NOREAD=0
```

### 6.4 产物侧 claims（`out/re_work/fog_switch/claims_dll.txt`，36 条；两个独立口径）

```text
> python tools\audit_bytes.py out\re_work\fog_switch\claims_dll.txt --exe ra2youli\ra2render.dll
（地址口径：audit_bytes.py 硬编码 IMAGE_BASE=0x400000，故本文件用 VA' = 0x400000 + RVA）
0x4046e4   ff 05 40 1a 2e 10          ff 05 40 1a 2e 10      OK     inc [s_radarDarkenDriven]（计数③，原生档）
0x4048f6   ff 05 40 1a 2e 10          ff 05 40 1a 2e 10      OK     inc [s_radarDarkenDriven]（计数③，自绘档）
0x4026e8   c6 05 f0 01 48 00 e9       c6 05 f0 01 48 00 e9   OK     patch[0]=0xE9 写入 0x4801F0（挂钩点未变）
0x4029a8   c6 05 38 5d 65 00 e9       c6 05 38 5d 65 00 e9   OK     patch[0]=0xE9 写入 0x655D38（挂钩点未变）
0x402a15   c6 05 9a 71 65 00 e8       c6 05 9a 71 65 00 e8   OK     patch[0]=0xE8 写入 0x65719A（挂钩点未变）
0x402ae2   c6 05 87 5d 65 00 e9       c6 05 87 5d 65 00 e9   OK     patch[0]=0xE9 写入 0x655D87（挂钩点未变）
--------------------------------------------------------------------------------------------------------------
合计 36 条：OK=36  MISMATCH/NOREAD=0

> python out\re_work\fog_switch\verify_dll_bytes.py            （按 PE 头真实 ImageBase=0x10000000 独立复算）
DLL ...\ra2youli\ra2render.dll  size=135680  md5=491C25F9DE72E6A5EB3484E4CF154DA3  真实 ImageBase=0x10000000
汇总：36 OK / 0 FAIL
```

---

## [7] 风险与红线提示

* ① **同步语义 / 命令序**：**未新增任何引擎状态写** —— `s_fogMasterGate`、三个计数、`s_fogLayerDraws` 均为 DLL 私有内存；总闸=0 时反而**减少**写（不再写 `[esp+0x13]`、不再调用 `0x47F250`）。唯一触及「渲染时序」的是 L4 桩（dirty-rect 域，不进帧 CRC/存档/RNG），且总闸=1 时与旧补丁逐位等价（`popfd` 还原 `0x6D3D97` 的 flags 后 `jmp 0x6D3E37`，同目标同 flags）。
* ② **随机数消费序**：**未触及**（无 `Random`/`rand` 调用点或节流相位变化）。
* ③ **存档结构**：**未触及**（无序列化字段新增/变更；`s_*` 均 DLL 私有）。
* ④ **渲染像素等价性**：**触及** —— 总闸=1 的语义目标是「与旧 DLL 逐位一致」，静态上成立（开闸路径指令同序同值，仅多一次不改变状态的门比较），但**像素级等价需真机对拍**（U5）。
* **需要 MP 门控矩阵 / 真机对拍验收**：是。联机既有约束未变（`EnableMinimapFog` 在 `MpActive` 下仍强制 0；`TargetScanKey` 仍强制 position）。本改动**不宣称「零风险 / 零 Desync」**；混联建议按既有 `mp_release_safety_checklist` 走 MP-G04（判据已按 §[3] E2 更新）。
* **禁止事项遵守**：未启动游戏、未注入、未改 exe、未伪造实测（所有真机项一律 [待实测] / [纸面规格]）。

---

## [8] 交付物清单

| 类型 | 路径 | 规模 |
|---|---|---|
| 代码 | `ra2render/blitter_hooks.cpp`、`ra2render/ra2render.h` | 总闸 5 条 + 1 启动日志 + 1 遥测行 + 3 计数 + 1 新 naked 桩 |
| 产物 | `ra2render/ra2render.dll` ≡ `ra2youli/ra2render.dll` | 135,680 B / MD5 `491C25F9…4DA3` |
| 配置 | `ra2render/ra2render.ini` ≡ `ra2youli/ra2render.ini` | 7,001 B / SHA-256 `0DAD9A41…A8C0`（键与默认值零变化） |
| 新文档 | `docs/re/fog_switch_report.md`（本文件） | 见工作区 |
| 验收清单 | `out/re_work/fog_switch/ZCODE_ACCEPTANCE_FOG_SWITCH.md` | 1 份 |
| 备份 | `out/re_work/fog_switch/ra2render.dll.bak-961E4B6C`、`ra2render.ini.bak-07321883` | 134,144 B / 4,902 B |
| 断言 | `claims_exe.txt`（28 条）、`claims_dll.txt`（36 条） | 64 条，全 OK |
| 校验脚本 | `verify_dll_bytes.py`、`evidence/f1_*.py`（6 支）、`evidence/f5_verify_*.py`（7 支） | 可复跑 |
| dump / 证据 | `out/re_work/fog_switch/evidence/`：F1_disasm.txt、F1_xref.txt、F1_candidates.txt、F1_cellclass_draw.txt、F1_drawfog_stores.txt、F1_flag_writers.txt、F5_product_disasm{,_b,_c,_d,_e,_f,_g}.txt、F5_obj_symbols.txt、F5_patch_bytes_construct.txt | 15 份 |

---

## [9] 待裁决项

| # | 分叉 | 建议 | 理由 |
|---|---|---|---|
| D1 | 总闸=0 时是否也压制引擎自身 FogOfWar 位（Scenario `&0x1000`）？ | **不建议现在做**。保持「不写引擎状态」的更纯净语义；像素级无压暗已由 B1/B2 短路保证 | 写 Scenario 位属既有 S2（MP RISK）面；只有「总闸=0 + 建筑/弹道子键也=0 + rules `FogOfWar=yes`」的极端组合才可能触及 `0x47EFE0` 的 FOG 分支（该分支无混色）。若 ZCode 在 U2 发现观感异常再决定加兜底 |
| D2 | 混色桩计数按「像素」还是「桩进入次数」？ | 保持现状（像素数，与 `s_minimapFogPixels` 同口径） | 关闸判据只看「是否恒 0」，与口径无关；64 位改法需付每像素 2 条指令代价 |
| D3 | 是否给 L4 增加独立键（`[Render] L4DirtyMode`）？ | **暂不加**（本任务要求不新增键）。若 Q7 折中（vision-dirty）落地再按 G-04 加键 | 不新增键是本次裁决；总闸已可关掉该耦合 |
> 【W3 勘误 · W3-A6/ISSUE-SECTION-L4DIRTYMODE】改前：[Render] L4DirtyMode；改后：[FogOfWar] L4DirtyMode=force-full；依据：ra2render/blitter_hooks.cpp:757; ra2render/ra2render.ini:251；分级：P0
| D4 | `EnableMinimapFog=1` + 总闸=0 时「敌点隐匿」失效（U4） | 接受，已在 ini 注释声明「需总闸=1」 | 隐匿能力与自绘灰化同生共死（同一函数尾声）；默认 mode 3 下本就不生效 |

---

# 附录 A. F1 路径清单（速查，含 xref 来源）

| # | 路径 | 关键 VA | 字节 | xref / 调用者 | 证据文件 |
|---|---|---|---|---|---|
| 1 | 我方追加 FOG.SHP 层 | `0x0047F250` | `A0 C6 E7 89 00` | 仅 Hook_CellClass_Draw（产物 VA `0x100020B4`） | F5_product_disasm_e.txt |
| 2 | 引擎自身 FOG.SHP 调用 ×2 | `0x00480278`/`0x00480290` | `E8 D3 EF FF FF`/`E8 BB EF FF FF` | `CellClass::Draw` 内（门 `0x00480251`） | F1_xref.txt / F1_cellclass_draw.txt |
| 3 | B1 混色 | `0x0047F40F` | 49B（原版插值混色） | `0x47F3E9..0x47F47B` 循环 | F1_disasm.txt |
| 4 | B2 混色 | `0x0047F4AE` | 51B（原版插值混色） | `0x47F482..0x47F4FE` 循环 | F1_disasm.txt |
| 5 | 黑雾/灰雾层二选一 | `0x0047EFE0` | 624B（无混色） | `CellClass::Draw @0x480223` | F1_candidates.txt |
| 6 | L4 全量刷 | `0x006D3D99` | `0F 8D 98 00 00 00` | `0x6D3D80` 战术重绘路径 | F1_disasm.txt |
| 7 | 小地图减暗驱动位 | `0x00655D87` / `[esp+0x13]` | `8B 47 04 89 6C 24 14` | `RadarClass::Plot_Cell`（`0x655C50` 内） | F1_disasm.txt |
| 8 | 小地图自绘闸（H1） | `0x00655D38` | `89 44 24 28 A1 50 35 B7 00` | `Plot_Cell` 中部（`0x578080` 返回值落地） | F1_disasm.txt |
| 9 | 小地图跳帧强驱（H2） | `0x0065719A` | `E8 91 93 00 00` | `0x656EC0` 主循环（唯一 call 点） | F1_xref.txt |
| 10 | 排除项：50% 掩码 | — | **全库 0 处** `and reg,0x7BEF` | — | F1_candidates.txt「模式搜索 B」 |

---

# 附录 B. 真机验收步骤（给 ZCode；A/B 单变量）

> 前提：`ra2youli/gamemd.exe` 为基线；DLL 用 §[0] 的 135,680 B 版本（MD5 `491C25F9…`）；两份 ini 用 7,001 B 版本。
> **全程只改 `[FogOfWar] EnableStarCraftFog` 一个键**（A = 0 / B = 1），其余键固定：
> `EnableMinimapFog=1`（固定开启，用于检验小地图一致性）、`RadarFogGuardMode=3`、`EnableBuildingFog=1`、`EnableBulletFog=1`、`FadeFogTransition=1`。
> 独立清单文件：`out/re_work/fog_switch/ZCODE_ACCEPTANCE_FOG_SWITCH.md`。

## B.1 场景（同一局、同一存档、同一镜头）

1. 载入同一战役/遭遇战存档：己方部队已离开某片已探索区，该区当前**非直视**。
2. 镜头固定在标记位置（建议固定书签或固定坐标），**不要滚动**。
3. 游戏速度保持默认（不要按 `+` / `-`）。

## B.2 步骤

| 步 | 动作 | 记录 |
|---|---|---|
| B0 | 启动游戏进入局内，等待 ≥10 秒 | 保存 `ra2render.log` 首屏：应含 `[ra2render-fog] 灰雾总闸: …` 行（打印总闸与 5 子键的生效值/来源） |
| B1 | **A 组**：ini `EnableStarCraftFog=0` → 重启游戏 → 进入同一场景 | ① 主视图截图（已探索非直视区）② 小地图截图 ③ 等 ≥6 秒后抓 `ra2render.log` 中 `[ra2render-telemetry-fogswitch]` 行（取 2 次，间隔 ≥4 秒） |
| B2 | **B 组**：ini `EnableStarCraftFog=1` → 重启游戏 → 同一场景 | 同上三份记录 |
| B3 | 像素对比 | A 组「已探索非直视区」与「同屏直视区」的同种地表像素做直方图/逐像素差；A/B 组相同屏幕区域做 diff |

## B.3 判据（三项，缺一不可）

1. **目视无半透明黑**：A 组主视图无灰雾压暗（已探索非直视区与直视区观感一致）；小地图无减暗（即使 `EnableMinimapFog=1`）。B 组应恢复现有灰雾表现（对照组）。
2. **三计数恒 0**：A 组 `ra2render.log` 中 `半透明层绘制次数` / `混色桩介入次数` / `小地图减暗驱动次数` **全为 0**（连续两行遥测都是 0）；B 组应 > 0（前两项明显增长）。
3. **像素一致（无压暗残影）**：A 组已探索非直视区与直视区的**相同地表纹理**像素值一致（无约 50% 的系统性压降偏移）；A/B 组同屏同场景 diff 应表现为「仅灰雾区域变亮」而非「全屏变化」。

## B.4 注意事项

* 若启动日志显示 `EnableMinimapFog 生效=0`，说明被联机保守门拦下（`MpActive=true`）——请在单机下测试。
* 若 A 组仍见压暗：抓 `[ra2render-telemetry-fogswitch]` 行 + 截图，回报「三计数中哪个非 0」，可直接区分：① 层未短路 / ② 桩未短路 / ③ 小地图未短路 / ④ 引擎原生路径（U2）。
* 改 ini 请在退出游戏后进行（本版支持运行期生效，可另做一次「运行中改键」对比作为加分项）。
* 建议附加 **U5 回归**：用旧备份 DLL（MD5 `961E4B6C…`）在总闸=1 同场景截一帧，与新件逐像素 diff（应完全一致）。
* 语言/分辨率/花色等渲染设置与上次一致，避免非灰雾差异污染 diff。

---

# 附录 C. 产物级证据（反汇编原文节选）

> 对象：`ra2youli/ra2render.dll`（135,680 B / MD5 `491C25F9DE72E6A5EB3484E4CF154DA3`，真实 ImageBase = `0x10000000`）。
> 完整清单：`out/re_work/fog_switch/evidence/F5_product_disasm_*.txt`。

## C.1 短路点① + 计数①（Hook_CellClass_Draw）

```text
RVA 001FB3 VA 10001FB3  8B 0D E4 19 02 10    mov eax, dword ptr [0x100219E4]     ; g_pOrigCellClassDraw
RVA 001FBB VA 10001FBB  85 C0                test eax, eax
RVA 001FBD VA 10001FBD  74 0A                je 0x10001FC9
RVA 001FC5 VA 10001FC5  8B CE                mov ecx, esi                        ; 原版 CellClass::Draw 恒定执行
RVA 001FC7 VA 10001FC7  FF D0                call eax
RVA 001FC9 VA 10001FC9  80 3D 0B 10 02 10 00 cmp byte ptr [0x1002100B], 0         ; ★ 总闸 g_enableStarCraftFog
RVA 001FD0 VA 10001FD0  0F 84 10 01 00 00    je 0x100020E6                        ; ★ 短路①（整段灰雾层不执行）
RVA 001FD6 VA 10001FD6  85 F6                test esi, esi
RVA 001FD8 VA 10001FD8  0F 84 08 01 00 00    je 0x100020E6                        ; pCell == 0
RVA 001FE5 VA 10001FE5  E8 B6 29 00 00       call 0x100049A0                      ; UpdateVisionGrid
   ...  cellX/cellY 边界（cmp cx,0x1FF / ja）+ OFF_CELL_FLAGS(0x12C) bit3 已探索检查 ...
RVA 00209D VA 1000209D  66 A3 20 10 02 10    mov word ptr [0x10021020], ax        ; s_fogBlendStrength = strength
RVA 0020A3 VA 100020A3  FF 05 38 1A 2E 10    inc dword ptr [0x102E1A38]           ; ★ 计数① s_fogLayerDraws++
RVA 0020AC VA 100020AC  6A 0F                push 0xF
RVA 0020AE VA 100020AE  FF 75 10             push dword ptr [ebp + 0x10]
RVA 0020B1 VA 100020B1  FF 75 0C             push dword ptr [ebp + 0xC]
RVA 0020B4 VA 100020B4  B8 50 F2 47 00       mov eax, 0x47F250                    ; ★ 引擎 FOG.SHP 层
RVA 0020B9 VA 100020B9  FF D0                call eax
RVA 0020BB VA 100020BB  B8 00 01 00 00       mov eax, 0x100
RVA 0020C0 VA 100020C0  66 A3 20 10 02 10    mov word ptr [0x10021020], ax        ; 恢复 256
```

## C.2 短路点②（B1/B2 混色桩：开闸/关闸两条出口并列）

```text
===== B1 桩（Hook_FogBlendB1_Stub，RVA 002120）=====
RVA 002120 80 3D 23 10 02 10 00   cmp byte ptr [0x10021023], 0    ; 总闸镜像 s_fogMasterGate
RVA 002127 0F 84 84 00 00 00      je 0x100021B1                   ; ★ 关闸出口
RVA 00212D FF 05 3C 1A 2E 10      inc dword ptr [0x102E1A3C]      ; ★ 计数②（仅开闸路径）
   ... 43 条强度混色指令（movzx ebx,[s_fogBlendStrength]; and ecx,0x7BEF; imul/shr 逐通道）...
RVA 0021A7 66 89 08               mov word ptr [eax], cx          ; ★ 桩内唯一落像素
RVA 0021AA B9 40 F4 47 00 FF E1   mov ecx,0x47F440 / jmp ecx      ; 开闸出口
RVA 0021B1 B9 40 F4 47 00 FF E1   mov ecx,0x47F440 / jmp ecx      ; ★ 关闸出口（无像素写、无 0x7BEF、无插值）
RVA 0021B8 CC                      int3

===== B2 桩（Hook_FogBlendB2_Stub，RVA 0021C0）=====
RVA 0021C0 80 3D 23 10 02 10 00   cmp byte ptr [0x10021023], 0
RVA 0021C7 0F 84 84 00 00 00      je 0x10002251                   ; ★ 关闸出口
RVA 0021CD FF 05 3C 1A 2E 10      inc dword ptr [0x102E1A3C]      ; ★ 计数②
RVA 002247 66 89 08               mov word ptr [eax], cx          ; 桩内落像素
RVA 00224A B9 E1 F4 47 00 FF E1   mov ecx,0x47F4E1 / jmp ecx      ; 开闸出口
RVA 002251 B9 E1 F4 47 00 FF E1   mov ecx,0x47F4E1 / jmp ecx      ; ★ 关闸出口（无像素写）
```

## C.3 短路点③/④/⑤

```text
===== H3 原生减暗驱动代理（RVA 002350）=====
RVA 002350 80 3D 23 10 02 10 00   cmp byte ptr [0x10021023], 0      ; ★ 总闸
RVA 002357 74 29                  je 0x10002382                     ; ★ 短路③：直通跳板（不读不写 [esp+0x13]）
RVA 002359 8B 0D 50 19 02 10      mov ecx, dword ptr [0x10021950]    ; &s_radarCtx
RVA 002372 8D 54 24 13            lea edx, [esp + 0x13]              ; &[esp+0x13]（判定位）
RVA 002376 89 51 10               mov dword ptr [ecx + 0x10], edx    ; ctx->pFlag
RVA 00237A E8 81 22 00 00         call 0x10004600                    ; RadarHook_NativeDecide
RVA 002382 FF 25 48 1A 2E 10      jmp dword ptr [0x102E1A48]         ; → 跳板（回放 7B 后 jmp 0x655D8E）

===== RadarHook_NativeDecide 内（计数③ 与 *pFlag 写的顺序证据，RVA 004623 起）=====
RVA 004623 80 3D 0B 10 02 10 00   cmp byte ptr [0x1002100B], 0      ; C++ 侧总闸兜底
   ...
RVA 0046DA 84 FF                  test bh, bh                        ; ours != 0 ?
RVA 0046DC 74 1B                  je 0x100046F9
RVA 0046DE FF 05 FC 19 2E 10      inc dword ptr [0x102E19FC]         ; s_nativeForcedDarkHits++
RVA 0046E4 FF 05 40 1A 2E 10      inc dword ptr [0x102E1A40]         ; ★ 计数③ s_radarDarkenDriven++
RVA 0046EA 8B 46 10               mov eax, dword ptr [esi + 0x10]    ; ctx->pFlag
RVA 0046ED 88 38                  mov byte ptr [eax], bh             ; ★ *ctx->pFlag = ours

===== L4 桩（Hook_L4FullRedraw_Stub，RVA 0022C1）=====
RVA 0022C1 80 3D 23 10 02 10 00   cmp byte ptr [0x10021023], 0      ; ★ 总闸
RVA 0022C8 74 08                  je 0x100022D2                     ; ★ 短路④：走原版语义分支
RVA 0022CA 9D                     popfd                                   ; 开闸：还原 flags（与旧 E9 补丁同 flags/同目标）
RVA 0022CB B9 37 3E 6D 00         mov ecx, 0x6D3E37
RVA 0022D0 FF E1                  jmp ecx
RVA 0022D2 9D                     popfd                                   ; 关闸：还原 0x6D3D97 cmp 的原始 flags
RVA 0022D3 7D 07                  jge 0x100022DC                          ; 原版条件跳转
RVA 0022D5 B9 9F 3D 6D 00 FF E1   mov ecx,0x6D3D9F / jmp ecx              ; 原版 fallthrough
RVA 0022DC B9 37 3E 6D 00 FF E1   mov ecx,0x6D3E37 / jmp ecx              ; 全量重绘

===== H2 跳帧强驱代理（RVA 002390）=====
RVA 002390 80 3D 23 10 02 10 00   cmp byte ptr [0x10021023], 0      ; ★ 总闸（短路⑤）
RVA 002397 74 15                  je 0x100023AE
RVA 002399 80 3D E8 19 2E 10 00   cmp byte ptr [0x102E19E8], 0      ; s_minimapFogGate
RVA 0023A0 74 0C                  je 0x100023AE
RVA 0023A2 80 3D 57 19 02 10 00   cmp byte ptr [0x10021957], 0      ; s_minimapForceRefresh
RVA 0023A9 74 03                  je 0x100023AE
RVA 0023AB 32 C0 C3               xor al, al / ret                  ; 强制全量刷新
RVA 0023AE B8 B8 4D B0 00         mov eax, 0xB04DB8                 ; 原版逻辑
RVA 0023B3 8B 00 85 C0 0F 94 C0   mov eax,[eax] / test / sete al
```

## C.4 三个新遥测符号：对象符号表 + 产物地址链

```text
> dumpbin /symbols ra2render\blitter_hooks.obj      （节选原文）
014 0000000B SECT4  notype  External  | ?g_enableStarCraftFog@@3_NA (bool g_enableStarCraftFog)
043 00000023 SECT4  notype  External  | _s_fogMasterGate
044 002C00E8 SECT3  notype  External  | _s_fogLayerDraws
045 002C00EC SECT3  notype  External  | _s_fogBlendStubHits
046 002C00F0 SECT3  notype  External  | _s_radarDarkenDriven
184 00000000 SECT42 notype () External | ?Hook_FogBlendB1_Stub@@YAXXZ (void __cdecl Hook_FogBlendB1_Stub(void))
186 00000000 SECT46 notype () External | ?Hook_L4FullRedraw_Stub@@YAXXZ (void __cdecl Hook_L4FullRedraw_Stub(void))
```

| 符号 | 产物 VA | 自增点（产物 VA） | 遥测引用点（产物 RVA） | 语义 |
|---|---|---|---|---|
| `s_fogLayerDraws` | `0x102E1A38` | `0x100020A3`（inc，门后、调 0x47F250 前） | `0x1624`（push） | 半透明层绘制次数 |
| `s_fogBlendStubHits` | `0x102E1A3C` | `0x1000212D`（B1）、`0x100021CD`（B2） | `0x1618`（push） | 混色桩介入（像素）次数 |
| `s_radarDarkenDriven` | `0x102E1A40` | `0x100046E4`（原生档）、`0x100048F6`（自绘档） | `0x1610`（push） | 小地图减暗驱动次数 |
| `s_fogMasterGate` | `0x10021023` | `0x100013E8`/`0x100014EF`/`0x100034C3`（setne 同步） | `0x1608`（movzx+push） | 总闸汇编侧镜像 |

遥测行格式串在产物中的位置（**已按 FOG-SPLIT 独立复算订正**，见 §[3] E5）：
F3① 启动行 = `.rdata RVA **0x187F0**`（VA `0x100187F0`；引用点 `0x15FE`）；F3② fogswitch 行 = `.rdata RVA 0x18E58`（引用点 `0x162E`）。二者与上述计数地址的 push 链紧邻，构成「格式串 ↔ 计数符号」的交叉印证。

> 【原记】「F3① 行 = `.rdata RVA 0x18D28`（引用点 `0x15FE`）」—— 该锚点有误：`0x18D28` 是**常规遥测行** `[ra2render-telemetry] BlitCalls: %llu, …`
> （对 135,680 B / MD5 `491C25F9DE72E6A5EB3484E4CF154DA3` 的部署件按 UTF-8 文本搜索：`[ra2render-fog] ` @ fileoff `0x16FF0` = RVA `0x187F0`；
> `[ra2render-telemetry]` @ fileoff `0x17528` = RVA `0x18D28`）。启动行真实锚点 = **RVA `0x187F0`**。

> 【口径订正】上表「自增点（产物 VA）」给的是**指令起点**；若用 4 字节立即数（`FF 05` 后的 imm32）扫描定位，命中点 = 指令起点 **+2**（如 `s_fogLayerDraws` 的 `inc`：指令起点 `0x100020A3`，立即数字段起于 `0x100020A5`）——
> 二者为**同一条指令**的两种口径，非两条不同 inc（对同一构建件逐条反汇编可证）。

## C.5 挂钩点未变（补丁形状）

```text
RVA 0026E8  C6 05 F0 01 48 00 E9   mov byte ptr [0x4801F0], 0xE9   ; CellClass::Draw 5B（E9 + rel32）
RVA 0029A8  C6 05 38 5D 65 00 E9   mov byte ptr [0x655D38], 0xE9   ; H1 9B（E9 + rel32 + NOP×4）
RVA 002A15  C6 05 9A 71 65 00 E8   mov byte ptr [0x65719A], 0xE8   ; H2 5B（E8 + rel32，等长替换 call）
RVA 002AE2  C6 05 87 5D 65 00 E9   mov byte ptr [0x655D87], 0xE9   ; H3 7B（E9 + rel32 + NOP×2）
（L4：0x006D3D99 补丁首字节同为 E9，但 rel32 现指向 Hook_L4FullRedraw_Stub —— 见附录 C.3 / §2.3④）
```

## C.6 关闸时「不落回 50%」的完整可达性论证（三条）

1. **静态唯一性**：引擎 .text 中执行 FOG.SHP 逐像素写入的位置只有 3 处（`0x47F43D`、`0x47F4BB`、`0x47F4DE`），且都在被补丁覆盖的 49/51 字节区内；补丁把入口改写成 `jmp 桩`，因此这三条路径**必经桩**。
2. **关闸出口无写**：桩的关闸分支（`RVA 0x21B1` / `0x2251`）只做 `mov ecx,imm32` + `jmp ecx`，目标为循环后继（`0x47F440` / `0x47F4E1`）；其后继的第一个写操作是目的指针推进（`add eax,2` 等），**不含像素写入**。
3. **不存在「原生 50%」可落回**：全 exe （1,394,120 条指令）**0 处** `and reg,0x7BEF`；「50% 压降」只出现在我方代码（产物 `RVA 0x2145` 桩内 `and ecx,0x7bef`、`RVA 0x48DD` 自绘 `and eax,0x7bef`），二者都在总闸门内 ⇒ 关闸即全部不可达。