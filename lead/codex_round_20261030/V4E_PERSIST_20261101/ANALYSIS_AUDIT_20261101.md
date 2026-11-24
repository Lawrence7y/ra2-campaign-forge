# ANALYSIS_AUDIT_20261101 —— 现有分析实现口径核查（v4-e 准备轮；纯只读，不改件）

> **性质声明**：本判定书为纯离线只读核查：核对现有分析实现与已钉死口径的一致性，**只登记、
> 不改件**（发现不一致不改任何原件——任务书停止条件）。核查对象与全部引用行号以 2026-11-01
> 本轮实读为准（行号锚见 fingerprints.txt 同批哈希：`_h8_waittrace_decomp.py`=`d27f676e…`、
> `_xva_p01_stall.py`=`43bb5581…`）。写域=`lead/codex_round_20261030/V4E_PERSIST_20261101/`。

## §0 核查范围与判据基准

| 对象 | 判据基准 | 结论速览 |
|---|---|---|
| `_h8_waittrace_decomp.py`（等待轨迹分解） | V4D_RECOMPUTE_20261101.md §三-1/§四-2（停滞时长=卡住帧值首末拍跨度、不含段尾至下一推进拍间隔；战斗段=首推进拍→末拍；≥100ms；占比=合计/战斗段） | **一致（§1）** |
| `_xva_p01_stall.py`（occ_a 探针） | STALL_AUDIT_20261101.md §1（occ_a=全覆盖口径；窗分类 R0-R4；读失败窗处理） | **一致，两处文字级登记（§2）** |
| `_h8_waittrace_decomp_v4d.py` | ——（任务书指定对象） | **现场不存在**，登记替代锚（§1.4） |
| fingerprints.txt | 文献值（§501/§507/§508/V4D_RECOMPUTE M7） | 全部吻合（§3） |

---

## §1 `_h8_waittrace_decomp.py` 停滞口径逐处核对

**结论：实现与「卡住帧值首末拍跨度」口径一致，无出入。**

### §1.1 停滞段构造（核心行，L105-L111 原文）

```python
    # 停滞episode（delta==0 连续段，时长>=0.1s）
    stalls = []
    for s0, e0 in runs_of(bdl, lambda x: x == 0):
        end_t = bts[e0] if e0 < len(bts) else bts[-1]
        dur = end_t - bts[s0]
        if dur >= 0.1:
            stalls.append((bts[s0], end_t, dur, bfs[s0], bfs[e0 - 1]))
```

对齐关系（依据 L53-56、L76-90）：
- `deltas[i] = fs[i+1] − fs[i]`（L61-66），`bdl = deltas[first_adv − 1:]`（L89），故 `bdl[j]`
  对应拍对（first_adv−1+j, first_adv+j）的帧差；`bts = ts[first_adv:]`（L87）。
- `runs_of(bdl, Δ==0)` 返回 `[s0, e0)` 极大连续段 ⇒ bdl[s0..e0−1] 全 0 ⇔ 帧值在
  拍 first_adv+s0 … first_adv+e0 保持不变（**卡住帧值首见拍=bts[s0]，末见拍=bts[e0]**）。
- `dur = end_t − bts[s0] = t(末见拍) − t(首见拍)` ——**正是「卡住帧值首末拍跨度」；
  下一推进拍是 first_adv+e0+1（bdl[e0]≠0），其间隔 bts[e0+1]−bts[e0] 不计入**。
  与 V4D_RECOMPUTE §三-1「段时长=t(段内最后一个拍)−t(段内第一个拍)……不含段尾到下一推进拍
  之间的最后一个拍间隔」逐字对应。

### §1.2 其余口径件

- **段末越界防御**（L108）：`end_t = bts[e0] if e0 < len(bts) else bts[-1]` ——段延伸至末尾无
  闭合 delta 时取末拍。与 V4D_RECOMPUTE §四-2「‘段末点越界取末拍’为防御性条款」同式；
  v4-b/c/d 三趟均满足「末推进=末拍」，该条款实际未触发（V4D_RECOMPUTE W13b/X4）。
- **战斗段与占比**（L90、L112-L114）：`b_span = bts[-1] − bts[0]`（首推进拍→末拍），
  占比=`100.0 * stall_tot / b_span` ——与 V4D_RECOMPUTE §四-2「战斗段=首推进拍→末拍；
  占比=合计时长/战斗段时长」一致。
- **阈值**（L110）：`dur >= 0.1`（≥100ms 计入）——与口径一致；v4-c 存在贴线段
  （99.8/100.3ms 一簇，V4D_RECOMPUTE §三-2、§508 复算回收注③），段数对阈值定义敏感属
  数据性质非实现缺陷，**登记沿用**：v4-e 若段数贴线，判读须附阈值 ±2ms 灵敏度注。
