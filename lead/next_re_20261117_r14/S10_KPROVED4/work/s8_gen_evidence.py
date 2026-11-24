"""s8: generate final evidence files for the 8 selected rows + holding tables + sites."""
import sys, os, json, csv
sys.path.insert(0, os.path.dirname(__file__))
from core import Bin, build_rtti, sweep_calls, FuncMap, disasm_range, holding_tables, attribute_base
from capstone.x86 import X86_OP_MEM, X86_OP_IMM

HERE=os.path.dirname(__file__)
OUT=os.path.join(HERE,'..','EVIDENCE')
b=Bin(); rtti=build_rtti(b); sw=sweep_calls(b); fm=FuncMap(b,rtti,sw)

SEL=['004D55C0','004D55F0','004D9C10','00517CC0','004DBAD0','006F3AD0','006FBDC0','006FBC90']
NAME={'004D55C0':'FootClass::StopMoving','004D55F0':'FootClass::MoveTo',
      '004D9C10':'FootClass::Can_Enter_Cell','00517CC0':'InfantryClass::slot9',
      '004DBAD0':'FootClass::slot13','006F3AD0':'TechnoClass::slot44',
      '006FBDC0':'TechnoClass::slot168','006FBC90':'TechnoClass::slot169'}
# reasons for ③b failure (from detailed analysis)
REASON={
 '004D55C0':'③a: single null-guard(test [this+0x674]; push 0x80004003; call 0x7dc720 assert) + one virtual call [ecx+0x48]; no jump-table/loop-with-write/callee-return HRESULT comparison; 0x80004003 is an assert argument not a compared return value (D-42 ② needs callee-return comparison like 004D94B0 cmp eax,0x80004002).',
 '004D55F0':'③a: two null-guards with push 0x80004003 assert + virtual calls [ecx+0x44]/[eax+0x10]; no jump-table/loop-with-write/callee-return HRESULT; assert-code push not ③b②.',
 '004D9C10':'③a: forward-only guards (test loco; test arg; assert E_POINTER; one virtual call [ecx+0x1c]); no loop, no jump table, no compared HRESULT; return is boolean from literal xor, not a falsifiable error-code convention.',
 '00517CC0':'③a: one backward-branch search loop (+0x45..+0x4F: cmp [eax],edi / je / inc ecx / add eax,4 / cmp ecx,edx / jl) but loop body has NO explicit data write and NO falsifiable return (function returns void); only pointer/index advance — fails M7 (loop needs explicit write or falsifiable return). cmp ecx,-1 at +0xAF is a field-default copy, not an error code.',
 '004DBAD0':'③a: long linear field-serialization (240 ins); 8 jcc are independent null-checks all converging to the same field-writer call 0x4a1d50; cmp edx,-1 at +0x15B/+0x194 are remaining-time calculations, not error codes; no loop/jump-table/memory-shape assertion.',
 '006F3AD0':'③a: floating-point geometry computation; 2-path index selection (test esi/jge; neg/cmp 5/jg) is only 2 mutually-exclusive paths (<3 for 细则#1); push 0x80004003 assert is not callee-return HRESULT; 3 field writes are all stack scratch [esp+0x30/34/38], not ctor memory-shape.',
 '006FBDC0':"③a/细则#1 rejected (M4): ~25 jcc guard gates but ALL negative paths converge to the SAME `xor al,al; pop; ret` false-return stub (+0xE5/+0xF7/+0x123/+0x145/+0x164/+0x190/+0x1B7); distinct gate predicates but identical action ⇒ fails D-42 细则#1 '各闸动作不同' (same rejection as 004DDDE0).",
 '006FBC90':'③a/细则#1 rejected (M4): ~14 jcc guard gates but ALL negative paths converge to the SAME `xor al,al; ret` false-return at +0x12C (success is mov al,1 at +0x11D); distinct predicates identical action ⇒ fails 细则#1 (same as 004DDDE0).',
}

# holding tables tsv
with open(os.path.join(OUT,'holding_tables.tsv'),'w',encoding='utf-8') as f:
    f.write('entry\tname\tn_holds\tvt\tbyte_off\tslot\tCOL\tTD\tTD8_inline_name\tattribution\n')
    for e in SEL:
        hs=holding_tables(b,rtti,int(e,16))
        base,note=attribute_base(hs)
        for h in hs:
            f.write(f"{e}\t{NAME[e]}\t{len(hs)}\t{h['vt']:#x}\t{h['byte_off']}\t{h['slot']}\t{h['col']:#x}\t{h['td']:#x}\t{h['name']}\t{base}\n")

# sites tsv
with open(os.path.join(OUT,'ring4_verified.tsv'),'w',encoding='utf-8') as f:
    f.write('entry\tsite\tat_E8_boundary\trel32_target\trel32_ok\toutside_body\n')
    rem=json.load(open(os.path.join(os.path.dirname(os.path.dirname(HERE)),'S10_KPROVED3','work','a_rows_remaining.json'),encoding='utf-8'))
    sites_by={r['entry']:[s for s in r['ring4_direct_sites'].split(';') if s] for r in rem}
    for e in SEL:
        ea=int(e,16); st,en=fm.extent(ea)
        for s in sites_by.get(e,[]):
            sa=int(s,16); tgt=sw['calls'].get(sa)
            outside = not (st<=sa<en)
            f.write(f"{e}\t{s}\t{sa in sw['boundaries']}\t{tgt:#08X}\t{tgt==ea}\t{outside}\n")

# per_row evidence
for e in SEL:
    ea=int(e,16); st,en=fm.extent(ea)
    hs=holding_tables(b,rtti,ea); base,note=attribute_base(hs)
    lines=[f'entry={e}', f'name(②attrib)={NAME[e]}', f'extent=[{st:08X},{en:08X}) size={en-st}',
           '', '## ② HOLDING TABLES (full enumeration, RTTI COL=vt-4 -> TD=COL+0xC -> TD+8 inline)']
    for h in hs:
        lines.append(f"  vt={h['vt']:#x} slot={h['slot']} byte+0x{h['byte_off']:x} COL={h['col']:#x} TD={h['td']:#x} name={h['name']}")
    lines.append(f'  ② attribution = {base} ({note})')
    # verify parent table same slot differs
    lines.append('')
    lines.append('## ①/④ ENTRY & SITES')
    rem_sites=None
    rem=json.load(open(os.path.join(os.path.dirname(os.path.dirname(HERE)),'S10_KPROVED3','work','a_rows_remaining.json'),encoding='utf-8'))
    for r in rem:
        if r['entry']==e: rem_sites=[s for s in r['ring4_direct_sites'].split(';') if s]
    lines.append(f'  ① entry E8-direct-target: {ea in set(sw["calls"].values())}')
    for s in (rem_sites or []):
        sa=int(s,16); tgt=sw['calls'].get(sa)
        lines.append(f'  ④ site {s}: boundary={sa in sw["boundaries"]} target={tgt:#08X} ok={tgt==ea} outside_body={not(st<=sa<en)}')
    lines.append('')
    lines.append('## ③b VERDICT: FAIL (③a)')
    lines.append('  '+REASON[e])
    open(os.path.join(OUT,'per_row',f'{e}.txt'),'w',encoding='utf-8').write('\n'.join(lines))

print('evidence written for', len(SEL), 'rows')
