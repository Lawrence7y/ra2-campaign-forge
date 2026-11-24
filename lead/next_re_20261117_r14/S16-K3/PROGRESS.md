# S16-K3 PROGRESS（卡号 S16-K3）— 假前提重做 + S 口径 DoD 复算

写域仅 `S16-K3\`。目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`（只读）；
Python 3.12.10 + capstone 5.0.7 `skipdata=True` + pefile 2024.8.26；复跑见 `work\`，原始输出见 `EVIDENCE\`。

## 结论表（三级分级 + 证据路径）

| 项 | 结论 | 级 | 证据 |
|---|---|---|---|
| T1 AbstractClass 槽契约 | 24 码槽；**slot6=`0x4C9150` 纯虚桩**、slot12 GetSize 空桩、slot13=`0x410410` 基类块；slot24=COL ptr | **[已证]** | `EVIDENCE/E01_t1_slots.txt`; `SLOTS.md`; KB22 §0/§1.1/§3 |
| T1 三类槽表 | SuperClass 24 槽(v[12]→0x80)、SWT 28 槽(v[12]→0x100, v[27] 末槽)；RTTI 名逐一 | **[已证]** | `E01`; `SLOTS.md §1`; `work/t1_slots.py` |
| T2 `0x6CDFD0` `SuperClass::Save` | v[6] + 11 条完整体 + RTTI TD `8423E0`；`0x410320` 非虚 | **[已证]** | `EVIDENCE/E02_t2_bodies.txt`; `E03_forwarders.txt`; `LAYOUT.md §2.1` |
| T2 `0x6CE220` `~SuperClass` | v[8] + 规范标量删除析构(体自证) + RTTI | **[已证]** | `E02`; `LAYOUT.md §2.2` |
| T2 `0x6CE8D0` `SuperWeaponTypeClass::Save` | v[6] + 同构 11 条体 + RTTI TD `842600` | **[已证]** | `E02`; `LAYOUT.md §2.3` |
| T2 `0x6CEFE0` `~SuperWeaponTypeClass` | v[8] + **复杂**析构(写 4 vtable+0xA8E330 注销+`0x4109C0`) + RTTI | **[已证]** | `E02`; `LAYOUT.md §2.4` |
| T2 假前提撤销 | `0x410320` 作槽值 0 次、非虚、非 `AbstractClass::Save`（后者=slot13 `0x410410`） | **[已证]** | `E02 §A`; `LAYOUT.md §0`; `DISAGREE.md D1/D2` |
| T4 7 条 `Class::sub_` 定名 | 逐条真取证后**全部不可定**，保持 sub_（提升 0 条） | **[未证]**→占位 | `EVIDENCE/E04_t4_naming.txt`; `UNKNOWNS.md U1` |
| T3 DoD 第 1 条（**S 口径**） | named **49/90=54.44% 不达标**；proved 46/90=51.11% 达标；**整体不达标** | **[已证]** | `DOD.md`; `work/t3_dod.final.out.txt` |

## 给审计员的核心数字（可独立复算）

**核心数 1 — 4 条重做后成立 4/4，但依据全改写（数值不变，proved 仍 46/90）。**
复算：① `python work/t1_slots.py` 看三类槽表；② `python work/t2_bodies.py` 打 4 条完整体（首 ret 即止、后 nop），
看 `0x410320` 在 `.rdata/.data` dword 0 次；③ `python work/t2_forwarders.py` 扫 1214 表得
v[6]→`0x410320` 54 类 / v[5]→`0x410380` 41 类 / 交叉 0；④ 对 LAYOUT §1 的 a/b/c/d 判据逐条核对。
敏感性（LAYOUT §3.1）：若审计用「语义字节必在函数自身」严标准，则 2/4 成立 ⇒ proved 44/90=48.89% 不过。

**核心数 2 — S 口径 named% = 49/90 = 54.44%（不达标）；L 口径 83/90 = 92.22%（仅面板对照）。**
复算：`python work/t3_dod.py`：读 `coverage.tsv` ∩ `function_atlas.tsv` 得 S16=90；
基准 named_S=42 / named_L=73 / proved=42（与 PANEL + a-S16-K2-B ★A 逐字吻合）；
套本卡 `coverage_delta.tsv` 14 行（10 命名 + 4 提级，其中 7 条 `Class::sub_` 按 S 不计、3 条真名 + 4 条 slot→真名 = +7）
⇒ named_S=49、named_L=83、proved=46。DoD 门槛 named≥81、proved≥45。

**核心数 3 —槽号契约：「Save」双槽，COM Save=槽 6 / `AbstractClass::Save` 基类块=槽 13。**
复算：`E01` 直接读 `0x7E1F50+4*6=0x7E1F68` → `0x4C9150`（`33 C0 C3`）；`+4*13=0x7E1F84` → `0x410410`
（体写 `+0x10`/`+0x20`）；与 KB22 §1.1/§3 逐格吻合，**无 DISAGREE**。`0x410320` 不在任何槽（D1）。

## 交付与边界
- 产物：`SLOTS.md`(T1 三类槽表)、`LAYOUT.md`(T2 重做)、`DOD.md`(T3 六条对账, S 口径结论)、
  `UNKNOWNS.md`、`DISAGREE.md`(D1–D7)、`EVIDENCE\E01..E04`(未截断)、`work\`(可复跑)、`coverage_delta.tsv`(14 行)。
- **未**改 `COVERAGE\coverage.tsv`、未改 `ra2youli\`、未写主台账、未 git commit/push。doD 结论按 S 口径：**S16 不达标**。
