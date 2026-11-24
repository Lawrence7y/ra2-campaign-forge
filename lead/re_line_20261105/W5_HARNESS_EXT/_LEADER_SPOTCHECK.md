# W5 交付核查（RE 线驱动器自做，**不是** W5 工作流的一部分）

> W5（`dwfrun-72eac164`，`gemini-3.8-flash$high`）在飞，phase 1 已 settled 2/4。
> 本文件记录我**在等待期间对已落盘产物的独立核查**——不采信 W5 的自述。
> 零真机、零母本改动。

## 0. 已落盘产物与我的独立重跑

| 产物 | 大小 | 我是否独立重跑 | 结果 |
|---|---|---|---|
| `qc151_trip.harness8_v4_ext.py`（扩项副本） | 498,054 B / 9,078 行 | 只做静态分析（**不运行**） | 见 §2、§3 |
| `_w5_diff_proof.py` + `_out.txt` | 8,609 B / 1,260 B | **是，我亲自重跑** | `EXIT=0`，最终判定 PASS |
| `_w5_test.py` + `_out.txt` | 12,781 B / 2,238 B | **是，我亲自重跑** | `EXIT=0`，6 条用例全 PASS |
| `_w5_burden.py` + `_out.txt` | 12,021 B / 5,881 B | 读输出 + 独立核口径 | 见 §4 |
| `sections/Q1_EXT_BODY.md` | **尚未落盘** | — | Q1 仍在 executing |
| `sections/Q3_OFFLINE_TEST.md` | **尚未落盘** | — | 仍在 executing |
| `W5_HARNESS_EXT.md`（总报告） | **尚未落盘** | — | phase 3 才写 |

## 1. 改动面证明（我亲自重跑，`EXIT=0`）

```
母本 SHA256: 38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8
副本 SHA256: 03972aba5721a07e30d7ce010022dca3b8e584134c54c9579f2ca3eaa64e53e4

[检验 1] 识别到 W5EXT 插入块 8 个 → 删块后 SHA256 == 母本 SHA256 ⇒ PASS
[检验 2] 新增 221 行, 删除 0 行, 修改 0 行 ⇒ PASS
[检验 3] 六个禁止面 API 出现次数与母本逐项相同（差异全 +0）⇒ PASS
```

**这一项是本次交付里最硬的部分**：「删块即还原」用 **SHA256 逐字节相等**证明，
不是靠人声明。

## 2. ★ 我发现的缺陷 D-W5-1：`authorized` 分支不写 `S4/s4_gate` rec

**位置**：`qc151_trip.harness8_v4_ext.py:1256-1262`（W5EXT s4-gate-hook）

```python
if authorized:
    rec.add("W5EXT", "s4_hard_assertion", "FAILED_ALLOW_LOADER",
            "script:s4_injection_gate", note=...)
    S4_VERDICT["gate"] = "w5_refused_allow_loader"
    S4_VERDICT["exit_code"] = EXIT_INJECTION_SUSPECTED
    return False
```

**母本对照**（`:1231-1235` 等）：母本在每条 S4 结论上都写 `rec.add("S4", "s4_gate", ...)`
与 `rec.add("S4", "s4_exit_code", ...)`。

**我的判定**：
- **功能上仍阻断**：`S4_VERDICT["exit_code"] = 62`，`main()` 取到 62，进程会退出。
- **但审计轨迹不全**：下游若按 `group=='S4' and key=='s4_gate'` 判读，**看不到这条拒绝**，
  与母本「S4 结论必在 rec 里」的既有约定不一致。
- **严重度：中**（不改阻断行为，破坏可审计性）。
- **修法（1 行）**：在该分支补 `rec.add("S4","s4_gate","w5_refused_allow_loader","script:s4_injection_gate")`
  与 `rec.add("S4","s4_exit_code",EXIT_INJECTION_SUSPECTED,...)`。

★ **我不是 W5 的复核员**，这条只是我读代码时的发现，**尚未经 W5 phase 2 复核确认**。

## 3. 我核过的两个疑点，结论都是「W5 对、我原先怀疑错了」

### 疑点 A：枚举失败时 `_W5_STATE` 未填充，S4 硬断言会不会误放行？