- **读败处理**（L96-L101）：delta=None 段单列统计、不并入停滞；构造停滞段用 `x == 0` 精确匹配，
  None 不满足 ——与 V4D_RECOMPUTE §四-2「候选段=相邻**有效**拍 Δframe=0 的极大连续段；
  读败拍打断段」一致（本族三趟读败均 0，规则未实际触发）。
- **相位切分**（L77-L86）：首推进=首个 `fs[i] > fs[i−1]` 拍（i≥1）；装载段=等待起点→首推进
  （L143 脚注 2：非纯读图时长）——与 §507 口径一致。

### §1.3 数值交叉验证（实现级）

- 本件（原件）对 v4-b/v4-c 的输出 `waittrace_decomp_20261101.txt`：v4-b 237 段/92.6s/89.6%、
  v4-c 90 段/11.844s/20.5%（§507 收录）；v4-d 由 §508「最短内联参数化（原件 @d27f676e 零改动）」
  复算=28 段/3.701s/9.4%，与 V4D_RECOMPUTE W13 独立复算 28 段/3.6996s/9.366% 在 ±2% 容差内
  逐项吻合（偏差 ≤0.4%rel）——**两趟两上下文交叉成立（V4D_RECOMPUTE §四-6 实现交叉验证）**。

### §1.4 登记（副本缺失，不改件）

- **任务书指定对象 `_h8_waittrace_decomp_v4d.py` 现场不存在**。§508 方法件如实条已载：
  v4-d 复算因「长件誊写 4 次损坏（2 件删、1 件覆盖修正）、exec/cp 路线被门拦截 ⇒ 改最短
  内联参数化（原件 @d27f676e 零改动）」，版本化副本已被删；在场者为原件
  `_h8_waittrace_decomp.py` 与输出 tee `waittrace_decomp_v4d_20261101.txt`（两者哈希已入
  fingerprints.txt A/A2 节）。
- **对 v4-e 轮的含义务登记**：如需对 v4-e 重算等待段，按 runbook 步5 副本法（cp 原件→副本内改
  TRIPS 指向 v4-e+v4-d 对照）或 §508 内联参数化法执行，**必须重新落版本化副本+tee 同步落盘**
  （§505 黄 7-9 教训：分析脚本必须连 tee 落盘，否则不可逐位复现）；不得原地改原件。

## §2 `_xva_p01_stall.py` occ_a 实现与 STALL_AUDIT §1 一致性核对

**结论：行为与 §1 定义一致；两处文字级差异不构成行为差，登记备查。**

### §2.1 occ_a / occ_i 双口径（§1 定义对照）

- §1 定义：`occ_a = (head+interior+tail 冻结合计) ÷ (末样本 t − 首样本 t)`；
  `occ_i = interior 合计 ÷ (末帧沿 t − 首帧沿 t)`；T_STALL=0.1s；帧沿=f 值变化点（方向不论）。
- 实现：
  - L23 `T_STALL = 0.1` ✓；
  - L131-L134 帧沿=相邻样本 `fs[i] != fs[i−1]`（**方向不论**，f 回退也成沿）✓；
  - L156-L176 三类段收集：head（窗首样本→首个帧沿，L158-162）/ interior（相邻帧沿间，
    L163-167）/ tail（末帧沿→窗末样本，L168-172）；**零帧沿窗**（r w2/e4 w2 型）整窗记为
    head 段（L173-L176）✓；
  - L185-L187 `sum_all`=三类段合计；L194-L196 `occ_all_pct = 100.0*sum_all/span`，
    `span = ts[-1] − ts[0]`（L107）——分母=样本跨度 ✓；
  - L188-L190 `edges_span = trans[-1][1] − trans[0][1]`（末帧沿−首帧沿，仅 ≥2 沿时非零）、
    L191-L193 `occ_interior_pct` ——普查口径复算 ✓；零/单帧沿窗 occ_i=None（STALL_AUDIT §3
    表 r w2/e4 w2 行「—」与此吻合）。

### §2.2 窗分类 classify()（L62-L84）与 §1 R0-R4 对照

| §1 判据（互斥按序） | 实现 | 判 |
|---|---|---|
| R0 读失败主导：error 含「ReadProcessMemory 失败」或 有效样本/名义拍数<80% | L63 `if read_fail or (coverage<0.80)`；read_fail=L105 `"ReadProcessMemory" in err_text`；coverage=n/nominal，nominal=round(span_s×hz)（L108-L113） | ✓（文字级差异见 §2.3 登记 a） |
| R1 无推进：覆盖段内上行帧沿=0 | L65 `n_adv_up == 0`（L137-L145 逐对统计 df>0） | ✓ |
| R2 加载期：覆盖段内 max(f)<10 | L67 `f_max_cov < 10`（L197 max(fs)） | ✓（无读失败时全窗=覆盖段，等价） |
| R3 终局期：units_final ≤ max(100, 0.15×units0) | L69 `uN <= max(100, 0.15*u0)`（uN 取 counters 末个非 None，L233-L238） | ✓ |
| R4 活动战斗期：其余；按 occ_a 细分 快<2%/混合 2-25%/滞态≥25% | L71-L80 | ✓ |
| 修饰标记：>10ms 缺口合计>50% 样本跨度 | L82-L83（gap10_sum_pct=L127-L129） | ✓ |

