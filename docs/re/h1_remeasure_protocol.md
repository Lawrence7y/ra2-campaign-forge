# H1 指纹复测协议 · evidence schema 与离线判分（H1RM）

> 任务卡 ZC-H1RM · 执行方 MiMo（M 轨起草）· 工作区 `D:\Project\ra2-campaign-forge`
> 上游：`docs/re/h1_map_fingerprint.md`（§3 指纹 / §5 复测建议）、`docs/re/h1_fanout_mechanism.md`
> 协议卡全文见文末 §7 与 `out/re_work/dispatch_v30/prompt_zcode_h1_remeasure.txt`
> 证据等级：`[实证]` / `[推演]` / `[待实测]`。真机数字一律 `[待实测]` 直至 ZCode 回报。
> 写作用域：本文件、`tools/h1_remeasure_score.py`、`out/re_work/h1_remeasure/**`、协议卡 txt。
> 禁止：`bench_replay.py`、地图、游戏、台账、RESULT。

---

## 0. 一句话

H1 三档图已从 7× 同格堆叠修成 **unique==total / max_stack=1** 并带 **H1FP1 指纹**；本轮用
「S1 指纹门禁 + A2 delta + 国家矩阵 + except 门禁」真机复测，离线脚本 `tools/h1_remeasure_score.py`
一键判分。**三档 delta 落带且指纹 100% 之前，H1 前提性能 ROI 保持冻结。**

---

## 1. 期望指纹与标度目标 `[实证]`（`tools/h1_map_fingerprint.py verify`）

| 档位 | fingerprint | 条目数 | target T（设计 2 槽） | delta 落带 |
|---|---|---|---|---|
| U0050 | `H1FP1\|U0050\|26c371932de7` | 350 | 50 | [40, 60] |
| U0200 | `H1FP1\|U0200\|4bf2d6692bd5` | 1400 | 200 | [160, 240] |
| U0800 | `H1FP1\|U0800\|1189b6b550ff` | 5600 | 800 | [640, 960] |

旧图 hash（判「装了旧图」用，不得当新图）：`4b8c8af9210b` / `734cbc26717c` / `57e0157ed7cd`。

**误选签名带**（命中即 `MISSELECT_SIG`，禁止当标度点）：

| 签名 | 带宽 | 来源 |
|---|---|---|
| 178 | 178±20 | `segD_run.py` 误选检出 |
| **713** | **713±20** | 旧 U0200 误选（7×100+SU）；**硬红线：不得再当 U0200 读数** |
| 2852 | 2852±40 | `segD_run.py` 误选检出 |

---

## 2. 判分总览

| # | 判据 | 条件 | 失败含义 |
|---|---|---|---|
| J1 | 指纹作废率 | 作废局/H1 尝试局 ≤ 20% 为测量健康线；**计入表的局必须 100% 过 S1** | 测量链路先修 |
| J2 | A2 delta | 三档 mean(delta) ∈ [0.8T, 1.2T] | 标度不成立 |
| J3 | 误选签名 | 有效标度表不得含 178/713/2852 带内读数 | 整批 FAIL |
| J4 | 国家矩阵 | 8 格覆盖，每格 n≥3（或声明预算） | 缺证据 |
| J5 | 性能 coverage | coverage = 有效性能样本/有效对局 > 0，fps/tick/cpu 齐 | 附表空 |
| J6 | except 门禁 | 无隐瞒新生；无注入区 EIP | 红线 |
| J7 | 还原 | 地图 + ra2md.ini 还原且 sha256 一致 | 未收口 |

**ROI 解冻（全部满足）**：R1 三档 delta 落带 ∧ R2 计入局指纹 100% ∧ R3 无 MISSELECT 混入 ∧ R4 段5 还原+except 全绿。
任一不满足 ⇒ 输出 `ROI=KEEP_FROZEN`。

---

## 3. evidence schema（`h1_remeasure_evidence_v1`）

### 3.1 JSON（主格式）

```json
{
  "schema": "h1_remeasure_evidence_v1",
  "batch_id": "H1RM-20260930-01",
  "game_dir": "ra2bench",
  "executor": "ZCode",
  "notes": "optional",
  "runs": [ { "…": "见 3.2 行字段" } ]
}
```

