# NAMED-PUSH — S11 批次 B1（前 18 行）· 最终报告

> 状态：**完成**。先建目录 → 先写 REPORT 骨架 → 逐行核完即落 `EVIDENCE/`。

## 批次信息
- 子系统：**S11** ｜ 批次：**B1**（`p3b2_named == True` 且非伪名，按 entry 升序前 18）
- 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S11_B1`
- 目标：`ra2youli\gamemd.exe`，SHA-256 现场复算 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（与卡面期望一致）
- ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)`（VirtualSize 口径，与卡面一致；18 个 entry 全在其内）
- 工具：Python 3.12.10 + capstone 5.0.7（`skipdata=True`）+ pefile 2024.8.26；无 venv、未 pip install
- 只写本批目录：`REPORT.md / PROGRESS.md / delta.tsv / base_rate.tsv / EVIDENCE/ / work/`；未改 `coverage.tsv`、`PANEL.md`、`R14_COMMON.md`、台账、`SURVEY_3B2`、`S04_PUSH_*`

## 筛选命令（照卡面）
```bash
cd D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S11_B1\work
python filter_b1.py
```
```python
rows  = list(csv.DictReader(open(SURVEY_3B2/hits_detail.tsv, encoding="utf-8"), delimiter="\t"))
s11   = [r for r in rows if r["subsystem"] == "S11"]
named = [r for r in s11 if r["p3b2_named"] == "True"]
real  = [r for r in named if not r["name"].split("::")[-1].startswith(("fn_", "sub_"))]   # 排除伪名
real.sort(key=lambda r: int(r["entry"], 16))
batch = real[:18]
```
筛选结果：S11 命中 **31** → `p3b2_named=True` **29** → 其中 `fn_/sub_` 伪名 **0**（S11 这一族全是 `XxxLocomotionClass::slotN`）→ 可用 29 → 取前 18。

## D-40 四环口径（严格，按卡面 + 本批三陷阱）
1. **① 入口**：`.text` 内、函数边界自洽（atlas 边界 + 入口首条即指令 + 单一 ret 收尾）
2. **② 类身份**：`.rdata` 槽内 4B == entry → 回扫 `[vt-4]=COL(sig=0)` → `[COL+0xC]=TD` → `TD+8` 类名字串；`Class::` 部分只作线索；**并强制陷阱③**：该 vtable 必须是**对象主虚表**（`COL.offset==0` 且构造器把它装到 `[this+0]`、表首槽是真函数而非 this 调整 thunk），小成员表/副表不算
3. **③ 整体合同**：只认 ③b②，判据三条同时满足：(A) `call` → `test/cmp eax` → `jcc`，两指令间无 eax 覆写；(B) 被调返回约定字节可伪证（≥2 个出口常量且含具名错误码/哨兵，多值状态码算，`{0,1}` 布尔不算）；(C) 两路动作实质不同——一路**立即 epilogue 原样上抛**，另一路继续主流程（"多调一次清理再汇合"不算）
4. **④ 使用见证**：活虚表派发——构造器把该 vtable 装进 `[this+off]`，构造器由 `push size; call operator new; mov ecx,eax; call ctor` 唯一实例化；entry **direct caller = 0**（非 direct-only）；**㉓ 锚点不得落在析构器**
5. **②④ 不同源**：② 锚 `.rdata` RTTI 字节链，④ 锚 `.text` 安装指令 + 实例化链

## 本批总表（18 行逐行核完）

