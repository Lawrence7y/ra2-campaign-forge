# P01-VERIFY · 0x55D877 冻结出口与 [Scenario+0x62C] 挂起深度计数器定谳：独立复算全部字节级主张成立，headline CONFIRMED（4 处注记级偏差，均不动摇主链）

核验对象：`P01/REPORT.md`（headline=0x55D877 冻结出口=单机局挂起门；+0x62C 是 ScenarioClass 挂起深度计数器，inc 0x684174 / dec 0x684195 / 复位 0x6836D2，非暂停布尔/同步/跳帧）。
核验方式：不信任原报告结论，用共享引擎 `ra2tool.Engine` 从字节独立重算每条 keyFact；外部锚用本仓 vendored YRpp 与 docs/re 图集原文核对。

---

## 0. 现场自证

| 项 | 我运行的命令 | 结果 |
|---|---|---|
| 零真机 | `tasklist /FI "IMAGENAME eq gamemd.exe"`（另查 ra2loader.exe / YURI.exe） | 三条均「信息: 没有运行的任务匹配指定标准。」——无游戏进程 |
| 母本只读 | `python -I -X utf8 P01/verify1_all.py`（Engine 构造内 SHA 断言） | SHA256 匹配 `ra2tool.py:29` 期望值，只读打开，零写入 |
| 解码覆盖 | 同上，`eng.coverage` | **99.9984% / 1,394,120 insns / resync=66**。原报告写 100.00%——1,394,120 条与 resync=66 与我完全一致，99.9984% 四舍五入即 100.00%，同一数字 |
| IAT 锚 | `eng.resolve_iat(0x7E11F0)` / `(0x7E1530)` | `('KERNEL32.dll','Sleep')` / `('WINMM.dll','timeGetTime')` ✓ |
| 基线四项 | 同上，`disp_hits` 全镜像普查 | 0xA8ED84=**1007/10**（写回 0x55DE81）✓；0xA8ED80=**46/1**（0x7778CE）✓；0xA8B230=**1293/3**（0x52BA94/0x52BAB6/0x6BEB7D）✓；MLF rets=**3** ✓ |

产物件（本写域 P01/ 新增）：`verify1_all.py`、`verify_stdout.log`、`verify_aux.txt`。未改动 REPORT.md、落盘件、台账、母本。

---

## 1. 结论（逐条 keyFact，每条带证据级别）

| # | keyFact（原报告） | 判定 | 级别 |
|---|---|---|---|
| KF1 | 冻结段 0x55D7C9 je 0x55D7D4(74 09)、0x55D7CE jne 0x55D878(0F85 A4)、0x55D82E je 0x55D878(74 48)；省略号内前置门 0x55D7DA mov al,[edi+0x630] | **CONFIRMED** | [字节] |
| KF2 | +0x62C 写点全集 3 处（复位 0x6836D2 / inc 0x684174 / dec 写回 0x684195） | **CONFIRMED** | [字节] |
| KF3 | [0xA8B230]=ScenarioClass::Instance 而非 GameLogic（0x52BA60 new 0x3740→ctor 0x6832C0→存；0x52BAB6/0x6BEB7D 置空；0x683610 写 [ebp+0x214]=0xF4240；Scenario.CPP 串） | **CONFIRMED**（YRpp 外部锚直接证实） | [字节] |
| KF4 | 字段族：+0x614 ElapsedTimer（冻结/re-arm@0x68422C）、+0x620 PauseTimer（[0x628]=时长秒×60，16ms/刻时钟 0x6C8C40）、+0x630 武装旗标、+0x35A2、[0xA8ED9C]、[0xB054CC]、[0xB07784] | **CONFIRMED**（[0x624] 语义 1 处小注，见 §4） | [字节] |
| KF5 | inc 0x684060 调用点 4 处、dec 0x684180 调用点 3 处、启动器 2 处、0x53B610=33 C9、.data:0x872E78→0x6E4080 | **CONFIRMED**（VA 表述 1 处注记：0x6DF6FD/0x6E4080 是装参 mov 的 VA，call 指令在 +6） | [字节] |
| KF6 | 冻结体执行集 6 项；正常体 28 唯一调用目标被跳过；返回值同式 al=([0xA8E9A0]==0) | **CONFIRMED**（「28」为 [0x55D878,0x55DE4F) 截断口径，全区间实为 32，见 §4-2） | [字节] |
| KF7 | 0x55E160=帧节流（SP 分支 [0x887348]/[0x887350]+Sleep edi=[0x7E11F0]），两路径共用 | **CONFIRMED** | [字节] |
| KF8 | 门=GameMode∈{0,5}（GeneralDefinitions.h:670）；同步等待/跳帧被证伪；ESC 暂停未被钉为主因 | **CONFIRMED** | [字节+外部锚] |
| KF9 | MLF rets={0x55D877,0x55DEC7,0x55DEDB}；reach_without(INC 块)={0x55D877,0x55DEDB} | **CONFIRMED** | [字节] |
| KF10 | 基线四项 1007/10、46/1、1293/3、3 rets | **CONFIRMED** | [字节] |
| 预测 | 真机判据（+0x62C 非零即冻结、0xA8ED84 停涨而泵/渐变计数变化、GameMode 门等） | **PARTIAL**：静态判据全部字节支撑；但「带 PauseTimer 的挂起由 MLF **每帧 dec 一次直到 0**」与字节矛盾（见 §2-E），counter>1 时余量不会被自动释放 | [推导] |
| 冲突登记 | [0xA8B230] 任务基线称 GameLogic→纠正 ScenarioClass；「世界更新照跑」→纠正「渲染/泵/节流照跑、世界模拟跳过」 | **CONFIRMED**（纠正方向正确且有必要） | [字节+文证] |

