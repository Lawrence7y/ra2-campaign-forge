# NAMED_PUSH_AUDIT15 — 异族独立审计 SUMMARY

## 范围

本次只审 **2 行**，来自两个不同批次（执行器均为 **Hy4**；本审计员为异族）：

| # | 来源 | entry | subsystem | delta 自报 name |
|---|---|---|---|---|
| 1 | `NAMED_PUSH_S18_B4/delta.tsv` | `007B10C0` | S18 | `IPXInterfaceClass::slot15` |
| 2 | `NAMED_PUSH_S09_B1/delta.tsv` | `004F45B0` | S09 | `MouseClass::slot17` |

**取法**：两个 `delta.tsv` 都是 6 列（`entry subsystem name one_line_semantics grade evidence_path`），各只有 1 个数据行；取第 2 行全部字段，表头不计。

**镜像**：`D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`，本地 SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（与卡片期望一致）。ImageBase `0x400000`，`.text=[0x401000,0x7E038D)`。
**工具**：Python 3.12.10 + capstone 5.0.7（`skipdata=True`）+ pefile 2024.8.26，无 venv、未 pip install。
**证据纪律**：`delta.tsv` / `REPORT.md` / `EVIDENCE/ROW_*.txt` 只当地址线索，**一处未作证据**；下列全部结论出自本审计员对字节的独立反汇编（`work/auditlib.py`、`work/r1_vt.py`、`work/r1_rtti2.py`、`work/r1_imports.py`、`work/r1_ctor.py`、`work/r1_main.py`、`work/r1_final.py`、`work/r2_vt.py`、`work/r2_main.py`、`work/r2_sites.py`、`work/r2_callee.py`、`work/r2_branch.py`、`work/r2_global.py`、`work/final.py`）。

## 判定

- **报告行数 2 / PASS 2 / FAIL 0**

| entry | subsystem | verdict | ② 主虚表（槽→entry） | ③b | ④ | ④≠② | ㉓ | ⑤ |
|---|---|---|---|---|---|---|---|---|
| `007B10C0` | S18 | **PASS** | `0x007F794C` slot15 @`0x007F7988` | 3b2 | ctor `0x7B0DA4` | no | 不适用（全镜像仅 1 写点） | ✓ |
| `004F45B0` | S09 | **PASS** | `0x007E1964` slot17 @`0x007E19A8` | 3b2 | ctor `0x005BDA4A` | no | **真陷阱存在**，已避开 | ✓（1 处引证错） |

## FAIL 逐条原因

- **无**（本批 2 行均 PASS）。

## 三个判据要点专项结论

### 要点一 · ② 是否用主虚表（不是小成员表）—— **2 行都是主虚表**

- `007B10C0`：`0x007F794C`，`[vt-4]`@`0x007F7948` = COL 指针 `0x0080EA60`；COL 字节 `00…00 | F8 D8 84 00 | 50 EA 80 00` ⇒ **`offset=0`**；TD @`0x0084D8F8` 名串 `. ?AVIPXInterfaceClass@@`；构造器在 `0x7B0DA4` 装到 **`[this+0]`**；整表 24 槽、槽值成建制落在 `0x7B1xxx`。类层次旁证：BCD 解出基类 `. ?AVWinsockInterfaceClass@@`。`TD` 全镜像只出现 2 次（本 COL 的 pTD 字段 + 一个 BCD）⇒ **不存在第二张同 TD 的 COL**；entry 作为指针全镜像**只出现 1 次**。
- `004F45B0`：`0x007E1964`，COL `0x007FAB38` **`offset=0`**，TD `.?AVMouseClass@@`。**同时排掉副表**：MouseClass 另有 `0x007E195C`，其 COL `0x007FA9B8` 为 **`offset=0x5518`**、slot17 = `0x004F4480`（另一个函数）⇒ 本行取的是零偏移主表，与上一批 `006BFF90/006C0A10`（内嵌成员表误当主虚表）不同类。
- 说明 `004F45B0` 还出现在另外 8 张表（DisplayClass / GScreenClass / MapClass / TabClass / PowerClass / RadarClass / ScrollClass / SidebarClass），**全部是 slot17、COL.offset 全为 0**。按 §8.7 判据 1 已枚举全部持有表；「MouseClass::slot17」是这 9 个成立命名之一。

