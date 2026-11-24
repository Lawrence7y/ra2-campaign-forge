# C09 · DISAGREE（与前片/潜在审计的分歧点与依据）

## D1. WorldDominationTour(WDT) 自定义类族 —— 前片无此family，本卡新增
- 前片（C01–C08）类规则表无 `WorldDominationTour`/`WDT*`。本片 0x71–0x72 段出现 113 个此类虚表函数，是本镜像（ra2youli 中文定制版）专有模式。
- 本卡处置：按类名与 .cpp 字面拆分到 S09（UI/游戏选项，如 GameOption/ToolTip/TextButton/`WDTSel.cpp`/`WDTGameOptions.cpp`/`WDTProps.cpp`）与 S21（战役/得分/剧情，如 Campaign/History/State/Territory/Conflict/Map/Selection/`WDTTerr.cpp`）。
- 分歧风险：审计可能认为整套 WDT 应归 S18（多人/游戏模式）或 S09（全 UI）。本卡不坚持唯一解：给出 high 候选但语义均标 `[未证]`，等 P1 类布局卡或真机确认再定。见 UNKNOWNS §5。

## D2. 通用容器实例类型不计 high（沿用 C08 纪律，影响 S22 计数）
- 222 个 S22 函数为泛型容器/智能指针：`T_VectorClass<UnitClass>`、`T_DynamicVectorClass<TemporalClass>`、`T_rc_ptr<WDTState>`、`T_VectorCursor<...>` 等。
- 若按嵌入类型判 Sxx 会把这些普通容器方法虚高成 core high（C08 曾因此类问题记 DISAGREE）。本卡先于 core 规则识别为 S22 core=False，不计 high。
- 审计若认为容器方法应按实例化类型归 Sxx：本卡反对——容器 slot 语义（Add/GetItem/Count）与实例化类型无关，YRx 库里是同一份模板代码逐字节同构。

## D3. StringTable → S22（非 S17 存档；修订本卡初稿的一处规则笔误）
- 本卡初稿曾误把 `^StringTable::` 写入 S17 规则行（与 SwizzleManagerClass 同列），4 个 `StringTable::LoadFile/ReadFile/Unload/StringTable` 被归 S17 high。
- 已修正：StringTable 是字符串表工具，归 S22（`随机数/数学/字符串/第三方库`），仍为 self_known `[已证]` high。修正后 S17 仅剩 1 个 low（CoCreateInstance 导入猜测），S22 high=4。high 总数不变（423）。
- 说明此举以求分级诚实、子系统归属准确，非迁就数字。

## D4. jmp32 疑似真入口 = 0（与 C06 的 72/78 口径刻意不同）
- C06 曾报 72/78（92%）jmp32 为真入口，被审计质疑判据过宽。Lead 数据点：C04 19 个 jmp32 仅 2 真、C03 0 真。
- 本片 8 个 jmp32 目标全部 align16=0 + prev=other（3 个还是 test/cmp 分支标签），按 R14-R1 严格判据（16 对齐 + 前驱 nop/ret/jmp + 非分支标签）**0 计入**。
- 本卡不为凑数放宽；17 个疑似真入口全部来自 call32（每片唯一被 R14-R1 认可的硬通道）。见 UNKNOWNS §2/§3。

## D5. 17 个 call32 洞目标 = atlas 函数尺寸低估，不是「无调用者死代码」
- 17 个 call32 目标 owner=None（不在任何 atlas 函数区间），但每个都有真实 `E8 rel32` 直接调用站点（1–2 处），前驱 nop 填充、序言完整。
- 按纪律 §7「不用无调用者=死代码」与 §6-17「站点归属用函数区间包含」，这些是真入口候选。本卡报「疑似真入口」并建议 P1 补 atlas；不擅改 atlas（写域只读）。
- 若审计认为 owner() 用全 atlas 区间判定会把「尺寸低估的函数尾部」误当洞：本卡承认这是萎缩 size 的后果，但结论（真入口）与 R14 既有的 0x4824D4 atlas 空洞补录先例一致。

## D6. 虚表槽数走独立 RTTI（14044），不采信 vtables_v2.json 的 13351
- 前片审计坐实 v2.json 槽数少计 1（1214/1218 张表丢末槽，共 693）。本卡自写 struct PE + COL→TD→vtable 连续 .text 指针定界，实测 total_slots=14044、delta `{1:794,0:327,-1:85,-2:8}`、net +693，与 C03/C08 审计一致。
- 所有 vtable 类/槽号证据均来自 `work/rtti_independent.json`（真实槽），不读 v2.json 的 slots 做分类。

## D7. 分级不虚高
- 63 个 [已证] = 明确的 YRpp/kb 具名地址名（方法名已证、语义据名标 `[未证]`）；367 个 [静态推断] = vtable core / module；其余 862 `[未证]`。
- 440 个零证据函数一律 S22 low，未编造 Sxx 归属；S14/S04/S02/S08 等 low 子系统 high=0 据实报，不补数。
