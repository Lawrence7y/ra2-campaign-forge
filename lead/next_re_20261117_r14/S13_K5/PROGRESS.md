# S13-K5 PROGRESS（≤60 行）

目标只读 `ra2youli\gamemd.exe`，SHA-256 `73201CC0…F67476` 现场复算一致；Python 3.12 + capstone 5.0.7(skipdata=True)+pefile；未 import S13_K4/work，未改 coverage.tsv / 游戏文件，未 git commit。
双通道：A=VA→RVA 直读 PE 字节并从入口逐条反汇编至 ret/CFG；B=自写 COL+0xC→TD、TD+8 内联名串 + 虚表 slot 值 + ctor/registry 交叉。均不依赖 atlas entry+size。

## 任务一：6 行闭合
| entry | 新语义名 | 闭合要点 | 证据 |
|---|---|---|---|
| 0040F510 | WarheadTypeClass::FindOrMakeIndex | `<none>`/`none`+strcmp 0x7c8d20；扫 [0x8874c4]/cnt[0x8874d0] +0x24；push 0x1d0→new 0x7c8e17→ctor 0x75cec0；返索引/-1 | EVIDENCE/resolver_compare.txt, PROOF_SIX.md |
| 0046C440 | BulletTypeClass::FindOrMakeIndex | `<none>`+strcmp；扫 [0xa83c84]/cnt[0xa83c90] +0x24；push 0x2f8→new→ctor 0x46bbc0；返索引/-1 | 同上 |
| 004393F0 | BombClass::slot8_deleting_dtor | VT 0x7e3d10 slot8；写自身 vptr + 摘注册表 + base dtor + test[esp+0xc],1 + delete 0x7c8b3d + ret 4 | EVIDENCE/dtor_compare.txt, rtti_vt_registry.txt |
| 0046C890 | BulletTypeClass::slot8_deleting_dtor | VT 0x7e4948 slot8；同上（两个注册表） | 同上 |
| 0062AF70 | ParasiteClass::slot8_deleting_dtor | VT 0x7ef890 slot8；同上（test[esp+0x10],1） | 同上 |
| 007730F0 | WeaponTypeClass::slot8_deleting_dtor | VT 0x7f73b8 slot8；同上（test[esp+0x10],1） | 同上 |
重要差异（不照抄先例）：0x75E3B0 是 pointer-return resolver；0040F510/0046C440 的创建核心同型，但多一段 post-ctor 扫描并返回 registry index/-1，故命名为 FindOrMakeIndex。逐字节表见 resolver_compare.txt。
ECX 全写入点已列于 EVIDENCE/ecx_write_trace.txt；ctor 内 ecx→ebp/esi→vptr 写已回溯。

## 任务二：字节候选普查（独立脚本 work/gen_evidence.py + work/finalize.py）
盘上非已证候选 193 行，按字节而非名字形状重判：
- 可证(K2/K4 已证但未并入 coverage.tsv)：21 行（8 K2 B8 + 6 K4 B8 + 7 K4 行为级）。
- 可证(本卡入 delta)：6 行；可证(本卡行为级、未入 delta)：2 行（0046B990/0046B9A0 thunk，836c240404+tail jmp，目标逐条至 ret）。
- 不可证(缺链)：164 行；逐行缺环见 EVIDENCE/byte_census.tsv。
真名复查：在去掉盘上 [已证] 与 K2/K4/本卡 6 行后的 166 行中，仅 00708080 `death_handler` 是真名；未发现其它被名字形状误埋的真名行。见 EVIDENCE/true_name_recheck.tsv。

## 任务三：分母只登记，不裁决
coverage_README.md 原文规则：容器模板（T_VectorClass_*/T_DynamicVectorClass_*/T_TClassFactory_*/T_VectorCursor_* 等）显式归 S22，sem=container_template。
逐行核：240 行 S13 中命中 92 行（?$DynamicVectorClass 29、?$VectorClass 28、T_DynamicVectorClass 18、T_VectorClass 17，合计 92）；当前均仍在 S13 且 proved=0。清单见 EVIDENCE/container_template_92.tsv。
两种分母并列：240 口径 74/240=30.83%（门槛 120/240=50%）；148 口径 74/148=50.00%（门槛 74/148=50%）。是否剔除 92 行归 S22 由 Lead/用户裁决，见 DISAGREE.md。

## 任务四：基线自算（统一大小写）
盘上：S13∩atlas=240；grade 已证47/静态推断160/未证33。四阶段 proved：盘上 47/240=19.58%（148 口径 31.76%）；并 K2 55/240=22.92%（37.16%）；并 K2+K4 68/240=28.33%（45.95%）；再并本卡 74/240=30.83%（50.00%）。证据：EVIDENCE/baseline_recompute.txt。

交付：PROGRESS.md / UNKNOWNS.md / DISAGREE.md / coverage_delta.tsv(6 行无表头) / EVIDENCE\ / work\。
