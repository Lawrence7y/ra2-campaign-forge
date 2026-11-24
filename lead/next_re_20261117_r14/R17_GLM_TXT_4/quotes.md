# quotes · R17-GLM-TXT-4（只读摘录，路径相对 lead\next_re_20261117_r14\）

## reconcile.tsv（R17_R19_RTTI_XCHECK\reconcile.tsv）
1: class_name	bucket	note
214: AVWWMouseClass	COVERAGE_ONLY	可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 WWMouseClass，该裸名在Q1集合中
332: AVRTacticalClass	COVERAGE_ONLY	可能原因：人工语义文本把名字片段粘连到Class后缀标识符；依据：coverage token包含Q1裸名 Tactical
242: PAVBombClass	COVERAGE_ONLY	可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 PAV 后为 BombClass，该裸名在Q1集合中

## REPORT.md（R17_R19_RTTI_XCHECK\REPORT.md）
67: - **BOTH 209**；**COVERAGE_ONLY 220**；**RTTI_ONLY 779**；三桶合计 1208。

## four_classes.tsv（R17_R17_SLOT73_MAP\four_classes.tsv）
1: class_name	main_vtable	slot_count	slot_73	slot_107	main_plus_0x124
2: .?AVAircraftClass@@	0x007E22A4	341	0x004D3780	0x004196B0	0x007E23C8
5: .?AVUnitClass@@	0x007F5C70	344	0x004D3780	0x0073F0A0	0x007F5D94

## vtable_hits.tsv（R17_R16_SLOT73_SEM\vtable_hits.tsv，全文件仅 2 行）
1: table	va	slot	value	file_offset
2: TechnoClass	0x007F4A84	73	0x006F4A70	0x003F4A84

## edi_writes.tsv（R17_R18_EDI_GAP\edi_writes.tsv，数据行第 2–12 行共 11 行）
2: 0x43F191	mov edi, ecx	8B F9	initial (excluded)
3: 0x43F1DA	pop edi	5F	case0 early-ret path (0x43F1CA->ret@0x43F1E6; never reaches 0x43F5D8)
4: 0x43F387	lea edi, [esi+edx]	8D 3C 16	case1/3 inner loop (0x43F379..0x43F3D4) - CLOBBER
5: 0x43F3DA	mov edi, [esp+0x30]	8B 7C 24 30	case1/3 after loop - RESTORE this from spill
6: 0x43F5C9	pop edi	5F	al!=0 ret path (ret@0x43F5D5; never reaches 0x43F5D8)
7: 0x43F5E0	pop edi	5F	epilogue outside window (>=0x43F5D8)

## REPORT.md（R17_R18_EDI_GAP\REPORT.md）
13: 窗口 [0x43F191, 0x43F5D8) 内共 **4** 条（不含初始 mov）：

## LEAD_LOCK（lead\LEAD_LOCK）
869:         ⇒ 结论：GLM 在「≤8 项纯文本/表内算术」确有实效（三卡共抓出 2 处真实数字/表述缺陷），
870:            但仍【不用于】字节级 / 装配形态 / 宿主身份判定。此边界保持不变。

## GOAL_THREE_TARGETS_20261018.md（lead\GOAL_THREE_TARGETS_20261018.md）
40370: **限制（必须先于数字；否则 220 必被下游误读为「名字错」）：**
40373: ③ 因此 **BOTH 只说明「不矛盾」**，不是类名正确性判定；**COVERAGE_ONLY 不等于「名字错」**，只表示按本抽取口径未与 988 个有 RTTI 的裸名精确相撞。本项**不是**类名正确性判定。
40375: 在上述限制口径下的数字（已从盘上复算）：TD 名字 **988**（`.?AV` **962** / `.?AU` **26**，962+26=988）；从 `coverage.tsv` 第 4 列抽出以 `Class` 结尾的不同类名 **429** 个；三桶 **BOTH 209 / COVERAGE_ONLY 220 / RTTI_ONLY 779**（合计 1208）。
