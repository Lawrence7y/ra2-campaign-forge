目标 A：达成（fallback `0047F250`→`Draw_Fog`，+1 真名）；目标 B：未达成（direct 最多且实交 **2 行** < 10）。
# S08-K1 PROGRESS

- 状态：已完成本卡；开工骨架 2026-11-18 15:28 +08:00 已先落盘。
- 目标只读校验：`ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`，4,825,360 B，未改动。未建 venv / 未 pip install / 未 import 他卡 work。

## 停机与扫描
- ⑨ 核验：coverage 原始 S08 行 23；与 `function_atlas.tsv` 求交后 **22**；named **19**、proved **1** `[静态推断]20/[未证]1`，与卡面一致。第 23 行 `0065B800` 不在 atlas，不进分母。
- capstone 5.0.7 + pefile 全 `.text`（VA `00401000`, VirtualSize `4,060,045`）线性 skipdata 扫 **1,392,592 条指令**（真实 1,392,527 / skip 65），覆盖 **100%**。
- raw `E8` 字节 81,715；指令边界 `E8 rel32` **68,253**，与基准一致。
- ⑲ 自检：`hasattr(op,'index')=False`；已知 `call dword ptr [edx+0x14]` 的 `mem.index=0`、`index is None=False`（`EVIDENCE/capstone_selfcheck.json`）。

## 目标 A（+1 真名）
- 优先 `004309D0`：二进制链完整（`PBEACON.SHP`/`RDRBEACN.SHP`、`Failed to load BeaconArt`/`Failed to load RadarBeaconArt`、全局 `0x89C474/0x89C478`），但按地址全库查无 YRpp `CALL/JMP` 或既有真名记录 ⇒ **不命名**，留 `sub_004309D0`。
- 按卡面 fallback 攻 `0047F250`：二进制体内 `FOG.SHP`（`0x81CE10`）+ 懒加载 `0x89E760` + `ret 0xC`；异源 `docs/re/ARCHITECTURE_ATLAS.md:4336` 与 `docs/re/fog_firststage_site_locate.md:52-53` 均记 `Draw_Fog 0x47F250` ⇒ 命名 **`Draw_Fog`**（非 `Class::sub_`）。
- ⑱ 冲突按 entry 扫描 155 命中，见 `EVIDENCE/CONFLICT_SCAN.tsv`；唯一需报告的命名分歧是 `0047EFE0`（前卡 `MapClass::DrawShroudFogLayer` vs docs `Draw_Shroud`），本卡 **只报不改名**。

## 目标 B（direct-only 升格）
- 22 行 strict direct 入口仅 **3**：`004309D0←00687BB2`、`0047EFE0←00480230`（已证，不重复升）、`0047F250←00480278/00480290`。
- 可升且实交 **2 行**：`004309D0` `[静态推断]→[已证]`、`0047F250` `[未证]→[已证]`；其余 19 行 direct=0，**不为凑数放宽**。
- 严格判据：site 必在指令边界；`site+5+rel32==entry` 逐字节复核；caller 由 atlas entry+size 归属且不等于目标体内。未用 atexit/槽号/slot-baseline/P=R=100%。
- 基线+差分：同一批行 raw-byte E8 命中 3 / strict 命中 3 / 差 0；随机基线 seed=20261118、22 样本中 10 行有 strict direct（仅作参考，不替代差分）。

## 结果
- 新增真名 **1**（`0047F250→Draw_Fog`）；direct 升格 **2** 行。
- S08 并入后（atlas∩coverage 复算）named **20/22**、proved **3/22**；proved 门槛 11，仍差 8。
- 交付：`coverage_delta.tsv`（2 行）、`DIRECT_ONLY.tsv`（4 个站点，3 个入口）、`EVIDENCE/PROOF_*.txt`、`EVIDENCE/scan_summary.json`、`EVIDENCE/CONFLICT_SCAN.tsv`、`UNKNOWNS.md`、`DISAGREE.md`。
