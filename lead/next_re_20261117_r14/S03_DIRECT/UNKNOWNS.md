# S03-DIRECT · UNKNOWNS.md

1. **31 行升 [已证] 后 name 仍为槽名 / 占位式**：卡面要求「只动 grade，不动名字/subsystem」，因此 `Class::slotN` / `Class::vslotN` / `?$VectorClass::…` 等原样保留。这些行只证明「入口有 direct call 字节证据」，不证明槽语义；按 §8.1 ⑬「入口已证 ≠ 语义已证」，本卡仅升 grade。
2. **VIRTUAL_SKIPPED 76 行只按名字/语义判虚表来源**：若某行既无 direct call site、名字也不含 `slotN`/`vslotN`/`rtti-vftable` 字样但实际经虚表可达，本卡无法从名字旁路判定，未列入（仍保持原 grade）。这是静态判据的覆盖盲区。
3. **1 行非虚表派生、未命中 direct、未列入 VIRTUAL_SKIPPED**：`0040E4A0`（`CCINIClass`，语义 `FileSystem/MIX member (kb-weak:30_ini)`），来源为 kb-weak 弱信号而非虚表，本卡不升格也不列入虚表跳过表，留待裁决。
4. **caller grade 只是加分项**：31 行中 39 个 caller 站点为 `[已证]`（13 个不同 caller），其余为 `[静态推断]`/`[未证]`；按卡面「无则不勉强」，不影响升格。
5. **全 .text 覆盖口径**：扫描到 `.text` VirtualSize 末端 0x7E038D（100%），raw E8 81,715 与卡面一致；交付站点全在范围内，无范围外站点（避开错源 ㉖）。
