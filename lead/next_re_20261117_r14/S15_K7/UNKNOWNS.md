# S15-K7 UNKNOWNS

## Baseline caveat
- First local recompute double-counted K3/K4 deltas already merged into live coverage (would give 142). Corrected work/t0_baseline.py and EVIDENCE/baseline_recompute.txt use live coverage only: 141/158 named, shortfall 2, as the card states.

## Remaining 14 unnamed after the 3 proposed rows
006D0F00: 15B helper, sets [this+0x5545]=1 then indirect virtual call; no array/RTTI/source name; weak host-level caller only.
006D6070: waypoint-to-cell/camera helper; multiple classes/call sites; no method-level authoritative name.
006E1830: waypoint-to-CellStruct and cell-state substep; the real sound-action FUNCTION is another address; no name.
006E4790: bounded strncpy 0x1F wrapper; caller-side Execute timer block only; no source symbol.
006E47C0: paired rep-movsd copy with 006E4790; no symbol/vtable/string anchor.
006EA3E0: TeamClass::AI helper constructing TagClass; not a TAction body; no authoritative name.
0070F120: talk-bubble display substep called twice by the real YRpp TalkBubble wrapper; no name.
00721270: Theme-name index getter with none fallback; no YRpp ThemeClass method/address; only one binary channel.
0072DDB0: PlayMovie init half sharing a global flag with 0072DEF0; YRpp PlayMovie is another address; naming either half would mispair.
0072DEF0: PlayMovie cleanup half; paired with 0072DDB0; no independent source name.
00751590: Voc index-to-name helper returns Invalid Voc/none; YRpp FindIndex/GetName are other addresses; no source method name.
00752460: Vox index-to-pointer helper with none fallback; YRpp GetName is another address; no source method name.
00763610: %c/%c%c wsprintf helper; no method name; caller-side format strings are not enough.
00763690: two CRT wrappers; no string/vtable/source address anchor.

## Method coverage
- Scalar delete destructor: 0 true positives on all 17 with a positive baseline of 169 .text sites.
- Body strings: no unique INI/EVA/%s anchor in any residual target body.
- RTTI: only the three named arrays yielded class-element proof; other targets do not operate on RTTI-identifiable DynamicVectorClass arrays.
- Source-name channel: YRpp macro yielded three names; no YRpp literal addresses or explicit methods for the remaining 14.

No placeholder names, no Class::sub_, no ledger/coverage/game-file modification, no git commit.
