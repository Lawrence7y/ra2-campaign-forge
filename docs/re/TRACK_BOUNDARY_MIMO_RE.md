# 轨道边界：MiMo 本侧 vs 逆向代理（2026-09-30）

> 目的：用户将另派 agent/子代理**推进逆向任务**；本文件是**写作用域与选题边界**，避免多写者互相覆盖。
> 双方都必须遵守：只读 `ra2youli/**`、`ra2bench/**` 游戏文件、`gamemd.exe`；顶层台账 `REVERSE_ENGINEERING_AND_PATCHES.md` **仅 Lead 合并**；`ra2render/**` 默认仅代码轨（ZCode），本边界两侧都**不擅自写**。

---

## 1. 轨道划分

| 轨道 | 执行方 | 选题范围（做什么） | 写作用域（唯一） | 禁区 |
|---|---|---|---|---|
| **M · 测量/产品/harness** | **MiMo（本会话）** | H1 地图与负载修复、进图指纹、bench harness、except 门禁/协议、勘误补丁块、收尾与记忆、ZC 卡片起草 | `tools/bench_*.py`、`tools/*fingerprint*`、`out/loadbench/H1*`（经工具生成）、`out/re_work/h1_map_fix/**`、`out/re_work/harness_closeout/**`、`out/re_work/errata_patches/**`、`docs/re/h1_*.md`、`docs/re/harness_*.md`、`docs/re/zc11_*.md`、`docs/re/errata_*.md`、`docs/re/TRACK_BOUNDARY_MIMO_RE.md` | `docs/re/ARCHITECTURE_ATLAS*.md`、纯 exe 反汇编专章、`out/reverse/fn_*`、`out/re_work/net_sync/**` |
| **R · 逆向取证** | **另一代理 / 其子代理** | gamemd.exe 静态/动态逆向：LightConvert `0x420140`、堆/SBH、触发器/AI、渲染/迷雾机制、新结构体偏移、源码锚点 | `out/reverse/**`（`fn_`/`feat_`/`who_` 前缀）、`out/re_work/re_sprint/**`、`out/re_work/*_disasm*`、`docs/re/<新主题>_deep_dive.md`、`docs/re/ARCHITECTURE_ATLAS*.md`（若其被 Lead 授权） | `tools/bench_*.py`、`out/loadbench/**`、`out/re_work/zcode_live/**`、`out/re_work/h1_map_fix/**`、harness/勘误块 |
| **A · 注入实现** | ZCode（代码轨，**两边都不写**） | `ra2render` Hook/桩/Gap NOP | `ra2render/**`、`ra2youli/ra2render.*` | 无授权不得代写 |
| **L · 台账** | Lead | `REVERSE_ENGINEERING_AND_PATCHES.md` 合并 | 顶层台账 | 其他轨道只交 §九草稿 |

---

## 2. 共享只读（双方可读、都不可写）

- `ra2youli/`、`ra2bench/` 内游戏文件与 `gamemd.exe`
- `out/re_work/zcode_live/RESULT_ZC11.md` 与 `zc11/evidence/**`（引用可，不改）
- `docs/re/except_zc11_forensics.md`、`h1_fanout_mechanism.md`、`fog_*.md`、`landing_pack_*.md`
- `out/reverse/symbols.json`、`m1_blit_targets.txt`
- 工具：`tools/audit_bytes.py`、`tools/verify_anchors.py`、`tools/verify_bss_claims.py`（修复须提工单，避免并行改）

---

## 3. 交叉接口（唯一允许的协作面）

| 接口 | 方向 | 规则 |
|---|---|---|
| 崩溃/堆 | R 产出机制 → M 写 harness 门禁 | R 不改 bench；M 不反汇编新函数专章 |
| H1 负载 | M 修图/指纹 → R 可解读引擎 fanout | R 不改 `out/loadbench` |
| 迷雾/LightConvert | R 定位站点 → 真机 dump 卡由 M/R 起草、ZCode 执行 | dump 证据落 `out/re_work/zcode_live/**` 或 `out/re_work/re_sprint/**`（约定后不换） |
| 勘误 | 两侧各出补丁块 → Lead/用户解冻后写 | **禁止**就地改冻结源文档 |
| 新文档 | 各用新文件名 | 禁止改对方已有主题文档 |

---

## 4. 冲突升级

1. 撞写同一文件：**后到者停手**，改投本边界写域或请用户裁决。
2. 证据等级：一律 `[实证]/[推演]/[待实测]`，禁止伪造实测。
3. 发现对方领域问题：写进**自己**报告的「跨轨提示」节，不代改对方文件。

---

## 5. 本侧（MiMo）当前认领（2026-09-30 波次）

1. H1 地图 cell 互斥修复 + 进图指纹（P0）
2. RESULT[7] 勘误补丁块 + harness 对局后 `except.txt` 门禁（P0/P1）
3. except A/B 真机协议卡（交 ZCode 执行）+ 与 R 轨接口说明

**明确让给 R 轨**：`0x420140` LightConvert dump 分析、SBH/堆深入、触发器运行时、新 ABI 偏移、`ARCHITECTURE_ATLAS` 补丁。
