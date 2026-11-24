# S17-PADD · PROGRESS（加固唯一严格达标子系统）

- 卡号 S17-PADD｜目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`（只读，自算一致）｜Python 3.12.10 + capstone 5.0.7(skipdata=True) + pefile 2024.8.26，未建 venv / 未 pip install / 未改台账 / 未 commit。
- 必读已核：R14_COMMON §8.1 错源⑬⑭⑮⑯⑰㉓ / §8.5 主条 / §8.6 六条（条1 四环、条3 ③b 四档）/ §8.7 判据1/2/3/5/6/8 / §8.8 RULING-R15 条4（D-43(A) 宽读法）。

## 一、盘上重算（不照抄卡面）
| 量 | 本卡自算 | 卡面 | 一致 |
|---|---|---|---|
| S17 coverage 全行 | 104 | — | — |
| S17 atlas∩coverage（分母 n，大小写归一） | **102** | 102 | ✓ |
| named_S(R14) | **94** | 94 | ✓ |
| proved（atlas 内 `[已证]`） | **54** | 54 | ✓ |
| proved_strict（`[已证]` 且语义无 `[未证]`） | **53** | 53 | ✓ |
| 门槛 | named 92 / proved 51 / strict 51 | 同 | ✓ |
| 三余量（补前） | +2 / +3 / +2 | 同 | ✓ |
- 表外 2 行 = `006CF320`/`006CF410`（均 `[静态推断]`），不计分母。S17 全表 `[已证]`+语义含 `[未证]` 恰 **1 行** = `006CF240`（与 MEASURE-F3A 一致）。

## 二、三线逐行结论
| 线 | 目标 | 实补 | 交付行 |
|---|---|---|---|
| A named | ≥96 | **0** | 无（见 UNKNOWNS U1）|
| B proved | ≥56 | **2** | `006CF430`, `004A2990` |
| C proved_strict | ≥55 | **1** | `006CF240`（语义补证，grade 不变）|
- 合计 **3 行**（≤8）；自报 3 = delta 3（§8.7 判据7 ✓）。

## 三、逐行四环摘要（详见 EVIDENCE/FOUR_RINGS.md）
| entry | 线 | ② 全持有表（RTTI） | ③b 档位/入口偏移 | ④ 站点 |
|---|---|---|---|---|
| 006CF240 | C | vt `7F4108` slot4，COL `80B730`→TD `842730`→`.?AVSwizzleManagerClass@@`，单表 | ③b②+③b③：`+0x0B` E_POINTER / `+0x1B`,`+0x70` S_OK / `+0x61`,`+0x64` 写8字节对 / `+0x68` 清零 | **476** 个 direct E8（site+5+rel32==entry，全体外、非自环，`push 0xB0C110`=this）|
| 006CF430 | B | vt `7F4108` slot0，同上 RTTI，单表 | ③b②+③b③：`+0x0B` E_POINTER / `+0x27`,`+0x3A` GUID cmp / `+0x3F` E_NOINTERFACE / `+0x51` AddRef / `+0x55` S_OK | 活 vt：ctor `0x6CF0C8`/`0x6CF0FC` 装 `[0xB0C110]=7F4108`、`0x6CF1D4` 装 this；slot0≠行1 slot4 |
| 004A2990 | B | vt `7E5DAC` slot0 + `7E5D94` slot6（同 TD `81FC30`=`.?AVCStreamClass@@` 双接口表）| ③b②+③b③：`+0x09` E_POINTER / `+0x30`,`+0x45`,`+0x5A` GUID cmp / `+0x72` E_NOINTERFACE / `+0x7E` AddRef / `+0x81` S_OK | 活 vt：ctor `0x4A2820`（`mov esi,ecx`）装 `[esi]=7E5DAC`/`[esi+4]=7E5D94`；install site 不共用 |

- 三行 §8.7 判据1（全持有表枚举）✓；判据2（② 类名=name 类）✓；判据5（偏移逐字同 EVIDENCE）✓；判据8（交付语义 0 个自陈未证）✓。
- 类归属 fail-closed：TD+8 内联名串逐字符读，全命中；无「读失败仍猜名」。

## 四、③b 基率
- 池 S17 `[静态推断]`∩atlas = **45** 行；检测器忠实实现 §8.6 条3 四档、按 atlas size 限界（不跨函数）。命中 **11/45 = p 0.244444**（①1/②8/④5）；本卡行 B 两行均命中 ②。
- N=2，seed 20261119，2000 次：K=987，E[N]=N·p=0.488889，MC 均值=0.493500，P(两行都过)=0.053000。`K=行数×均值` 是恒等式，不作校验（§8.7 判据3）。

## 五、补后核心数字
- 补后：n=102，named_S **94**（余 +2）、proved **56/102=54.90%**（余 +5）、proved_strict **56/102=54.90%**（余 +5）；三门槛 92/51/51 全过。

## 六、一句话结论
- **S17 更稳**：proved 与 proved_strict 余量各由 +3/+2 升至 +5/+5，最脆弱的 strict 线补上唯一自陈未证行且新增 2 行带 ③b 字节证据；named 线因无合法异源通道维持 +2（未削弱）。