**headline 判定：CONFIRMED。** 0x62C 的 inc/dec/复位三写点、GameMode∈{0,5} 双门、帧号不 inc、渲染/泵/节流照跑——每个环节都从字节独立复现；「暂停布尔/同步等待/跳帧」三种解释均被字节排除。

---

## 2. 证据（VA + 字节 + 推导链，全部出自本次 verify1_all.py 实跑）

### A. 冻结段逐字节（KF1/KF8）
39 处关键字节硬断言全部通过（log 无 HARD-FAIL），7 个分支目标用「VA+指令长+rel」机器复算：0x55D7C9+2+0x09=0x55D7D4 ✓、0x55D7CE+6+0xA4=0x55D878 ✓、0x55D7E2+2+0x3D=0x55D821 ✓、0x55D7F9+2+0x10=0x55D80B ✓、0x55D807+2+6=0x55D80F ✓、0x55D80D+2+0x12=0x55D821 ✓、0x55D82E+2+0x48=0x55D878 ✓（我的脚本在第 8 条手写 rel 常量笔误 0x000751B，capstone `call 0x5d4d50` 仲裁为 0x5D4D50，属核验脚本笔误非镜像问题）。0x55D7DA=`8A 87 30 06 00 00`（前置武装旗标门）✓。0x55D7C2 `A1 38 B2 A8 00` → 门变量 [0xA8B238]；外部锚：YRpp `SessionClass.h:54` `Instance@0xA8B238` + `:56 GameMode GameMode` + `GeneralDefinitions.h:670` `enum class GameMode{Campaign=0x0,LAN=0x3,Internet=0x4,Skirmish=0x5}`——**Campaign=0/Skirmish=5 与字节双证**。0xA8B238 写点含立即数 3/4/5/0（30 处），与多模式语义一致。

### B. +0x62C 家族与写点全集（KF2）
`disp_hits_field(0x62C)` 全镜像 **18 处**，与 B_field62c.txt 逐 VA 一致；W 命中 7 处：0x665EDE、0x671836、0x6836D2、0x684174、0x684195、0x71106E、0x71463F。我对每处独立回溯 0x40 字节窗口找 `[0xA8B230]` 装载：0x55D826/0x6840BC/0x684174/0x684186/0x684195/0x6841A0 全部命中 `mov reg,[0xA8B230]`；0x6836D2 的 ebp 由 0x683610 序言 `mov ebp,ecx`（0x68361A，fastcall this=Scenario）落实。**Scenario+0x62C 的写点恰 3 处**：0x6836D2 `mov [ebp+0x62C],ebx(0)`、0x684174 `inc [eax+0x62C]`、0x684195 `mov [ecx+0x62C],eax`（dec eax@0x684194 后写回）。其余 4 个 W（0x665EDE/0x671836/0x71106E/0x71463F）的所在函数窗口内**均无** [0xA8B230] 引用，且 0x665650 经 0x52BABE `push 0x18C0`→new→ctor→存 [0x8871E0]（伴生单例）确认非 Scenario——排除成立。

