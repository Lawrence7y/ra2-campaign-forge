# coverage.tsv 说明（M1-FIX8 / 当前版：14,493 行）

## 本表内容
`coverage.tsv` **14,493** 行真函数入口（`subsystem` 均 `^S\d\d$`）：
atlas exact **12,916** + 5 早期新增 + **476** P0-GATE + **1,096** P0-RESIDUAL。
非函数/非函数首字节条目 **112** 行在 `probe_and_data_entries.tsv`；41 条无来源 `[已证]` 已降级，见 `UNSOURCED_PROVED.tsv`。

## 合并规则（未改）
- 同一 entry 多来源：grade 高者优先 `[已证]` > `[静态推断]` > `[未证]`；
- 同 grade 但 subsystem/name 不一致 → 只登记 `CONFLICTS.tsv`（本次 476 并表 **0 新增冲突**，因其与既有 coverage/probe 交集为 0），保留先出现者、标 `conflict=1`；不裁决；
- 审计更正只登记 `PENDING_CORRECTIONS.tsv`（79 条，本次未改）；`CONFLICTS.tsv` 156 条未改。
- 476 行 grade 按保守口径：411 锚到 vtable 槽 → `[静态推断]`、65 无槽 `sub_XXXXXXXX` → `[未证]`（未采用 P0-GATE 的「槽值/前驱 `[已证]`」）。

## P0-GATE 476 的 subsystem 映射（PLAN §1，PLAN_R14_SUSTAINED.md:33-54）
- 用 RTTI 类名关键字映射：`LocomotionClass*`→S11、`TeamClass*`→S14、`HouseClass*`→S14、`WeaponTypeClass*`→S13、`*CommandClass`→S09、`T_Blit*`/`T_RLEBlit*`→S07 等；
- 容器模板（`T_VectorClass_*`/`T_DynamicVectorClass_*`/`T_TClassFactory_*`/`T_VectorCursor_*` 等）按审计 `class_to_sub` 建议显式归 S22，sem 标 `container_template`（210 条）；
- **映射不出 = 77 条**（65 无 RTTI 类名 + 12 类名无规则匹配）→ S22 且 sem 写「未映射」——S22 垃圾桶指标，需 P1 细化。
- 476 与 coverage/probe 交集 0、落 atlas 区间 0（P0_GATE counts.json 亦报 0），无「落在已知函数体内」阻断情形。

## 分母说明（三分母，当前口径）
- atlas 分母 12,916（下界，本表面板列分母）；
- 当前 `coverage.tsv` **14,493**（= atlas 12,916 + 5 早期 + 476 P0-GATE + 1,096 P0-RESIDUAL）；
- 估计真实 **14,715（区间 14,500–15,300）**（§956；已取代 P0-CLOSE 13,755~13,792）；剩余未裁定缺口 **≈222（区间 222–820）**（估计值非枚举，另立卡）。

> 注：本节以下「M1-FIX5b / 第四次并表 / 方法教训」各段中含 13,397 / 13,755~13,792 / 476→474 等数字，均为**当时的历史口径或对旧派卡错误的更正记录**，非当前值；当前值以本文件抬头与本三分为准。

## `coverage_outside_atlas.tsv` 476 的口径（重复扣减作废）
`coverage_outside_atlas.tsv` = **476** = VT 411 + TRUE 65，**已扣除** 2 条 `ALREADY_IN_COVERAGE`（`004F8440`/`00535E50`，二者已在 `coverage.tsv`）。Lead 曾在派卡文中要求「476→474」，那是在 M1-FIX4 已扣过一次的基础上**重复扣减**，已作废；本卡维持 476。

## 判据：判定函数入口（M1-FIX4 确立，后手照此）
1. **16 字节对齐**（`addr % 16 == 0`）；
2. **首字节不是 `E8`/`E9`/`EB`**；
3. **前驱非 fall-through**：前驱为 `C3`/`C2`（ret）后接纯 nop 填充，或明确 ret/int3 边界；
4. **有合法序言**（`83EC4C`/`53578BF9`/`B9imm32`/`8B442404`/`518B0D` 等）。
⇒ 「不在 atlas 区间内」≠「是函数」。

