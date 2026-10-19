# W3-APP2 派工单 · 补追加 §13（m35 补丁块落进原版侧 ATLAS）—— M35P 参数驱动

> 派发：2026-10-02 20:2x（Lead）· 前置：**APPR 已验收（28/28，§475）** · **M35P 产物齐（anchor_current.json + dryrun_sim.json）**
> 执行：ZCode（专会话）· 预估 40–70 分钟 · **本卡是目前程序里唯一获准写 ATLAS 的卡（唯一写者）**

## 开工门禁（任一不满足 ⇒ 停手回报，不许写）

1. 现件指纹 = `out/re_work/qc/W3_20261001/scope/atlas_game/ARCHITECTURE_ATLAS_GAME.md` **1,212,472 B / sha256 前 12 位 `1dce588aa505` / mtime 18:17:38** —— 变了即停（说明有别的写者）。
2. **M35P 产物在档且自证通过**：`out/re_work/zcode_live/W3_20261002/m35p_prep/` 下 `anchor_current.json` + `dryrun_sim.json`（+ 其 verify 绿）。产物缺失/红 ⇒ 停手回报"等 M35P"。
3. 补丁源件在档：`out/re_work/zcode_live/W3_20261001/m35_ch13_expand/M35_ch13_atlas_patch.md`（17,571 B，APPR 已核存在）。

## 任务

1. **快照**：改前全文件 sha + 行数 + 备份副本（进你的写域）。
2. **落位**：按 M35P `anchor_current.json` 给出的锚点（**以它的实测为准，禁止用历史行号**——1.2MB 文件上 L1489 等旧行号已失效）把 §13 补丁块**章内插入**（APP1 形态：锚点行后插入，**不是文件尾追加**；E-APPR-1 教训）。插入前用 `anchor_current.json` 的唯一性断言确认锚点 count==1。
3. **Δ 对拍（本卡核心）**：实际插入后重跑官方工具 `atlas_unique_va`/`verify_anchors` 等，实测 Δ 必须与 `dryrun_sim.json` 的预测**逐项相等**（unique_va 增量、逐章归属守恒：§13 增、他章不减）。对不上 ⇒ 回滚快照并如实报告差异，**不许改预测凑数**。

## 验收形态（自写 verify_app2.py，Lead 将亲跑）

- **纯插入可还原**：difflib opcode ⊆ {equal, insert}；删掉插入行回写 ⇒ 逐字节 == 改前快照；
- **块逐字节相等**：插入块正文 == 补丁源件对应块；章号归属 = §13、块内无 H2 越界、m35 正文单份（occ==1）；
- **Δ 实测 == 预测**（dryrun_sim.json 逐项）；
- **门禁全绿**：`tools/verify_anchors.py` 323/323、YR 侧不受影响（本卡不碰 YR 侧文件）；
- **负控 ≥2（副本上做）**：① 把块挪到别章锚点 ⇒ 归属检查必须 FAIL ② 改坏块内一个字节 ⇒ 逐字节相等必须 FAIL；原件复跑对照绿；
- **只读纪律**：除 ATLAS 真件与你的写域外零写入；`m35_ch13_expand` 只读（sha 前后全等）；game.exe/coverage_ledger/dispatch 台账零写入；
- 空扫描 = INSTRUMENT_FAILED；改后门禁仍红 ⇒ 回滚 ATLAS 并报告（不许削弱门禁）。

## 交付

`out/re_work/zcode_live/W3_20261002/app2_atlas_append/`：`APP2_REPORT.md` + `verify_app2.py` + 快照/负控/Δ 对拍原文。完成后回报 `[0]`：改前/改后大小与 sha、Δ 实测 vs 预测表、verdict tally 原文。
