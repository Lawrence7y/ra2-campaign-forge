# LEAD_FACT · 地图启动失败弹窗的 CSF 标签真值（含用字勘误）

> 取证：Lead（本会话）｜ 日期：2026-11-13 17:38
> 方法：用 W30 的 `csf.py` + `mixlib.py` 从 `ra2bench\langmd.mix` 提取官方 `ra2md.csf` 并全量检索。**独立于 W31 卡**（W31 同时在跑同类分析）。

## 1. 提取与检索（本次实测）

```
MixFile("ra2bench\langmd.mix").get("ra2md.csf") -> 332,973 bytes
read_csf(..., strict=False) -> labels=5211, warnings=0

检索「無法啟動選取地圖」「無法啟動」「選取地圖」：
HIT name='MSG:UnableMapSelect'  text='無法啟始選取地圖！\n'   nvalues=1
HIT name='MISSION:LosePowr'     text='剩下的發電廠電力不足，無法啟動時間機器'
total labels=5211
```

## 2. 真值

- **标签名 = `MSG:UnableMapSelect`**
- **文本 = `無法啟始選取地圖！\n`**（注意是 **啟始**，不是「啟動」；末尾带 `\n`）
- 全表 5,211 条标签中**唯一**匹配地图选取失败语义的条目（另一条 `MISSION:LosePowr` 是电力不足，无关）

## 3. 用字勘误（必须改口）

`[本次实测]` 屏幕上实际渲染的是 **「無法啟始選取地圖！」**（引擎逐字显示 CSF 文本）。
- W27 报告 `CAMPAIGN_LIVE.md:97` 写作「無法啟**動**選取地圖!」——**用字有误**；
- 我自己在 `REVIEW/LEAD_W27_RAW_VERDICT.md` 初版照抄了「啟動」，且声称"亲眼看图"——**我当时把字形读错了**（始/動 形近）。特此更正：图上的字是「啟始」。

`[本次实测]` 这个差别不只是错别字：**若按「啟動」去 exe 里搜字符串必然落空**，正确路径是
「中文文本 → CSF 标签名 `MSG:UnableMapSelect` → 用 ASCII 标签名在 `.text` 做 xref」。

## 4. 对下游的用处

1. **W31 卡的判据**：W31 已把错误消息引到 `MSG:UnableMapSelect`，与我这条独立结论一致 ⇒ 它的路线是对的，报告可按此交叉核对。
2. **W33 卡的对照**：`NextScenario` 推进失败最终若走到同一标签，则两卡的判定链应能闭合。
3. **禁止外溢**：不得写「引擎报『無法啟動選取地圖』」，正确写法是标签 `MSG:UnableMapSelect`（文本「無法啟始選取地圖！」）。

## 5. 复现

```powershell
# 依赖 W30 交付的 csf.py / mixlib.py（其 ts_crc_hash 才能从 langmd.mix 取到 ra2md.csf）
python -c "import sys;sys.path.insert(0,r'...\W30_csf_capability\ra2forge_patched_v10');from ra2forge import csf,mixlib;..."
```
`[本次实测]` 注意：用项目 **原始** `ra2forge/mixlib.py` 的 `crc_hash()` **取不到** `ra2md.csf`（需 TS 4 字节尾部填充哈希，见 W30 `DISAGREE.md` §1）。

---

## 6. 全库「錯誤字樣」登记表（回应 W43 审计 MAJOR-4）

`[本次实测]` 19:45 全库检索 `無法啟動選取地圖`（正确应为 **啟始**），命中如下。
**判定口径**：下列文件**绝大多数是在引用错误字样并顺带说明勘误**，属正当留痕，**不算未更正的错误**；只有「当作事实陈述且未标注」才算。

| 文件 | 处数 | 性质 |
|---|---:|---|
| `W27_campaign_live\CAMPAIGN_LIVE.md` | 5 | 原卡把转录误读当事实写下（**未标注**）⇒ 引用时须对照本文件 |
| `W27_campaign_live\DISAGREE.md` / `UNCOVERED.md` | 1 / 2 | 部分为勘误讨论 |
| `W31_map_start_failure\DISAGREE.md` | 3 | **明写「任务书字面不符」并给正确文本** ⇒ 正当留痕 |
| `W31_map_start_failure\WHY_MAP_FAILS.md` | 1 | 同上，标注了差异 |
| `W31_map_start_failure\EVIDENCE\s01_*.{py,stdout.txt}` | 1 / 1 | 证据原样（检索用的错误串）⇒ 正当 |
| `W32_campaign_menu_entries\UNKNOWNS.md` | 1 | 引用性质 |
| `W33_nextscenario_dataflow\NEXTSCENARIO_FLOW.md` | 2 | 部分为引用 |
| `W39_mapselmd_live2\DISAGREE.md` | 1 | **明写「7× 放大确认是啟始」** ⇒ 正当 |
| `W28_nextscenario_form\{NEXTSCENARIO_FORM,UNCOVERED}.md` | 2 / 1 | 引用性质 |
| `REVIEW\_w33_prompt.md` | 1 | 我派卡时写错（历史 prompt，不改） |
| `REVIEW\LEAD_CORRECTION_campaign_blockers.md` | 2 | 我早期文件，**未逐处标注** ⇒ 阅读时以本文件为准 |
| `RUNLOG.md` | 1 | 历史记录，保留原文 |

`[处置]` 卡片自己的文件属其写域，**我不改**；Lead 侧以本文件与 `LEAD_VERDICT_Q2_CLOSED.md` §11 为准。
`[引用纪律]` 凡引用上述文件的该字样，一律**改写成** `MSG:UnableMapSelect`（CSF 标签）或 `無法啟始選取地圖！`（文本），并注「来源卡片原文为错字」。