## 方法教训：Lead 的派卡措辞也可能错（本卡四次，必须实测确认）
1. 「C01 entry 是十进制」——实测为伪（C01 delta 全 8 位十六进制，含 `a`/`c`）。
2. 「48 行全是 atlas 之外的真实函数入口」——实测仅 7 行在区间外。
3. R14-R7「7 个真新增」——审计直读字节纠正为 5 个（`004824D4` 是 E8 call 站点、`006CDE44` 是 `::JumpTable`）。
4. 本次派卡「13,395 / 476→474」——**重复扣减** 2 条 `ALREADY_IN_COVERAGE`（其在 M1-FIX4 已从 outside 移除、且不在 476 池内）；停机核验后 Lead 裁定改为 13,397 / 维持 476。
⇒ **执行员职责是实测并如实报告差异，不是照抄派卡文；凡冲突先报告再执行。**

## 判据：「N/N 通过」不等于证据（P0-GATE 审计基线）
P0-GATE 曾报「411/411 是指令边界」，审计实测基线：`.text` 内 **34.7%** 的 4B 对齐地址、**36.5%** 的 16B 对齐地址本来就是 sweep 起点，对齐起点中 **78.6%** 的前驱是函数中部指令 ⇒ 该判据零区分力（违纪律 17）。真证据是**前驱 ∈ {`nop`,`int3`,`ret`,`jmp`} 的 411/411**（基线 21.4%，`0.214^411 ≈ 1e-270`）。
⇒ **写「N/N 通过」前，先测基线：随便挑 N 个会不会也过？**

## evidence_path 引用可核查性
M1-FIX4 抽样 50 行（随机种子 20261117，按来源卡解析、含十进制变体）命中 50/50=100%；`00535E50` 原 E02 断裂已改指 `P0_CLOSE/VT_DIRECT_ENTRIES.tsv#00535E50`。本次 476 行 evidence_path 统一指向 `P0_GATE/EVIDENCE/ENTRY_ADJUDICATION_FULL.tsv#<addr>`（真实可查）。

## M1-FIX6b（第四次并表）追加
- `coverage.tsv` 14,493 = 13,397 + P0-RESIDUAL 1,096；C08 77 已随 P0-GATE 476 并入（本次不重复插）；第4笔 S 卡报 0；N_FIX 34 就地提级（行数不变）。
- **`coverage_outside_atlas.tsv` 重定义**：本表是「atlas 之外被发现、且已裁定并入 coverage.tsv 的入口『溯源表』」，不是「未覆盖清单」；476 行全标 `merged=Y`。判断剩余未裁定请看 `coverage_unresolved.md` / PANEL，不看本表行数。
- 剩余未裁定缺口 **≈222（区间 222–820）**，为已知通道不完备上限（估计值，非枚举清单）；P0 已按 R14-R8 收口。
- 1,096 条 P0-RESIDUAL 无 RTTI 类名 ⇒ S22/未映射（未映射 1,096）；grade 保守 `[静态推断]`。N_FIX 34 name 更正未执行（只提级 grade）。

## M1-FIX7 混装版次说明
**本表混装版次：grade 落地不完整，`UNSOURCED_PROVED.tsv` 列出 41 条已降级项。**
- 41 条 `[已证]` 无任何 delta 断言、亦不在 N_FIX 记录内（C02 6/C03 5/C05 5/C07 9/C08 3/C09 12/表外 1）；已降 `[未证]`，11 条自造名同时回退 `sub_XXXXXXXX`。详见 `UNSOURCED_PROVED.tsv`。
- `004C9150` 按 PENDING_CORRECTIONS 降为 `[静态推断]`。降级后 `[已证]` = 1,022（原 1,064 − 41 − 1），行数 14,493 不变。
- **`high`（普查 conf，4,789）与 `[已证]`（本表证据等级，1,022）是两量纲**，实测重合仅 17.7%，C01 是唯一 high≡[已证] 片（96/96），不得据以混用。
- S22 68.2% 为无信息填充，**不得参与百分比排名或覆盖率结论**；引用「全镜像 X%」须注明分母口径。
- ≈222 为估计值（区间 222–820），非枚举清单；逐地址裁定需另立卡。
