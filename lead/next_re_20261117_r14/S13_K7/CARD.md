# S13-K7 · 只做审计认证的 exact 绑定（S13 proved 主攻）

## 背景（引用审计 a-S13-K6 的裁决原文要点，勿重新普查）
`a-S13-K6` 判 **FAIL**：45 行里 34 行用的「slot-baseline」判据检出力 = 0
（全 `.text` 中 `call [reg+{0,4,8,C,10,14}]` 共 6,313 处 / 3,130 owner，每 slot 的 `[已证]` owner 有 79–202 个
⇒ 任意 45 个函数都会通过）。只有 **11 行是 exact 绑定**，另有 **3 条漏扫**，且 **slot6 契约未命名**。

## 本卡唯一的任务
把这 14 个 entry 做到底，然后停手。**不要扩大范围，不要重新普查全族。**

### A. 11 行 exact（每行必须凑齐四环才给 `[已证]`）
`0040B880` `0040B930` `0040F7C0` `0040FD90` `0040FE40` `0046B7E0` `0046B890`
`0062B250` `0062B300` `0065C0D0` `0065C180`

四环定义（缺一即降到 `[静态推断]`，并在 PROGRESS 写明缺哪环）：
1. **入口**：该地址是被引用虚表的槽值，`vptr-site = vt + 4*slot` 且 `[vptr-site] = entry`（逐字节）。
2. **槽归属**：RTTI 自走链 `[vt-4] = COL` → `[COL+0xC] = TD` → 名在 `TD+8` **内联串**（不是指针）。读不到就 fail-closed 停下，不许猜。
3. **exact 绑定**：全 `.text` 找到**形如** `mov ecx, <global>; mov edx, [<global>]; call [edx+slot]` 的调用点，
   且**该 global 处 vptr 的写入有实证站点**（给出 `mov dword[<global>], <vt>` 的站点地址）。禁止 slot-baseline。
4. **语义**：函数体与 `ArrayClasses.h` 的 slot 合同逐一吻合（给出体内指令序列）。

### B. 补扫 3 条漏扫（审计已指出候选池应闭合于 56 = 8 个 `DynamicVectorClass` 虚表 × 7 槽）
`0048AD60`(slot6) `0054E8E0`(slot6) `0048AD70`(slot1)
⇒ 先把**56 个槽位**列全（8 表 × 7 槽），标出其中属 S13 的与属 S22 的，证明不再漏扫。

### C. 命名 slot6
`slot6` 契约 = **`GetItem(int)`**：`mov eax,[ecx+4]; mov ecx,[esp+4]; mov eax,[eax+ecx*4]; ret 4`
⇒ 对满足该字节合同的 entry 命名 `GetItem`（带类前缀或模板前缀，按盘上既有命名风格）。
**其余槽按合同定名**（不得编名）：`ArrayClasses.h` 的 slot0–6 合同。

## 强制自证（审计会照这三条打回）
- **检出力基线**：先算「在全部 `.text` 里随便挑 11 个函数、用我这张卡的判据会不会也过」。若是，判据作废，重做。
- **⑭ 环④ 必须真被调用**：数一遍 direct call 目标，引用的地址必须在体内真出现。
- **⑮ 环① 不得编造**：引用的全局必须在体内真被引用。
- **⑯ 类归属看 vt 共享与覆盖**：同址同槽多类共享 + 子类覆盖版直调 ⇒ 归**基类**那级。
- **⑰ 两条通道须各自提供对方给不出的信息**，同源不算两条。

## 交付（绝对路径，只写这里）
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K7\` 下：
`PROGRESS.md`(≤60 行，四环逐行打勾表) / `UNKNOWNS.md` / `DISAGREE.md` / `EVIDENCE\`(不截断) / `work\`(可复跑脚本)
`coverage_delta.tsv`：8 列（entry, subsystem, name, one_line_semantics, grade, evidence_path, **name_kind**, 备注）
  `name_kind ∈ {symbolic, behavioral, placeholder}`（R14-R17 裁定 3）。
**每完成 2–3 行就增量落盘 PROGRESS.md**（先写骨架再补），不要憋到最后。

## 核心数字（给审计员复算）
① 56 个槽位中四环齐全的条数 ② exact 绑定的调用点数 ③ 补扫 3 条各自的 exact 命中情况 ④ 检出力基线值
