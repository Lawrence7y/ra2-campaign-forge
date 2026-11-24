# S13-K8 DISAGREE — 与上游/审计的分歧与裁定理由

## 1. 与 a-S13-K5 执行员「164 行不可证」的分歧(本卡核心)
- 执行员把 0065BED0/0075E510/16 容器dtor 共 18 行判「不可证(缺独立RTTI类属+ctor注册/删除闭环)」。
- 本卡亲验: 这 18 行四环齐全 —— ②RTTI 链真实可读(`[vt-4]→COL→[COL+0xC]→TD→TD+8`, 例 WarheadTypeClass COL=0x80D360 TD=0x847C18 名串 `.?AVWarheadTypeClass@@`);
  ③体内 vptr重写+operator delete(0x7C8B3D)+ret4; ④ctor 通过 imm32 引用装入该 VT(每类 1–6 处)。
  ⇒ 执行员「缺类属」是假阴性。审计 PARTIAL 的 (b) 点成立。本卡 18/18 全捞回, 与审计一致, 与执行员原判分歧。

## 2. 与「slot 在已证 owner 里存在」式判据的分歧(a-S13-K6 教训)
- 本卡**不用**该判据。环④用「全 .text 字节级 imm32 引用该 VT 地址」+「指令边界 call 目标命中」穷举, 不用「某 slot 值落在已证 owner 集合」。
- 检出力基线 0/150: 随机 16B 对齐 .text 起点用同一判据 0 命中 ⇒ 判据有区分力(对比 a-S13-K6 的检出力=0 判据)。

## 3. 命名冲突(⑱)实测
- 按 entry 扫 docs/re + re_atlas/kb + GOAL_THREE_TARGETS 台账 + COVERAGE 四源:
  18 个新名(`X::scalar_deleting_dtor`)的 entry **0 个语义命名冲突**。
- 唯一命中: COVERAGE/coverage.tsv 的 18 条原行(占位名 slot8/vslot0, 本卡正是要替换它们) + 台账 L12439 的 `| 66 | 0x108 | 0x0046B910 |`(字段偏移表, 非函数命名)。
- 结论: 新名 `scalar_deleting_dtor` 与盘上既有名不撞; 见 EVIDENCE/naming_conflict_scan.txt。

## 4. 分母与「达标」措辞(D-37 未裁)
- 本卡只交 grade, 不改分母、不宣布达标。240 口径 74→92 / 148 口径 74→76 为审计 VERDICT 的算术延伸(见其「修正后」段), 仅供合卡员参考;
  D-37(S13 92 容器模板是否改归 S22)未裁前, 一律双分母并列, 不写「达标」。

## 5. 9 个 sub_ 行的降级(可回退项)
- 0041C230 等 9 行原 census [静态推断] → 本卡 [未证](缺②③, 无虚表槽)。依 CARD「四环严格」。
- 若审计认为非虚表行不适用环②, 这 9 行可回退 [静态推断]; **不影响** 18 行捞回与核心数字。已记 UNKNOWNS.md。

## 6. 环③/环④同源(⑰)核查
- ③取函数体内 vptr写+delete+ret4(通道A: 本函数字节); ④取函数体外 imm32 VT引用/call目标(通道A的另一位置, 但证据命题不同: 「本函数做什么」vs「谁引用此VT」)。
- 两者命题不同、数据位置不同, 不算「同一句话两半」, 各计一环, 符合⑰。
