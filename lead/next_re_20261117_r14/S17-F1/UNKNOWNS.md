# S17-F1 · UNKNOWNS（未闭环项）

> 只列静态未能闭环、且本卡不臆造结论的项。每项给定位思路。等级见 PROGRESS.md。

| ID | 未闭环项 | 现状 | 定位思路（本卡只做静态，真机属 P2） |
|---|---|---|---|
| U1 | **34/35 模板块的类名 / RTTI** | 35 个实参全是 `.bss` 全局对象（#1 `0xA83E30` … #35 `0xB04BD0`），静态镜像中其类描述符（`_RTTICompleteObjectLocator`）无文件内引用；仅 #17 `0x6805F0`/`0x8B4120` 经 YRpp `Save_Sides` 符号定名 SideClass 向量 | 真机在 `Save_Core` 35 个 call 点下断读 EDX→`[obj]` vtable→`[vt-4]` COL→`COL+0xC` TD→类名；或 hook 模板 `0x67FDF0` 一次存档全量打印 EDX/`[EDX]`（线索 `savegame_block_manifest.md §12.4.4`）。**本卡不据对象地址/相邻全局猜类名**（纪律 8/16） |
| U2 | **每块 ↔ 子系统语义映射** | 块函数是逐字节同构的 `DynamicVectorClass<T*>` 序列化模板，块号本身不编码子系统；块↔对象由 `mov edx` 给出，但对象类名 U1 未定 | 随 U1 RTTI 定名后，按对象 VA 回填；`Count==Items+0xC` 已证布局可辅助核对每块元素类型 |
| U3 | **Save/Load 是否逐类一一对应** | Save 侧 35 模板块 + 28 内联向量；Load 侧仅 16 助手入口（`0x680F70..0x681840`）+ 15 处 `IStream::Read`；两侧数量级不同，未在镜像内找到与 `0x67FDF0` 家族对称的 35 条读块函数 | 真机读档时对 `0x67FDF0..0x680F6F` 下断看是否命中（若命中则 Save/Load 共用模板、靠 IAT `0x7E15F4`/`0x7E15F8` 切方向）；静态已确认两侧函数集不同（本卡 `EVIDENCE\analysis_main.txt` §3/§4） |
| U4 | **CONTENTS 内部块头 magic / 块 id 表 / 逐块字节布局** | 静态只推出通用块格式 `[u32 Count][元素×]`（OLE CLSID 子存储、无裸指针、无独立 length）；`CONTENTS` 首 4B `0x3278` 非版本魔数；版本闸 `0x2B898` 在 OLE 元数据流 `Internal Version` 不在 CONTENTS | P2：真机 dump `.SAV` 的 `CONTENTS` 流（线索已有 `ALL01UMD.sav` 1,205,666 B）+ OLE 解析逐流；或读档时下断 `IStorage::OpenStream`/`OleLoadFromStream` 记录每次读的长度序列反推块序。**本卡只读静态，不读真机档** |
| U5 | **`[0xABCE08]` 一次性标志全镜像复位写者** | 本卡仅在 `0x55DBEE` 见置 1；未做全镜像穷举其复位写者（§894 亦记此为 `[未证]`） | 全 `.text` 扫 `mov byte [0xABCE08],0` 与 `and [0xABCE08],0`；即便有复位也是"按需存档"，不改变"非每帧"结论 |
| U6 | **`0x67CEF0` 之外是否还有 UI 快捷命令直达写档** | 本卡实测 4 调用者（`0x4C7AC0`/`0x4C7B3D`/`0x559E85`/`0x55DC92`），均为写档/网络/取档场景；镜像内 `0x67D0C0`（线索称 Save 外层）实为 0 调用者的体内点，非入口 | 真机在 4 调用者下断，配合菜单命令派发（`ui_command_dispatch` 线索）确认快捷路径；静态 rel32 扫描已排除第 5 个直接调用者 |
| U7 | **读档侧每类 Load 函数逐条定名** | `Load_Core` 内有到 `0x685120`/`0x6D03A0`/`0x722D00`/`0x72AD20` 等 20+ E8 调用，未逐类定名（本卡任务 2 要求"顺序清单"，已给调度点地址与 15 处 `IStream::Read`，逐类类名未闭） | 按 `IStream::Read` 后紧接的 vtable/IPersistStream 调用反查类；或随 U1 定名后与 Save 侧配对 |

## 明确排除（非 UNKNOWN，仅说明为何不追）

- **"存档总入口 = `0x67D0C0`"**：排除。该地址落在 `0x67CEF0`（size 1040 = `0x67CEF0..0x67D300`）函数体内部，rel32 扫描 0 调用者；`0x67CEF0` 内 `0x67D1AF` 才 `call 0x67D300`。见 `DISAGREE.md` D2。
- **"`0x67CEF0` 是 Load"**：排除。其日志串 `SAVING GAME [%s - %s]`、`StgCreateDocfile [0x7E15C8]`、`call 0x67D300`（写序列化器）三重坐实为写档。真正的读核心是 `0x67E440`（`StgOpenStorage`+`OpenStream`+`OleLoadFromStream`）。见 D1。
- **"0x67D300 每帧协调器"**：已在台账 §894 / R14_COMMON §1 作废，本卡复核门控证据一致，不重做。