### C. [0xA8B230] 身份（KF3）
独立复现：refs=1293 / writes=3。0x52BA60 起：`push 0x3740; call 0x7C8E17`（new，对象大小 0x3740）→ `mov ecx,eax; call 0x6832C0` → 0x52BA94 `A3 30 B2 A8 00` 存实例；分配失败 je 0x52BAB6 `89 1D 30 B2 A8 00` 置空 ✓；0x6BEB7D `89 1D 30 B2 A8 00`（delete 后置空）✓。ctor 链：0x6833DB `call 0x683610` ✓；0x6835E1 `push 0x83D838`（push 0x158=行号 344，assert 形态）→ 串解出 `D:\ra2mdpost\Scenario.CPP` ✓；0x683610 序言 `mov ebp,ecx`（ebp=Scenario）后 `C7 85 14 02 00 00 40 F4 0F 00`→**[ebp+0x214]=0xF4240=1,000,000** ✓、[ebp+0x20C/0x210]=0x2BB、[ebp+0x60C/0x610]=1、重置 +0x614/+0x620 两计时器、**[ebp+0x62C]=0@0x6836D2、[ebp+0x630]=0@0x6836D8**、以 [0xA8ED84] 武装 [ebp+0x11E8] ✓。**外部锚（本仓原文核对）**：YRpp `ScenarioClass.h:58` `static constexpr reference<ScenarioClass*, 0xA8B230u> const Instance{}`、`:86` `ScenarioClass(){THISCALL(0x6832C0);}`、`:102` `DWORD unknown_62C;`、`:103` `WORD unknown_630;`。布局自洽反推：sizeof(Randomizer)=0x3F4（`Randomizer.h` bool+Next1+Next2+Table[0xFA]）⇒ Difficulty1/2@0x60C/0x610、**ElapsedTimer@0x614、PauseTimer@0x620**（TimerStruct=12B）、unknown_62C@0x62C——与 0x683610 重置块的写序完全吻合，报告的 +0x614/+0x620 命名获布局级确认。

### D. 挂起/释放函数与时钟（KF4/KF11）
0x6C8C40=`FF 15 30 15 7E 00 / C1 E8 04 / C3`=timeGetTime()>>4（16ms/刻）✓。0x684060 全函数：esi=ecx=时长秒、时长=0 跳过计时器设置、`lea ecx,[esi+esi*2]; lea ecx,[ecx+ecx*4]; shl ecx,2`=**×60** → [0x628]=时长×60 ✓、[0x620]=now ✓、[0x630] 已为 1 则 `jne 0x68417A` 直退**不加计数** ✓、置 [0x630]=1、counter==0 首挂 call 0x406F00、SP 判别 [0xA8B238]、ElapsedTimer 冻结（[0x614]≠-1 → acc+=now-start、start=-1@0x684102）✓、[0x35A2]→[0xB054CC]（refs=2，唯一 W=0x68411B）✓、恢复序列 [0x887640] vtbl+0x28/0xC、[0x35A2]=1、[0xA8ED9C]=1、call 0x54F720、[0xB07784]=0、尾 `inc [eax+0x62C]` ✓。0x684180：counter==0 直退、`48` dec + 0x684195 写回、再读==0 进恢复块 ✓；re-arm：0x68421E cmp [eax+0x614],-1 → 0x68422C call clock → [esi]=now ✓。镜像：[0xA8ED9C] W 含 0x684159=1/0x6841FC=0 与主循环 0x48CE73 刷新 ✓；[0xB07784] W 含 0x684165/0x68420D/0x684282/0x6842E5=0 与 0x55DE94=edi（MLF 追帧）✓。渐变机：[0xA9FAB0] state 写点全在 0x53Bxxx（0x53B4F7=1、0x53B58D=2、0x53B68F=3、0x53B732=0）；[0xA9FA98] 计数 W 含 **0x53B597=0x2D**（45）✓；[0xA9FAA8] 唯一 W=0x53B4F1、[0xA9FAD1] 唯一 W=0x53B549 ✓；[0x887324] W 含 0x6853BF（场景重建）✓；泵 0x5D4D50 头 `mov eax,[0xB73550]`+`mov [0xAA0430],ebx`（inc 后写回）✓。

