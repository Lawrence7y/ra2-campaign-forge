"""S10-KPROVED3 step 6: generate final EVIDENCE (holding_tables, ring3b, summary, per_row)
and coverage_delta.tsv from verified facts. All offsets entry-relative.
"""
import csv, os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core

HERE=os.path.dirname(os.path.abspath(__file__))
EV=os.path.join(HERE,'..','EVIDENCE')
os.makedirs(EV,exist_ok=True)
os.makedirs(os.path.join(EV,'per_row'),exist_ok=True)

# Verified rows: entry, final_name(from-attrib), orig_name, holds(list of dict), tier, offset_evidence, semantics
ROWS=[
 dict(entry='004D82B0', name='FootClass::slot289', orig='FootClass::slot289',
      holds=[dict(vt='0x7e8c94',slot=289,col='0x800948',td='0x817b78',tn='.?AVFootClass@@')],
      attrib='FootClass', tier='③b④', off='+0x104..+0x11A',
      sem='[vtable slot289] 数组删除左移完整循环：mov ecx,[esi+0x58c](Items)@+0x104 / inc eax@+0x10A / mov edx,[ecx+eax*4]@+0x10B / mov [ecx+eax*4-4],edx@+0x10E(写) / cmp eax,[esi+0x598](count)@+0x118 / jl 回边@+0x11A；②FootClass vt7e8c94 slot289；④direct 00417782/0051CBB1/00738983'),
 dict(entry='004D5690', name='FootClass::slot335', orig='AircraftClass::slot335',
      holds=[dict(vt='0x7e22a4',slot=335,col='0x7fb4c0',td='0x817b90',tn='.?AVAircraftClass@@'),
             dict(vt='0x7e8c94',slot=335,col='0x800948',td='0x817b78',tn='.?AVFootClass@@')],
      attrib='FootClass', tier='③b④', off='+0x3F9..+0x40F',
      sem='[vtable slot335] 数组删除左移完整循环：mov ecx,[ebx+0x58c](Items)@+0x3F9 / inc eax@+0x3FF / mov edx,[ecx+eax*4]@+0x400 / mov [ecx+eax*4-4],edx@+0x403(写) / cmp eax,[ebx+0x598](count)@+0x40D / jl 回边@+0x40F；②两表同slot335按⑯归基类FootClass；④direct 0052236E/00741689'),
 dict(entry='004DB260', name='FootClass::slot53', orig='AircraftClass::slot53',
      holds=[dict(vt='0x7e22a4',slot=53,col='0x7fb4c0',td='0x817b90',tn='.?AVAircraftClass@@'),
             dict(vt='0x7e8c94',slot=53,col='0x800948',td='0x817b78',tn='.?AVFootClass@@')],
      attrib='FootClass', tier='③b④', off='+0x38..+0x89',
      sem='[vtable slot53] 8 邻格 overlay 值 -1 完整循环：mov dx,word[ecx*4+0x89f688]@+0x3D / call 0x5657a0(GetCellAt)@+0x72 / mov dl,[eax+0x122]@+0x77 / dec dl@+0x7D / inc esi@+0x7F / cmp esi,8@+0x80 / mov [eax+0x122],dl@+0x83(写) / jl 回边@+0x89；②两表同slot53按⑯归基类FootClass；④direct 00414112/00517E6C/0051DF53/0073584F/007440B4'),
 dict(entry='00702D40', name='TechnoClass::slot56', orig='AircraftClass::slot56',
      holds=[dict(vt='0x7e22a4',slot=56,col='0x7fb4c0',td='0x817b90',tn='.?AVAircraftClass@@'),
             dict(vt='0x7e3ebc',slot=56,col='0x7fc618',td='0x8193a8',tn='.?AVBuildingClass@@'),
             dict(vt='0x7e8c94',slot=56,col='0x800948',td='0x817b78',tn='.?AVFootClass@@'),
             dict(vt='0x7eb058',slot=56,col='0x8033b8',td='0x825508',tn='.?AVInfantryClass@@'),
             dict(vt='0x7e4960',slot=56,col='0x7fb4f0',td='0x816f08',tn='.?AVTechnoClass@@')],
      attrib='TechnoClass', tier='③b①', off='+0x2EE',
      sem='[vtable slot56] 5 路可核跳表分派：cmp eax,0xe/ja 默认@+0x2EE前 / xor ecx,ecx / mov cl,byte[eax+0x703214]@+0x2EE / jmp [ecx*4+表] → 5 个 .text 目标(0070315F/007030D3/00703035/00703115/007031F8)全可核；②5表同slot56按⑯归基类TechnoClass；④direct 00744790'),
 dict(entry='00706640', name='TechnoClass::slot273', orig='AircraftClass::slot273',
      holds=[dict(vt='0x7e22a4',slot=273,col='0x7fb4c0',td='0x817b90',tn='.?AVAircraftClass@@'),
             dict(vt='0x7e3ebc',slot=273,col='0x7fc618',td='0x8193a8',tn='.?AVBuildingClass@@'),
             dict(vt='0x7e8c94',slot=273,col='0x800948',td='0x817b78',tn='.?AVFootClass@@'),
             dict(vt='0x7eb058',slot=273,col='0x8033b8',td='0x825508',tn='.?AVInfantryClass@@'),
             dict(vt='0x7e4960',slot=273,col='0x7fb4f0',td='0x816f08',tn='.?AVTechnoClass@@'),
             dict(vt='0x7f5c70',slot=273,col='0x80cc68',td='0x842d80',tn='.?AVUnitClass@@')],
      attrib='TechnoClass', tier='③b①', off='+0x24',
      sem='[vtable slot273] 4 路可核跳表分派：call [eax+0x68] / dec eax / cmp eax,4 / ja 默认@+0x24前 / jmp [eax*4+表] → 4 个不同 .text 目标(0070666B/00706683/0070668A/00706BAD)；另有两处完整循环@+0x436..+0x455与+0x50C..+0x52B(读+写+推进)；②6表同slot273按⑯归基类TechnoClass；④direct 004DAFAB'),
 dict(entry='00708C30', name='TechnoClass::slot174', orig='AircraftClass::slot174',
      holds=[dict(vt='0x7e22a4',slot=174,col='0x7fb4c0',td='0x817b90',tn='.?AVAircraftClass@@'),
             dict(vt='0x7e8c94',slot=174,col='0x800948',td='0x817b78',tn='.?AVFootClass@@'),
             dict(vt='0x7eb058',slot=174,col='0x8033b8',td='0x825508',tn='.?AVInfantryClass@@'),
             dict(vt='0x7e4960',slot=174,col='0x7fb4f0',td='0x816f08',tn='.?AVTechnoClass@@')],
      attrib='TechnoClass', tier='③b①', off='+0x1E',
      sem='[vtable slot174] 5 路可核跳表分派：dec eax / cmp eax,4 / ja 默认@+0x1E前 / jmp [eax*4+0x708d54] → 5 个 .text 目标(00708C55/00708CD9/00708CB4/00708D4D/00708C7A)全可核；②4表同slot174按⑯归基类TechnoClass；④direct 0044D715'),
 dict(entry='004D94B0', name='FootClass::slot288', orig='FootClass::slot288',
      holds=[dict(vt='0x7e8c94',slot=288,col='0x800948',td='0x817b78',tn='.?AVFootClass@@')],
      attrib='FootClass', tier='③b②', off='+0xD1..+0xDD',
      sem='[vtable slot288] 可证伪返回约定：call 0x45aea0@+0xCC / cmp eax,ebx / jge 放行@+0xD1..+0xD3 / cmp eax,0x80004002(E_NOINTERFACE) / je 放行@+0xD5..+0xDA / 其余负值 push eax→call 0x7dc720 断言失败@+0xDC..+0xDD；②FootClass vt7e8c94 slot288；④direct 0041AAA6/0041AD06/0041ADB4/0051B1D2/00742D0B/00743161'),
 dict(entry='004DDDE0', name='FootClass::slot28', orig='FootClass::slot28',
      holds=[dict(vt='0x7e8c94',slot=28,col='0x800948',td='0x817b78',tn='.?AVFootClass@@')],
      attrib='FootClass', tier='③b①′', off='+0x70..+0xC3',
      sem='[vtable slot28] 6 道互斥闸的多路守卫链(各闸动作不同)：test ch,1→坐标偏移调整@+0x70 / call 0x586360 结果 test→返回ebx@+0x93 / test ebx,ebx→返回ebx@+0x97 / test [eax+0xc8d]→返回2@+0xAB / call 0x578460 结果 test→返回2@+0xBE / cmp ebx,0x33→返回ebx@+0xC0；三种结局(ebx/1/2)、五个不同被调(700600/578080/565730/586360/578460)、无共同汇入call ⇒ D-42细则#1成立；②FootClass vt7e8c94 slot28；④direct 00417FAA/0051F833/007404F6'),
]

