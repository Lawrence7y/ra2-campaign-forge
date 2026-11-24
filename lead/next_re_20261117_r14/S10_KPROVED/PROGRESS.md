# S10-KPROVED PROGRESS

- 2026-11-18 13:45 +08:00 开工：已重读 `R14_COMMON.md`（§1/§6/§8/§8.4）与本卡 `CARD.md`；写域仅限本卡目录与 `_ghidra/S10-KPROVED`。
- 输入指纹：exe SHA-256 `73201CC021...F67476`（4,825,360 B，与卡面一致）；coverage `B903B798…83E48F`；atlas `4527079B…63DB69`；Python 3.12.10 / capstone 5.0.7 / pefile 2024.8.26。
- ⑨ 自算：`S10∩atlas` n=526、named(L)=513、proved=117、`[静态推断]`=396、`[未证]`=13，与卡面一致；named 严格 S 口径为 82，但本卡不动名字。
- ⑲ 自检：已知 `call [edx+0xA4]` / `call [ecx+eax*4+8]` 的 `op.index` 均为 `0`（不是 `None`），所以按 `op.type==MEM && base/reg 存在` 解析，不按 `index is None` 过滤。
- 全镜像 `.text` `0x401000..0x7E038D` 线性 sweep：155,215 条指令；指令边界真 `call rel32` 6,958 条 / 1,119 目标；间接 call 3,012 条。
- direct-call 分布：396 行中 0=365、1=28、2=1、3=2 ⇒ direct-call 候选 31 行；不采用「最近 E8」启发式。
- vt 粗扫：`.rdata` 中有 130 张「≥6/8 个 `.text` 指针且至少 1 处 imm ref」的类虚表，覆盖 201 个静态行；这只是 C2 候选池，不等于环④。下一步只认 exact `mov ecx,<global>` + `mov edx,[global]` + `call [edx+slot]` 且 global 有 vptr 写实证。