### E. 调用点普查与执行集（KF5/KF6/KF7）
E8 直接调用全镜像普查：call 0x684060 = **4** {0x53B612, 0x657CA0, 0x6DF703, 0x6E4086}（数目✓；原报告 VA 0x6DF6FD/0x6E4080 是装参 `mov ecx,[esi/ecx+0x90]`（6 字节）的地址，call 指令在其 +6）；call 0x684180 = **3** {0x53B6E6, 0x55D81C, 0x657CC8} VA 全同 ✓；call 0x53B460 = **2** {0x6DFAC5, 0x6E2F96} ✓；call 0x55E160 = **2** {0x55D854, 0x55DE9A} ✓；call 0x53B560 = 2 {0x53A747, 0x55D83A} ✓。`u32(0x872E78)=0x6E4080` ✓。0x53B610=`33 C9` 且 capstone 直接印 `xor ecx, ecx`（时长=0）✓。冻结体 0x55D830..0x55D877 直接 call 5 个（0x5D4D50/0x48D080/0x53B560/0x4F4480/0x55E160）+ 虚调 `FF 52 5C`（[0x887324] vtable+0x5C）= 6 项执行集 ✓。返回值：0x55D859 `mov cl,[0xA8E9A0]`、0x55D863 `test cl,cl`、0x55D86D `sete al` ⇒ **al=([0xA8E9A0]==0)**，字节 `5F 5E 84 C9 5D C6 05 58 CD AB 00 00 0F 94 C0 5B 81 C4 B4 01 00 00` 与报告逐字节相同，[0xABCD58] 帧尾清零 ✓。0x55E160：0x55E2B4 起 SP 分支用 [0x887350]/[0x887348]，`call edi`（edi=[0x7E11F0]=Sleep）@0x55E279/0x55E2AD，[0x887330] 目标间隔在列 ✓。INC 块字节 `8B 15 84 ED A8 00 / A1 84 77 B0 00 / 42 / 3B C7 / 89 15 84…`（0x55DE7E=inc edx、0x55DE81=mov [0xA8ED84],edx）✓。

### F. CFG（KF9）
`func_rets(0x55D360,0x55DEE0)` = {0x55D877, 0x55DEC7, 0x55DEDB} ✓；`reach_without(0x55D360,0x55DEE0,0x55DE73,0x55DE84)` 过滤 ret = **{0x55D877, 0x55DEDB}**，0x55DEC7 不可达 ✓——冻结出口口径成立。

### G. 预测子句的一处字节矛盾（降 PARTIAL 的唯一实质原因）
prediction 称「带 PauseTimer 的挂起会在到期后由 MLF **每帧 dec 一次直到 0**」。字节：到期帧 0x55D815 `mov byte [edx+0x630],0` 清武装旗标 → 下一帧 0x55D7DA 读旗标=0 → 0x55D7E2 `je 0x55D821` **跳过整个计时器块**，直接 test counter——不再 dec。即 dec 只发生一次；counter>1 时余量不会被 MLF 自动释放（与报告 §1.2「旗标=0 时直接跳过计时器块……无计时器挂起不被自动释放」自洽，prediction 子句口误）。counter=1 的常见情形（单次挂起）行为与 prediction 一致。

---

## 3. 与本仓既有记载的对账