# ② holding tables TSV
ht=['entry\tname\tn_holds\tvt\tbyte_off\tslot\tCOL\tTD\tTD8_inline_name\tattribution']
for r in ROWS:
    for h in r['holds']:
        ht.append('\t'.join([r['entry'],r['name'],str(len(r['holds'])),h['vt'],str(h['slot']*4),str(h['slot']),h['col'],h['td'],h['tn'],r['attrib']+'(base)' if len(r['holds'])>1 else r['attrib']]))
open(os.path.join(EV,'holding_tables.tsv'),'w',encoding='utf-8').write('\n'.join(ht)+'\n')

# ③b TSV
r3=['entry\tname\ttier\tentry_rel_offset\tevidence']
for r in ROWS:
    r3.append('\t'.join([r['entry'],r['name'],r['tier'],r['off'],r['sem']]))
open(os.path.join(EV,'ring3b.tsv'),'w',encoding='utf-8').write('\n'.join(r3)+'\n')

# per_row detail files
for r in ROWS:
    txt=['=== %s %s'%(r['entry'],r['name']),
         'orig_classification_name: '+r['orig'],
         '② holding tables (all):']
    for h in r['holds']:
        txt.append('  vt=%s byte_off=0x%X slot=%d COL=%s TD=%s name=%s'%(h['vt'],h['slot']*4,h['slot'],h['col'],h['td'],h['tn']))
    txt.append('  attribution = %s%s'%(r['attrib'],' (base-level per 错源⑯, %d tables same slot)'%len(r['holds']) if len(r['holds'])>1 else ' (single table)'))
    txt.append('③b tier=%s offset=%s'%(r['tier'],r['off']))
    txt.append('  '+r['sem'])
    txt.append('④ sites: see ../ring4_verified.tsv and ../sites/%s.txt'%r['entry'])
    txt.append('① entry 16B-aligned: %s ; E8 direct target: yes'%('yes' if int(r['entry'],16)%16==0 else 'no'))
    open(os.path.join(EV,'per_row',r['entry']+'.txt'),'w',encoding='utf-8').write('\n'.join(txt)+'\n')

