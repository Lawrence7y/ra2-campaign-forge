# PROGRESS — S16S21 B1

- [x] 读卡 `_cards\NAMED-PUSH.md` 全 80 行
- [x] 建目录 `NAMED_PUSH_S16S21_B1\{EVIDENCE,work}`；复制 `np_core.py`
- [x] 材料自校验：SHA-256 复算 = 期望值；`.text=[00401000,007E038D)`；capstone 5.0.7 / pefile 2024.8.26
- [x] 写 `REPORT.md` 骨架（先骨架后干活）
- [x] 筛选 `work/filter_b1.py`：S16 named=True 4 行 + S21 named=True 3 行 = **7 行**，伪名（`fn_`/`sub_`）**0** 个 ⇒ 全取
- [x] pass1 机械预筛 7/7（①②③④ 原始事实落 `work/pass1.txt`）

## 逐行（7/7 已核完）

1. [x] `0046D000` S21 CampaignClass::slot5 — ② PASS / ③b② PASS（0x410380 判负，E_POINTER 0x80004003）/ ④ PASS（构造器 0046CB70，operator new@006C02C1）⇒ **[已证]**
2. [x] `0046D050` S21 CampaignClass::slot6 — ② PASS / ③ **FAIL**（`call 0x410320; test; jl; xor eax,eax; ret` 为纯转发+零默认，③a 形态）/ ④ PASS ⇒ 不产出
3. [x] `0046D090` S21 CampaignClass::slot8 — ② PASS / ③b② PASS（容器 FindIndex 的 −1 下标哨兵）/ ④ PASS（同一构造器锚点，㉓ 排除自身删除析构器写点 0046D096）⇒ **[已证]**
4. [x] `0053AE50` S16 PsyDom::Start — ② **FAIL**（全镜像 4B VA 引用 0 处，无虚表槽）/ ③ **FAIL**（`call 0x7c8e17` operator new 空判断 = malloc null check，③a）/ ④ FAIL（仅 1 direct caller）⇒ 不产出
5. [x] `006CEF80` S16 SuperWeaponTypeClass::slot27 — ② PASS / ③ **FAIL**（`cmp eax,6` 是类型标签判定，两路均可返 0x46，被调 `call [eax+0x2c]` 未钉死）/ ④ PASS ⇒ 不产出
6. [x] `0071A760` S16 TemporalClass::slot23 — ② PASS / ③ **FAIL**（本体 323 条内所有 `test/cmp eax` 均为空指针/计数/标签判定，无多值错误码约定）/ ④ PASS ⇒ 不产出
7. [x] `0071B1B0` S16 TemporalClass::slot8 — ② PASS / ③b② PASS（容器 FindIndex 的 −1 下标哨兵）/ ④ PASS（构造器 0071A467，operator new@006C073E，㉓ 排除 0071B1BD）⇒ **[已证]**

## 落盘
- [x] `EVIDENCE/ROW_0046D000.txt`、`ROW_0046D090.txt`、`ROW_0071B1B0.txt`
- [x] `delta.tsv`（3 行）、`base_rate.tsv`、`REPORT.md` 定稿
