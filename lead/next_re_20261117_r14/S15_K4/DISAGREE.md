# DISAGREE.md — S15-K4 异议与偏离记录

## D1 · 与 S15-K3 基线无数字分歧（停机核验通过）
现场重算得 `158/137/95/need 143/shortfall 6`，与 S15-K3 PROGRESS/PANEL 逐值一致；按纪律 9 不停机、不凑数。证据：`EVIDENCE/t0_baseline.txt`、`work/t0_recompute.py`。

## D2 · 上一轮 K4 的 RTTI 脚本有缺陷，已作废并由修正版覆盖
`EVIDENCE/rtti_init_chain.txt` / `work/rtti_chain.py` 把 `TD+8` 当指针又要求 TD 落在 `.rdata`，得“0 个有效类”，是假否定。R14_COMMON §8.1⑧ 的链是 `COL+0xC → TD`，`TD+8` 是**内联名串**（实际读到 `.?AVTEventClass@@`/`.?AVTriggerClass@@`，TD 在 `.data`）。修正版 `work/rtti_chain_fixed.py` 实测 2,919 个有效 vptr 写点 / 302 类，输出 `EVIDENCE/vtable_rtti_fixed.txt`。旧文件保留作过程记录，不作结论依据。

## D3 · ABI 深挖文档来自 ra2bench 镜像，仅作符号线索
`docs/re/trigger_tag_abi_deep_dive.md` 头部写的是 ra2bench 镜像（MD5 4f37486…），不是本卡目标 SHA。因此本卡只取其中 `GetHouse 0x726910` 的符号线索；所有字节、调用者、RTTI、字段写点均在本目标 gamemd.exe（SHA 73201CC0…F67476）上复算。未把该文档当权威二进制证据单独使用。

## D4 · coverage 对 0x7264C0 的标签与 YRpp 不符，未擅自改 coverage
coverage 把 `0x7264C0` 标为 `TriggerClass::TriggerClass`；但 `YRpp/TriggerClass.h:95-98` 给 `RegisterEvent ... { JMP_THIS(0x7264C0); }`，函数体首部 `8A 46 44 / 84 C0 / 8A 46 30 / ...` 也与深挖文档的“Enabled/Destroyed 双门”一致。本卡在 `0x726551/55C` 的 this 来源论证中使用“事件注册消费方”语义，不依赖 coverage 的错标签；不修改 coverage。

## D5 · 不重签 K3 的两条命名，避免双计
K3 的 `006E2A10`/ `006E2AA0` 在 live coverage 中仍是 `sub_`，但 K3 delta 已单独交付。本卡全项目裸/带零十六进制 grep 未找到第二条独立“命名”通道；按派卡“同一条再下结论须补第二条独立通道”保持 `sub_`，不写入本卡 delta，也不在跨卡统计中重复加一次。

## D6 · 两条新名的等级拆分（不虚报 [已证]）
- `00726910`：YRpp 显式 `GetHouse`，深挖文档给地址，字节/RTTI/栈参三支撑 ⇒ `[已证]`。
- `0071FA30`：YRpp 只给字段名 `House`，未给该 getter 显式方法地址；虽有写点+读点+RTTI+同 this 调用者双支撑，仍降 `[静态推断]`。named(S) 按“非 sub_ 即命名”仍 +1；proved 只 +1。

## D7 · 写域与卫生
只写 `lead/next_re_20261117_r14/S15_K4/`；未改 `COVERAGE/`、台账、`ra2youli/`，未 git commit。`EVIDENCE/source_grep_bare_hex.txt` 是 rg 输出，rg 对若干 dangling symlink 报 os error 2 但主体结果完整；本卡只把它用作“无第二类命名通道”的补充否定，不用它做任何穷举性唯一结论。
