# S11-DIRECT · DISAGREE.md

## D1 — 3 个 [未证] 行有 direct call site，但因 ⑱ 冲突不升格

`005AE860` / `005AF1A0` / `007559B0` 在 `coverage.tsv` 中是 S11 `[未证]`（`sub_XXXXXXXX`，语义「调用图邻居弱信号」），
全 `.text` 扫描均有 direct call site（分别 49 / 28 / 14 个），按 direct 判据本应升 `[已证]`。
但 ⑱ 按 entry 地址查全库发现**语义冲突**（它们不是 Locomotor/寻路函数）：

- `005AE860`：`docs/re/bullet_particle_fog_deep_dive.md:148` 记 `Matrix3D::Identity`；
  `docs/re/vxl_cache_layout.md:206` 记「初始化单位矩阵」。
- `007559B0`：`docs/re/ARCHITECTURE_ATLAS.md:3858,3946`、`docs/re/vxl_cache_layout.md:218`、
  `docs/re/vxl_render_sort.md:380`、`docs/re/atlas_rev/R7_vxl_fx_gap.md:191` 均记为
  **阴影投影矩阵查表函数**（表 `0xB45188`）。
- `005AF1A0`：未直接命中文档，但紧邻 `005AE860`（Matrix3D::Identity）且调用图与矩阵函数重叠；
  与 `005AF980`/`005AEA10`（同族矩阵函数，coverage 归 S22）同域，S11 归属同为弱信号。

**处置**：不升格（列入 `work/conflict_excluded.json` 与 `EVIDENCE/direct_call_sites.tsv`，
不进 `coverage_delta.tsv`）。卡面要求「只动 grade、不动 subsystem」，若把它们升为 `[已证]`，
会把弱信号错归类固化成 `[已证]` 的 S11 行。留待合并员/裁决处理 subsystem 归属。

## D2 — 基线误命中率偏高（direct 判据对函数入口非特异）

随机抽 11 个 atlas 函数入口，direct 判据误命中 1–8 个（10 seed 均值 ≈4.7/11）。
原因：atlas 中大部分真实函数本就有 direct 调用者，判据区分「是否真实函数」不特异。
这不是本卡判据错误——本卡只用 direct 判据作为「该入口有字节级外部调用证据」，
不做「随机行也过」的区分度声明；差集检验（`weak_hits=11, strong_hits=11, weak_only=0`）
证明 11 个候选全部由同一强判据命中，无弱判据伪命中。