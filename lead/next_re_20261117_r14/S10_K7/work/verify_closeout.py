from common import Image, EV, ROOT, sha256, GAME, COVER
import datetime, bisect, struct
img=Image(); L=[]
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
L.append(f'closeout_checks_time_cst={now}')
L.append(f'game_sha256={sha256(GAME)} size={GAME.stat().st_size}')
L.append(f'coverage_sha256={sha256(COVER)} size={COVER.stat().st_size}')

# baseline target rows (col5 raw bytes)
raw=COVER.read_bytes()
for line in raw.splitlines():
 if line.startswith(b'006B7010\t') or line.startswith(b'004E0E80\t'):
  c=line.split(b'\t')
  L.append(f'baseline_target={c[0].decode()} col5_hex={c[4].hex()} col5_latin1={c[4].decode("latin1")}')

def need(name, cond, detail=''):
 L.append(f'CHECK {name}: '+('PASS' if cond else 'FAIL')+((' | '+detail) if detail else ''))
 if not cond: raise SystemExit('check failed: '+name)

# 006B7010
body=img.read(0x006B7010,0xF0)
need('6B7010_vptr_write_bytes', img.read(0x006B7015,27).hex()=='c70750367f00c7470434367f00c747082c367f00c7470c24367f00')
need('6B7010_no_scalar_flag_test', bytes.fromhex('f644240801') not in body)
need('6B7010_plain_ret_tail', img.read(0x006B70F3,4).hex()=='5f5e59c3')
need('6B7010_vtable_slot8_to_wrapper', img.u32(0x7F3670)==0x006B8140)
wrap=img.read(0x006B8140,0x20)
need('6B8140_calls_body_then_flag_delete_ret4', wrap[:30].hex()=='568bf1e8c8eefffff644240801740956e8e809110083c4048bc65ec20400')
need('6B7010_delete_call_1', img.read(0x006B704F,5).hex()=='e8e91a1100')
need('6B7010_delete_call_2', img.read(0x006B70D2,5).hex()=='e8661a1100')
need('7C8B3D_delete_to_free', img.read(0x7C8B3D,11).hex()=='ff742404e8a208000059c3')
for vt,col in [(0x7F3650,0x809AE8),(0x7F3634,0x809A80),(0x7F362C,0x809A68),(0x7F3624,0x809A50)]:
 got_col=img.u32(vt-4); td=img.u32(got_col+0xC); nm=img.cstr(td+8,64)
 need(f'RTTI_{vt:08X}', got_col==col and td==0x00840120 and nm=='.?AVSpawnManagerClass@@', f'COL={got_col:08X} TD={td:08X} name={nm}')
need('ctor_A_same_group_order', img.read(0x006B6CEF,27).hex()=='c70650367f00c7460434367f00c746082c367f00c7460c24367f00')
need('ctor_B_same_group_order', img.read(0x006B6EE6,27).hex()=='c70650367f00c7460434367f00c746082c367f00c7460c24367f00')
need('ctor_A_caller_new_then_call', img.read(0x006F3F9D,9).hex()=='6a74e8734e0d008bf8' and img.read(0x006F3FF0,8).hex()=='8bcf5056e8972cfc')
need('ctor_B_caller_new_then_call', img.read(0x006C0A3C,14).hex()=='6a74e8d483100083c40485c0740d' and img.read(0x006C0A4A,7).hex()=='8bc8e84f64ffff')

# 004E0E80
b=img.read(0x004E0E80,0x50)
need('4E0E80_vptr_write', img.read(0x004E0E98,6).hex()=='c7060c927e00')
need('4E0E80_fields', img.read(0x004E0E8B,13).hex()=='895604894608c6460c0188560d')
need('4E0E80_allocator_call', img.read(0x004E0EB1,12).hex()=='c1e00250e85d7f2e0083c404')
need('4E0E80_returns_this_stdcall', img.read(0x004E0EC4,4).hex()=='8bc65ec2')
calls=[]
for ins in img.cs.disasm(b,0x004E0E80):
 if ins.mnemonic=='call': calls.append(ins.op_str)
need('4E0E80_only_allocator_call', calls==['0x7c8e17'], str(calls))
col=img.u32(0x7E920C-4); td=img.u32(col+0xC); nm=img.cstr(td+8,80)
need('RTTI_7E920C', col==0x008009E0 and td==0x008225B8 and nm=='.?AV?$VectorClass@PAVAbstractClass@@@@', f'COL={col:08X} TD={td:08X} name={nm}')
pat=struct.pack('<I',0x004E0E80); st=0; hits=[]
while True:
 i=img.data.find(pat,st)
 if i<0: break
 hits.append(i); st=i+1
need('4E0E80_no_exact_vtable_slot_hit', len(hits)==0, f'{len(hits)} file hits')
# verified direct caller count via atlas ranges
atlas=ROOT/'lead'/'next_re_20261112_r10'/'W130_atlas'/'function_atlas.tsv'; ents=[]
for ln in atlas.read_text(encoding='utf-8',errors='replace').splitlines()[1:]:
 c=ln.split('\t')
 if len(c)>=2:
  try: ents.append((int(c[0],16),int(c[1])))
  except: pass
cs=[]
for e,sz in ents:
 for ins in img.cs.disasm(img.read(e,sz),e):
  if ins.mnemonic=='call' and ins.op_str=='0x4e0e80': cs.append(ins.address)
need('4E0E80_direct_caller_count', len(cs)==8, ', '.join(f'{x:08X}' for x in cs))
need('4E0E80_caller_passes_two_zero_args', img.read(0x004D3291,6).hex()=='53899e800500' and img.read(0x004D3298,2).hex()=='538b')
need('4E0E80_caller_ecx_this', img.read(0x004D3299,12).hex()=='8bcfc786840500000000f03f')

(EV/'CLOSEOUT_CHECKS.txt').write_text('\n'.join(L)+'\n',encoding='utf-8')
print('CLOSEOUT_CHECKS written; see EVIDENCE/CLOSEOUT_CHECKS.txt')