### 要点二 · ④ 锚点是否落在析构器里（㉓）—— **行 1 无此陷阱；行 2 陷阱真实存在，已避开**

这是本批最实质的差异，两行的 ㉓ 情况完全相反：

- **`007B10C0`：㉓ 物理不适用。** `0x7F794C` 在全镜像的 imm32 写点**恰好 1 处**（`0x7B0DA4`，`C7 06 4C 79 7F 00`），宿主 `0x7B0D90` 是**真构造器**（返 `this`、置 -1 初值、无 `call 0x7C8B3D`、无 `test byte[esp+8],1`、不向基类表回退）。该类 deleting dtor 写的是基类 `WinsockInterfaceClass` 的表，属 ㉓ 所述正常回退 ⇒ 不存在「活表 + 死表」成对争抢。
- **`004F45B0`：㉓ 成对陷阱真实存在，`0x7E1964` 的 4 个 imm32 写点里 2 个是析构器**：
  - `0x40D1B2` ∈ 函数 `0x40D1B0`，该函数由 `0x40D19A push 0x40D1B0` + `0x40D19F call 0x7C978A`（**atexit**，本审计独立核过：`0x7C978A` = `push [esp+4]; call 0x7C970C; neg/sbb/neg/dec; ret`，成功返 0 失败返 −1，紧邻 `0x7C979C` 分配 0x80 项表存 `0xB78BC0`/`0xB78BBC`）注册；本体是「装自身 vptr → 循环 4 次销毁子对象（`call 0x40AFD0`/`0x40D300`）→ `call 0x652C00` 基类析构」⇒ **全局非删除析构器 = ㉓ 定义的死表**。
  - `0x40D295` ∈ 函数 `0x40D290`：同样装自身 vptr + 销毁 4 子对象 + `call 0x652C00`，随后 **`0x40D2D9 test byte [esp+0x10],1` + `0x40D2E1 call 0x7C8B3D`** ⇒ **标量删除析构器 = 死表**。
  - 唯一合法的活表写点是 `0x5BDA4A` ∈ 函数 `0x5BDA40`：`call 0x692290`（基类 ctor）→ 装 `0x7E1964` 到 `[esi]` 与 `0x7E195C` 到 `[esi+0x5518]` → 清零字段 → **`mov eax,esi; ret`**（返 this）；唯一调用点 `0x40D195`，`ecx=0x87F7E8`（全局 MouseClass 实例，全镜像被引用 **3700** 次，是真活对象）。
  - ⇒ **本行 ④ 必须取 `0x5BDA4A`**。delta 未给 ④ 地址，既没踩雷也没给证；本审计补证并**显式剔除** `0x40D1B2`、`0x40D295`。若取这两处任一，按 ㉓ 即判 FAIL。
  - 这与 `M72/PANEL` 记录的 S07 情形同型（同一虚表也被析构器写入，因执行器 ④ 取在行外构造器而未触雷）——再次印证 **㉓ 不是形式检查，是真会命中的判据**。

### 要点三 · ③b 可伪证性（多值状态码 / `Find` 返 −1 算，`{0,1}` 布尔不算）—— **2 行都过，但强度不同档**

- **`007B10C0`：强档。** 用的是「`cmp eax,−1` 哨兵驱动分支」这一档：`0x7B114C 83 F8 FF` → `0x7B1156 75 28 jne`（中间 `mov [esi+0x3f06c],eax` 与 `pop edi` 都不动 eax/flags，**不是覆写陷阱**）。失败 = `INVALID_SOCKET = -1`，成功 = 有效 `SOCKET` 句柄（多值，非 {0,1} 布尔）；被调方经 IAT 独立解出为 `WSOCK32!socket/bind/setsockopt/WSAGetLastError/closesocket/htons`。共 5 处哨兵检查。旁证：`socket(6,2,1000)` = **AF_IPX**，与类名互相印证。
  - ⚠ 弱臂披露：第 3~5 处（setsockopt）两臂只差推入的日志串、随后汇合 ⇒ 属「同一 call 仅差参数」。③b② 的成立实质靠第 1、2 处（socket / bind）。