| # | entry | name（原样） | ① | ② 类身份 | ③b | ④ 见证 | 四环 | 产出 |
|---:|---|---|---|---|---|---|---|---|
| 1 | 004AF610 | DriveLocomotionClass::slot6 | ✓ | ✗ 副表 COL.offset=0x18 | ✗ | ✓ | 否 | 否 |
| 2 | **004AF720** | DriveLocomotionClass::slot0 | ✓ | ✓ 主表 COL.offset=0 slot#0 | ✓ | ✓ ctor 004AF540 @004AF5C2 | **是** | **[已证]** |
| 3 | 004B5B70 | DropPodLocomotionClass::slot16 | ✓ | ✗ 副表 offset=4 | ✗ | ✓ | 否 | 否 |
| 4 | 004B6040 | DropPodLocomotionClass::slot17 | ✓ | ✗ 副表 offset=4 | ✗ | ✓ | 否 | 否 |
| 5 | **004B62C0** | DropPodLocomotionClass::slot6 | ✓ | ✓ 主表 offset=0 slot#6 | ✓ | ✓ ctor 004B5AB0 @004B5ADD | **是** | **[已证]** |
| 6 | **004B6470** | DropPodLocomotionClass::slot0 | ✓ | ✓ 主表 offset=0 slot#0 | ✓ | ✓ ctor 004B5AB0 @004B5ADD | **是** | **[已证]** |
| 7 | 004B64E0 | DropPodLocomotionClass::slot6 | ✓ | ✗ 副表 offset=0x18 | ✗ | ✓ | 否 | 否 |
| 8 | 004CCB40 | FlyLocomotionClass::slot16 | ✓ | ✗ 副表 offset=4 | ✗ | ✓ | 否 | 否 |
| 9 | 004CCC80 | FlyLocomotionClass::slot17 | ✓ | ✗ 副表 offset=4 | ✗ | ✓ | 否 | 否 |
| 10 | 004CCFD0 | FlyLocomotionClass::slot18 | ✓ | ✗ 副表 offset=4 | ✗ | ✓ | 否 | 否 |
| 11 | 004CF610 | FlyLocomotionClass::slot9 | ✓ | ✗ 副表 offset=4 | ✗ | ✓ | 否 | 否 |
| 12 | 00514310 | HoverLocomotionClass::slot16 | ✓ | ✗ 副表 offset=4 | ✗ | ✓ | 否 | 否 |
| 13 | 00516CA0 | HoverLocomotionClass::slot25 | ✓ | ✗ 副表 offset=4 | ✗ | ✓ | 否 | 否 |
| 14 | 00516E10 | HoverLocomotionClass::slot26 | ✓ | ✗ 副表 offset=4 | ✗ | ✓ | 否 | 否 |
| 15 | 0054B1C0 | JumpjetLocomotionClass::slot17 | ✓ | ✗ 副表 offset=4 | ✗ | ✓ | 否 | 否 |
| 16 | 0054DB50 | JumpjetLocomotionClass::slot6 | ✓ | ✗ 副表 offset=0x18 | ✗ | ✓ | 否 | 否 |
| 17 | **0054DC60** | JumpjetLocomotionClass::slot0 | ✓ | ✓ 主表 offset=0 slot#0 | ✓ | ✓ ctor 0054AC40 @0054ACC3 | **是** | **[已证]** |
| 18 | 006622C0 | RocketLocomotionClass::slot16 | ✓ | ✗ 副表 offset=4 | ✗（无站点） | ✓ | 否 | 否 |

`base_rate`：`rows_checked=18  ring2_ok=4  ring3b_ok=4  ring4_ok=18  all_four=4  rate=0.2222`

## 逐环裁定依据

### ① 入口 —— 18/18 PASS
每个 entry 都是 atlas 的函数起点（`atlas_func_of(entry)==entry`，size 93–377），入口首条即指令边界（`push ebx` / `mov eax,[esp+0xc]` 等），收尾为单一 `ret`/`ret 0xc`，无跨函数拼接。

### ② 类身份 —— 4/18（**这是本批的决定性环**）
**18/18 的 RTTI 都能解析出线索类名**，但按陷阱③只有 4 行落在**对象主虚表**：

- 全镜像 4B 引用：**每个 entry 恰好 1 处，全在 `.rdata` 的 vtable 槽；`.text` 内 0 处** ⇒ 既无 direct caller 也无立即数引用，只能虚表可达。
- 按 RTTI COL 反查每个 Locomotion 类的**全部 vtable**，发现每类都有 3 张表，且 `COL.offset`（MSVC `RTTICompleteObjectLocator` 的 offset 字段）把它们钉得很干净：

