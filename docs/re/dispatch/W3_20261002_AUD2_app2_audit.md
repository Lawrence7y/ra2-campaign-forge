# W3-AUD2 派工单 · APP2 独立审计（§13 落位的第三方复核）

> 派发：2026-10-02 21:2x（Lead）· 前置：**APP2 已验收（46/46，§483）** —— 项目铁律：大写写操作必有独立审计（APP1→APPR 同款）
> 执行：WorkBuddy（新会话）· 预估 40–70 分钟 · 你是审计者不是复读机

## 现件（开工门禁，变了即停手）

- `out/re_work/qc/W3_20261001/scope/atlas_game/ARCHITECTURE_ATLAS_GAME.md` = **1,228,146 B / sha256[:12]=c1059552116b / mtime 21:04:20**
- 改前快照（回滚源）：`out/re_work/zcode_live/W3_20261002/app2_atlas_append/atlas_before_snapshot.md` = 1,212,472 B / 1dce588aa505
- 补丁源件：`out/re_work/zcode_live/W3_20261001/m35_ch13_expand/M35_ch13_atlas_patch.md`（17,571 B）

## 审计问题（逐条独立取证，不许拿 APP2 的工具当唯一判据）

1. **纯插入 + 可逐字节还原**：你自写解析（difflib/行级）复核 opcode ⊆ {equal, insert}；**删掉 APP2 插入的行回写 ⇒ sha == 1dce588aa505 改前快照**（逐字节）。插入块的位置/行区间由你自己算，不抄 APP2 报告。
2. **插入块 == 补丁源件逐字节**：块内容与 `M35_ch13_atlas_patch.md` 对应块 byte-equal；插入点 = §13 样板句行之后（M35P 实测 L2711 系 —— 用消歧规则**现推**锚点行，不照抄行号）；模板句保留、append-only。
3. **两格分母同步**：补丁 L86/L92 的陈旧分母已按卡面改为写入时实测（7,106/7,110、D=7,110）—— 现读断言 + **同时确认改前陈旧值（2,579/2,582、D=2,582）在现件 0 命中**。
4. **Δ 独立复算**：+31 行、逐章守恒（§13 增、他章不减）—— 用**你自己的**行数/章界统计（不是 APP2 的 step 日志）；unique_va 用官方 `tools/atlas_va_crosscheck.py` 独立跑：改前快照 vs 现件（若官方工具只能对现件跑，则用 APP2 的 xc_before/xc_after 原始 JSON **复核其内部一致性** + 抽 5 个 VA 字节实读）。
5. **负控 ≥2（你自己的副本）**：① 把块挪进他章 ⇒ 你的章归属检查必红 ② 改块内一字节 ⇒ 逐字节相等必红；原件对照绿。
6. **红线自证**：game.exe `c4bf2a57a80f` 未变；两份 coverage_ledger、dispatch 台账、`m35_ch13_expand` 聚合 sha 前后全等（APP2 执行窗 20:58–21:15 之后你再测一次）；YR 侧 `docs/re/ARCHITECTURE_ATLAS.md`（f939d6e3e709 / 470,294 B）未被 APP2 碰。
7. **APP2 报告的诚实项复核**（§8 残差三条）：§13.6 快照三元组残差、就地注记未插、Mimosa 钩子 4 次拦截绕行 —— 逐条判定"披露是否充分、有无藏问题"。

## 铁律

- **写域仅** `out/re_work/workbuddy/W3_20261002/aud2_app2_audit/`。**ATLAS 现件与快照、补丁件、APP2 产物全部只读**；不碰任何 verify_*.py（你测出的红只报告不修 —— 已知：CS7 括号波在测绘中）。
- 开工/收尾各测一次现件指纹，全程不变才继续；空扫描 = INSTRUMENT_FAILED；证据现读现抄。

## 交付

`out/re_work/workbuddy/W3_20261002/aud2_app2_audit/`：`AUD2_REPORT.md` + `verify_aud2.py`（正控+负控必咬）+ 原始取证。完成后回报 `[0]`：七问逐条 + verdict tally 原文。
