# S13-KPROVED2 · UNKNOWNS

## U1 · 四环齐全数 = 0；46 行候选全部缺 ④（决定性）

行源 = S13 静态推断池 126 行，按下表排除后得 **46 行候选**（明细 `EVIDENCE/candidate_pool.tsv`）：
- 3 行 M26 白名单（0040F870/0054E890/0054EA70）+ 11 行 S13_K9：均为 `[已证]`，**本就不在 126 静态池内**（已核 `m26 in static? []` / `k9 in static? []`）。
- 18 行 S13_K8 的 `scalar_deleting_dtor`（D-39 待裁，本卡不碰）。
- 62 行容器族 slot1–6（§8.4 映射表已覆盖）：`?$/*T_*VectorClass*::vslot1..6 / slot1..6` 与 `::GetItem/GetItemIndex/FindItemIndex/SetCapacity/operator==/Clear`。

46 行候选的 ②/③b/④ 结论（逐行见 `EVIDENCE/candidate_pool.tsv`，`verdict=FAIL`）：
- **② 环：46/46 PASS**。全为 RTTI 可解虚表槽（`has2_rtti=1`；SURVEY_RING24 `EVIDENCE/classification.tsv`）。本卡不据 ② 升格。
- **④ 环：46/46 FAIL**（任一不成立即不升，D-40）。两条独立通道 + 等价形式穷举均为 0：
  - 通道 A（capstone 5.0.7 skipdata=True 全 `.text` 线性反汇编，1,392,592 指令）：命中候选的 E8 direct-call 目标 **0**；全镜像 distinct `E8` 目标 6,728（与基准逐字相同，证明扫描有效）。
  - 通道 B（纯字节扫 `E8 rel32`，81,715 个 `E8` 字节，经 1,392,592 指令边界集过滤）：命中候选 **0**；A==B。
  - 活 vtable 派发（"构造器装活表 + `vt[slot]==entry` + site 不共用" 全条款）：46 行 `has4_loose=0`、`has4_strict=0`（SURVEY_RING24 双通道，已独立复现 S21 与 M32）。候选 VA 均以 4B dword 出现在**一张**虚表槽（`work/dword_va_scan.json`：46/46 有 vslot hit），即"entry→其虚表"与 ② 同源（D-39），不构成独立第四环；且无静态 global 接收者的 exact 派发。
  - 等价形式：`E9` 尾跳仅命中 `0046AFD0`/`0046AFF0`，站点 `0x46B990`/`0x46B9A0` 实为 `sub dword[esp+4],4; jmp`（多重继承 this 调整 thunk，候选→候选别名），既非 E8 direct call 也非虚表槽派发，不满足 D-40 ④；`EB` 短跳命中 0（`work/ring4_equiv.json`）。
  - 调用链上下各一层（纪律 6）：direct 全镜像穷举已覆盖所有 `E8` 调用者；虚表侧全槽持有枚举见 dword 扫描；未发现任何等价使用见证。

结论：**四环齐全 = 0，coverage_delta.tsv = 0 数据行**（只写表头）。与 SURVEY_RING24「S13 A=0/126 严格档、④ dir/lv=0/0」及 S13-K12 审计（14 行活表实为 atexit 析构器基类表、非活 vptr）完全一致。本卡不凑数。

## U2 · ③b 基率（供参考，不改变 0 行结论）

seed 20261119 / 2000 次 / 抽 8，D-42 忠实检测器（操作化见 `EVIDENCE/baselines.json`）：
- S13 静态池 N=126：strict K=18 / p=0.142857 / E[8]=1.142857 / MC=1.105000；loose K=43 / p=0.341270 / E[8]=2.730159 / MC=2.692000。
- 候选池 N=46：strict K=8 / p=0.173913 / E[8]=1.391304 / MC=1.433000；loose K=15 / p=0.326087 / E[8]=2.608696 / MC=2.618500。
- `K=N·p`、`E[8]=8p` 为恒等式，不作校验（§8.7 判据 3 / M3）。③b 再高也不能替代 ④；本卡 0 行非因 ③b 不足，而是 ④ 结构性缺失。

## U3 · 两口径 proved 现场重算（未改 coverage.tsv）

- 240 口径：`89/240 = 37.0833%`（grade：已证 89 / 静态推断 126 / 未证 25）。
- 148 口径（D-37 剔除 92 行容器模板实例化，其 14 行已证一并从分子剔除）：`75/148 = 50.6757%`。
- 分母定义按 D-37 裁决前默认 (A)=240 交；148 为并列参考口径。

## U4 · 未做事项（边界）

- 未碰 D-39 的 18 行（裁决项）、未碰 YRpp 双吻合放宽（D-41 默认 (A)）、未改 subsystem（D-37 未裁）。
- 未用 Ghidra（本卡判据为字节级穷举 + RTTI 链，不需 -noanalysis 反编译；Ghidra 并发槽留他卡）。
- 未改 coverage.tsv / 台账 / STATUS_BOARD / _audit / 游戏文件；未 git commit。
