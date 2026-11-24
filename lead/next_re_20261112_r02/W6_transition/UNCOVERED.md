# UNCOVERED.md —— 未覆盖与不确定项

- run_id: `NEXT_RE_20261112_R02`；生成时刻(UTC): `2026-11-12T17:01:14.006117+00:00`

1. **对局结束过渡（W_C）未覆盖**：对局结束过渡不可达：中止路径落点=skirmish_screen（未出现结算屏），自然结束不可脚本化。

2. **符号解析未做**：USER32/KERNELBASE/ntdll 偏移只按 模块+偏移 比对；帧的「前一条调用」描述仅对 Lead 已证的 `gamemd+0x207f17(Sleep 30)` 与 `gamemd+0x20833f(EnumChildWindows)` 成立。

3. **单线程采样**：只抓游戏窗口线程；其它线程（音频/网络/渲染）状态本卡未采。

4. **抓栈扰动**：每次抓栈短暂冻结窗口线程（≤50ms）；已量化记录但不宣称零扰动。

5. **StackWalk64 深度局限**：32 位无 PDB 下走查常在第 4 帧正常终止（`stackwalk_false:0`）；更外层帧依赖挂起窗口内只读原始栈 + EBP 链交叉核验，栈残留 ≠ 活跃帧。

6. **单图单趟**：仅 `{'index': 265, 'display_name': '[8] Proving Grounds', 'n_items': 268, 'n_hits': 1, 'pattern': 'Proving Grounds'}` / 一局内连续覆盖；未覆盖其它地图、不同负载、联机/录像、长时间运行后的自然停推。

