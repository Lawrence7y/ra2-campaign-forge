# S15-K7 PROGRESS (third/final S15 naming card, static)
Target SHA-256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476, size 4825360; Python 3.12 + capstone 5.0.7(skipdata=True) + pefile; no Ghidra; only this card dir written. Grade read only from column 5; atlas entries lower/coverage upper normalized before intersection.
Live recompute: S15 coverage=159 rows; intersect atlas=158; named=141/158=89.24%; proved=98/158=62.03%; threshold ceil(0.9*158)=143; shortfall=2. Evidence: EVIDENCE/baseline_recompute.txt; work/t0_baseline.py. NOTE: my first recompute double-added K3/K4 deltas (already merged into live coverage); corrected script uses live coverage only.
Result: 3 new names, all [已证], name_kind=symbolic, conflict=0, n_sources=2 each (binary chain=1, YRpp source=1). Post delta named=144/158=91.14%, shortfall=-1; proved unchanged because these rows were [未证] before. Delta has 9 columns, no header (peer convention).
Method sequence follows S13-N1: (1) scalar-delete destructor bounded scan; (2) mirror string scan; (3) RTTI array element-type proof; (4) proven-caller direct-call anchoring.
(1) Paired baseline 169 .text sites contain test byte [esp+8],1 + call 0x7C8B3D + ret 4 (e.g. 0040195E, 00487E88, 0077321A). All 17 bounded target bodies: 0 true positives. Evidence: EVIDENCE/s1_dtor_baseline.txt.
(2) Bounded/window string scan: only <none>/none sentinels in 006E6310/006F1920/00727AA0/00751590, Invalid Voc in 00751590; no unique INI/EVA/%s in target bodies. Caller-side IDs Tag/Teams found, used only as reinforcement. Evidence: EVIDENCE/s2_string_scan.tsv; s2_string_regions.txt; s5_caller_contexts.txt.
(3) RTTI direct proof: 0xB0E780 vt 0x7F4558 -> DynamicVectorClass<TagTypeClass*>; 0xA8ECA0 vt 0x7EA0E4 -> DynamicVectorClass<TeamTypeClass*>; 0x8B4178 vt 0x7E9BA4 -> DynamicVectorClass<TriggerTypeClass*>. COL vt-4, TD+8 inline name. Evidence: EVIDENCE/s3_array_rtti.txt; naming_proofs.md.
(4) All three named entries are directly called by live-coverage [已证] TActionClass::LoadFromINI (0x6DD5B0): sites 0x6DD6C6, 0x6DD64F, 0x6DD68C inside atlas interval 0x6DD5B0+0x2CD. Evidence: EVIDENCE/s5_caller_contexts.txt.
Named 1: 006E6310 = TagTypeClass::FindOrAllocate. Body sentinel/Find/new 0xA4 + TagType ctor 0x6E5B60; array RTTI TagTypeClass*; YRpp AbstractTypeClass.h:13-31 + TagTypeClass.h:15. Two channels; no literal address needed.
Named 2: 006F1920 = TeamTypeClass::FindOrAllocate. Body sentinel/Find/new 0xF8 + TeamType ctor 0x6F06E0; array RTTI TeamTypeClass*; YRpp AbstractTypeClass.h:13-31 + TeamTypeClass.h:23. Two channels.
Named 3: 00727AA0 = TriggerTypeClass::FindOrAllocate. Body sentinel/Find/new 0xB4 + TriggerType ctor 0x726C80; array RTTI TriggerTypeClass*; YRpp AbstractTypeClass.h:13-31 + TriggerTypeClass.h:17. Two channels.
Conflict search by entry address over 6994 files (docs/re, re_atlas/kb, COVERAGE, all R14 cards, YRpp): only sub_ / semantic labels; proposed exact names 0 prior hits. Evidence: EVIDENCE/s4_name_conflict_search.txt.

17 residual rows, per-row decision:
006D0F00 不可定: 15B helper sets [this+0x5545]=1 then indirect vcall; no YRpp/array/RTTI name; caller contexts only weak.
006D6070 不可定: waypoint-to-cell/camera-target shared helper; 14 sites across classes; no method name.
006E1830 不可定: waypoint-to-CellStruct/to-cell-state substep; YRpp real action is other address; no method name.
006E4790 不可定: retains sub_. strncpy(dst,src,0x1F) wrapper inside Execute timer block; no source symbol; not promoted.
006E47C0 不可定: paired rep movsd 8-dword copy with 006E4790; no symbol/vtable/string anchor.
006E6310 可定: TagTypeClass::FindOrAllocate [已证]; see proof.
006EA3E0 不可定: TeamClass::AI helper constructs TagClass and virtual-calls; not action body; no authoritative name.
006F1920 可定: TeamTypeClass::FindOrAllocate [已证]; see proof.
0070F120 不可定: talk-bubble display substep called by real TalkBubble wrapper; no authoritative name.
00721270 不可定: Theme-name index getter with none fallback; YRpp has no ThemeClass method address; single binary channel.
00727AA0 可定: TriggerTypeClass::FindOrAllocate [已证]; see proof.
0072DDB0 不可定: PlayMovie init half sharing global flag with 0072DEF0; real PlayMovie is other address; naming would mispair.
0072DEF0 不可定: PlayMovie cleanup half; paired with 0072DDB0; no independent source name.
00751590 不可定: Voc index-to-name helper; Invalid Voc/none fallback; YRpp FindIndex/GetName are other addresses.
00752460 不可定: Vox index-to-pointer helper with none fallback; YRpp GetName is other address; no source name.
00763610 不可定: %c/%c%c string helper after CFG closure; no source method name; not counted as format-string anchor.
00763690 不可定: two CRT wrapper calls; no string/vtable/source address anchor.

Deliverables: PROGRESS.md, UNKNOWNS.md, DISAGREE.md, coverage_delta.tsv (9 cols), EVIDENCE/, work/. No ledger/coverage/game-file write, no git commit.