### 3.2 行字段（每局一行；JSON 对象 / CSV 一行）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `run_id` | str | Y | 唯一，如 `S3-N1-U0050-r1` |
| `seg` | str | Y | `0`..`5` |
| `map_kind` | str | Y | `h1` \| `empty` |
| `tier` | str | Y | `U0050` \| `U0200` \| `U0800` \| `NA`（空图用 `NA`） |
| `player` | str | Y | `Americans` \| `Russians` \| `Random` |
| `enemy` | str | Y | 同上 |
| `unit_count` | int | Y | 0 或 10（矩阵轴） |
| `credits` | int | N | 默认 0；N5 用 10000 |
| `fingerprint_read` | str | Y* | 进图回读原文；空图可 `""` |
| `fingerprint_expect` | str | N | 缺省按 §1 表 |
| `name_read` | str | N | UI/scenario Name 原文 |
| `units_seen` | int | Y | 计数（建议 @f15） |
| `sample_frame` | int | N | 默认 15 |
| `fps_avg` | float | N | 段4 |
| `cpu0_avg` | float | N | 段4 |
| `tick_miss` | float | N | 段4 |
| `except_fresh` | bool | Y | 段5；false=无新生 |
| `except_eip` | str | N | 有 except 时贴 Eip |
| `except_sha256` | str | N | |
| `restored` | bool | Y | 收尾是否还原 |
| `invalid` | bool | N | 执行方预作废（S1 不过等） |
| `invalid_reason` | str | N | |
| `notes` | str | N | |

\* `map_kind=h1` 时必填。

### 3.3 CSV 等价

表头即 3.2 字段名逗号拼接；空值留空；bool 用 `true`/`false`。脚本两种都吃。

---

## 4. 判分算法（与 `tools/h1_remeasure_score.py` 一致）

1. **载入** JSON/CSV → 规范化字段。
2. **S1 指纹**（仅 `map_kind=h1`）：
   - `fingerprint_read == fingerprint_expect`（缺省查 §1 表）⇒ `fp_ok`；
   - 否则 `invalid=True, reason=fp_mismatch|fp_missing`，计 J1 作废。
3. **误选签名**：`units_seen` 落入 178±20 / 713±20 / 2852±40 ⇒ `misselect=True`，
   **强制剔出有效标度表**；若执行方未标 invalid 也算 J3 警告（有混入则 FAIL）。
4. **A2 delta**（每档）：对每个矩阵格 `(player,enemy,unit_count)`，
   `delta = mean(units_seen|h1,fp_ok) − mean(units_seen|empty,同格)`；
   档 `delta_mean = mean(各格 delta)`；落带 ⇔ `0.8T ≤ delta_mean ≤ 1.2T` 且样本齐。
   缺空图对照 ⇒ 该格 `delta=null`，档判 `NO_EMPTY_CTRL`（FAIL-证据）。
5. **矩阵覆盖**：8 格 = {美蘇,美随机,蘇随机,随机随机}×{UC=0,10}；`min_rounds` 默认 3。
6. **性能**：`coverage = n(fps 或 cpu 或 tick 非空) / n(有效 h1 局)`。
7. **except/还原**：任意 `except_fresh=true` 记 J6 违规（除非 `invalid`）；`restored=false` 记 J7。
8. **ROI**：R1–R4 全真 ⇒ `ROI=UNFREEZE_CANDIDATE`，否则 `ROI=KEEP_FROZEN`。

退出码：`0` 总判 PASS（允许非阻断 WARN），`1` 总判 FAIL。

---

## 5. CLI

```powershell
# 判分（JSON 或 CSV）
python tools\h1_remeasure_score.py path\to\evidence.json
python tools\h1_remeasure_score.py path\to\evidence.csv --md out\re_work\h1_remeasure\SCORE.md

# 离线单测（写假数据并跑通 schema）
python tools\h1_remeasure_score.py --selftest

# 仅打印 schema 字段
python tools\h1_remeasure_score.py --schema
```

默认 markdown 报告落 `out/re_work/h1_remeasure/SCORE.md`（可用 `--md` 覆盖）。

---

## 6. 假数据单测约定

`out/re_work/h1_remeasure/selftest/`：

| 文件 | 意图 | 期望总判 |
|---|---|---|
| `fake_pass.json` | 三档 delta 落带、指纹齐、矩阵齐、无签名混入 | **PASS** / `ROI=UNFREEZE_CANDIDATE` |
| `fake_fail_713.json` | U0200 读数=713（旧误选签名） | **FAIL**（713 剔出后 U0200 无有效标度；J3 无泄入但 hard_flag=U0200_READ_AS_713） |
| `fake_fail_fp.json` | 指纹不匹配仍计数 | **FAIL**（J1 作废 → U0050 无有效数据） |
| `fake_fail_scale.json` | U0800 delta 出带（400≠800） | **FAIL**（J2 OUT_BAND）/ `ROI=KEEP_FROZEN` |

