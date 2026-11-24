# conflicts.md - 来源间矛盾清单

规则：只并列记录、不自行裁定；数字与来源逐字一致。

## C01 · R28 缺陷量化的四个数字在台账 1063 与看板第11轮之间不一致
- 来源 A（台账 1063，落盘 `R17_LEDGER_1063/SECTION.md` 事项4；派发卡 `_cards/R17-LEDGER-1063.md` 事项4）：
  host_changed=108 / fn_end_changed=82 / position_assert 翻转=4 / NON_TARGET 需重分类=33；
  按类 call 267（69/47/1）、mov 70（30/28/3）、other_cmp 1（1/1/0）、other_test_imm 7（4/3/0）、stack_ff5424 9（4/3/0）。
- 来源 B（看板 `STATUS_BOARD.md` 第11轮段 L249-L250）：
  host_changed=129 / fn_end_changed=125 / position_assert 翻转=5 / NON_TARGET 需重分类=19；
  按类 call 267（84/76/1）、mov 70（35/39/3）、other_cmp 1（1/1/0）、other_test_imm 7（5/5/1）、stack_ff5424 9（4/4/0）。
- 来源 C（台账修订 `R17_LEDGER_1063R/SECTION.md` 事项4）：与来源 B 完全相同（129/125/5/19），并写 stats.tsv 的 108/82/4/33 是早期中间态、已被 REPORT.md 取代、不得引用。
- 状态：并列记录，不在本索引裁定哪一版为权威。索引 F15 采用来源 B/C，limitations 已指向本条；
  引用来源 A 的四个数字时须与来源 B/C 并列。两者共同点：形态命中数 267/70/1/7/9=354（不受 host 修正影响）。