**结论：不会。** 事实链：
- `_W5_STATE` 初始值含 `"ra2render_hits": None / "ra2loader_hits": None`（`:183-190`）；
- hook 用 `.get(...) or []` 取值（`:1263-1264`）⇒ `None` 变 `[]`；
- 枚举失败时 `res = False` ⇒ `if ... or not res:` 命中 ⇒ 走 `FAILED_INJECTION_SUSPECTED` **阻断**。

### 疑点 B：`_measure_poll_span_mother` 绑定顺序会不会绑到 hook 自己？

**结论：不会。** 母本 `_measure_poll_span` 定义在 `:4077`，
`_measure_poll_span_mother = _measure_poll_span` 在 `:4120` ⇒ **母本函数已存在**，
绑定的是原函数；`:4184` 再重新定义 `_measure_poll_span` 为分发器。顺序正确。

## 4. 负担口径核对（Q4 的「6 读」）

**Q4 的追加口径成立，但正文表述可以更严谨**：

| 项 | 值 |
|---|---|
| 沿事件那一拍的**总** RPM 次数 | **7**（1 次判沿 + `read_sample` 内 6 次） |
| 其中**属于追加**的 | **6**（`f_pre` + 四 VA + `f_post`） |
| 判沿那 1 次 | 属**既有** 500 Hz 轮询，**不计入追加** |

⇒ Q4 用「+6 读 / +24 B」算追加是对的；但正文应写明「判沿那 1 次不计入追加」，
否则读者会以为沿事件只花 6 次读。

**Q4 纠正了我 A2 的一处低估**：A2 只算 4 次（四 VA），漏了 D-19 第 5 条要求的
前后帧号读 ⇒ **实际追加是 6 次（1.5 倍）**，整体增幅从 **+10.475% → +15.713%**，
最坏窗从 **+25.08% → +37.63%**。**这是 A2 的口径缺陷，Q4 纠对了。**

## 5. 节拍影响（**未实测，只算账**）

500 Hz ⇒ 每拍预算 2.000 ms。最坏窗 31.4 沿/s ⇒ 每 31.8 ms 一次沿，该拍做 7 次 RPM。
若单次跨进程只读 RPM ≈ 10–20 µs（**未实测**），7 次 ≈ 70–140 µs，
占 2 ms 预算的 **3.5%–7%** ⇒ 节拍**大概率不崩但会被挤占**。
★ **单次 RPM 耗时未实测**，此段不得当作已量化结论。

## 6. flag-off 的一个不完美处（诚实账）

`s4_scan_names` 的包装是**无条件**执行：

```python
def s4_scan_names(names) -> dict:
    scan = _s4_scan_names_mother(names)
    _W5_STATE["ra2render_hits"] = list(scan.get("ra2render_hits") or [])
    ...
```

⇒ flag-off 时**仍会**多做一次 dict 读取与两个 list 构造。
**零语义差、但不是零计算差。** 与 TASK.md「为 0 时行为与母本逐字相同」的要求相比，
这是**极小的偏离**，应写进诚实账，**不构成阻断**。

对比：`_measure_poll_span` 与 `s4_injection_gate` 两个包装都有 `if not on: return mother(...)`
的早退，**这两处是干净的**。

## 7. 诚实账

1. **我亲自重跑**：`_w5_diff_proof.py`（`EXIT=0`，最终判定 PASS）、
   `_w5_test.py`（`EXIT=0`，6 条全 PASS），以及我自己的两支静态核查脚本。
2. **我未运行**扩项副本本体（铁律：不跑真机；副本会启动游戏）。
3. **我未验**：单次 RPM 耗时、扩项在真实 500 Hz 循环下的节拍稳定性、
   `K` 值（每沿 7 次读的实际墙钟）。
4. **我未验**：D-W5-1 是否被 W5 的 phase 2 复核员独立发现（W5 仍在跑）。
5. **本文件不是 W5 的交付件**，是驱动器的等待期核查；W5 的自述与我这份如有冲突，
   **以能重跑出结果的那一份为准**。
6. 本文件**零真机、零母本改动、未 commit**。
