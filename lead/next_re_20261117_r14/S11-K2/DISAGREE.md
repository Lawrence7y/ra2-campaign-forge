# S11-K2 DISAGREE（派卡前提与字节实测的冲突 / 跨卡数字冲突）

> 全部为本卡 `work/fresh_*.py`（capstone `skipdata=True`，纯字节通道，不依赖 `function_atlas.tsv`）独立重取结果。文件：`EVIDENCE/fresh_core.txt`、`fresh_closure.txt`、`fresh_baseline.log`、`fresh_slots.txt`、`fresh_fields.txt`。

## D1 · 派生前提 proved=13 为旧值（已由 Lead 裁定）
派卡写「S11 `[已证]` 仅 13（3.53%，atlas 368）」。实测与权威现值：
- 当前 `coverage.tsv`：S11 共 **379** 行，`[已证]` **18** / `[静态推断]` 351 / `[未证]` 10；
- `COVERAGE/PANEL.md`（post-M2，atlas 分母 368）：S11 proved **17**（4.62%）。
- 二者自洽：atlas 内 17 + atlas 外 1 = 全表 18。13 是 M2 并表前旧截面。
- **处置**：增量起点取 atlas 内 17 / 全表 18（Lead 2026-11-17 裁定）；不凑数到 13。

## D2 · 「GetSize = v[12]」惯例在本类族不成立（核心分歧，Lead 已批准按字节走）
派卡要求「`v[12]` 的 `B8 <imm32> C3`」「必须叠加值确在本类 vtable **槽 12**」。
字节实测（`fresh_core.txt` 扫全 12 类 30 张表全部槽、`fresh_slots.txt` 全槽常量返回扫描、`fresh_closure.txt` off4 slot11/12 逐条反汇编）：
- 全部 **11** 处 `B8 imm32 C3` 落在 **off=0（IPersistStream 侧）vtable 的 slot 9**；**无一处**在 off=4 slot 12。
- off=4 slot 11 = `0055ABD0`（`mov eax,[esp+8]; xor ecx,ecx; xor edx,edx; mov [eax],ecx; mov [eax+4],edx; ret 8`）——是向输出缓冲写两个 0 的普通函数。
- off=4 slot 12 = `0055A8C0`（`mov eax,[esp+4]; push esi; mov ecx,[eax+8]; mov edx,[ecx]; call [edx+0x1C8]; ...; ret 8`）——经 `[this+8]` 宿主指针转调宿主虚方法的普通函数。
- 基类 `LocomotionClass` off0 slot9 = `004C9150`（`33 C0 C3` = xor eax,eax;ret）= §971 多抽象类共用桩，已排除（不当作任何具体类 GetSize）。
- **根因**：Locomotor 是多接口 COM 对象（IPersistStream@off0 + ILocomotion@off4(50 槽) + IPiggyback@off24(8 槽)×6 类），「槽 12 = GetSize」是 AbstractClass 单继承惯例，在 COM 多继承类上不成立。
- **处置**：判据「必须叠加值确在本类 vtable 槽」保持不变，但叠加对象改为实测的 **off0 slot 9**；11/11 双向闭合（factory `push<size>`→`operator new 0x7C8E17` 的 size 与各类 off0 slot9 imm 逐类相等）。这条**推翻项目长期默认**，影响后续所有 COM 接口族 GetSize 取证（Lead 已批准并记一笔）。

## D3 · §969 基线数字 837/543 与本卡 666 不一致（跨卡冲突）
派卡引用 §969「全镜像 `B8 imm32 C3` 约 837，543 落非槽 12」。本卡实测（`fresh_baseline.log`）：
- `.text` raw `B8 imm32 C3` = **666**；全文件（含非 `.text` 段）= **668**；其中 16B 对齐 287、4B 对齐 359；落 Locomotion 任一 vtable 槽仅 **11**。
- S06-K2 独立测得也为 666（据 Lead 转述）；两独立卡一致。§969 837/543 疑为不同量纲/模式（含非 `.text` 或含无 `ret` 形态）。
- **处置**：本卡以实测 666 为准；调停 837 vs 666 由 Lead 另派卡，不在本卡范围。

## D4 · K1 `006C41D0` = Jumpjet CreateInstance 地址错误（沿用审计 M2）
S11-K1 delta 写 `006c41d0 JumpjetClassFactory::CreateInstance`；其自身 `_audit/VERDICT.md` M2 已更正为 **`006C4190`**（= ctor `006C40C0` + 0xD0）。本卡 `fresh_closure.txt` 独立字节佐证：ctor `006C40C0` 的 CI 在 `006C4190`，其 `push 0x98`（68 imm32）→ `new` → ctor `0054AC40`（installs 7ECE34/7ECD68）；`006C41D0` 落在 CreateInstance 函数中部（`call 0x7C8B3D` 之后），非入口。本卡 delta 不采用 `006C41D0`。

## D5 · 三分母口径（引用百分比必标）
本卡所有「全镜像 X%」按 R14-R13：**A = atlas 12,916（下界）/ B = 估计真实 14,715（14,500–15,300）/ C = ≥18,431（18,431–18,700）**；不用 A 宣布 P0 完成，引用 12,916 必标「下界」。S11 proved 变化用「atlas 分母」与「全表」双口径报告，不混用。
