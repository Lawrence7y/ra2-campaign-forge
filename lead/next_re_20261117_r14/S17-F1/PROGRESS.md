# S17-F1 · PROGRESS（≤60 行）

> 卡号 S17-F1｜静态双通道：capstone 5.0.7 `skipdata=True` + pefile + Ghidra `-noanalysis`（SLEIGH）
> 目标 `gamemd.exe` SHA-256 `73201CC0…F67476`（实测全串 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`），4,825,360 B，ImageBase `0x400000`。
> 等级：`[已证]`（双通道字节/反汇编一致）/ `[静态推断]`（单通道但逻辑闭合）/ `[未证]`。

## 核心数字（给审计）

| # | 数字 | 值 | 复算方法 |
|---|---|---|---|
| N1 | 存档总入口 | `0x67CEF0`（外层构造器）；核心 `0x67D300`（Save_Core） | `python work\analyze_main.py` §3 rel32 扫描：`0x67D300` 唯一调用者 `0x67D1AF`；`0x67CEF0` 4 调用者 |
| N2 | 被序列化类/块数 | **35 函数式模板块 + 28 内联向量块 + 标量块**（共 63 个向量级调度单元） | `work\analyze_main.py` §1：35 模板块（stride 0x80，35/35 OK）；`work\analyze_deep.py` §A：28/28 Count 全局 |
| N3 | Swizzle 字段数 | 每调用 1 个 `void**` 字段；样本 TEventClass **3 字段**（`+0x28/+0x30/+0x54`）；全镜像 **476** 登记点 | `work\analyze_boundary_iat.py` §3 + `work\analyze_main.py` §3 HereIAm rel32=476 |
| N4 | `0x67D300` 门控证据 | `0x55DBCD/DBD3/DBD9/DBDE/DBE0/DBEE/DC92` | `python work\analyze_deep.py` §D + `EVIDENCE\ghidra_dump.log` gating 段 |

## 结论表

| 项 | 结论 | 等级 | 证据路径 |
|---|---|---|---|
| 存档总入口 | `0x67CEF0` 存档文件构造器（1040 B，`StgCreateDocfile`+`SAVING GAME`+`call 0x67D300`）；非线索所说 "Load" | `[已证]` | `EVIDENCE\analysis_main.txt` §3/§4；`EVIDENCE\verify_bytes.txt` |
| Save_Core | `0x67D300`，4411 B / 1706 指令 / 52 直接 call / 唯一调用者 `0x67D1AF` | `[已证]` | `EVIDENCE\analysis_boundary_iat.txt` §2/§4 |
| Save_Core 类边界（双通道） | capstone last-ret `0x67E43B` → size 4411 = atlas `4411` | `[已证]` | `EVIDENCE\analysis_boundary_iat.txt` §2 |
| 写档门控 | `cmp [0xA8B238],0` + `test [0xABCE08]` + 一次性置位；进程内最多一次，非每帧 | `[已证]` | `EVIDENCE\analysis_deep.txt` §D；`EVIDENCE\ghidra_dump.log` |
| 35 模板块 | `0x67FDF0+0x80·i`，i=0..34；127 B 代码体 md5 全等 `9f6770a9cd27…`（35/35），128 B 口径 `cb13908da7ed…` | `[已证]` | `EVIDENCE\analysis_main.txt` §1；`EVIDENCE\analysis_deep2.txt` §1 |
| 每块实参对象 | 由 `mov edx,<VA>` 给出，35 组已逐条抽出（#1 `0xA83E30` … #35 `0xB04BD0`） | `[已证]` | `EVIDENCE\analysis_main.txt` §1 |
| 内联向量块 | 28 个，`Count==Items+0xC` 28/28；Count 全局逐条见 FLOW §3 | `[已证]` | `EVIDENCE\analysis_deep.txt` §A |
| S-1 标量块 | `0x67F7E0` @`0x67D421`（写 CurrentFrame `0xA8ED84`）；读侧 `0x67F9C0` @`0x67E8B5` | `[已证]` | `EVIDENCE\verify_bytes.txt`；`EVIDENCE\analysis_deep.txt` §B |
| 序列化原语 | `IStream::Write(Count)` → `QueryInterface(IID_IPersistStream@0x7F7C80)` → `OleSaveToStream[0x7E15F4]` → Release | `[已证]` | `EVIDENCE\ghidra_dump.log` template 段；`EVIDENCE\analysis_boundary_iat.txt` §1 |
| 模板块语义 | `HRESULT Serialize(LPSTREAM ecx, DynamicVectorClass<T*> edx)`；Count@+0x10, Items@+4 | `[已证]` | `EVIDENCE\ghidra_dump.log` template 段 |
| Load_Core | `0x67E440`，`StgOpenStorage[0x7E15E4]` + `OpenStream("CONTENTS")@0x83D5A8` + `OleLoadFromStream[0x7E15F8]` | `[已证]` | `EVIDENCE\analysis_deep.txt` §B；`EVIDENCE\verify_bytes.txt` |
| Save/Load 非一一对应 | Save 35 模板块 vs Load 16 助手入口 | `[已证]` | `EVIDENCE\analysis_main.txt` §3/§4 |
| Swizzle 单例 | `0xB0C110` = `SwizzleManagerClass::Instance`，vptr `0x7F4108`（10 槽）；`0x6CF0C8` 静态写 vptr | `[已证]` | `EVIDENCE\analysis_deep.txt` §C；`EVIDENCE\analysis_deep2.txt` §3 |
| Here_I_Am | `0x6CF240`(slot4)/`0x6CF2C0`(slot6)：记 `{原值,&字段}` 8B 表项，`0x6CF2A8 mov [edi],0` 清字段 | `[已证]` | `EVIDENCE\analysis_deep.txt` §C；`EVIDENCE\verify_bytes.txt` |
| Reset 回填 | `0x6CF350`（slot3 经 `0x6CF230`）：两表 qsort 后匹配原值，`0x6CF3BA mov [edx],eax` 回填，末清两表 | `[已证]` | `EVIDENCE\analysis_deep2.txt` §2 |
| TEventClass 字段范围 | ctor `0x71F8C0`：`0x71F908`+0x28、`0x71F916`+0x30、`0x71F924`+0x54 | `[已证]` | `EVIDENCE\analysis_boundary_iat.txt` §3 |
| 文件块结构 | OLE2/CFB；版本闸在元数据流 `Internal Version`（`0x0002B898`@`0x83D560`），不在 CONTENTS；块 = `[u32 Count][元素×]` | `[静态推断]` | FLOW §7；流布局 `[未证]` 见 `UNKNOWNS.md` |

## 分级与口径

- **双通道**通道 1 = capstone/pefile（不依赖 atlas）；通道 2 = Ghidra SLEIGH `-noanalysis`（不依赖 atlas）。二者反汇编逐字节一致（`EVIDENCE\ghidra_dump.log`）。atlas 仅用作 size 交叉校验（4411/127/118 三处吻合），非定论来源。
- `boundary_check` 超限返回 `unknown` 而非 False（`work\pe_util.py`）；关键字节边界 `0x67D342/0x67D386/0x67DF0F/0x6CF2A8` 均 `True`（`EVIDENCE\analysis_main.txt` §6）。
- `capstone skipdata=True` 全程开启；`0x71F93F` 处 `.byte 0xe8` 即 skipdata 生效证据（`EVIDENCE\analysis_boundary_iat.txt` §3）。
- 类名未用头文件名启发式，也未用会泄漏前向声明的作用域栈；34/35 块类名保持 `[未证]`。
- 字段偏移未单独定语义；`0x67FDF0` 的 Count/Items 语义由该模板**自身写点**（`mov [edi+0x10]`/`[edi+4]`）+ OLE 写流读点双重支撑。

## 未闭环摘要（详见 UNKNOWNS.md）

U1 34/35 模板块类名（静态不可定，需真机 RTTI）｜U2 每块 ↔ 子系统语义映射｜U3 Save/Load 逐类一一对应性｜U4 CONTENTS 内部块头 magic/id 表（P2）｜U5 `[0xABCE08]` 全镜像复位写者。
