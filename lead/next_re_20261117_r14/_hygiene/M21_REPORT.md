# M21_REPORT — S15_K7 PASS 3 行并表
1. 快照 `_hygiene/M21_before/` 4 文件已写 `SHA-256SUMS.tsv`；CONFLICTS 未改，仍含 468 数据行。
2. `006E6310`: `sub_006E6310 [未证]`→`TagTypeClass::FindOrAllocate [已证]`；新语义载标识符+宏合同来源、二进制侧『恰有一个地址实现该合同』、new 0xA4/GetSize 0x6E64A0 双点均 `[已证]`；nsrc=2、conflict=0。
3. `006F1920`: `sub_006F1920 [未证]`→`TeamTypeClass::FindOrAllocate [已证]`；new 0xF8/GetSize 0x6F20B0 双点闭合，但 GetSize 仅 `[静态推断]`；nsrc=2、conflict=0。
4. `00727AA0`: `sub_00727AA0 [未证]`→`TriggerTypeClass::FindOrAllocate [已证]`；new 0xB4/GetSize 0x727CB0 双点均 `[已证]`；nsrc=2、conflict=0。
5. 审计 D-E 已采纳：B 独立的是名字+宏合同，不含类↔数组绑定（YRpp 数组常量与 RTTI 安装点读同一常量）；不因措辞不对称降级。
6. coverage 18,431→18,431 行，entry 增删 0；sub_ 全表 6,894→6,891、S15∩atlas 17→14。
7. grade（只读第 5 列）before `[未证]` 11,030 / `[静态推断]` 6,028 / `[已证]` 1,373 → after `[未证]` 11,027 / `[静态推断]` 6,028 / `[已证]` 1,376（+3）；atlas 内 proved 1,368→1,371。
8. S15 盘上复算（atlas W130 ∩ coverage 大写 entry；仅 R14-R14 口径）：named 144/158=91.14% ≥ 门槛 ceil(0.9×158)=143；proved 101/158=63.92% ≥ 门槛 ceil(0.5×158)=79 ⇒ **两线均达标**。strict 102/158=64.56% 仅并列参考。
9. 审计 D-C 更正落实：卡面「proved unchanged」只对基线 98/158=62.03% 成立；三行 grade 提级使 after proved=101/158，与盘上复算一致。
10. 冲突/PENDING：三行跨 `[未证]`→`[已证]`，同 grade name/subsystem 冲突 0，CONFLICTS 468→468（+0）；PENDING 272→274（+2：3 行共享的通道措辞更正 1；Team GetSize `[静态推断]` 弱点 1）。
11. PANEL 保留 named_pct_S(R14/strict) 双列、S13 240/148 双分母、S22 不参与排名、三分母 12,916/14,487/18,431 不变。
12. 弱点：`006F1920` 的 `new` size 0xF8 可证，但 `0x6F20B0 TeamTypeClass::GetSize` 仅 `[静态推断]`；按审计 PASS 保留 `[已证]`，弱点已在语义、PENDING 与 PANEL 中如实标注。
13. after SHA-256: coverage 234dbea2abedf061d0ec28525833afc8b1dc94903e5f16464ccac5f8aa6348ed；PANEL a8138f85f4b848f8a54d37149691b684666e6eee366056a7a9d462365fb7b1ba；CONFLICTS a14499692822f7a44b843070fa93a53621fba6d72a075aadc97b2de232ea35b3；PENDING 4cb723ccdbc89a6ab9d60a56f7c9ace68f2dafc917baaf993793919d5e1dd3a0。
