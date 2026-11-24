# DISAGREE.md — S15-K3 与卡面/前序的异议与偏离记录

## D1 · 卡面"差 6"复现无误，但本卡只补出 2，剩余差 4（诚实报，不凑数）
- T1 盘上自算：分母 158、named(S)=137、proved=95、need=143、shortfall=6，与 PANEL S15 行
  `158|137|86.71|95|60.13` 及 S15-K2 PROGRESS/VERDICT 逐值吻合 ⇒ **无数字分歧**。
- 派卡提示"5 条很可能需要先查"已全部查（见 UNKNOWNS U2），但严格取证后**均不可定**：
  它们是 action handler 内的坐标/相机/显示子步或配对 init/cleanup，不是 ACTION_FUNC 本体，无权威名。
  另查 YRpp 精确地址仅命中 2 条（本卡已交）。⇒ 如实交差 4，不编名补足（不违反 §966 教训）。

## D2 · 2 条命名走 YRpp 精确地址通道，非 S15-K2 的"派发ID→enum"通道
- S15-K2 的 25 条动作名靠"跳表薄壳唯一 call → 派发 ID → enum 名"；这 2 条（`006E2A10/006E2AA0`）
  无任何 handler 内直接 call（xref=0），那条通道覆盖不到 —— 这是 S15-K2 的方法盲区，不是它错。
- 本卡用 `YRpp\TActionClass.h` 的 `ACTION_FUNC(name, addr)` 精确地址宏（等价于 JMP_THIS 函数地址），
  再用字节反汇编独立确认语义（遍历触发器表→Destroy/FireActions）。同文件邻项 `0x6E2AF0=EnableTrigger`
  与 coverage 已入账名吻合，证明该地址表版本正确。双通道不同源（外部符号表 + 本卡字节），符合升级硬规矩①。

## D3 · grade 从 [未证] 升 [已证] 的依据（非复用结论）
- 两条原为 `[未证]`；升级依据是本卡**字节级证据**（读写指令 `mov eax,[edi+0x50]` / `[0xA8EAEC]` 基址 +
  `[ecx+0x24]` 读 + 两条 `call` 到已证 TriggerClass 方法 + `ret 0x10` 指令边界），可独立复算，
  满足 STATUS_BOARD "升级类动作硬规矩①"。不是"复用 S15-K2 结论"、不是"只有探针脚本"、不是"恒 0 读数"。

## D4 · 事件 L1 提示在本盘面不适用（非"
-b"型否定，是口径澄清）
- 派卡称"L1 的 12 个元素就是 12 个事件处理函数，若有无名的直接可定"。实测 12 个 handler 全不在
  atlas/coverage（`EVIDENCE/vtable_scan.txt`），是 `HasOccured(0x71E940)` 体内跳表标签，非独立入口，
  对 named(S) 分母 158 无贡献。已列入 UNKNOWNS U3，非"否定功能存在"，只是"不计 named"。

## D5 · 写域/卫生
- 未改 `COVERAGE/`，未写台账，未改 `ra2youli\` 任何文件，未 git commit。全部派生品在 `S15-K3\`。
- 附带：T3 抽查时我第一版脚本把 ID81 的 handler 索引算错（用了 ID80 的 `0x6DEBD0`），
  自查后纠正为 ID81=`0x6DDB67`（`ACT[80]=0x6DDB67`，唯一 call `0x6E01C0`）。错误只在我自己的
  一次性核查脚本，未进任何交付台账/证据结论，最终 T3 5/5 成立。记录于此以示透明。
