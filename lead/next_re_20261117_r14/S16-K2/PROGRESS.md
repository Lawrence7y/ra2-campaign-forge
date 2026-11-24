# S16-K2 PROGRESS（卡号 S16-K2）— 逼近 DoD 门槛定点卡

## 结论表

| 项 | 基线(PANEL) | 本卡交付后 | 跨阈 |
|---|---|---|---|
| atlas 内 named（分母 90） | 73 / 90 = 81.11% | **83 / 90 = 92.22%**（+10） | ✅ ≥90%（阈值 81） |
| atlas 内 [已证]（分母 90） | 42 / 90 = 46.67% | **46 / 90 = 51.11%**（+4） | ✅ ≥50%（阈值 45） |
| 全 coverage 口径（分母 92，atlas 外 2 行本已 named+proved） | 75 / 92 = 81.52% / 44 / 92 = 47.83% | **85 / 92 = 92.39% / 48 / 92 = 52.17%** | ✅ 两口径同向 |
| 新命名（均有依据类型+地址） | — | 10 条 | `coverage_delta.tsv` |
| 新升 [已证]（字节级硬证） | — | 4 条 | `coverage_delta.tsv` |

实现：只交 `coverage_delta.tsv`（14 行 = 10 命名 + 4 提级），**未改** `COVERAGE\coverage.tsv`。

## 核心数字（给审计员，可独立复算）

1. **atlas 内 named=83/90、proved=46/90**。复算：① `python work/t1_filter.py` 得基线 90/73/42（与 PANEL 完全吻合，DISAGREE=无）；② 取 `coverage.tsv` 按 `coverage_delta.tsv` 的 entry 覆盖 name/grade（同名 entry 14 行）；③ 计 `subsystem==S16 且 entry∈atlas` 的行中，`name` 不匹配 `^sub_[0-9A-Fa-f]{8}$` 者 83，`grade=='[已证]'` 者 46。分母 90 用 `function_atlas.tsv` 与 coverage S16 交集实测。
2. **本次新升 [已证] = 4**（0x6CDFD0 / 0x6CE220 / 0x6CE8D0 / 0x6CEFE0）。复算：`python work/verify_rtti.py`（COL→TD 类名与 v[6]/v[8] 槽值）+ `python work/verify_proof.py > EVIDENCE/E04_proof_candidates.txt`（逐条字节：Save=10 条纯转发 call 0x410320 ret 0xC；dtor=call 0x6CB120/0x4109C0 + `test [esp+8|0xC],1` + 条件 call operator delete 0x7C8B3D）。**未用 GetSize 判据**（避免 §969 837/543 与 §972 imm8 陷阱）；靠 RTTI 定类 + 槽位 + 规范型字节三重。
3. **分母口径两列**：PANEL 面板列只统计 atlas 分母 12,916 下界内的 S16=90；全 coverage S16=92（多出 0x004F8440 / 0x004F9370 两行，均 atlas 外且本已 named+proved）。估计真实分母 14,715 与本卡百分比无关。R14-R11 要求「全镜像 X%」以 14,715 为底——本卡只报子系统字面 DoD，两口径并列，不外推全镜像。

## 提级凭什么（每条硬证）

- **0x6CDFD0 → SuperClass::Save**：vftable `0x7F3FE8` v[6]（RTTI COL `0x80B610`→TD `0x8423E0`=`.?AVSuperClass@@`）；函数体 `8B 44 24 0C / 8B 4C 24 08 / 8B 54 24 04 / push×3 / call 0x410320(AbstractClass::Save) / ret 0xC`；与 `docs/re/superweapon_re.md:708-721` 逐字吻合。`EVIDENCE/E04_proof_candidates.txt`, `E01_rtti_vtables.txt`
- **0x6CE220 → ~SuperClass**：同 vft v[8]；`call 0x6CB120`(dtor 体) + `test byte [esp+8],1` + 条件 `call 0x7C8B3D`(operator delete) + `ret 4`；标量删除析构规范型。同上证据。
- **0x6CE8D0 → SuperWeaponTypeClass::Save**：vft `0x7F4090` v[6]（RTTI COL `0x80B6C8`→TD `0x842600`=`.?AVSuperWeaponTypeClass@@`）；与 0x6CDFD0 同构纯转发 `call 0x410320 / ret 0xC`。同上证据。
- **0x6CEFE0 → ~SuperWeaponTypeClass**：同 vft v[8]；`call 0x4109C0`(dtor) + `test byte [esp+0xC],1` + 条件 `call 0x7C8B3D` + `ret 4`。同上证据。
- 以上 4 条均**非**字段偏移定语义、非 `call [reg+disp]` 虚槽调用计数、非源文件名猜类；类名只认 RTTI TypeDescriptor（纪律 5）。

## 新命名依据（摘要，全量见 coverage_delta.tsv 与 E03/E04）

- `0x00539EB0 LightningStorm::Start`：项目已入账地址名（`superweapon_re.md:780,808`；`re_sprint_S2_report.md:136,164`）+ Launch case2 调用点 + RandomRanged 字节。
- `0x0053AE00 / 0x0053B410 …::AnnounceActive`：字节级字符串 `Msg:LightningStormActive`@`0x82809C` / `Msg:DominatorActive`@`0x8280B8` 实测（E04）+ `call 0x734E60` 查表 + `call 0x5D3BA0` 派发。
- 其余 7 条用「调用者已知名函数 / 源文件串(R036) / 字节模式」给候选名，凡拿不到确定符号者采 `Class::sub_XXXXXXXX` 透明形式（不编像样的名字，遵 §966）。

## 证据/复跑

- 证据：`EVIDENCE/E00..E05`（未截断；E00 含 92 行全量靶子与 T1 基线口径）。
- 复跑（cwd=项目根，只读 `gamemd.exe`）：`python work/t1_filter.py && python work/verify_rtti.py && python work/verify_proof.py && python work/gen_deliverables.py`。capstone `skipdata=True`；未用 Ghidra（无需副本）。
