# C04 · UNKNOWNS（未解决项）

## 1. 无法归类 / 低置信函数（288）

`coverage_delta.tsv` 中 `source=none` 的函数 **288** 个，统一归 S22 兜底、grade=[未证]：
- 无 vtable 槽、无具名地址名、无特征字符串、无源文件归属、无具名亲戚、无特征导入 API。
- 多数是小转发桩或局部 helper（`n_instr` 低、`n_callers` 低）。完整地址见 `EVIDENCE/classification_trace.tsv` 过滤 `source==none`。
- 另有 `source=relay_vote`(148) / `source=import`(15) / `source=string`(13) 共 176 个弱信号函数，grade=[未证]，未计入 high。
- 这 288 个不应被合并员误当 [已证]；建议 P1 用 YRpp/kb 或逐函数线性反汇编追 this/参数来源细化。

## 2. atlas 空洞入口：严格 26 + 排除的 69 个 EB 短跳（卡纪律）

全 `.text` skipdata=True 扫出本片 owner=None 的洞目标共 **95** 个，但按 opcode 细分：
- **26 个 rel32 命中**（7 个 E8 call + 19 个 E9 jmp32）→ 入 `atlas_gaps.tsv`，为本卡核心数字 3。
- **69 个仅由 EB(rel8) 短跳命中** → **不计入** rel32 命中，列于 `work/gap_detail.json` 的 `short_jmp_only` 段与 `EVIDENCE/gap_candidates.tsv`（conf 列标 `SHORT-JMP-ONLY(非rel32)`）。

关于 69 个 EB 短跳目标（C01 的 `0x4824D4` 同类场景）：
- 证据：全部 79 个 jmp8 引用站点（首 8 个/目标）`owner(site)==None`，即短跳源也落在 atlas 空洞内 —— 这是线性反汇编穿越无函数区的产物，**不是**从已知函数发起的入口发现。
- 首指令形如 `test al,al ; jne ...`、`mov edx,[ecx] ; push eax ; call ...`、`dec edi ; jns ...`，均为函数中部分支/循环体，非独立函数序言。
- 分布集中：0x4F8xxx–0x4F9xxx（17）、0x527xxx–0x52Axxx（16）、0x501xxx–0x505xxx（11）、0x536xxx–0x53Bxxx（8）等。
- 判读：按卡纪律「不要硬算成 rel32 命中」，本卡不把它们列为函数入口；但**不排除**其中确有真实小函数（需 P1 逐点证真）。若审计按 C02 宽松口径（call/jmp 含 EB）复算，会得 95，属口径差异非数据错误（见 DISAGREE D-1）。

`0x4824D4` 位于 0x482xxx（C02 范围 0x456E00–0x4A60CB），**不在本片**，故 `atlas_gaps.tsv` 不含它 —— 与 C01/C02 记录不冲突。

## 3. 26 个 rel32 洞入口的真伪分级
- **7 个 call 目标**（高置信候选入口）：`0x4F3AB0`、`0x4FFD90`、`0x50C160`、`0x518D80`、`0x528170`、`0x528220`、`0x538D40`。首指令多为 `sub esp,N ; push ...` / `mov eax,[esp+4]` 等序言形态，call rel32 按 x86 语义指向函数入口。
- **19 个 jmp32 目标**（证据较弱）：多数首指令是 `test/je`、`cmp/jle`、循环体 `mov esi,[esi] ; test` 等**函数内部分支点**（如 `0x504D2F`、`0x527466`、`0x5274BD`、`0x529394`、`0x52A153`、`0x52A345`），可能并非新函数入口，而是某未建函数内的分支标签。本卡按「rel32 目标且 owner=None」的机械定义收录并标 `high(jmp32-rel32)`，但**不声称**它们是真函数入口（P1 需逐点追邻居函数边界）。
- 全部 26 个 `boundary_check` 均为 True（落在指令边界），无 `unknown`/`False`。

## 4. vtable 槽方法语义未证
723 个函数命中 vtable 槽，本卡只确定「属于类 X 第 N 槽」并据类映射 Sxx，**槽对应的具体方法名/语义未逐证**（除 96 个具名地址）。例如 S09 的 285 个 high 多为 `*CommandClass` 槽，只能确定「是某 UI 命令类的槽」，具体是 `Execute()` 还是 `GetDescription()` 未证。P1 的 UI 卡需结合 YRpp `CommandClass` 槽序逐点确认。

## 5. 归属可商榷项（已按 PLAN §1 定规则，记录分歧空间）
- `InfantryTypeClass`/`UnitTypeClass`/`AircraftTypeClass`（类型类）本卡归 **S05**（对象模型/类型族），而 `InfantryClass`（实例）归 **S10**（单位行为 AI）；类型类亦可论属 S10。依据：类型类是 AbstractType 族，与 kb/20 类型布局同类。
- `HouseTypeClass`、`TeamTypeClass` 归 **S14**（House/AI），亦属类型族可论属 S05。
- `MapClass::RedrawSidebar`（具名）归 **S06**（MapClass 前缀），但语义是侧栏刷新，可论属 S09；按"类前缀优先"规则归 S06。
- `TechnoClass::CanBePermaMindControlled`（具名）归 **S12**（TechnoClass 前缀同 C02 NAME 规则），语义偏战斗可论属 S13。
- 通用容器模板 `T_DynamicVectorClass_*`/`T_VectorClass_*`/`T_TypeList_*` 按元素类型映射（如 `Vector<TeamTypeClass*>`→S14、`Vector<IonBlastClass*>`→S16）；元素为纯 `H`/`PAD`/`AG` 时归 S22。

以上均为候选分类，语义一行按普查要求标 [未证]，合并员如遇更精确名字按 grade 优先级合入即可。
