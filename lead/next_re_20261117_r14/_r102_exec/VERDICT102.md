# R102 EXEC · C11 三处「永远通过」行为级取证（独立实现）

执行者：R102 子代理（角色 exec，家族 hy4）。脚本：`r102_exec_c11holes.py`；机器读数：`r102_exec_c11holes.json`。

复跑：

```bash
python3 /home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/_r102_exec/r102_exec_c11holes.py
```

最后一次复跑：`n_checks=30 n_fail=0`（脚本自身退出 0）。真树三个门禁文件的 sha256 在执行前后未变：`check_disc.py=0e37df51...878a1`、`DISC_RECHECK.tsv=b383af3f...434ceb`、`DISC_UNVERIFIABLE.tsv=0ffeeff5...2aab61`。所有变异发生在 `/tmp/r102exec_*` 沙箱；沙箱把项目根每个顶层条目（含 `_r102`）symlink 过去，只对 R14 目录的 3 个门禁文件用真实副本覆盖，R14 本身在沙箱中是真目录，产物路径按相对 ROOT 解析亦可命中（`_r102` 仅作 symlink 存在，门禁 TSV 不含 `_r102` 路径，故从未被解引用，保证独立性）。

## 正控先绿、反控才携带信息

- 原样沙箱 S0：`exit=0`，C11 per-id FAIL 为空，C7 31/31。这是正控。若正控不绿，后续任何 FAIL 都可能来自沙箱构造缺陷而非变异，反控就没有信息量。
- 每个变异都带一个「有判据 / 无判据」方向：
  - Q2 有判据：清空冻结档并重钉 sha → 12 个 per-id C11 FAIL；无判据：只改 sha 常量、TSV 不动 → 只有 TAMPERED，无 per-id FAIL。说明 12 个 FAIL 来自「摘帽」，不是来自改哈希。
  - Q3 有判据：破坏 id 3 的凭证行 → C11 id 3 FAIL；无判据：再写「无」→ 该 per-id FAIL 消失。C7 在两个方向都保持 31/31，证明变异只落在 C11。

## 汇总表

| 问 | 项目 | 结果 |
|---|---|---|
| Q1 | 真可 FAIL（claims-有、非冻结、当前凭证通过） | 5 个 id：3, 4, 22, 27, 28 |
| Q1 | 冻结豁免（claims-有、在冻结档、当前凭证失败） | 12 个 id：1, 2, 5, 6, 7, 8, 9, 10, 18, 20, 24, 25 |
| Q1 | 写无豁免（claims-无，C11 直接 continue） | 14 个 id：11, 12, 13, 14, 15, 16, 17, 19, 21, 23, 26, 31, 32, 33 |
| Q1 | 结构上不可能 FAIL（冻结 12 + 写无 14） | 26 / 31；其中仅由第 7 列硬短路决定的为 14 |
| Q2 | 清空冻结档 + 重钉 sha 后 exit | 1（FAIL） |
| Q2 | FAIL 的 C11 行集合 | 恰好 = 原冻结 12 个 id（1,2,5,6,7,8,9,10,18,20,24,25），无其他门禁项 FAIL |
| Q3 | 翻转前 exit（破坏 id 3 凭证后，仍写「有」） | 1，C11 FAIL id=3，C7 31/31 |
| Q3 | 翻转后 exit（id 3 第 7 列改「无」） | 仍为 1，但 C11 per-id FAIL 已清空；残留的是 C11b 缺口钉住漂移 |
| Q3 | 再重钉 C11B_PIN_GAP 后 exit | 0（PASS），C7 仍 31/31 |
| Q4 | C11_LANDABLE AST Load 次数 | 2（行 253、258；定义于行 246） |
| Q4 | LANDABLE ∩ 写无豁免 | 7 个 id：11, 12, 13, 14, 15, 17, 26（正好等于 C11B_PIN_GAP） |
| Q4 | LANDABLE ∩ 真可 FAIL / ∩ 冻结 | 5 个（3,4,22,27,28） / 0 个 |

Q2 清空后仅留表头那份文件的 sha256 = `001afa864f938c4894ca11f5d3405efb2cc216a80608e79f6292be22d3a0da92`。

## 四问详述

### Q1 分桶

31 行 = 17「有」+ 14「无」。17「有」再按冻结档与 verifier 结果拆成 12 冻结 + 5 真可 FAIL。`recheck_verify.verify_recheck_line()` 对 17 个「有」逐行实测：只有 3、4、22、27、28 返回 PASS，其余 12 个均因产物里没有本纪律的自描述行而 FAIL；这 12 个恰好全部在冻结档里，因此当前 exit 0。

「结构上不可能 FAIL」按当前状态为 26（12 冻结 + 14 写无）。若按「仅 C11 循环体内、不看冻结档豁免」的最硬结构短路口径，则为 14（写无直接 `continue`）。两种口径的数字都列出，避免混淆。