| 项 | 既有记载 | 本次复核 | 裁决 |
|---|---|---|---|
| [0xA8B230]=GameLogic（任务基线） | 1293/3 | 数目一致；身份=ScenarioClass::Instance（字节三重链 + YRpp ScenarioClass.h:58/86 + atlas 2157「ScenarioClass 实例」） | 原报告纠正**正确** |
| docs/re/ARCHITECTURE_ATLAS.md:2138/2157 | 记 ScenarioClass::Instance | 原文核对一致（2157 行注释「ScenarioClass 实例」） | 原报告 conflict 陈述属实 |
| MLF 3 rets / 免-inc 可达 / 1007/10 / 46/1 / 1293/3 | 台账基线 | 全部一致 | **一致** |
| INC 块 0x55DE73..0x55DE84 / 0x55DE7E+0x55DE81 | 基线 | 字节一致 | **一致** |
| G_TICKTGT=0x887330 / 0x7E11F0=Sleep / 0x7E1530=timeGetTime | ra2tool.py:40 与台账 | 0x55E1C7 读 [0x887330]、IAT 双解 ✓ | **一致** |
| 任务标题「世界更新照跑」 | 任务书 | 冻结体 6 项执行集无任何世界更新调用（正常体目标全被跳过） | 原报告纠正**合理** |

## 4. 诚实账

**核验没做的：**
1. 真机判据未执行（零真机铁律），prediction 的运行时半边只能静态背书。
2. 4 个外来 [x+0x62C] 写点（0x665EDE/0x671836/0x71106E/0x71463F）所在对象未定名——仅以「其函数内无 [0xA8B230] 引用 + 0x665650=0x8871E0 单例 ctor + INI 键串形态」排除，未做全调用链证明。
3. 间接访问形态（rep movsd / memset 整对象拷贝）未排查（沿用原报告的已声明边界）。
4. 报告 §1.9「动作处理器区」归类与动作号，属原报告自报的强推测，本次未另行取证。

**发现的偏差（均注记级，不动摇 headline）：**
1. **「正常体 28 个唯一调用目标」是截断口径**：原 v5 脚本区间为 [0x55D878,0x55DE4F)；全正常体 [0x55D878,0x55DEC7) 实测 **32** 个（多出 0x55DE8F→0x684290、0x55DE9A→0x55E160、0x55DE9F→0x725C70、0x55DEA4→0x637270，其中两个原报告在 §2.3/§2.5 已单独提及）。多出的 4 个同样被冻结体跳过，主结论反而更强。
2. **inc 调用点 VA 表述**：0x6DF6FD/0x6E4080 是装参 mov（`mov ecx,[esi/ecx+0x90]`）的 VA；call 指令 VA=0x6DF703/0x6E4086。数目 4 无误。
3. **prediction「每帧 dec 一次直到 0」**与字节矛盾（§2-G），counter>1 时余量需显式释放或新挂起请求再武装。
4. **[0x624] 语义小注**：字节链确认「mov eax,[esp+8] → mov [edx+4],eax」（[0x624]=局部槽 [esp+8]），但原报告「=参2」的语义解释存疑——4 个调用点（0x53B612/0x657CA0/0x6DF703/0x6E4086）均无栈参 push，[esp+8] 够不着栈参数；且全镜像 530 处 call 0x6C8C40 前「lea ecx,槽」的模式与 0x6C8C40 不写内存的字节并存，未解。该字段不进入任何 keyFact 主链与真机判据（判据只读 [0x620]/[0x628]）。
5. coverage 显示 99.9984%（原报告 100.00% 为四舍五入），insns/resync 完全一致。

**本次核验自身可能出错的：** 我的复算脚本 branch-target 第 8 条手写 rel 笔误（已由 capstone 仲裁）；verify_aux 的 ctx230 窗口仅 0x40 字节，跨基本块的基址追踪弱于原报告 provenance 启发式——但 A 档 6 处全部命中，不影响结论。

## 5. 复算入口

```bash
cd D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/P01
python -I -X utf8 verify1_all.py            # 全部 keyFact 独立复算（~4min，引擎全量重同步解码）
# 单点（示例）：
python -I -X utf8 -c "
import sys; sys.path.insert(0, r'D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104')
from ra2tool import Engine
eng = Engine(); print(eng.coverage)
print(eng.disasm(0x55D7C2, 0xC0))            # 冻结段逐字节
print([h for h in eng.disp_hits_field(0x62C) if h[1]=='W'])  # 7 处 W
print(eng.disp_hits(0xA8B230).__len__())     # 1293
print(eng.rd(0x53B610, 2).hex())             # 33c9
"
# 外部锚：YRpp/ScenarioClass.h:58,86,100-103；YRpp/SessionClass.h:54,56；YRpp/GeneralDefinitions.h:670；docs/re/ARCHITECTURE_ATLAS.md:2157
```