| 类 | COL.offset=0（主表） | COL.offset=4（48 槽副表） | COL.offset=0x18（8 槽副表） |
|---|---|---|---|
| DriveLocomotionClass | 007E7F7C / slot0=004AF720 | 007E7EB0 / slot0=004B4D90（thunk） | 007E7E8C / slot0=004B4DC0（thunk） |
| DropPodLocomotionClass | 007E8344 / slot0=004B6470 | 007E8278 / slot0=004B6740（thunk） | 007E8254 / slot0=004B6770（thunk） |
| FlyLocomotionClass | 007E8AC0 / slot0=0055A9B0 | 007E89F4 / slot0=004D0510 | — |
| HoverLocomotionClass | 007EADC8 / slot0=0055A9B0 | 007EACFC / slot0=004D0510 | — |
| JumpjetLocomotionClass | 007ECE34 / slot0=0054DC60 | 007ECD68 / slot0=0054DFF0（thunk） | 007ECD44 / slot0=0054E020（thunk） |
| RocketLocomotionClass | 007F0BE8 / slot0=0055A9B0 | 007F0B1C / slot0=004D0510 | — |

- **副表判定证据**（陷阱③）：副表 slot0 的字节是 `83 6C 24 04 E9 …` / `83 6C 24 18 E9 …`，即 `sub dword ptr [esp+4], N; jmp <真实函数>` 的 **this 调整 thunk**；安装点是 `mov [esi+4], vt` / `mov [esi+0x18], vt`（子对象偏移），不是 `[this+0]`。卡面给的副表 slot0 `004105E0`（`sub [esp+4],4; jmp 0x410260`）、`00410580`（`xor al,al; ret 8`）、`00410590`（`ret 4`）与之一一对应同型。
- **主表判定证据**：COL.offset==0；构造器 `mov [esi], vt`（esi=ecx=this）落在 `[this+0]`；表首槽是真函数（`53 8B 5C 24 08 55 8B 6C` = `push ebx; mov ebx,[esp+8]; push ebp; mov ebp,[esp+0x14]`），不是 thunk。
- **阳性对照**：同类判据作用在 S22 已知主表 `007EF890`（ParasiteClass）上得 `COL.offset=0`、slot0=`00410260`——与卡面"主表 slot0 常见 00410260"自洽。本族 4 张主表的 slot0 不是 00410260 而是**类级 QI**（`004AF720`/`004B6470`/`0054DC60`，字节同模板的 `push ebx; mov ebx,[esp+8]…`），故判据不能用"slot0 是否等于 00410260"硬套，改用 `COL.offset==0 + thunk 排除 + 安装偏移 [this+0]` 三条独立字节证据。

⇒ **② 只 4 行成立**（004AF720 / 004B62C0 / 004B6470 / 0054DC60）；14 行的 entry 只出现在副表，按陷阱③ 不算类身份，判 FAIL。**这 14 行不是"没名字"，而是"名字落在子对象接口表上"。**

### ③ 整体合同 —— 4/18（全部 ③b②）
4 行成立，两类站点：

1. **三行同模板的 QueryInterface 实现**（004AF720 / 004B6470 / 0054DC60，字节级同模板、地址各异）：
   - `call 0x55A9B0`（基类 QI）→ 零间隔 `cmp eax,0x80004002` → `jne`
   - 被调多值返回约定可伪证：`0055A9BD mov eax,0x80004003; ret 0xc`（E_POINTER）、`0055AA46 mov eax,0x80004002; ret 0xc`（E_NOINTERFACE）、`0055AA4F xor eax,eax → 0055AA51 ret 0xc`（S_OK）
   - taken 路 = `pop esi/ebp/ebx; ret 0xc`（eax 不碰，基类 HRESULT 原样上抛，跳过全部 IID 逻辑）；fall 路 = `mov ecx,4; mov edi,0x7E9B10; repe cmpsd` 比 16B IID → 命中 `lea eax,[ebx+0x18]`/`mov [ebp],eax`/`call [ecx+4]`(AddRef)/`xor eax,eax`；未命中返 E_NOINTERFACE
2. **一行流读入助手**（004B62C0）：`call 0x55AA60` → 零间隔 `test eax,eax` → `jl`；被调 `0055AA6B mov eax,0x80004003`+`0055AA71 ret 0xc`（E_POINTER）/ `0055AAA4 jl` 透传内层流 Read 负 HRESULT / `0055AAB4 ret 0xc` 不碰 eax；taken 路 `pop edi; pop esi; ret 0xc` 原样上抛，fall 路继续 `call [ecx+0x10]` 读流、`call [ecx]`、`call 0x4B4D60`、`call [0x7E15F4]` 等实质工作

