# S16-K1 PROGRESS（卡号 S16-K1）

## 结论表

| 项 | 结论 | 级 | 证据 |
|---|---|---|---|
| `SuperClass` RTTI / vft / ctor / GetSize | TD `8423E0`，vft `7F3FE8`，ctor `6CAF90`，GetSize v[12]=`6CE210`→`0x80` | 已证 | `EVIDENCE/E01_rtti.txt`, `E02_vftable_slots.txt` |
| `SuperWeaponTypeClass` RTTI / vft / ctor / GetSize | TD `842600`，vft `7F4090`，ctor `6CE5B0`，GetSize v[11]=`6CE900`→`0x100`；v[12] 是 Checksum（槽位与 SuperClass 错开） | 已证 | `E01`, `E02` |
| SuperClass 字段数 | **27**（具名行，见 LAYOUT §2）；最大偏移+宽 `0x7C+4=0x80` = GetSize `0x80` | 已证 | `E11_super_fields.txt`, `E01/E02` |
| SWType 字段数 | **31**（具名行，见 LAYOUT §3）；最大偏移+宽 `0xFC+4=0x100` = GetSize/工厂 `0x100` | 已证 | `E05_swtype_ini_loader_full.txt`, `E07_loader_keys_pairing.txt`, `E02` |
| INI 键→偏移 | `RechargeTime→+B0`（×900.0）、`Type→+B4`、`Action→+BC`、`Range→+F8`、`PostClick→+EE`、`PreClick→+ED`、`AuxBuilding→+C8`、`UseChargeDrain→+E5` 等 19 键实证 | 已证 | `E04_ini_strings.txt`, `E06_ini_key_context.txt`, `E07` |
| 充能更新函数 | **`0x6CBCA0` `HasChargeProgressed`**；调用点 **2**（活 `4F8E4A`；死 `4F9397`，0 调用/0 imm32） | 已证 | `E03_callmap.txt`, `E08_charge_callers.txt`, `E10_perframe_chain.txt` |
| 每帧证据 | `55DE81 CurrentFrame+1` → `55DE9A call 55E160` → `55E269 call [eax+0x5C]`（House vft `7EA8A0` slot23=`4F8440`）→ `4F8E28..4F8E4A` 每 House 每 Super 1 次 | 已证 | `E10_perframe_chain.txt` |
| RulesClass 倍率 | **存在**：`[0x8871E0]+0x760`=`ChargeToDrainRatio`(double)；写点 `67185D`；用于 `6CBF64/6CBF72/6CBA1D`；另有 `Rules+0xD70` AI 阈值 | 已证 | `E11_super_fields.txt`, `E13_rules_charge_ratio.txt`, kb/30:2419 |
| 充能状态机 | 未充能→充能→就绪→发射/泄放回充；判据 `6CBD5D/65/67`；`ChargeDrainState` 4 态 `-1/0/1/2` | 已证 | `E11`, LAYOUT §4 |
| 启动链 | `4FAE50`→`ClickFire 6CB920`→3×`Launch 6CC390`→12 路跳表 `6CDE44`→效果 | 已证（UI 上游未知） | `E12_launch_chain.txt` |
| 双通道 | A=atlas `entry+size`；B=raw capstone `.text` 全扫（1,394,120 insn/66 skipdata + 序言/ret 区间）。两通道不同源；atlas 洞 `4F830C..4F93E0` 由 B 补齐 | 已证 | `E03`, `E08`, `E09`, `E10` |

## 核心数字（复算方法）

1. **字段数 27 / 31**：数 LAYOUT §2/§3 具名行；复算 `python work/s11_super_fields.py` + `work/s07_loader_keys.py`，按偏移去重。
2. **充能函数 `0x6CBCA0` 调用者 2（1 活 1 死）**：`work/s03_callmap.py` 全 `.text` skipdata 扫 `E8 rel32`，再 `work/s08_callfreq.py` 查 `calls[0x6CBCA0]`；死证 `work/s08_callfreq.py` 输出 `0x4F9370` 的 `call sites=[]` 且 `imm32 refs=[]`。
3. **GetSize 一致性**：`work/s02_vftable_slots.py` 解 v[11]/v[12]；最大写偏移来自 ctor/loader/工厂 `push 0x100`；`0x7C+4=0x80`、`0xFC+4=0x100`。

## 证据/复跑

- 证据：`EVIDENCE/E01..E12`（未截断，逐条指令含字节）。
- 复跑：`python work/s01_rtti.py && python work/s02_vftable_slots.py && python work/s03_callmap.py && python work/s05_dump_loader.py && python work/s07_loader_keys.py && python work/s08_callfreq.py && python work/s10_perframe.py && python work/s11_super_fields.py && python work/s12_launch.py`（cwd=项目根，Python 3.12.10 + capstone 5.0.7 `skipdata=True` + pefile 2024.8.26；只读 gamemd.exe）。
- 已删临时 Ghidra 副本（未使用；双通道已由 atlas + raw capstone 构成）。
