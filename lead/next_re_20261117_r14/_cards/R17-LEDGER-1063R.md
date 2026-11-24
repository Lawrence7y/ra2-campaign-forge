# 卡 R17-LEDGER-1063R · 书记员修订 §1063（仅事项 4 的数字须换源，其余不动）

## 〇、为什么改
你上一版 `R17_LEDGER_1063\SECTION.md` 的事项 4 用了 `stats.tsv` 的数字（host 108 / fn_end 82 / assert 4 / 需重分类 33）。
**那份 `stats.tsv` 是早期中间态，已被 `R17_R28_R12_REPAIR\REPORT.md` 取代。**
Lead 已用**纯表内算术**独立核定（对 `host_fix.tsv` 的 354 行逐行比 `old_host` vs `new_host`、`old_fn_end` vs `new_fn_end`）：

- **host_changed = 129**（不是 108）
- **fn_end_changed = 125**（不是 82）
- position_assert 翻转 = **5**（不是 4）
- `NON_TARGET(base from stack)` 64 行中**需重分类 19 行**（不是 33）
- 按类：call 267（host 84 / fn_end 76 / assert 1）、mov 70（35 / 39 / 3）、other_cmp 1（1 / 1 / 0）、other_test_imm 7（5 / 5 / 1）、stack_ff5424 9（4 / 4 / 0）
  自洽校验：84+35+1+5+4 = **129**；76+39+1+5+4 = **125**。

**请你自己也核一遍**（读 `host_fix.tsv` 逐行比列即可，不要读 `stats.tsv`）；与上述不符就并列报出。

## 一、要做的修改（其余事项一字不动）
1. **替换事项 4 的四个总量数字**为 129 / 125 / 5 / 19，并替换按类明细。
2. **新增一句口径说明**（放在事项 4 内）：`stats.tsv` 记录的是**早期中间态**（108/82/4/33），
   **已被 `REPORT.md` 取代，不得引用**；`REPORT.md` 才是权威。
3. **删除或改写**事项 4 里「`stats.tsv` Q4 recount」这类**把 stats.tsv 当权威**的表述 ——
   Q4「形态命中数不变」的依据请改引 `REPORT.md` 的 Q4 重扫表（call@0x124=181、call@0x1AC=86、mov 55+15=70、
   other_cmp=1、other_test_imm=7、stack_ff5424=9，其余形态 0；合计 267+70+1+7+9=354），
   以及 `host_fix.tsv` 按 class 计数同样得 354 这一路独立核算。**结论（形态数不变）保持不变。**
4. 事项 4 末尾「上述全部数字均自盘上逐行重算，0 处与卡面不符」这句，改为如实说明：
   **卡面（派发卡）当时引的是 stats.tsv 的 108/82，本次修订按 host_fix.tsv 与 REPORT.md 更正为 129/125**；
   并写明这是**Lead 派发卡引用过期中间态**造成的，不是执行方错。

## 二、其余事项（不要改）
- 事项 1（R25 作废）：**保持原样**。你原先正确区分了 `call_target` 列（`0x43B740`/`0x43B680`）与 `host` 列，
  并写了「host 列 15 行中 4 行与真实定界不同」——这句是对的，**不要改成"host 列只有被调目标"**。
- 事项 3（C3/C2 缺陷）、事项 5（R27）、事项 6（交付）、事项 7（GLM）：保持原样。

## 三、铁律
1. 只写 `lead\next_re_20261117_r14\R17_LEDGER_1063R\` 下 `SECTION.md`、`numbers.tsv`、`SELFCHECK.md`。
2. **不要修改** `R17_LEDGER_1063` 下任何文件（保留原版以便对照）。
3. 不得改台账、看板、`coverage.tsv`、`R14_COMMON.md`。
4. 结尾仍必须写：「本草为 §1063 草稿，由 Lead 逐字追加；书记员未自行改动台账。」
5. 严格 **7 分钟**；先落 numbers.tsv 再写正文。