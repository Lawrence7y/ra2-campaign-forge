# S11-DIRECT · UNKNOWNS.md

1. **8 行升 `[已证]` 后语义 name 仍为占位名 / 槽名**：卡面要求「只动 grade，不动名字/subsystem」，
   因此 `sub_XXXXXXXX` / `Class::slotN` 原样保留。这些行只证明「入口有 direct call 字节证据」，
   没有证明 slot 语义；按 §8.1 ⑬「入口已证 ≠ 语义已证」，本卡仅升 grade，不宣称语义已证。
2. **VIRTUAL_SKIPPED 只列「名字/语义显示虚表来源」的 323 行**：若某行既无 direct call site、
   名字也不含 `slotN`/`vslotN`/`rtti-vftable` 字样但实际经虚表可达，本卡无法从名字旁路判定，
   统一未列入（仍保持原 grade）。这是静态判据的覆盖盲区。
3. **caller `[已证]` 加分项**：8 行中有 `00415C60` 的两个 caller 均为 `[已证]`，
   `0040B270`/`0055A930` 各有一个 `[已证]` caller；其余 caller 为 `[静态推断]`/`[未证]`。
   按卡面「无则不勉强」，不影响升格。
4. **`[未证]` 冲突行归属**：3 行（005AE860/005AF1A0/007559B0）的 subsystem 归属待裁决；
   本卡只报不改，未升格。