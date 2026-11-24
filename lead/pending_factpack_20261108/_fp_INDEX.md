# _fp_INDEX · 待裁四卡事实基础包总索引（只备料不裁决）

- 任务：为 N10-C02／C03／C06／C07 四张 proposed 卡备料；本目录 = 唯一写域 `lead/pending_factpack_20261108/`。
- 纪律实况：零真机、零采样代码；上游件（含 PENDING/GOAL/DQ/n11_protocol_spec 全部）零改动、仅 Read+hashlib+切片；未 commit、未 push。Python 一律 `python -I -X utf8 -c` + 绝对路径；指纹 hashlib。
- 日期：2026-11-08 深夜至 11-09（备料会话）。

## 1 产出件

| 件 | 内容 |
|---|---|
| `_fp_N10-C02_Q1.md` | Q1 D-13 技术前提与最小观测协议：要裁什么／事实前提 6 条／现存 7 条／缺口 4 条 |
| `_fp_N10-C03_Q2.md` | Q2 F8 推导路代价：7 万的来源链与口径（算法/分母/五条限制）／技术事实 vs 价值判断划界 |
| `_fp_N10-C06_Q5.md` | Q5 帧数/重复性/阈值：逐裁项输入需求表／锚清单／硬前置=先导趟 |
| `_fp_N10-C07_Q6.md` | Q6 责任身份：要补登三字段／非技术裁决依据／现盘零记载检索实录 |
| `_fp_fingerprint_out.txt` | 17 件上游件 hashlib 实算输出（sha256/bytes/lines） |
| `_fp_goal_slices_out.txt` | GOAL 承重行切片实跑输出（50-56/4387-4395/5136-5144/5822-5834/6015-6072/6640-6650/8400-8416/9737-9760） |
| `_fp_fingerprint.py`（未落盘成功——三次被 Mimosa PreToolUse 拦截，改用 `python -I -X utf8 -c` 内联实跑，指纹结论不受影响） | — |

## 2 指纹核验（本会话 hashlib 实算 vs 编排方清单 = 10/10 MATCH）

| 对象 | SHA256 | 字节数 | 判定 |
|---|---|---|---|
| lead/PENDING_DECISIONS.md | 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7 | 52419 | MATCH |
| lead/GOAL_THREE_TARGETS_20261018.md | 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede | 759518 | MATCH |
| lead/d13d14_cards_20261108/DECISION_QUESTIONS.md | 0a709f2da12e0234cd94ff0baf521652e7d1aed6cfd04929b9728adbfd85bf5f | 27172 | MATCH |
| lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md | 7a617a43b32fc2e38c7e46ff9d436f903810ad9cae919fc0eb891a0f9f5796e0 | 29619 | MATCH |
| lead/n11_protocol_spec_20261108/_ps_N11_MIN_OBS_PROTOCOL_SPEC.md | 3d463483ad0d53d048a9cad9990b6c0e8b72485ef20eeaa8c519074ebdf94bda | 44300 | MATCH |
| lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md | c0dfb0d17edab4d0d89c43dc48bce4b84354fd13bd89cae7277aa15e82cf65f2 | 54351 | MATCH |
| lead/static_spec_n9_20261107/STATIC_COUNT_SPEC.md | 5b933fe2fcb3cc35c5026cb57b45f29da29c90b67a618346af248744ed3ccdb9 | 32281 | MATCH |
| lead/spec_static_closure_20261108/STATIC_GAP_CLOSURE.md | e0c00683fb23b0b3777d71639f3d7d265208057969073e53fd2b7195d0c3e1f7 | 28648 | MATCH |
| lead/direction_ruling_20261108/RULING_DIRECTION.md | 0ebd68dd11a2a54a33e30c6c658d12656fb1af77f14ef4c5724f829d3d90c653 | 16514 | MATCH |
| lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md | c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c | 27225 | MATCH |
| （另实算 7 件）RULING_D24 / RULING_D26 / D27 / D28 / D29 / D30 / W8_STATIC_LOCATE | 见 `_fp_fingerprint_out.txt` | — | 登记实算值 |

（注：行数口径 = `bytes.decode().splitlines()`，比编排方 lines 少 1——不计末尾换行；以 sha256+bytes 为 MATCH 依据。）

## 3 可裁性判定汇总（readyCount = 1）

| 卡 | 判定 | 一句话依据 |
|---|---|---|
| N10-C02（Q1） | **部分足以裁** | 「是否进入无采样实现规格评审」半边事实已足（协议规格已成文+首件复核 confirmed+D-31 保留该方向+四门逐字在盘）；「如何变更 D-13 技术方案」缺备选方案集（现盘无任何文件列出 K4 新时基机理候选等第二套以上方案） |
| N10-C03（Q2） | **部分足以裁** | 7 万的推导式/分母/带宽/对照路现状全部在盘已亲核；缺「接受度判据/对照基线」（价值判断，现盘不可得）与口径④声明（文字活可先裁） |
| N10-C06（Q5） | **部分足以裁** | 规则/方法/锚/负面清单已足；判线数值是纯裁决动作；**各卡帧数与重复趟数有硬前置**（先导趟数据⇒四门⇒用户当轮明示），未放行采集前产不出数 |
| N10-C07（Q6） | **现盘事实已足以裁** | 裁决内容=「确认补登动作与通道」；身份原则、非技术裁决定性、现盘零记载系统检索、登记模式先例、D-31 deferred 口径全部在盘；缺的 ID 值是裁决后执行输入，非裁决前提 |

**readyCount = 1**（判定「现盘事实已足以裁」的卡数；N10-C07）。

## 4 备料会话发现的现盘状态要点（供裁决者，非结论）

1. **卡面已被现盘部分超越**：DQ 卡面写「三选一未裁／状态未同步」；现盘 PENDING:22-28 已有 D-31 同步行（2026-11-08，依据 RULING_DIRECTION Q4）：D-13 维持 PAUSE、实施 BLOCKED，「仍需用户在 D-13 三选一（A/C/暂停）上明示后方可归档」（PENDING:27）。卡面所引 PENDING 行号（:34-40/:105/:68 等）为旧版快照，现盘行号以备料包所记为准。
2. **D-31（RULING_DIRECTION.md）已把四卡中三卡的缺口显式列 deferred**（:93）：「实际代价接受度、降采样参数、帧数/重复趟数/阈值/扰动上限及实际责任身份；缺输入不编数值、不编身份」——即 D-31 未裁这些项，与四卡 proposed 状态一致。
3. **两份 N-11 协议规格件并存**：首件 `_ps_…`（13 维，独立复核 verdict=confirmed）与正式件 `OBSERVATION_PROTOCOL_SPEC.md`（12 维重组稿，**自身未经独立复核**，OBS:430）——评审若引用，须注意复核覆盖面只到首件。
4. `lead/n10c04_ruling_20261108/` 目录在备料会话开始时已存在（仅指纹脚本两件，他轮产出），未触碰——N10-C04 不属本任务四卡。
