# S03-K2R · DISAGREE.md

## D1 — 推翻上轮 #6「3 个内嵌基类无独立堆分配」
- 上轮：3 内嵌基类无独立堆分配 ⇒ GetSize 2/5。
- VERDICT + 本卡：RawFile ctor `0x65CA80` 在 `0x407BB1`/`0x6BC099` 各 `push 0x24; call 0x7C8E17; call 0x65CA80` ⇒ 对齐口径 **3/5**。本卡以三态收口，RawFile 为 **独立分配点**。证据：`EVIDENCE/E_S03K2R_alloc_tri_state.txt`。

## D2 — 推翻上轮 #7 的 7W/3R 等偏小计数
- 上轮 BufferIO `+0x29`=7W/3R、Raw `+0x14`=3W/7R 等。
- 本卡三形式重扫：15W/9R、4W/10R 等，7 项与审计逐项一致；上轮属于窗口截断 + 访问形式漏扫。证据：`EVIDENCE/E_S03K2R_fields_v4.txt`。

## D3 — 「没找到」不得写成「不存在」
- BufferIO/CDFile 独立分配点本卡状态是 **未找到**（全镜像三形式与 wrapper chain 均 0），不是「不存在」。证据：`work/recheck_alloc.py`、`work/recheck_alloc_chain.py`。

## D4 — 基线数字不随重做漂移
- hash 8/8、atlas 194 / named 125 / proved 18 / delta +4 与上轮一致；不因 FAIL 重算而改。证据：`EVIDENCE/E_T2_hash_mix.txt`、`work/t1_targets.py`、`coverage_delta.tsv`。
