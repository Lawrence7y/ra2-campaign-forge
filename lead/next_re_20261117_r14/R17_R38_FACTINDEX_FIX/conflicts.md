# conflicts.md - 来源间矛盾清单（升级版）

规则：只并列记录；已澄清的假冲突须同时纠正来源指认与状态。

## C01-clarified · 假冲突（已澄清）：R28 缺陷量化 108/82/4/33 vs 129/125/5/19
- 来源 A（**非台账**，已被取代的草稿目录 `R17_LEDGER_1063/SECTION.md` 事项4；该目录已有 `SUPERSEDED.md`）：
  host_changed=108 / fn_end_changed=82 / position_assert 翻转=4 / NON_TARGET 需重分类=33；
  按类 call 267（69/47/1）、mov 70（30/28/3）、other_cmp 1（1/1/0）、other_test_imm 7（4/3/0）、stack_ff5424 9（4/3/0）。
  这组数字是 `stats.tsv` 的过期中间态，不是台账正文。
- 来源 B（看板 `STATUS_BOARD.md` 第11轮段）：
  host_changed=129 / fn_end_changed=125 / position_assert 翻转=5 / NON_TARGET 需重分类=19；
  按类 call 267（84/76/1）、mov 70（35/39/3）、other_cmp 1（1/1/0）、other_test_imm 7（5/5/1）、stack_ff5424 9（4/4/0）。
- 来源 C（台账正本 §1063，落盘 `R17_LEDGER_1063R/SECTION.md` 事项4）：与来源 B 完全相同（129/125/5/19），并写 `stats.tsv` 的 108/82/4/33 是早期中间态、已被 `REPORT.md` 取代、不得引用。
- 状态：**假冲突（已澄清）**。台账 `§1063` 与看板一致，均为 129/125/5/19；差异全部来自把已取代的草稿目录 `R17_LEDGER_1063/` 误当台账。旧来源指认已同步更正，不再把该草稿目录写成“台账 1063”。
- 引用约束：引用 129/125/5/19 时应连带引“108/82/4/33 为过期中间态、不得引用”的警示句；只列数字仍会误读。
- 共同点：形态命中数 267/70/1/7/9=354（不受 host 修正影响）。