**未成立 14 行逐行理由**（各自独立地址）：
- `004AF610` / `004B64E0` / `0054DB50`：唯一站点 `call 0x45AEA0` → `test eax,eax` → `jge`，失败侧只多一次 `cmp eax,0x80004002; je` + `call 0x7DC720` 清理，随后**汇合到同一处**继续 → 不满足判据(C)（无 early-return 分离）；另两站点是 `call [ecx+0xc]` 间接、两路签名相同。
- `004B5B70`：站点 1 `call [edx+0x1c8]` → `cmp eax,ebx` → `jg`（间接虚调用，callee 不可定位）；站点 2–4 是 `call 0x7C8E17`（operator new）后的空指针判断（等同布尔）⇒ 均不成立。
- `004CCC80` / `004CF610` / `00516E10` / `0054B1C0`：站点全是**间接虚调用**（`call [edx+0x1c8]` / `[edx+0x2c]` / `[ebx+0x1ac]` / `[eax+0x184]` 等）或 `call 0x7DC720`（free 包装，无返回约定）⇒ callee 不能由字节定位，返回约定不可伪证（判据 B 失败）。
- `004B6040`：唯一站点是 `call 0x7C8E17`（operator new）后的空指针判断 ⇒ 指针空/非空，等同布尔，不算多值状态码。
- `004CCFD0`：站点 `cmp eax,2` / `cmp eax,1` 对比的是间接调用的返回值，callee 不可解析，且常量是小的枚举值 ⇒ 不可伪证。
- `00514310`：`call 0x65AD30` 实为**数组取值器**（`mov eax,[ecx+0xe4]; mov eax,[eax+ecx*4]; ret 4`），返回指针/null，非状态码；另两站点是间接调用。
- `00516CA0`：`call 0x47C520` 出口常量只有 `{0}`（单值）⇒ 不可伪证。
- `006622C0`：函数体内**没有任何** `call → test/cmp eax → jcc` 站点（sites=0）⇒ ③ 不成立。

**三陷阱排查**：4 行成立行的 `test/cmp` 与 `jcc` 均**两条相邻指令**（无反间 eax 覆写，见各 EVIDENCE 的字节）；每个 entry 到其被调的 call 各仅 1 处（非多路同一 call）；语义均由字节支撑，无"初始化/清零"模板句；无一行是 ③a（单调用+单写/纯转发）。

### ④ 使用见证 —— 18/18 PASS，但只有 4 行能与 ② 同时成立
- **锚点**：每行的 vtable 都有构造器安装点 `mov [esi], vt`（主表）或 `mov [esi+4]/[esi+0x18], vt`（副表），所在函数均**先调基类构造器 `0x55A6C0`**（不是重置基类 vptr 的析构体 `0x55A6F0`），尾 `mov eax,esi; … ret` 返 this：
  Drive `004AF540`(size 154) / DropPod `004B5AB0`(69) / Fly `004CC9A0` / Hover `00513C20` / Jumpjet `0054AC40`(185) / Rocket `00661EC0`
- **实例化链**（证明对象真的活着）：每个构造器都**只有 1 个直接调用者**，且形如 `push <size>; call 0x7C8E17(operator new); add esp,4; test eax,eax; je; mov ecx,eax; call <ctor>`：
  Drive `006C403C push 0x70` → `006C403E call 0x7C8E17` → `006C404C call 0x4AF540`；
  DropPod `006C493C push 0x30` → `006C494C call 0x4B5AB0`；
  Jumpjet `006C41BC push 0x98` → `006C41C1 call 0x7C8E17` → `006C41CF call 0x54AC40`
- **非 direct-only**：4 个 entry 的 direct caller = **0**，只能经活虚表派发。
- **㉓ 成对陷阱**：每类都存在删除式析构器（`test byte [esp+8],1` + `call 0x7C8B3D`），且其体内有同表重装点——Drive `004B4D00`（重装 `004B4D03`，free `004B4D33`）、DropPod `004B66F0`（`004B66F3` / `004B6723`）、Fly `004D03A0`（`004D03A9` / `004D03BD`）、Hover `005172C0`（`005172C9` / `005172DD`）、Jumpjet `0054DFA0`（`0054DFA3` / `0054DFD6`）、Rocket `006635C0`（`006635C9` / `006635DD`）。**④ 一律不取这些点**，改锚构造器。
- **②④ 不同源**：② 的锚是 `.rdata` 的槽 dword + COL + TD 名串字节；④ 的锚是 `.text` 的 `C7 06 <vt>` 安装指令 + operator new 实例化链。段、地址、指令类型都不同。

