# S08-N2 UNKNOWNS

## 未采纳 / 未定
- 0047EFE0：YRpp（本地+上游）0 命中；symbol_map 全 docs/re；CONFLICTS.tsv:392 OPEN（S08-K1:MapClass::DrawShroudFogLayer vs coverage:sub_0047EFE0）。
  跨项目源 VERA20K 有 `shroud_blit 0x0047EFE0`（shroud.meta.json），但属测试夹具语义标签、且该 entry 已有 OPEN 命名争议，本卡不采纳以免扩大冲突；留待 lead 裁决。
- 0047F250：YRpp 0 命中；symbol_map 仅 docs/re（Draw_Fog 已被 COMMON-R10 作废为 docs-only 单通道）；
  VERA20K 只有 "Fog frame blend (47F250)" 描述性注释非洁净符号；本卡不采纳。
- YRpp 通道①对本卡 3 个地址均无地址绑定行（本地 2433 文件 + 上游 CnCNet/yrpp master 2188 文件，含 raw byte / 6-8 位 / 大小写变体）。
- grep.app 公共代码搜索被限流（HTTP 429），未能作为独立通道；改用 Sourcegraph 公共 API 命中跨项目源。

## 已试通道清单（若需 0 条时的记录，本卡已拿到 1 条）
1. YRpp 本地全库地址 grep（含 6/8 位、大小写、0x、h 后缀、RVA、raw byte）
2. YRpp 上游 CnCNet/yrpp master 全库地址 grep
3. re_atlas/evidence/symbol_map.json names+srcs
4. 跨项目公开源：grep.app（限流）、Sourcegraph（命中 VERA20K）
5. 本体二进制 capstone/pefile 反汇编 + 串/全局/caller xref
6. ⑱ 按 entry 地址查全库冲突（docs/re + re_atlas/kb + 台账 + COVERAGE）

