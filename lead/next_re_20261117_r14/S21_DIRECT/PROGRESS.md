# S21-DIRECT · PROGRESS（卡号 S21-DIRECT · 执行员 agent-49）

## ⑨ 停机核验（atlas∩coverage 口径）
- 目标 ra2youli\gamemd.exe SHA-256 `73201CC0…F67476` 全值一致，只读未碰；Python 3.12.10 + capstone 5.0.7 + pefile 2024.8.26，无 venv/pip。
- S21 n=**129** / named=**91** / proved=**26** / 静态推断=**91** / 未证=**12** —— 与卡面逐字一致。raw coverage 132 行，3 行无 atlas 不入集（U1）。
- 只动 grade；名字/语义/subsystem 零改动。

## ② 扫描规模与覆盖率（EVIDENCE/scan_stats.json）
- `.text` VA `0x401000` RawSize `0x3E0000`=4,063,232 B；capstone 5.0.7 skipdata 线性全扫 **100.0000%** 覆盖。
- RawSize 口径 **1,394,186 条指令**；VirtualSize 口径 **1,392,592 条**（与项目基准逐字一致，错源 D 同 S20）。
- E8 原始字节 **81,715**；指令边界真 call **68,253**（与基准逐字一致）；E8@边界但非 call = 0。
- ⑲ 自检：mem 操作数 447,226 个，`hasattr(op,"index")`=**0**；`op.mem.index`==0 有 425,567、!=0 有 21,659 ⇒ 无 index 返 0 非 None 确认；脚本不依赖 `op.index`。
- 交付 66 站点全落自报覆盖范围（EVIDENCE/direct_call_sites_clean.tsv / work/all_direct_call_sites.tsv）。

## ①③ 交付结果
- **direct 升格 35 行**（12× `[未证]→[已证]` + 23× `[静态推断]→[已证]`，见 coverage_delta.tsv）。
- 逐行 66 站点逐字节复算：`site+5+rel32==entry` 全真、capstone call 全真、非自环全真、16B 对齐全真、前驱 nop(90) 全真、atexit=False 全真、全落 .text。
- ⑥ **VIRTUAL_SKIPPED = 64 行**（仅 .rdata 虚表可达、无 direct call、不升格）；direct 升级集 ∩ 虚表集 = **0**（EVIDENCE/virtual_reachable_rows.json）。
- ⑤ 并入后 S21 proved = 26+35 = **61**（门槛 65，仍差 4）。

## ④ 基线 / 差分 / 冲突（EVIDENCE/baseline_final.json）
- 随机基线（N=35，10 seed）：未对齐 10 seed 全 **0/35**（mean **0.0**）；aligned16 mean **0.6/35**。
- 弱扫(raw E8 任意偏移) vs 强扫(边界 E8) 差集 **0/0**（同源、零鉴别力，按 ㉔ 仅作旁证）。
- 有鉴别力差分（同一 35 行 × 弱「有 direct caller」vs 强「+入口判据16B/nop + 非atexit + 非虚表」）：weak 35/35、strong 35/35、差集 **0** ⇒ 无同源系统误差。
- ⑱ 按 entry 地址扫 618 文件（docs/re + re_atlas/{kb,evidence} + COVERAGE + 台账）：35 地址 190 处命中，绝大多数本行自证/所在函数引用；少量软语义归属（00686B20/00599650）只报不改名（U4）。

## 交付清单
`PROGRESS.md` / `UNKNOWNS.md` / `coverage_delta.tsv`(35行/8列) / `VIRTUAL_SKIPPED.tsv`(64行) /
`EVIDENCE/{scan_stats,summary,baseline_final,verify_direct,virtual_reachable_rows}.json` / `EVIDENCE/{all_direct_call_sites,direct_call_sites_clean}.tsv` /
`work/{scan_text,build_candidates,verify_direct,virtual_scan,baseline_final,conflict18,gen_deliverables}.py` + 全扫索引。

## 核心数字（审计复算）
① 35 ② 1,394,186 指令 / 68,253 E8 / 100% ③ 基线0.0+差分0 ④ VIRTUAL_SKIPPED 64 ⑤ 并入 proved 61（差4）。