# PROGRESS · W102 异族审计卡（攻击方）

> 卡：W102（DeepSeek-V4.1-Flash，**异族 / 攻击方**）
> 工作目录：`lead\next_re_20261112_r09\W102_audit_adversarial\`
> 读文件 + 读原始数据；**未启动游戏、未注入、未改 `ra2youli\`、未改主台账**。

| 时间 | 做了什么 | 结论 / 下一步 |
|---|---|---|
| T+0 | 整份读完 `R09_COMMON.md`（136 行） | 路径/硬禁令/7 条崩溃签名/表达纪律已记录；本卡不涉及崩溃族，只涉及度量学 |
| T+1 | 定位台账 §626/§627/§630/§633/§634（`GOAL_THREE_TARGETS_20261018.md:10413–10619`） | §634 的六个数字与措辞已逐字抄下 |
| T+2 | 读 W98 `DESIGN_PREREG.md`(61 行) / `SPLIT.md`(91 行) / `SUMMARY.csv` / `SUMMARY.md` | 预注册算法与自报数字已记录（**不采信，作为待比对象**） |
| T+3 | 6 趟 `run.ndjson` 结构核对：每份 ~24.8–24.9k 条 `kind=sample`，单 `win_tid`，`read_status` 全 ok | 数据可用；`run.ndjson` 里**没有**对象计数/单位数/帧内事件字段（与 §630-5 一致） |
| T+4 | 自写 `work/w102_recompute.py` 独立复算（不调用 `batch_analyze.py`，只对齐口径） | **6 个 trip 的 rate 与 SUMMARY.csv 逐位一致**（见 RECOMPUTE.md §1） |
| T+5 | 加第二通道（raw kernel+user 端点差）校验 | 两通道 6/6 趟**逐位一致到 1e-12**，`win_cpu_ms_delta` 无丢失（RECOMPUTE.md §1.1） |
| T+6 | 端点组合全枚举（2×2×2 = 8 个） | 中心份额 68.869/31.131 复现；**但包络是 58.45–82.47 %，不是 SPLIT 写的 61.1–79.9 %**（RECOMPUTE.md §3） |
| T+7 | 逐 10 s / 30 s / 60 s 相位切片 | 发现 cell 内强烈时间结构，量级远超 cell 间差（ATTACK_634 §3、ATTACK_ABBA §2 共用） |
| T+8 | 用 `installed_inputs\w94_design_g_*.json` 重算几何 | `g_near` Σd=8033 格·辆、`g_far` Σd=39850 格·辆 ⇒ **g_near 的行军不是 0，是 g_far 的 20.2 %** |
| T+9 | 定位 `g_far` 4.9064 pp 极差 | 不是某一趟越界，是**整条曲线上系统性偏移 ~5 pp**（裁掉任何一段都还是 4.3–6.1 pp），见 ATTACK_634 §3 |
| T+10 | 读 `OBSERVER_ABBA_PROTOCOL.md`(80 行) + `RULING_GPT61SOL.md` §Q3(90–117 行) | 协议 vs 裁决的偏差清单成立（ATTACK_ABBA §0） |
| T+11 | 3 区组功效数值实验 | `d_true/σ=0` ⇒ P(3 点同号) = **0.251**；要压到 5 % 需 `d_true ≈ 2σ` |
| T+12 | 非单调趋势 ABBA 反例 | 同一组实测数据、真实 `d=0`，仅改段序 ⇒ `d ∈ [-46.34, +46.34] pp`；单驼峰反例给 `d=-20.00 pp` |
| T+13 | 实测 python 冷启动 / `sleep(0.5ms)` 精度 | 冷启动 median **72.3 ms**（max 80.4）；`sleep(0.0005)` 实为 **1.018 ms** ⇒ **1 kHz 轮询从来不是 1 kHz** |
| T+14 | 写 `RECOMPUTE.md` / `ATTACK_634.md` / `ATTACK_ABBA.md` / `UNKNOWNS.md` / `DISAGREE.md` | 交付完成 |

## 复现全部数字

```powershell
$py="C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe"
$w="D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W102_audit_adversarial"
$env:PYTHONIOENCODING="utf-8"
& $py "$w\work\w102_recompute.py"   | Tee-Object "$w\EVIDENCE\A_recompute.txt"
& $py "$w\work\w102_geom.py"        | Tee-Object "$w\EVIDENCE\B_geom.txt"
& $py "$w\work\w102_far_rng.py"     | Tee-Object "$w\EVIDENCE\C_far_rng.txt"
& $py "$w\work\w102_abba_math.py"   | Tee-Object "$w\EVIDENCE\D_abba_math.txt"
```