### §2.3 登记（文字级差异与适用面，不改件）

- **登记 a（R0 子串宽度）**：实现匹配子串为 `"ReadProcessMemory"`（不含「失败」二字），§1 文本
  为「error 含 `ReadProcessMemory 失败`」。error 字段原文即「ReadProcessMemory 失败 …」形态
  （STALL_AUDIT §8 e4 w2 行），两者行为等价；若未来出现 error 文本含该子串但语义非读失败的
  记录（未见过此类），分类会偏保守归 R0——方向为「更早剔除停滞统计」，属安全侧，登记备查。
- **登记 b（R0 窗的 occ_a 数值仍输出）**：p01 对读失败窗仍输出 occ_a 数值（如 e4 w2
  「100.00(覆盖 47.6%)」），STALL_AUDIT §3 以类别列（读失败主导）承重、§9 建议 4 明确
  「读失败窗不得进入停滞占比统计」。**v4-e 复用时以类别为准：R0 窗的 occ_a 数字不进任何
  停滞对照**，仅作覆盖率证据留档。
- **登记 c（TRIPS 适用面）**：p01 的 TRIPS 清单（L25-L31）为 §502 普查 10 趟 28 窗，
  **不含 v4b/v4c/v4d，亦无 v4e**。v4-e 采窗复算须建**版本化副本**扩 TRIPS（或另写探针），
  不得原地改件（§505 黄 7-9+runbook v2 变更④），tee 随件落盘。
- **登记 d（f 回退窗）**：p01 帧沿按值变化计（方向不论），interior 段在 f 回退两侧各自成段
  ——与 §9 建议 3 一致（e4 w1 occ_a 85.22% 的承载，STALL_AUDIT §3/§7.1）；等待轨迹轨
  （decomp）按段内 delta==0 处理，f 回退=delta<0 打断段并另列跳帧统计（L103-L104），
  两轨对回退的处理各自自洽。

## §3 fingerprints.txt（同目录，本轮产出）

- **方法**：`_fp_gen.py` v2（写域内，64KB 块 I/O+逐字节状态机计数，不整文件载入内存）；
  sha256 全文件流式计算。
- **覆盖**：A 两个分析脚本；A2 两个分解输出 tee；B XVERIFY_A p01 两输出（txt/json）；
  C v4-b/v4-c/v4d 三趟 `h8_wait_trace.json`（sha256+元数据 n+实测样本数+首末样本）；
  D v4-d 三窗 `measure_w0/w1/w2.json`（sha256+样本数）。
- **文献锚核对（全中）**：v4b 实测样本数 9989（§501/§507 poll_count）；v4c 24712（§507 复核注）；
  v4d 17030（V4D_RECOMPUTE W4 beats）；v4d 三窗 t/f 各 12501（M7）；首末样本与 §507/W3/W5
  自洽（v4b 末样本 [120.0128, 271]=120.013s/271 帧 ✓；v4d 末样本 [42.4995, 800] ✓）。
- **生成器缺陷透明登记**：v1 版块对齐 token 计数法对跨 64KB 块边界的 `], [` 丢前缀漏计
  （v4c 漏 2、v4d 漏 1，v4b 恰好未触界故正确）；v2 改逐字节状态机后与文献值全部吻合。
  v1 从未对外发布（仅本轮内部试算），fingerprints.txt 以 v2 输出为准。

## §4 输入版本清单

见同目录 `V4E_PERSIST_CARD_20261101.md` §0（1-13 号输入，路径+关键节名全列）；本判定书
额外实读：`waittrace_decomp_20261101.txt`、`waittrace_decomp_v4d_20261101.txt`、
`frozen_recheck_v4d_pre.txt`（哈希/行数见 fingerprints.txt）。

## §5 总结论

1. `_h8_waittrace_decomp.py` 的停滞时长实现**就是**「卡住帧值首末拍跨度」（L105-L111 对齐
   论证 + 两趟两上下文数值交叉），与 V4D_RECOMPUTE 钉死口径无出入；
2. `_xva_p01_stall.py` 的 occ_a 实现与 STALL_AUDIT §1 定义一致，R0-R4 分类逐条对上；
   两处文字级差异（R0 子串宽度、R0 窗 occ_a 数值仍输出）登记备查，不改件；
3. 任务书点名的 `_h8_waittrace_decomp_v4d.py` 不存在（§508 已载缘由），登记替代锚并对
   v4-e 轮提出副本+tee 义务；
4. fingerprints.txt 哈希/样本数/行数与文献锚全部吻合，可供抽验。
