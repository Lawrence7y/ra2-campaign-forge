# S08-K1 PROGRESS（卡号 S08-K1）

## 结论表
| 项 | 结论 | 级 | 证据 |
|---|---|---|---|
| 迷雾载体 | **非独立位图/字节数组**：每格 `CellClass` 字段，经 `CellClass*` 数组 `0x87F924` 索引 | 已证 | E01 `0x5863D3/0x5863D9`；E13 V1/V2 |
| 格数组基址/stride/尺寸 | `0x87F924`（Map 单例 `+0x13C`）；stride **4**（指针）；**512×512=`0x40000`**（`idx=(Y<<9)+X`，边界 `cmp 0x40000`）；内存 `0x100000` B | 已证 | E01；E13 V1/V2 |
| Fog/Shroud 数组数 | **0 个独立数组 / 1 个格指针数组**；每格 **2 个独立字节** `+0x120` Shroudedness、`+0x121` Foggedness + `+0x12C` 两位(`0x08`探索/`0x10`Mapped) + `+0x13C` 灰雾计数 | 已证 | E01 读 `0x5863F2`/`0x58652E`，写 `0x4A98EC`/`0x4A990F`/`0x4A9947` |
| 每 House? | **全局一份**；路径 `ecx=0x87F7E8` → `[0x87F924+idx*4]` → CellClass 字段；无 per-House 数组 | 已证 | E01 两谓词 + E02 `0x487950` 转调 |
| 每帧更新入口 | **`0x508F60 HouseClass::UpdateSpySat`，调用者数 1**（`0x4F850C`）；主帧链 `0x55DE81`→`0x55E160`→`[eax+0x5C]`(House 虚槽)→`0x4F850C` | 已证 | E08/E09/E13 V3/V4；A n_callers=1、B=1 |
| 状态迁移 | 黑→灰/亮：`0x4A9890`(1)、`0x5678E0 RevealArea2`(22)、`0x577D90`(2)、`0x6D8700`(19)；亮→灰/黑：`0x487690 ReshroudCell`(2)、`0x577AB0`、超武 `0x6CD773/0x6CD79C` | 已证 | E01/E06/E08 |
| 判定函数 | `0x586360 IsLocationShrouded`（43 调用者，读 `+0x12C&8`）；`0x5864A0 IsLocationFogged`（1，读 `+0x13C>0`）；`0x487950 CellClass::IsShrouded`（9）；`0x5865E0`恒假 stub（25） | 已证 | E01/E02/E13 |
| 雷达缓冲 | 目标 Surface `this+0x121C`、背景 `+0x1220`、地形色缓存 `+0x123C`、宽/高 `+0x1240/+0x1244`、脏矩形 `+0x1248..1254`、脏点向量 `+0x1260/+0x126C`；8-bit 调色板 1B/px，每格 1 像素（缩放 `+0x1488`） | 已证(字段)/静态推断(格式) | E04/E05/E10 + 线索 |
| 雷达重绘 | **非每帧全量**：`0x656EC0` 五道脏门（`0x65715C..0x6571C3`），全无则 `je 0x657872`；增量点 `0x6574C3`/`0x657520`；全量 `0x657CE0`（10 调用者）单独 | 已证 | E05；E13 |
| 单位点来源 | `0x655C50 DrawCell`（3 调用者）→ RTactical 哈希 `+0x1258` → House RGB → `SetPixel` | 已证 | E04/E05 + 线索 |
| 渲染层级 | 黑幕叠加在 `CellClass::Draw 0x4801F0` 内：`0x480230 call 0x47EFE0`（唯一调用者），早于 `0x480251` 位门；对象侧迷雾门 `0x5865E0` 恒假 ⇒ 不硬剔除 | 已证 | E13 V3 + E01 + 线索 |
| 双通道 | A=atlas `entry+size`（区间包含）；B=全 `.text` skipdata 扫（1,394,120 insn/66 skip）；关键调用者数 A/B 对账一致（`0x508F60`=1、`0x586360`=43、`0x5864A0`=1） | 已证 | E01/E13 |

## 核心数字（审计复算）
1. **迷雾数组基址/尺寸**：`0x87F924` / `0x40000` 格 ×4 B = `0x100000` B。复算：E01 `cmp eax,0x40000`（`shl eax,9` = ×512）+ `mov eax,[edx+eax*4]`；`python work/s14_verify.py` 打印 V1/V2。
2. **Fog/Shroud 1 还是 2 数组**：0 个独立数组 / 1 格指针数组 + 每格 2 独立字节字段。复算：`work/s04_fieldscan.py` 看 `+0x120/+0x121` 分别有独立写函数（E03）；`work/s02_predicates.py` 看两条谓词读不同字段（E01）。
3. **每帧入口/调用者数**：`0x508F60` / **1**。复算：`python work/s01_sweep.py && python work/s14_verify.py`→V3 `callers(00508F60) n=1`；atlas `n_callers=1` 交叉（E13）。
4. **雷达缓冲地址/尺寸**：字段 `+0x121C/+0x1220/+0x123C`，尺寸由 Surface `vtable+0x80` 运行期取（`0x657D52`）；非固定 VA。复算：`work/s06_radar_focus.py`（E05）。
5. **雷达每帧全量?** **否**（五脏门 + 独立全量函数 `0x657CE0`）。复算：`work/s06_radar_focus.py` 的 `0x657150..0x657260`（E05）。

## 证据/复跑/合规
- 证据：`EVIDENCE/E01_predicates_raw.txt`(1537行)、`E02_api_raw.txt`、`E03_fieldscan.txt`、`E04_radar_raw.txt`(4091行)、`E05_radar_focus.txt`、`E06_frame_trace.txt`、`E07_perframe.txt`、`E08_reveal_chain.txt`、`E09_houseupdate.txt`、`E10/E11/E12`、`E13_verify.txt`、`E14_claims.txt`(30 断言 30 OK/0 MISMATCH) —— 均不截断。
- 复跑（cwd=项目根，只读 gamemd.exe）：`python work/s01_sweep.py && python work/s02_predicates.py > EVIDENCE/E01_predicates_raw.txt && python work/s04_fieldscan.py > EVIDENCE/E03_fieldscan.txt && python work/s06_radar_focus.py > EVIDENCE/E05_radar_focus.txt && python work/s14_verify.py > EVIDENCE/E13_verify.txt && python work/s15_claims.py`（其余脚本同法；s15 自写 E14_claims.txt）。
- Ghidra：未使用（双通道已由 atlas+raw capstone 构成，避免并发占额）；未复制/未删除 W150。
- 写域：仅 `S08-K1\` 与 `work/`；未改 `gamemd.exe`（SHA-256 开工 `73201CC0…F67476`）、未写台账、未 git commit。