## 与 S04 的败因对比（本批有多少行 ② 真的钉住了）

- **S04**：73 个 ③b② 机械命中 `named=0`，entry 作 4B VA 全镜像 0 引用、无虚表槽、无可回扫 RTTI 链 ⇒ ② **物理不可得**（不是判定问题，是候选池没有身份），36 行实测全败。
- **本批 S11**：18/18 全部 `p3b2_named=True`、**名字都是 `Class::slotN`（0 个 `fn_/sub_` 伪名）**，且 18/18 entry 在 `.rdata` 都有虚表槽、RTTI 都解析出与线索一致的类名 ⇒ **"有名字"确实解开了 S04 的死结：② 从 0/73 变成 18/18 有 RTTI 链**。
- 但本批发现的是**第二个、更细的 ② 缺口**：S11 是 Locomotion 族（多继承 COM 对象），每个类有 1 张主表 + 2 张子对象接口表，**14 行的槽落在子对象副表上**（`COL.offset=4`/`0x18`，slot0 是 this 调整 thunk、安装偏移 `[this+4]`/`[this+0x18]`）。按卡面陷阱③"小成员表 vtable 不是对象主虚表"，这 14 行的类身份不能成立 ⇒ 严格口径下 **② = 4/18**。
- 换句话说：S04 的败因是"没名字 ⇒ 无 RTTI 链"；本批的败因是"有 RTTI 链但 14 行挂在副表上"。**如果 Lead 采"副表 RTTI 也认类身份"的宽口径，② 会是 18/18，四环齐全 = 4 行（仍只这 4 行，因为 ③ 也只有 4 行成立）**——即宽窄口径下 **产出都是 4 行**，差别只在 ② 的报数（4 vs 18）。这一点请 Lead 定标。
- 另与 `S10_B1/S10_B2`（②18/18、④0/18、产出 0）不同：本批 ④ 在 18/18 都成立（构造器安装点 + operator new 实例化链），所以瓶颈从 ④ 移回 ②③。

## 待裁（2 项，未擅自扩面）
1. **副表 RTTI 是否算 ②**：本批 14 行的 vtable 是子对象接口表（COL.offset≠0、slot0 为 this 调整 thunk）。我按卡面陷阱③判 ② FAIL。若 Lead 认"RTTI 类名即类身份、不看主/副表"，则 ② 报 18/18，但 **all_four 仍为 4**（③ 只有 4 行成立），`rate` 仍 0.2222。
2. **③ 判据(C) 的宽严**：`004AF610`/`004B64E0`/`0054DB50` 的站点是 `call 0x45AEA0(nullable 流 QI) → test/jge`，失败侧先 `cmp 0x80004002` 再把非 E_NOINTERFACE 的负值交 `0x7DC720` 清理后**汇合**主流程。我判"无 early-return 分离 ⇒ 不成立"。若认"返回值被三级具名分支消费即算"，这 3 行 ③ 可从 4 → 7（但 ② 仍 FAIL，all_four 不变）。

## 产出清单
- `REPORT.md`（本文件）
- `PROGRESS.md`
- `delta.tsv`：**4 数据行**，全部 `[已证]`，`entry` 大写无 `0x`，`name`/`subsystem` 原样
- `base_rate.tsv`：`NAMED_PUSH_S11_B1	18	4	4	18	4	0.2222`
- `EVIDENCE/ROW_<entry>.txt` × 4（`004AF720` / `004B62C0` / `004B6470` / `0054DC60`）：逐环地址 + 机器码字节 + 逐行裁定
- `work/`：`filter_b1.py`（筛选）、`core.py`（PE+capstone+RTTI/虚表/安装点库）、`probe.py`、`families.py`（按类枚举全部 vtable）、`col_offset.py`（COL.offset 判主/副表）、`analyze.py`（③b 站点 + ④ 安装点）、`fstart.py`（atlas 函数边界）、`verify_base.py`（基类 ctor/dtor 区分）、`ctors.py`（实例化链）、`ring4.py`（18 行安装点归属）、`gen_evidence.py`（证据生成，数值全现场计算）、`chk.py`/`chkdtor.py`（数值复核）；输出 `probe.json`、`vtables.json`、`vtables2.json`、`analysis.json`、`calls.pkl` 及 `*.txt` 转储