# baseline
b=json.load(open(os.path.join(HERE,'baseline.json')))
bl=['# S10-KPROVED3 ③b base rate (seed 20261119, 2000 draws of 8, pool=S10 static-inference rows)',
    'pool = %d'%b['pool'],
    'strict ③b (incl D-42 detail#1 guards): %d/%d = %.4f'%(b['strict'],b['pool'],b['strict_rate']),
    'core ③b (①②③④ only): %d/%d = %.4f'%(b['core'],b['pool'],b['core_rate']),
    'loose D-42(A): %d/%d = %.4f'%(b['loose'],b['pool'],b['loose_rate']),
    'draws=%d mean_strict=%.4f rate_strict=%.4f ; mean_loose=%.4f rate_loose=%.4f'%(
        b['draws'],b['mean_strict'],b['rate_strict'],b['mean_loose'],b['rate_loose']),
    'per-cond: '+str(b['per_cond']),
    'K = rows x mean is an identity, NOT a consistency check.']
open(os.path.join(EV,'baseline_3b.txt'),'w',encoding='utf-8').write('\n'.join(bl)+'\n')

# summary
json.dump(dict(card='S10-KPROVED3',four_ring_complete=8,delta_rows=8,S10_A_total=49,
               remaining_pool=41,rows=[dict(entry=r['entry'],name=r['name'],attrib=r['attrib'],
               tier=r['tier'],offset=r['off'],n_holds=len(r['holds'])) for r in ROWS],
               baseline=b),open(os.path.join(EV,'summary.json'),'w',encoding='utf-8'),indent=1)

# coverage_delta.tsv (6 cols per card convention; here 6: entry subsystem name semantics grade evidence)
dl=['entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path']
for r in ROWS:
    dl.append('\t'.join([r['entry'],'S10',r['name'],r['sem'],'[已证]','EVIDENCE/per_row/%s.txt'%r['entry']]))
open(os.path.join(HERE,'..','coverage_delta.tsv'),'w',encoding='utf-8').write('\n'.join(dl)+'\n')
print('generated EVIDENCE + coverage_delta.tsv with',len(ROWS),'rows')

