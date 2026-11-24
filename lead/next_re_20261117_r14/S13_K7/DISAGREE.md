# S13-K7 DISAGREE

## D1 · 不沿用 a-S13-K6 的 slot-baseline
33 行 slot-baseline 已由审计证实检出力为 0，本卡完全不采用；只处理 11 行 exact 绑定与 3 条审计指定漏扫。

## D2 · 3 条漏扫不强行升格
若 `0048AD60` / `0054E8E0` / `0048AD70` 只有 RTTI + 合同字节、没有 exact global-vptr 调用站点，则保留 `[静态推断]`，缺环③；不以“槽位闭合”替代环④。

## D3 · slot6 命名范围
仅对字节合同 `8B 41 04 / 8B 4C 24 04 / 8B 04 88 / C2 04 00` 的 slot6 entry 命名 `GetItem`；S22 行只列闭合表，不纳入本卡 delta。

## D4 · owner grade 与 direct call
环④引用 exact 调用点的 owner 采用 a-S13-K6 已审计 [已证] caller，并在 EVIDENCE/exact_owner_proof.tsv 重新数 direct call 目标；不把“有虚表槽”当成“被调”。