另写 `fake_pass.csv` 验证 CSV 载入与 JSON 等价。
`--selftest` 断言上述判定 + hard_flag，全过 exit 0。

---

## 7. 协议卡全文（粘贴给 ZCode；与 `out/re_work/dispatch_v30/prompt_zcode_h1_remeasure.txt` 同文）

```text
【任务卡 ZC-H1RM】H1 指纹复测：cell 互斥修复后 units_seen 标度 + 国家矩阵 + ROI 解冻判据（P0）
（2026-09-30 · 上游 H1-MAPFIX / H1-FANOUT · 评分脚本 tools\h1_remeasure_score.py）

◆ 执行方：ZCode（唯一真机执行方）   ◆ 期望耗时：120–180 分钟（含空图对照 + 三档 × 国家矩阵）
◆ 工作区：D:\Project\ra2-campaign-forge · 游戏目录 ra2bench（所有命令带 --game-dir ra2bench）
◆ 基线（只读，不改）：
   ra2bench\gamemd.exe
   ra2bench\ra2render.dll = 152,576 B / MD5 3C1077BD44F2B0DB9D30D55C5C9DA68C（ZC-10B 部署态）
◆ 地图基线（新 H1 图，已含 H1FP1|tier|hash，装图前先自证）：
   U0050 → H1FP1|U0050|26c371932de7   （350 条目 / unique=350 / max_stack=1）
   U0200 → H1FP1|U0200|4bf2d6692bd5   （1400 条目 / unique=1400 / max_stack=1）
   U0800 → H1FP1|U0800|1189b6b550ff   （5600 条目 / unique=5600 / max_stack=1）
   复算：python tools\h1_map_fingerprint.py verify   → 三档全 PASS 才准装图。

◆ 目的/假设
  P1 验证 cell 互斥修复后，units_seen 随档位 50/200/800 标度（A2 delta 落带）。
  P2 验证进图指纹 S1 能拦下「旧 U0200 误选」（三轮皆 ≈713 不得再当 U0200 读数）。
  P3 给出「H1 前提性能 ROI 可解冻」的硬判据（见「判据 · ROI」）。
  本卡不改图、不改注入、不找根因；只做复测与判分。

◆ 绝对禁止
  伪造证据（截图唯一 MD5 + 进程留痕 + 图/ini 前后 sha256）｜挪旧读数/旧截图冒充本轮
  把「没读到指纹」写成「指纹通过」｜把 ≈713 读数直接当 U0200 标度点｜
  改 ra2render/** / ra2youli/** / gamemd.exe / .mix / 地图本体 / 台账 / docs
  改 tools/bench_replay.py（T15/T17 在用，本轮禁改）｜UI 失响应继续硬点｜点小地图当机位复位

◆ 段 0（装图 + 指纹自证）【必做】
  0.1 哈希核对 ra2bench（对照 out\loadbench\RA2BENCH_MANIFEST.md）；
      python tools\verify_anchors.py → 323/323。
  0.2 python tools\h1_map_fingerprint.py verify → 三档 PASS（贴原文；任一 FAIL 立即停手回报）。
  0.3 python tools\bench_map_install.py --install-a --game-dir ra2bench（H1 按旧名安装；先备份）。
      记录安装后游戏目录内三档图 sha256 + 读回 [Basic] H1Fingerprint / Name（F0 自证）。
  0.4 空图对照件：无 [Units]/[Infantry] 的同尺寸 skirmish 图（保留 waypoints）。
      若仓库无现成空图 ⇒ 用任意无预置单位的同尺寸遭遇战图，记录图名+sha256 写进 RESULT；
      禁止拿 H1 图删段冒充空图。空图不得带 H1FP1 指纹（无指纹是预期）。
  0.5 清点 ra2bench\except.txt：有旧件则哈希隔离到 evidence/pre_batch/，保证每局判新。
  0.6 锁定 ra2md.ini [Skirmish] 现状哈希（矩阵改 UnitCount/Credits 时每档留前后副本+sha256）。

◆ 段 1（S1 进图指纹门禁）【每局强制，先于一切 units_seen】
  进图后回读当前场景 Name / H1Fingerprint（UI 或 scenario/存档读回），对照目标档：
  S1-a 读回 == 目标档 H1FP1|tier|hash ⇒ 计数资格成立，进入段 2/3。
  S1-b 读回为其它档指纹 ⇒ 判「进错图」，本局 units_seen 作废（不进 delta 表），记 MISSELECT，重跑。
  S1-c 读不到 H1Fingerprint（旧图/装载失败）⇒ 判「装载物版本错」，对照旧图 hash 表
       （4b8c8af9210b / 734cbc26717c / 57e0157ed7cd）或文件 sha256，作废并重跑。
  S1-d Name 短标 fp:<hash12> 须与 H1Fingerprint 内 hash 一致；不一致按 S1-b 作废。
  S1-e 误选签名 ≈178/713/2852 仅作副证；与指纹冲突时以指纹为准。
  ★硬规则：旧误选签名 713（含 178/2852 带）**不得再当任何档的标度读数**。
    读数落在签名带（713±20 / 178±20 / 2852±40）⇒ 一律标 MISSELECT_SIG，
    禁止写入 A2 delta 表的「有效 units_seen」；即使某轮误贴 U0200 标签也不得采信。

◆ 段 2（A2 delta 口径）【必做】
  对每档 tier ∈ {U0050, U0200, U0800}：
    delta = units_seen(H1_tier) − units_seen(空图对照，同 player/enemy/UnitCount)
    期望   delta ∈ [T×0.8, T×1.2]，T = 50 / 200 / 800（设计 2 槽量）
  2.1 先过 S1，再进 delta；空图对照同样记 units_seen@同采样帧（建议 f15，与 EXCEPT-AB 对齐）。
  2.2 每档至少给出「均值 delta + 单轮明细」；三档各有一条落带才谈 ROI。
  2.3 若走 M2（负载挂 Neutral）另卡换版，本卡 target 仍按 2 槽设计量。

◆ 段 3（国家矩阵）【必做，每格 ≥3 轮或按预算写明】
  矩阵 = {美蘇, 美随机, 蘇随机, 随机随机} × {UnitCount=0, UnitCount=10}（共 8 格）
  对照锚（与 h1_map_fingerprint.md §5.3 对齐）：
    N1 美蘇   / UC=0 / Credits=0        基线（去 GenerateStartingUnits 噪声）
    N2 美随机 / UC=0 / Credits=0        敌国效应
    N3 蘇随机 / UC=0 / Credits=0        玩家国效应
    N4 随机随机 / UC=0 / Credits=0      旧 713 事故组
    N5 美蘇   / UC=10 / Credits=10000   复现 ra2bench 现状
    （UC=10 的随机组为矩阵补齐格，记录即可，判分权重同 UC=0）
  3.1 每格 H1 侧 ≥3 轮；空图对照每格 ≥1 轮（建议 ≥3）。
  3.2 先指纹后计数；国家对在大厅锁定后截图留证（禁止整批 Random 却记成美蘇）。
  3.3 产出矩阵表：格 | 档 | n | units_seen 均值±极差 | 空图均值 | delta | 落带? | 指纹通过率。

◆ 段 4（性能采样）【必做，注明 coverage】
  4.1 每档（U0050/U0200/U0800）至少 1 段有效对局记录 fps / tick / cpu0（tools\bench_metrics.py --run 或等价遥测）。
  4.2 RESULT 必须写 coverage = 有效性能样本数 / 有效对局数；禁止只贴最好的一局。
  4.3 性能数字只作附表，不参与 ROI 解冻主判据（主判据看 delta+指纹）。

◆ 段 5（还原 + except 门禁）【必做，必须用新 except gate】
  5.1 每局收尾立即跑：python tools\check_except_gate.py --game-dir ra2bench --check
      （或 bench_replay 现行集成的 except gate；不得只靠“没崩”口头结论）。
  5.2 except 新生 ⇒ 本局 FAIL_LANE，不得记 PASS；复制 except.txt 到
      evidence/seg5/gameNN_except.txt + CreationTime/字节数/SHA256 + Eip/寄存器/栈首帧摘要。
  5.3 收尾还原：bench_map_install.py --restore --game-dir ra2bench，贴 --verify 全 PASS + sha256；
      ra2md.ini 若改过 UnitCount/Credits，还原并贴 sha256（须与改前一致）。
  5.4 自证门禁原文：verify_anchors 323/323；h1_map_fingerprint verify 三档 PASS；
      check_except_gate 每局记录；bench_map_install --verify 全 PASS。

◆ 判据（写进 RESULT 与 evidence JSON，禁止只写结论）
  J1 指纹作废率 = S1 作废局数 / H1 尝试局数；>20% ⇒ 先修测量再谈标度（EXCEPT-AB J6 同口径）。
  J2 A2 delta 表：三档各 mean(delta) 与逐轮明细；落带 = [0.8T,1.2T]。
  J3 误选签名：凡 units_seen ∈ {178±20, 713±20, 2852±40} ⇒ MISSELECT_SIG，禁止计入 U0200/任意档标度点。
     「旧误选签名 713 不得再当 U0200 读数」为硬红线；出现且被计入有效表 ⇒ 整批判 FAIL。
  J4 国家矩阵：8 格覆盖与每格 n；N4（随机随机）对照旧事故是否被 S1 拦下。
  J5 性能 coverage 与 fps/tick/cpu 附表。
  J6 except 新生率 + 是否出现注入区 EIP（0x54D3xxxx / 0x01B00000 ⇒ 红线停）。
  J7 还原完整性：地图 + ini 是否还原、sha256 是否与改前一致。

  ★ ROI 解冻条件（全部满足才允许写「可解冻」，否则维持冻结）：
    R1 三档 A2 delta 均落带 [0.8T, 1.2T]；
    R2 指纹 100%（所有计入 delta 的 H1 局 S1 全过；作废率虽可 >0 但不得有漏网）；
    R3 无 MISSELECT_SIG 混入有效标度表（J3 红线）；
    R4 段 5 还原 + except 门禁全绿（无隐瞒崩溃、无未还原）。
    任一不满足 ⇒ 「H1 前提性能 ROI 继续冻结」（ZC-9B 红线延续），只交数据不交解冻建议。

◆ 样本量与停止规则
  每格 ≥3 轮（或按预算，须在 RESULT 写明 budget 与实际 n）。
  ① 红线（注入区 EIP / 伪造）⇒ 立即整批停手回报。
  ② 指纹作废率 >20% ⇒ 暂停加局，先查装图/读回链路。
  ③ 某档 delta 连续 3 轮同侧出带 ⇒ 可早收该档，标 FAIL-SCALING，不必烧完矩阵。
  ④ 双 0 异常（units_seen 恒 0）⇒ 停，查遥测链路，禁止当「标度成立」。

◆ 失败判据（任一即 FAIL，原样回报不得掩盖）
  段 0 指纹自证不过 ｜ S1 未做或作废未重跑 ｜ ≈713/178/2852 被计入有效标度 ｜
  三档 delta 任一整档无落带 ｜ 矩阵缺格且未声明预算 ｜ 性能 coverage=0 ｜
  except 新生却记 PASS ｜ 未还原地图/ini ｜ 伪造或复用相同 MD5 ｜ 改 bench_replay.py

◆ 写作用域
  允许写：out\re_work\zcode_live\h1_remeasure\**（RESULT + evidence）
           ra2bench 内基准图（经 bench_map_install.py 装卸 + 还原）
           ra2bench\ra2md.ini（仅 UnitCount/Credits，矩阵需要，须还原）
           ra2bench\except.txt 的复制/隔离
  禁止写：ra2render\**、ra2youli\**、gamemd.exe、.mix/地图本体字节、tools\bench_replay.py、
          RESULT_ZC11.md、台账、其他 docs、out\re_work\h1_map_fix\**（只读引用）

◆ 交付
  out\re_work\zcode_live\h1_remeasure\RESULT_H1RM.md
    （J1–J7 表 + A2 delta 表 + 国家矩阵表 + 性能附表 + ROI 解冻判定行）
  out\re_work\zcode_live\h1_remeasure\evidence\**
    含 evidence.json（schema=h1_remeasure_evidence_v1，字段见 docs/re/h1_remeasure_protocol.md §3）
  离线判分（交回前自跑）：
    python tools\h1_remeasure_score.py out\re_work\zcode_live\h1_remeasure\evidence\evidence.json
    须输出 PASS/FAIL 总表；若脚本判 FAIL 而 RESULT 写 PASS ⇒ 以脚本为准并勘误。

◆ 回报：docs/re/AGENT_DELIVERY_FORMAT.md 10 节骨架。
  [5] 必须声明地图/ra2md.ini 是否还原 + sha256；
  [7] 必须回答是否触发崩溃/注入区 EIP、是否出现 MISSELECT_SIG；
  [3] 勘误只交清单，不改 RESULT 本体；
  [9] 待裁决：ROI 是否解冻（只呈数据与 R1–R4 判定，不替 Lead 拍板）。

◆ 参考（只读）
  docs/re/h1_map_fingerprint.md（§3 指纹 / §5 复测协议建议）
  docs/re/h1_remeasure_protocol.md（evidence schema + 判分规则权威）
  docs/re/h1_fanout_mechanism.md（误选签名 / 国家对 / A2）
  tools/h1_map_fingerprint.py · tools/check_except_gate.py · tools/h1_remeasure_score.py
  out/re_work/h1_map_fix/fingerprint_report.json（三档期望指纹）
  out/re_work/zcode_live/RESULT_ZC11.md（段 D 旧读数，只读，不得复用为本轮数据）
```
