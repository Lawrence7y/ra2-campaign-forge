# S10-KPROVED4 · UNKNOWNS

> 卡号 S10-KPROVED4｜目标 `ra2youli\gamemd.exe` 只读，SHA-256 `73201CC0…F67476` 现场复核一致。8 行 ①/②/④ 全部成立，但 **③b 全部不成立（落 ③a）**，故 0 行进 delta。逐环证据见 `EVIDENCE/per_row/*.txt`、`EVIDENCE/holding_tables.tsv`、`EVIDENCE/ring4_verified.tsv`。

## U1 · 选题与排除集（16 行）
行源 = S10 A 集合 49 行（`S10_KPROVED2/_audit/EVIDENCE/a_set.json` 复算：pool 398 / has4 50 / A=49，与 SURVEY_RING24 S10 A=49 一致）。排除集合并去重 = 16 行：
- S10_KPROVED2 8 行：`004D74E0 004D7D50 004D7170 004D85D0 004DB3C0 004D9960 004DF040 004DB690`
- S10_KPROVED3 8 行：`004D82B0 004D5690 004DB260 00702D40 00706640 00708C30 004D94B0 004DDDE0`（004DDDE0 被 a-S10-KPROVED3 判 ③b①′不成立、整行不动）
- SEMFIX_SLOTS2 的 7 行 S10（`004D82B0 004D5690 004DB260 00702D40 00706640 00708C30 004D94B0`）全部是 KPROVED3 子集。
余 33 行。本卡取其中 8 行深查：按「最接近 ③b 的 8 种形态」选取（null-assert/单虚拟调用/搜索循环/字段序列化/几何计算/守卫链），以最大善意给每行机会，仍全部落 ③a。

## U2 · 8 行 ③b 逐行失败理由（核心）
| entry | name(=②归属) | ②归属(全持有表) | ③b 尝试档 + 入口相对锚 | 失败理由 |
|---|---|---|---|---|
| 004D55C0 | FootClass::StopMoving | 3 表同 slot → FootClass | 曾试②（push 0x80004003 @+0x0D） | E_POINTER 是传给 `call 0x7dc720` 断言器的**实参**，非被调返回值的比较；无 `cmp reg,0x8000xxxx` 分支 ⇒ ③a（对照 004D94B0 `cmp eax,0x80004002`） |
| 004D55F0 | FootClass::MoveTo | 3 表同 slot → FootClass | 曾试②（0x80004003 @+0x1C/+0x49） | 同上；两处 null-assert + 2 个虚拟调用，无跳表/回边/返回码比较 |
| 004D9C10 | FootClass::Can_Enter_Cell | 1 表 → FootClass | 曾试②（0x80004003 @+0x27） | 全前向守卫；返回 al 来自 `xor` 字面值，非可证伪错误码约定 |
| 00517CC0 | InfantryClass::slot9 | 1 表 → InfantryClass | 曾试④（搜索循环 +0x45..+0x4F） | 回边体内仅 `inc ecx`/`add eax,4`（推进），**无显式内存写、无可证 falsifiable 返回** ⇒ 违 M7；`cmp ecx,-1`@+0xAF 是字段默认值拷贝非错误码 |
| 004DBAD0 | FootClass::slot13 | 1 表 → FootClass | 曾试①′（8 jcc） | 8 jcc 是独立 null 检查，**全部汇入同一字段写器 `call 0x4a1d50`**；`cmp edx,-1`@+0x15B/+0x194 是剩余时间计算 ⇒ ③a |
| 006F3AD0 | TechnoClass::slot44 | 4 表同 slot → TechnoClass | 曾试①′/②（2 路索引选择 +0x27/+0x2E，0x80004003@+0xAE） | 索引选择仅 2 路（<3 道互斥闸）；3 处「字段写」全是栈暂存 `[esp+0x30/34/38]` 非 ctor 内存形状 ⇒ ③a |
| 006FBDC0 | TechnoClass::slot168 | 5 表同 slot → TechnoClass | 曾试①′（≈25 jcc） | **所有失败闸汇入同一 `xor al,al; pop; ret` 假返回桩**（+0xE5/+F7/+123/+145/+164/+190/+1B7），各闸动作相同 ⇒ 违 M4/细则#1「各闸动作不同」，与 004DDDE0 同类被否 |
| 006FBC90 | TechnoClass::slot169 | 5 表同 slot → TechnoClass | 曾试①′（≈14 jcc） | 同上，全部失败闸汇入 +0x12C 的 `xor al,al; ret`（成功是 `mov al,1`@+0x11D）⇒ 动作相同，细则#1 不成立 |

