# S03-C6 · DISAGREE

## D1 · 与 SURVEY_RING24 / 盘上 `name` 栏的分歧：M1/错源⑯ 归基类改写

- 盘上 `coverage.tsv` 与 `SURVEY_RING24\EVIDENCE\classification.tsv` 给以下 4 行的 `name` 栏按 CDFileClass 命名；本卡 delta 按 M1/错源⑯「同一地址被 ≥2 张表以同一 slot 持有 ⇒ 归基类级」改为基类级命名：
  - `00432050` 盘上 `CDFileClass::vslot12` → delta `BufferIOFileClass::vslot12`（2 表同 slot 12：CDFileClass `0x7E1668` + BufferIOFileClass `0x7E3A2C`）。
  - `004322A0` 盘上 `CDFileClass::vslot9` → delta `BufferIOFileClass::vslot9`（2 表同 slot 9，同上两 vt）。
  - `0065D190` 盘上 `CDFileClass::slot4` → delta `RawFileClass::slot4`（4 表同 slot 4：CD/CC/BufferIO/Raw）。
  - `0065D240` 盘上 `CDFileClass::slot15` → `RawFileClass::slot15`（3 表同 slot 15；本行不进 delta，记于 UNKNOWNS U1）。
- 依据：YRpp 继承链 `FileClass → RawFileClass → BufferIOFileClass → {CDFileClass, CCFileClass}`（`YRpp/CCFileClass.h:125,166`，`YRpp/Documentation/class_c_d_file_class.html:91`）；R14_COMMON §8.1 错源⑯；本卡 `EVIDENCE/rtti_all_tables.json` 全表枚举（P3 表长约束后）。
- 本卡 M2 落实：delta 的 `name` 栏类名与 ② 归属类名一致（BufferIOFileClass / RawFileClass / CDFileClass / CCFileClass 逐行对齐，见 `EVIDENCE/final8.json`）。② 栏内联名串逐字符读自 TD+8（`EVIDENCE/rtti_all_tables.json` 的 `td`/`name` 字段）。
- 影响：仅本卡 7 行 delta 的 `name` 栏；不写台账、不改 coverage.tsv、不改名其它 entry。C4/C5 已并的 12 行不在本卡范围。

## D2 · ③b① 档位判定：00431F70 / 0065D190 依赖 D-42 细则#1（多路守卫链）

- `00431F70`（③b①）与 `0065D190`（③b①+③b②）不含跳表；其 ③b① 依据 D-42 操作化细则#1「≥3 道互斥闸且各闸动作不同」：
  - 00431F70：三态标志闸（+0x06/+0x10/+0x15）+ mode 三路分派（+0x53/+0x6A/+0x86），各路动作不同（复位缓冲 / 清标志 / 读窗夹紧 / 重开+回跳 / seek），逐条见 `EVIDENCE/THREE_B_DETERMINATION.md#00431F70`。
  - 0065D190：文件名空闸（报错误码 2）/ is-open 闸（静默 0）/ DeleteFileA 结果闸（返回 1 或虚报错 0），动作互斥，见同文件 `#0065D190`。
- **敏感性**：若采用「①只认跳表/循环/错误码」的更严格口径，00431F70 与 0065D190 的 ③b① 落空。两行兜底不同：00431F70 无独立 GetLastError/-1 错误码约定（仅 mode 三值返回约定），严格口径下 → ③a（四环 7→6）；0065D190 有 DeleteFileA 结果 + 错误码 2 可证伪约定，③b② 仍成立（四环不变）。现行 D-42 细则#1（Lead 采纳）下两行均计 ③b①。
- 00432050 / 004322A0 / 0047AE10 的 ③b④ 为完整 I/O 循环，含显式写与回边，不依赖细则#1，严格口径下仍成立。0065CDD0 / 0065D0D0 的 ③b② 为 −1/GetLastError 可证伪约定，亦不依赖细则#1。

## D3 · ③a 不成立行

- `0065D240` 判 ③a（三闸汇同 `xor al,al; ret 4`），与 C5 的 00431F10/00473AE0/0047AF10 同型 ③a 先例一致；理由见 `UNKNOWNS.md#U1` 与 `EVIDENCE/THREE_B_DETERMINATION.md#0065D240`。无异议。

## D4 · 无 direct-call 单独升格

- 本卡 8 行 ④ 全为 direct-call，但均同时给出 ②（RTTI 全表）与 ③b 现场；遵守 D-40「direct call 不得单独升 `[已证]`」。00431F10/00473AE0/0047AF10（C5 已判 direct 命中但 ③a）不在本卡重选。