- **`004F45B0`：中档（依赖「字面 −1 返回」档，不是「`cmp −1` 哨兵比较」档）。** 站点 `0x4F45EF 85 C0 test` + `0x4F45F1 0F 85 4C 01 00 00 jne 0x4F4743`（第二站点 `0x4F4607`/`0x4F4609` 对 `[0x8A0E0C]` 同型），call→test 零间隔、零覆写。被调 `0x4A33A0` 返回域实测 **{−1 @`0x4A33BC` `83 C8 FF`; 1 @`0x4A3465`; 2 @`0x4A3581` `neg`/`sbb`/`and eax,2`; 0}** 外加一条 `[this]==2` 的透传 ⇒ **多值状态码，不是 {0,1} 布尔**，且含**字面 −1 返回**（命中 `MEASURE_F3A/CONTROLS.md` 第二档）。
  - ⚠ **消费侧是布尔坍缩**：`test eax,eax` 只判零/非零，把 `-1/1/2` 坍缩成同一臂。若日后把 ③b② 收紧到「必须 `cmp eax,−1` 级哨兵比较」，本行将只剩「字面 −1 返回」单腿 ⇒ **口径政策问题，请 Lead 按 D-46 决定**。本审计按现行口径判成立并显式披露。
  - ⚠ `jne` 目标 `0x4F4743` **同时是成功路的汇合点**（`0x4F473E call 0x4A3660` 之后顺序即落到 `0x4F4743`），形态与上一批被判死的 `007276A0`（公共续点、仅差 `sprintf("%d")`）同类；但本行两臂差异是整段工作体（约 `0x340` 字节、含 `0x4A35A0`×2 / `0x4A35F0`×4 / `0x4A3840`×2 / `0x4A3660` 共 7+ 次调用），量级远大于单条参数差异 ⇒ 本审计判「两路动作真不同」成立。

## 须入账备注（均不改变 PASS/FAIL，供 Lead 定政策与并表时写备注）

1. `007B10C0` 第 3~5 处 setsockopt 为弱臂（仅差日志串汇合）；executor 的「非同一 call 仅差参数」在**函数级**成立（socket/bind/setsockopt 是三个不同导入），在**三处 setsockopt 内部**不成立。
2. **本镜像 RTTI 的 `pTD`/`pCHD` 存绝对 VA（非 RVA）**：按 `IB+pTD_rva` 解会越界（`pefile` 抛 `PEFormatError`）。后续脚本若沿用旧 `parse_col` 会 fail-closed 误判「RTTI 读不到」。建议写进 `R14_COMMON` 技术条。
3. `004F45B0` 的 delta **完全没给 ②/④ 地址**（只给了 ③b 站点与被调方返回字节）；本审计独立补证：② = `0x007E1964` + slot17 @`0x007E19A8`，④ = `0x005BDA4A`。并表时 evidence_path 应指向本 VERDICT §④。
4. `004F45B0` 的 `0x7E1964` **4 写点中 2 处是析构器**（atexit 全局 dtor `0x40D1B2`、scalar deleting dtor `0x40D295`）——这是本批唯一真实命中的 ㉓ 陷阱形态，建议做成机械前置门槛：**同一 vt 的 imm32 写点若含 atexit 注册目标或含 `test byte[esp+N],1`+`call 0x7C8B3D`，该写点永久禁用作 ④**。
5. `004F45B0` delta 把 `0x4A3434 ret` 当「成功返 0」依据 **不实**：该处是 `[this]==2` 分支透传 `call [eax+0x14]` 的返回值，不保证 0；真正「成功返 0」在 `0x4A3581..0x4A3592`。结论本身仍成立，但引证张冠李戴（属「写值逐字符核对」纪律问题，非形态/方向错误）。
6. `004F45B0` 位于 **9 张表的 slot17**（MouseClass/Display/GScreen/Map/Tab/Power/Radar/Scroll/Sidebar），`MouseClass::slot17` 只是成立命名之一，不是 MouseClass 独有实现。
7. `007B10C0` 的 119 处 `call/jmp [reg+0x3C]` 已实测复现（`0x0040A6FD`、`0x00411FD5` 等），但无法逐点归属到 `IPXInterfaceClass` 对象 ⇒ **不作为 ④ 依据**，④ 只建立在构造器活表上。

## 交付物

- `VERDICT.md`：逐行五项结论 + 地址字节（含 ②/COL/TD、③b 站点表与被调方返回路径表、④ 四写点定性表）
- `verdict.tsv`：**2 行**，表头 `entry	subsystem	verdict	ring2_at	ring3b_form	ring4_at	same_source	reason`
- `SUMMARY.md`：本文件
- `work/`：全部反汇编脚本（可复算）
