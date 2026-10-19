# FOG-FIRSTSTAGE-R3 · 定位「地表侧 ×0.71875(23/32)」来源根因定谳报告

[META]
task=FOG-FIRSTSTAGE-R3  executor=Antigravity(agy)/1aeda6ec-c283-44bc-9bf8-6619379a565b  elapsed=480s  mode=read-only
scope_declared=docs/re/fog_firststage_rootcause.md, out/re_work/agy_fog_firststage/**

[0] 结论摘要
1. H-1 数据侧否定：FOG.SHP 满雾帧(Frame 15)为实心纯色菱形(900像素全为66，透明900像素为254)，无28.125%(9/32)网点图案。
2. H-2/H-3/H-4 代码与表驱动全部否定：CellClass::Draw(0x4801F0)不调地表blitter且无暗化实参；exe无184查表；原版tint为加性(-61)且已被桩覆写。
3. 站点判定为「未定位」，排查缩小至地表光栅化调色板或前级光照层；修法建议桩内反补偿(s'=round(s*1.391))，数据侧无法由SHP修复。

[1] 逐条必答项结论表
| # | 问题 | 结论 | 证据等级 | 证据锚点 |
|---|---|---|---|---|
| Q1 | H-1 是否成立 (FOG.SHP 数据侧) | **否定**：Frame 15 为 100% 满菱形实心纯色(值恒66)，等效遮盖率非 9/32(28.125%) | [实证] | out/re_work/agy_fog_firststage/r3/shp/analyze_fog_pixels.py; FOG.SHP off=29312 |
| Q2 | H-2/H-3/H-4 命中情况 | **全部未命中**：H-2(0x4801F0 无地表 blitter 传参)、H-3(无 184 静态表)、H-4(原版为加性 -61 且已被桩替换) | [实证] | 0x4801F0/0x6D3660/0x6D71E0/0x47F40F 反汇编与 claims_r3.txt 15/15 OK |
| Q3 | 落地修法建议与风险 | 建议桩内反补偿 (s'=round(s*1.391))；改数据侧 SHP 无效(桩已忽略 bl)；改调色板波及全图；桩内补偿需真机对拍验像素 | [推演] | 本文 §[0] 与 docs/re/fog_strength_rootcause.md §F4 |
| Q4 | 若全部未命中：排除项与下一步 | **未定位**；已排除 H-1/H-2/H-3/H-4；下一步对 0x47F40F 处 [eax] 读写前后下内存断点截取地表原始像素与 LightConvert 查表 | [实证]已排除+[待实测] | 下一步断点：0x47F40F (读地表像素瞬间), 观察 [eax] 与 0x547CF0 Tile blitter |

[2] 关键证据块
1. `0x004801F0 = 53 55 56 8B F1 8B 0D 24 73 88 00 57 8D 7E 24` # CellClass::Draw 入口 (ret 8 @0x480299, 仅 call 0x6D8700/0x47EFE0/0x47F250)
2. `0x006D3660 = 83 EC 38 53 55 56 57 8B F9` # F1 调用者入口 (0x6D3716 call 0x4801F0，实参仅 pCell, pLocation, pBounds，无暗化参数)
3. `0x006D71E0 = 81 EC C0 00 00 00 53` # 重绘调用者入口 (0x6D751A call 0x4801F0，无暗化实参，无 184/0xB8 传参)
4. `0x0047F403 = 8A 1F 47 80 FB 7F` # 读 FOG.SHP 像素 bl 并比较 0x7F；Frame 15 读入 bl=66 (0x42)
5. `0x0047F40F = 66 8B 08 66 83 F9 7F` # 原版加性桩 B1 入口 (已被 ra2render.dll 替换为混色桩)
6. `0x0047F42F = 8D 4C 11 81` # 原版加性 tint lea ecx,[ecx+edx-0x7f]，edx=66 ⇒ ecx-61，非乘性缩放
7. FOG.SHP 头与帧证据：SHA256=b8e3640435140041f0ac3d4ff18ad99b035a2292b685a2fd89c64bf1cc55e73f，大小 88,712 字节，Frame 15 活跃像素 900/1800 均全等于 66。

[3] 勘误
目标文件:行号 | 改前原文 | 改后文本 | 理由 | 影响面
---|---|---|---|---
docs/re/fog_strength_rootcause.md:47 | 引擎雾层调用点（我方保持不可达）：0x4801F0 CellClass::Draw 入口 / 0x480230 call 0x47EFE0 / 0x480251 = F6 C6 10 / 0x480278、0x480290 call 0x47F250 | 0x4801F0 实为 CellClass::Draw_Shroud_And_Fog (被 0x6D3716/0x6D751A 调用)，其内不含地表 blitter | 反汇编实证，0x4801F0 仅 0x9A 字节无地形光栅化 | 澄清地表绘制不在 0x4801F0 内，而在 0x6D7560/0x480350 |

[4] 未闭环清单
| # | 缺口 | 为何无法静态闭环 | 下一步取证方法 | 级别 |
|---|---|---|---|---|
| 1 | 地表原始像素何时被施加 ×0.71875 | exe 静态扫描未见 184 立即数与查表，疑在地形 8bit 转 16bit 的 LightConvertClass 动态生成表或基准图环境光 | 在 0x47F40F (读 [eax] 瞬间) 与 0x547CF0 (Tile blitter) 下只读断点对比写入像素值 | P1 |

[5] 写作用域合规声明
- 本次改动：新建 `docs/re/fog_firststage_rootcause.md`、`out/re_work/agy_fog_firststage/r3/**`
- 未触碰：`ra2render/**`、`ra2youli/**`、`REVERSE_ENGINEERING_AND_PATCHES.md`、`docs/RE_COORDINATION.md`、其他 `docs/re/*.md`、任何二进制与 `.mix/.map/.sav`
- 只读基线 MD5：
  - `ra2youli/gamemd.exe`: 4F37486E5B0DBE2AE5F45AEEE0F98367
  - `ra2youli/ra2render.dll`: EAAA1BE95BE88BCC67F58A2AFD1A42C9

[6] 门禁实跑输出
```
D:\Project\ra2-campaign-forge>python tools\verify_anchors.py
回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！

D:\Project\ra2-campaign-forge>python tools\audit_bytes.py out\re_work\agy_fog_firststage\r3\claims_r3.txt
合计 15 条：OK=15  MISMATCH/NOREAD=0
```

[7] 风险与红线提示
- ① 同步语义/命令序：未触及（纯只读静态分析）。
- ② 随机数消费序：未触及。
- ③ 存档结构：未触及。
- ④ 渲染像素等价性：触及（若后续采用方案 A 反补偿，雾区地表像素将产生变动，必须经 MP 门控矩阵与真机对拍验收，禁止宣称零风险）。

[8] 交付物清单
- 新文档：`docs/re/fog_firststage_rootcause.md` (约 80 行)
- 日志文件：`out/re_work/agy_fog_firststage/r3/FINDINGS.md` (68 行)
- 断言：`out/re_work/agy_fog_firststage/r3/claims_r3.txt` (15 条，audit 全 OK)
- 脚本：`parse_fog_shp.py`, `analyze_fog_pixels.py`, `disasm_cellclass_draw.py`, `disasm_f1.py`, `check_h2_calldraw.py`, `check_h3_tables.py`
- 产物目录：`out/re_work/agy_fog_firststage/r3/{shp,calldraw,alt}/`

[9] 待裁决项
1. 是否批准关闭「静态源码/数据侧排查」，直接采纳方案 A「混色桩内反补偿 s'=round(s*1.391)」？（建议批准：第一段已被多轮穷验证明非静态简单常数，桩内反补偿是最经济且可收口的工程闭环路线）。
