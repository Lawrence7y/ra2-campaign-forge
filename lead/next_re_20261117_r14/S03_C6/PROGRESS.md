# S03-C6 PROGRESS — S03 A 集合未并入部分：8 行四环取证（续 C4/C5）

# 状态：完成（2026-11-19T15:2x+08:00）。目标 ra2youli\gamemd.exe 只读（SHA-256 73201CC0…F67476 现场复算全值吻合，ImageBase 0x400000）；仅写 S03_C6\ 与 _ghidra\S03_C6\；未建 venv / 未 pip install / 未改游戏文件 / 未写台账 / 未改 coverage.tsv / 未 git commit / 未写 _audit\。
# 开工骨架先落（≥5 行）后继续；必读已核：R14_COMMON §1/§6/§7/§8.1/§8.5/§8.6 六条；PENDING D-40/D-41/D-42（含细则1/2/3）；SURVEY_RING24\PROGRESS.md。
# 工具：python 3.12.10 + capstone 5.0.7(skipdata=True,detail=True) + pefile 2024.8.26；.text 全扫 1,392,592 指令 / 68,253 E8@边界 / 81,715 raw E8（与基准卡逐字相同）；extent 用分类表自写 CFG，非 atlas entry+size。
# S03 A 集合自数 = 31（classification.tsv subsystem=S03 ∧ has4_strict=1 ∧ has2_rtti=1，与 SURVEY_RING24 记 S03 A=31 一致）。排除已并入 12（C4 的 7 + C5 的 5）+ 已判不成立 3（C5 的 00431F10/00473AE0/0047AF10）后余 16；本卡只取 8 行不扩。
# 本卡 8 候选：00431F70 00432050 004322A0 0047AE10 0065CDD0 0065D0D0 0065D190 0065D240。

## 结论表（①②③④ 四环 + ③b 档位；偏移均入口相对 +0xNN，见 EVIDENCE/THREE_B_DETERMINATION.md）
| entry | name(delta，②归基类) | ② 全表(vt/slot/名)+⑯ | ③b 档位 | ④ direct站点 | 四环 | 处置 |
|---|---|---|---|---|---|---|
| 00431F70 | BufferIOFileClass::vslot7 | 1 表 7E3A2C/7/BIO | ① 状态机+mode 三路 | 4 | ✅ | delta |
| 00432050 | BufferIOFileClass::vslot12 | 2 表同槽12 → 基类 BIO | ④ 缓冲读 I/O 循环+0xD 错误码 | 1 | ✅ | delta |
| 004322A0 | BufferIOFileClass::vslot9 | 2 表同槽9 → 基类 BIO | ④ 缓冲读 I/O 循环+0xD 错误码 | 1 | ✅ | delta |
| 0047AE10 | CDFileClass::slot2 | 1 表 7E1668/2/CD | ④ CD 路径链循环+可证伪开文件 | 7 | ✅ | delta |
| 0065CDD0 | RawFileClass::slot12 | 1 表 7F0904/12/Raw | ② WriteFile −1/GetLastError +① | 8 | ✅ | delta |
| 0065D0D0 | RawFileClass::slot11 | 1 表 7F0904/11/Raw | ② GetFileSize −1/GetLastError | 3 | ✅ | delta |
| 0065D190 | RawFileClass::slot4 | 4 表同槽4 → 基类 Raw | ① 3 闸 DeleteFile 链+② | 5 | ✅ | delta |
| 0065D240 | (RawFileClass::slot15) | 3 表同槽15 → 基类 Raw | ③a 三闸汇同 ret | 1 | ❌③ | UNKNOWNS U1 |

## 核心数字
1. **四环齐全数 = 7**（00431F70/00432050/004322A0/0047AE10/0065CDD0/0065D0D0/0065D190）；**coverage_delta.tsv = 7 行**（=自报行数，M6/M15 一致）。③ 环不成立 1（0065D240，U1）。
2. **S03 A 集合行数 = 31**（自数，与 SURVEY_RING24 一致）；本卡取 8（余 8 未动）。
3. ② 成立 = 8/8（RTTI 全表逐字符读通、vt[slot]==entry，P3 表长约束）；④ 成立 = 8/8（direct 站点双通道逐行一致）；③b 成立 = 7/8。
4. ④ direct 站点合计 = 4+1+1+7+8+3+5+1 = **30**（delta 7 行站点 = 4+1+1+7+8+3+5 = 29）。
5. **③b 基率**（池 N=97=S03∧[静态推断]∧有extent；seed 20261119，2000 次无放回取 8；detector 见 work/baselines.py）：
   - loose：池命中 K=34、p=34/97=0.350515、E[8]=8×p=2.804124、MC 实测 2.7545。
   - strict：池命中 K=18、p=18/97=0.185567、E[8]=8×p=1.484536、MC 实测 1.4615。
   - `K=行数×均值=8×p` 是恒等式非校验（M3/M13）；「②∧④ 入选率」不算基线。本卡 7 行 > 两档 E[8]（2.80/1.48），非随机可解释。

## P1–P4 / M1–M8 落实
- **M1/⑯**：`work/enum_vtables.py` 全表枚举（P3 表长约束），00432050/004322A0→BufferIOFileClass、0065D190/0065D240→RawFileClass 归基类；② 类名与 delta name 一致（M2，见 DISAGREE D1）。
- **M3/M13**：只报 ③b 基率 strict/loose；恒等式不冒充校验。
- **M4**：00431F70/0065D190 各闸动作逐条不同；0065D240 三闸汇同 ret ⇒ 判 ③a（不算 ③b①）。
- **M5**：`work/verify_offsets.py` 逐条核对入口相对 +0xNN 与自家 EVIDENCE 一致。
- **M6/M15**：delta 行数 7 = 自报行数 7。
- **M7**：00432050/004322A0/0047AE10 写「循环」均体内有显式 memmove/rep movsd 写 + 回边 + 可证伪闸。
- **M8**：7 行 one_line_semantics 全文无「未证/未定/弱信号/线索」等自陈未证字样（已脚本核查）。
- **纪律17/站点归属**：站点用函数体外 + 非自环判定，不用 entry_at_or_before；站点归属用函数区间包含。
- **纪律1/14**：③b 判断回溯 ecx=this 来源（均取调用者对象），thiscall 入口参数取自 [esp+0xC]/[esp+0x1C] 等实测取值。

## 复算方法（命令）
- ② `python work/enum_vtables.py` → EVIDENCE/rtti_all_tables.json；④ `python work/scan_sites.py` → EVIDENCE/direct_sites_card8.json（双通道一致）。
- ③b `python work/dump_triage.py` → EVIDENCE/dis/*.txt；`python work/verify_offsets.py` 核对偏移；判读见 THREE_B_DETERMINATION.md。
- 基线 `python work/baselines.py` → EVIDENCE/baselines.json；IAT `python work/res_iat.py`；汇总 `python work/verify_final8.py` → EVIDENCE/final8.json。

## 交付
PROGRESS.md（本文件，≤60 行）/ UNKNOWNS.md / DISAGREE.md / coverage_delta.tsv（7 行）/ EVIDENCE\ / work\。