注意：Q1 的「真可 FAIL」5 个是**当前已能通过 verifier、故一旦破坏证据即可 FAIL**的行。另外 12 个非冻结 claims-有行当前 verifier 也失败，但它们已全数在冻结档内，不存在「非冻结 yet 当前失败」的 latent 桶。

### Q2 洞 A：冻结摘帽

清空 `DISC_UNVERIFIABLE.tsv`（只留表头）并把 `FREEZE_SHA256` 改为新文件 sha256，门禁立刻 `exit=1`，且 12 条 FAIL 全部是 `C11 id N claims recheck but has no valid self-description line`，id 集合与原冻结档 12 个 id 完全相等，C7/C8/C10/C12 无新增 FAIL。结论：冻结档是这 12 行的唯一豁免来源，注释里的 sha 防篡改并不阻止「改锚 + 同步改常量」的合法路径。

无判据对照：只把 FREEZE_SHA256 改成全 0 而 TSV 不动 → 只有一条 `C11 frozen-class registry TAMPERED`，无 per-id FAIL，exit 仍为 1。证明上一步的 12 条 per-id FAIL 与哈希编辑本身无关。

### Q3 洞 B：写无即免检

为让变异只打到 C11，按卡面提示把 id 3 的产物复制为沙箱内的 `_R102EXEC_PRODUCTS/anchor_check_id3.txt`，只删掉其中 `DISC_RECHECK discipline=3 ...` 一行，并把第 5 列路径指向副本；该文件仍保留 `池未加载(未核验) 0` 这个 grep 锚，因此 C7 全程 31/31 绿。

- 破坏后（第 7 列仍「有」）：exit=1，C11 per-id FAIL = [3]。
- 再把第 7 列改为以「无」开头：C11 per-id FAIL 清空，但 exit **仍为 1**，因为新增的 C11b 段检出 `C11b loadable gap drifted: [3, 11, 12, ...] != pinned [...]`。这是当前门禁相对卡面背景（只谈 C11）的一个实测差异：写无可消除 per-id FAIL，但会触发另一条钉住告警。
- 再显式重钉 `C11B_PIN_GAP = [3, 11, 12, 13, 14, 15, 17, 26]` 后 exit=0。因此「写无即免检」在纯 C11 意义上成立，但要把整份门禁从 FAIL 翻回 PASS，还需同步改 C11b 钉住常量。

### Q4 恒量 C11_LANDABLE

AST 实测 `C11_LANDABLE` 被 Load 2 次（行 253：`int(_r[0]) in C11_LANDABLE`；行 258：`len(C11_LANDABLE)` 的 note 打印）。控制哨兵名（脚本中不存在的标识符）Load 次数为 0，证明计数方法本身没有把所有 Name Load 都算进去。卡面背景说的「第 240 行左右有该常量」准确（行 246），但「Load=0」是 R102 补丁之前的状态；当前脚本已新增 C11b 段，把它接上了两处 Load。

LANDABLE 的 12 个 id = 5（真可 FAIL）+ 7（写无豁免）+ 0（冻结）。7 个写无 id 恰好等于 `C11B_PIN_GAP`。即 LANDABLE 列的是「理论上可补证据的行」，其中 7 行已经被声明为「不补」，在 C11 下永不可能 FAIL。

## 我不确定的部分

1. 卡面把 C11_LANDABLE 描述为 Load=0 的死常量；我实测当前真树为 Load=2（C11b 已接线）。这意味着主会话可能在会话期间改过 `check_disc.py`（mtime 04:22，晚于我首次读取的 04:21），我的结论以当前落盘版本为准；若调度方期望的是补丁前版本，Q3 的「翻转后 exit」会不同。
2. Q1 的「真可 FAIL」定义依赖 `recheck_verify` 当前实现（它还会查立条表、round 窗口、sha 锚）。若 verifier 规则后续变更，5 个 id 的集合可能漂移；我的脚本在每次复跑时重新调用 verifier，不缓存。
3. Q3 通过「复制产物 + 删一行 + 改路径」使 C7 保持绿；这与卡面提示的操作等价，但若门禁未来增加「产物路径必须在白名单目录」等规则，该沙箱构造可能被新的检查项拦截，需要重造夹具。
4. Q1 的「26 行结构上不可能 FAIL」是行为口径（冻结 12 当前 verifier 全失败 + 写无 14 直接短路）。冻结档理论上存在「verifier 意外通过 → R87-T2 分支反而 FAIL」的反向路径，但当前 12 行都走的是失败分支；若某天冻结行补上了合规凭证，它会从豁免变成 FAIL，那时 26 这个数字会下降。
5. 沙箱把 `_r102` 也 symlink 进去但从未读取；我通过「门控 TSV 不含 `_r102` 路径」和「未打开任何 `_r102` 文件」两项做了独立性自证，但无法从外部证明主会话答案完全未被间接影响。