## U3 · 为什么不是「检测器太严」——三重独立自证
1. **检测器阳性对照**：同一 `core.disasm_range` + ③b 特征谓词跑 15 行已并入行（004D74E0/004D7D50/004D7170/004D85D0/004DB3C0/004D9960/004DF040/004DB690/004D82B0/004D5690/004DB260/00702D40/00706640/00708C30/004D94B0）：跳表行 jt=1（004D74E0/004D7D50/00702D40/00706640/00708C30）、循环写行 nw≥1（004D7170/004D85D0/004DB3C0/004D9960/004D82B0/004D5690/004DB260）、HRESULT 行 ep 命中 0x80004002（004DB690/004D94B0）。15/15 全被识别 ⇒ 谓词不漏阳性。证据：`EVIDENCE/b3_classification.json`、`work/s6_sanity_baseline.py` 输出。
2. **基率谓词交叉验证**：`work/s7_baseline.py` 在 S10 全 398 行池上跑独立谓词（strict=跳表∨循环显式写∨HRESULT 比较∨内存形状；loose=strict∨assert 码）。15 行已并入行中 14 行 strict=True（004DF040 因栈累加槽例外，审计当年也标注该行是「最弱一行」）；`004DDDE0` strict=False 与审计否决一致；**本卡 33 候选 0 行 strict=True**。证据：`EVIDENCE/baseline_3b.json`。
3. **字节级穷举**：全部 33 行函数体内 **0 个 `jmp dword ptr [reg*scale+...]`**（无跳表）、**0 个 `loop` 指令**、唯一后向分支是 00517CC0 的无写搜索循环（`work/s4_b3class.py` + `work/s5_guard_shape.py` + `EVIDENCE/disasm/*.txt`）。守卫链候选的汇合点逐条打到 `ret` 逐字核对（纪律 2：输出未截断、非「分支什么都不做」臆断）。

## U4 · ③b 基率（不是 ②∧④ 入选率）
- 池 = S10 `[静态推断]` 398 行（`SURVEY_RING24/EVIDENCE/classification.tsv` 现场筛 subsystem=S10 得 398）；seed **20261119**；2000 次每次不放回取 8 行。
- **strict**：K=55，`p = 55/398 = 0.138191`；E[8] = 8p = **1.105528**；MC = **1.1140**。
- **loose**：K=65，`p = 65/398 = 0.163317`；E[8] = 8p = **1.306533**；MC = **1.3300**。
- 操作化：strict=D-42 四硬档（①跳表 `jmp [reg*scale+disp]`；②被调用返回码 `cmp/test reg,0x8000xxxx` 且有分支；③构造器 `≥2 vt 写或 ≥10 字段布局断言`；④后向分支循环体内有显式非栈内存写）；loose=strict∨`push 0x8000xxxx` 断言码。两口径并列，未把 loose 当 ③b 升格依据。
- `K = N·p` 与 `E[8] = 8·p` 是恒等式（实测差 0.0），**非校验**（M3/§8.7 判据 3）；报的是 ③b 基率而非 ②∧④ 入选率（§8.7 判据 4）。证据：`EVIDENCE/baseline_3b.json`、`work/s7_baseline.py`。

## U5 · 与其它卡基率数字不可直接比较
`S10_KPROVED2` 自报 strict 0.2437/loose 0.5653、其审计复算 49/398=0.1231（仅四硬档）或 117/398=0.2940（含细则#1）；`S10_KPROVED3` 自报 0.3277/0.2395、其审计 0.4271/0.2123。这些口径互不统一（审计亦指出 loose 定义错、池 N 不一）。本卡按 D-42(C) 四硬档严格操作化自算 0.1382/0.1633，随口径差异披露于此，不声称与其它卡同值。

## U6 · 未测项
未做真机；未裁 D-37/D-38/D-39/D-41；未用 YRpp 第二通道（本批 ② 全部走 RTTI，不缺环）；未改 grade / 未改 coverage.tsv / 未写任何禁写目录。delta 自报 0 行 = 实际 0 行（M6/M15）。
