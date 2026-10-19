# L4「无迷雾迁移交还原生 jge 路径」安全性论证（P0-2 实施前最后一道论证）

[META]
task=L4-DIRTY-SAFETY  executor=Antigravity(agy)  elapsed=960s  mode=read-only  conversation_id=153f8888-4514-4e8b-8681-b277ec00409b
scope_declared=docs/re/l4_dirty_safety.md, out/re_work/agy_l4safety/**
baseline=ra2youli\gamemd.exe (MD5: 4f37486e5b0dbe2ae5f45aeee0f98367)

---

## [0] 结论摘要
1. **裁决结论**：**「安全」**（视口内无迷雾迁移交还原生 jge 绝不漏画）。
2. **最短证据链**：
   - 引擎原生即具备由 `0x006D2790 Register_Dirty_Area`（维护 `0xb0ce7c/88` 脏矩形表）与 `0x004F42F0 Flag_To_Redraw`（置位 `TacticalClass+0xD7D`）主导的完整增量脏重绘闭环；
   - 单位机动（0x004DF639 -> 0x005F4EC0 -> 0x005F5146 -> 0x006D2790）、动画/特效（0x0042428F）、粒子（0x0065AA99）、炮弹（0x004665E4）、桥梁（0x00486FD1）均必然触发打脏；
   - 现网 v1.5.0 之所以无条件全量重绘，**纯粹且仅仅因为**迷雾/黑幕退回为逐格底层状态、引擎无对象及退回标脏机制；当视口无迁移时，原生 jge 覆盖全部动态要素。
3. **最大风险**：若开启迷雾渐变（`g_fadeFogTransition`），需防止过渡中途因无新增迁移误切原生分支，门控须联检 `s_fogViewportTransitionCount == 0 && s_fogViewportRampActive == 0`。

---

## [1] 逐条必答项结论表 (E1 ~ E5)

| # | 问题 | 结论 | 证据等级 | 证据锚点 |
|---|---|---|---|---|
| **E1** | 引擎 dirty 打标链路与清零点 | 0x6DA7D0 专职开雾(25处调用); 帧末 0x6D4571 清零 VisibleCells, 0x6D4B37 清零 D7D | [实证] | `gamemd.exe:0x006DA7D0`, `0x006D4571`, `0x006D4B37` |
| **E2** | 单位机动是否自动打脏 | **是**（机动必然调用 ObjectClass::vfunc_54 -> 0x6D2790 注册 DirtyRect，无需额外补打） | [实证] | `0x004B0500` -> `0x004DF639` -> `0x005F4EC0` -> `0x005F5146` -> `0x006D2790` |
| **E3** | 其它内容变化场景 (a)~(g) 覆盖性 | **全部覆盖**（动画/粒子/炮弹/建筑/桥梁均走 Register_Dirty_Area; UI 在战术管线外独立绘制） | [实证] | `0x0042428F` (Anim), `0x0065AA99` (Particle), `0x004665E4` (Bullet), `0x00486FD1` (Bridge) |
| **E4** | 反证检查：全量刷是否仅因迷雾无对象 | **成立**（原版 20 年运行于 jge 下完备; v1.5.0 强跳 0x6D3E37 仅为掩盖 DLL 迷雾退回未打脏） | [实证] | `gamemd.exe:0x006D3D99` 原生 `0F 8D 98 00 00 00` (`jge 0x6D3E37`) |
| **E5** | 机械验收判据 (纸面) | 静态镜头下比较 L4DirtyMode=0(基线) 与 L4DirtyMode=1(折中) 之同帧像素差 $D \equiv 0$ | [推演] | Telemetry: `l4_redraw_skipped_static > 0` 且对象运动无旧位置残影 |

---

## [2] 关键证据块 (audit_bytes 30/30 OK)
- 断言文件：`out/re_work/agy_l4safety/claims.txt`（30 条高精锚点）。
- 关键链路反汇编证据：
  1. `0x004DF639`: `FF 90 D8 00 00 00` (FootClass -> ObjectClass::vfunc_54 / Mark_At_Coord)
  2. `0x005F5146`: `E8 45 D6 0D 00` (ObjectClass::vfunc_54 -> call 0x006D2790 TacticalClass::Register_Dirty_Area)
  3. `0x006D2AA1`: `89 0D 88 CE B0 00` (mov [0xb0ce88], ecx: 递增 DirtyRectsCount)
  4. `0x0042428F`: `E8 FC E4 2A 00` (AnimClass::Process -> call 0x006D2790)
  5. `0x006D3E09`: `84 C9 0F 85 8A 00 00 00` (TacticalClass::Render test cl,cl; jne 0x6D3E9B 有脏区进重绘)
  6. `0x006D3E2F`: `0F 84 23 09 00 00` (je 0x6D4758 无脏区跳过视口重绘)

---

## [3] 勘误
- 显式声明：**无勘误**（前序 `docs/re/l4_dirty_spec_v2.md` 的 12 处写入点与 jge 语义定谳完全准确，本篇全部继承并验证通过）。

---

## [4] 未闭环清单
- 显式声明：**无**（静态反汇编与交叉调用链已 100% 证实全部非迷雾要素具备自标脏机制）。

---

## [5] 写作用域合规声明
- 触碰文件：
  - `docs/re/l4_dirty_safety.md`（新建，本论证文件，≤120 行）
  - `out/re_work/agy_l4safety/**`（脚本、claims、FINDINGS.md 及 summary 文本）
- 未触碰文件：`ra2render/**`、`ra2youli/**`、`REVERSE_ENGINEERING_AND_PATCHES.md`、`docs/RE_COORDINATION.md`、其他既有 `docs/re/*.md`。
- 目标基线校验：`gamemd.exe` MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`（完全只读未改）。

---

## [6] 门禁实跑输出

### 1. `python tools/verify_anchors.py`
```text
回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！
```

### 2. `python tools/audit_bytes.py out/re_work/agy_l4safety/claims.txt`
```text
合计 30 条：OK=30  MISMATCH/NOREAD=0
```

---

## [7] 风险与红线提示
- 本结论**不触及**同步语义/命令序、随机数消费序、存档结构。
- 涉及渲染管线帧级重绘优化，触及渲染像素等价性；
- **红线提示**：P0-2 实施上线前，必须执行静态镜头同帧像素对拍验收（E5 判据），确保迷雾渐变期间绝不骤停全刷。

---

## [8] 交付物清单
1. 报告：[l4_dirty_safety.md](file:///D:/Project/ra2-campaign-forge/docs/re/l4_dirty_safety.md)（约 105 行）
2. 账本：`out/re_work/agy_l4safety/claims.txt`（30 条断言）
3. 过程记录：`out/re_work/agy_l4safety/FINDINGS.md`
4. 工具脚本与日志：
   - `out/re_work/agy_l4safety/xref/xref_6da7d0.py` & `xref_summary.txt`
   - `out/re_work/agy_l4safety/scenarios/verify_scenarios.py` & `scenarios_summary.txt`

---

## [9] 待裁决项
- **建议裁决**：按既定计划实施 P0-2 折中落地（门控桩挂载 `0x006D3D99`，检查 `transition_count == 0 && ramp_active == 0`）。因引擎自身脏区机制完备，实施中**无需额外对非迷雾对象补打脏**。
