# S13-K8 PROGRESS — 164行残行重裁（S13 战斗）

## 结论
- 起点: a-S13-K5 VERDICT 判「164不可证」含≥18误杀(点名 0065BED0/0075E510 + 16 容器dtor)。
- working set = byte_census.tsv 中 判定=不可证(缺链) 的164行 减去 K7/K9 的14地址 = 150行。
- 目标 SHA-256 现场复算 73201CC0…F67476(4,825,360B) 一致；只读。
- 结论: 18行四环齐全升 [已证](恰为审计点名18行), 106行 [静态推断](缺③具名语义), 26行 [未证](缺②③)。

## 四环判据(复算方法)
①入口 16B对齐+首字节非E8/E9/EB+vftable槽值即函数; ②类属 [vt-4]→COL→[COL+0xC]→TD→TD+8内联名串(fail-closed);
③语义 体内 mov [this],VT(vptr重写)+call 0x7C8B3D(operator delete)+ret 4 = scalar deleting dtor;
④见证 全.text 字节级 imm32 引用该VT(ctor装vptr) 或指令边界call目标命中。
禁「slot在已证owner存在」判据; 同源只计一环; 无vtable行②不可补。

## 18行逐行结论表(全部[已证], 证据路径见末)
| entry | 类(RTTI TD+8) | ① | ② | ③ | ④ | grade |
|---|---|---|---|---|---|---|
| 0075E510 | WarheadTypeClass | ✓ | ✓ | ✓ | ✓(5处VT引用) | [已证] |
| 0065BED0 | RadSiteClass | ✓ | ✓ | ✓ | ✓(4处VT引用) | [已证] |
| 0040BBC0 | VectorClass<BombClass*> | ✓ | ✓ | ✓ | ✓(4处VT引用) | [已证] |
| 0040BC10 | DynamicVectorClass<BombClass*> | ✓ | ✓ | ✓ | ✓(2处VT引用) | [已证] |
| 0040F8A0 | VectorClass<WarheadTypeClass*> | ✓ | ✓ | ✓ | ✓(3处VT引用) | [已证] |
| 0040F8F0 | DynamicVectorClass<WarheadTypeClass*> | ✓ | ✓ | ✓ | ✓(1处VT引用) | [已证] |
| 0040FE70 | VectorClass<WeaponTypeClass*> | ✓ | ✓ | ✓ | ✓(3处VT引用) | [已证] |
| 0040FEC0 | DynamicVectorClass<WeaponTypeClass*> | ✓ | ✓ | ✓ | ✓(1处VT引用) | [已证] |
| 0046B8C0 | VectorClass<BulletClass*> | ✓ | ✓ | ✓ | ✓(4处VT引用) | [已证] |
| 0046B910 | DynamicVectorClass<BulletClass*> | ✓ | ✓ | ✓ | ✓(2处VT引用) | [已证] |
| 0048AFD0 | VectorClass<DamageGroup*> | ✓ | ✓ | ✓ | ✓(6处VT引用) | [已证] |
| 0048B020 | DynamicVectorClass<DamageGroup*> | ✓ | ✓ | ✓ | ✓(1处VT引用) | [已证] |
| 0054EB50 | VectorClass<KamikazeControl*> | ✓ | ✓ | ✓ | ✓(5处VT引用) | [已证] |
| 0054EBA0 | DynamicVectorClass<KamikazeControl*> | ✓ | ✓ | ✓ | ✓(2处VT引用) | [已证] |
| 0062B330 | VectorClass<ParasiteClass*> | ✓ | ✓ | ✓ | ✓(3处VT引用) | [已证] |
| 0062B380 | DynamicVectorClass<ParasiteClass*> | ✓ | ✓ | ✓ | ✓(1处VT引用) | [已证] |
| 0065C1B0 | VectorClass<RadSiteClass*> | ✓ | ✓ | ✓ | ✓(3处VT引用) | [已证] |
| 0065C200 | DynamicVectorClass<RadSiteClass*> | ✓ | ✓ | ✓ | ✓(1处VT引用) | [已证] |

## 核心数字(给审计复算)
①重裁行数 150(164−14 K7/K9); ②[已证]18 / [静态推断]106 / [未证]26;
③检出力基线 0/150 = 0.000%(随机16B对齐.text起点, 同判据, seed=20261118);
④重叠: K7/K9(14) / K2(8) / K5(6) 全部 0(164清单本就不含K2/K5已并行, K9的14已剔除)。
审计点名18行 recovered 18/18; 修正后 S13 proved(240口径) 74→92(38.33%), (148口径) 74→76(51.35%)。

## 复算路径
- work/analyze_final.py (系统python3.12+capstone5.0.7+pefile, 独立编写, 不import S13_K5/K7代码);
- EVIDENCE/analysis_full.json 逐行四环布尔+证据; EVIDENCE/bodies_audit18.txt 18行体字节;
- EVIDENCE/entry_vt_slots.tsv 槽→RTTI映射; EVIDENCE/vt_rtti_registry.txt VT注册表;
- EVIDENCE/rtti_walk_proof.txt 2个类的COL→TD链; EVIDENCE/baseline_recompute.txt 基线复算;
- coverage_delta.tsv 150行8列。

## 纪律自检
- ⑰同源不双计: ③(体内形态)与④(体外VT引用)分属不同证据源, 各计一环。
- ⑱命名冲突: 18个新名按entry扫四源 → 0语义撞名(命中仅原coverage占位行+台账1处字段表; 见 DISAGREE.md)。
- ⑧非启发式: ④用全.text VT引用穷举, 不用「最近E8/E9」或「无调用者=死代码」。
- 升级硬规矩: 18行均有字节证据(可独立复算), 非复用结论/非探针/非零读数。
