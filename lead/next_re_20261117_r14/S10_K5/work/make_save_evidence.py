#!/usr/bin/env python3
"""Emit non-truncated four-part behavior evidence for 005B3970 Save."""
import hashlib
from pathlib import Path
from re_lib import *
CARD=Path(__file__).resolve().parent.parent
sha=hashlib.sha256((ROOT/'ra2youli'/'gamemd.exe').read_bytes()).hexdigest().upper()
o=[]
o.append('S10-K5 005B3970 SAVE / SERIALIZE BEHAVIOR EVIDENCE')
o.append('SHA256='+sha)
o.append('GRADE=[已证]  NAME=MissionClass::Save  (behavior name; class via RTTI/vtable, role via bytes; not single-source)')
o.append('\n=== FOUR-PART CLOSURE ===')
o.append('A. ENUM/CONSTANT ANCHOR')
o.append('  - 005B3060 dispatch reads mission-id enum from [this+0xAC]: 005B30B2 mov eax,[edi+0xAC]; 005B30C1 jmp [eax*4+0x5B34E8].')
o.append('  - 0x816CAC..0x816D28 = 32 mission-name pointers; table bound 0x816D2C used by 005B3910 loop. -1 sentinel -> "<none>" string 0x817474 in 005B3760/005B3910.')
o.append('B. WRITTEN FIELD OFFSETS in 005B3970')
o.append('  +0xAC(mission id), +0xB0, +0xB4, +0xBC, timer remaining computed from +0xC8/+0xD0 and 0xA8ED84 CurrentFrame, +0xC0.')
o.append('C. CALLER ARGUMENT')
o.append('  - entry edi = dword [esp+0xC] = first stack arg; forwarded as ecx to 005F6250 and each 4A1D50/4A1CA0 write.')
o.append('  - caller 0065AB10: ebx=dword [esp+8]; push ebx -> call 005B3970; same ebx is ecx for its own 4A1D50 writes. Therefore arg is stream/archive object.')
o.append('D. CALLEE SEMANTICS')
o.append('  - 005F6250 calls 00410410 [已证] AbstractClass::Save with edi, then writes many object fields with the same 4A1D50/4A1CA0 helpers.')
o.append('  - 004A1D50: push 4; push &value; call 004A1DE0 => writes a 4-byte integer (byte loop + checksum table).')
o.append('  - 004A1CA0 same structure for a single byte/bool; 00410410 proves those helpers are the Save serialization primitives.')
o.append('CONCLUSION: 005B3970 serializes MissionClass state into the caller-provided stream => MissionClass::Save.')
o.append('\n=== MISSION NAME TABLE SAMPLE (enum anchor) ===')
names=[]
for i in range(32):
 p=u32(0x816CAC+4*i)
 if not (0x816CAC<=p<0x816D2C): names.append('<bad:%08X>'%p); continue
 s=cstr(p,96); names.append(s)
o.append('count=32 first='+repr(names[:4])+' last='+repr(names[-4:]))
o.append('\n=== 005B3060 DISPATCH ANCHOR (entry region) ===')
o.append(fmt_block(0x5B30A0,count=36,stop_ret=False,max_bytes=256))
o.append('\n=== TARGET FULL ENTRY-TO-RET 005B3970 ===')
o.append(fmt_block(0x5B3970,count=120,stop_ret=True,max_bytes=1024))
o.append('\n=== BASE SERIALIZER 005F6250 FULL ENTRY-TO-RET ===')
o.append(fmt_block(0x5F6250,count=200,stop_ret=True,max_bytes=2048))
o.append('\n=== PROVEN AbstractClass::Save 00410410 ===')
o.append(fmt_block(0x410410,count=50,stop_ret=True,max_bytes=256))
o.append('\n=== DWORD/BOOL WRITE HELPERS ===')
o.append(fmt_block(0x4A1D50,count=30,stop_ret=True,max_bytes=128))
o.append(fmt_block(0x4A1CA0,count=80,stop_ret=True,max_bytes=512))
o.append('\n=== 004A1DE0 FULL ENTRY-TO-RET (dword serializer core) ===')
o.append(fmt_block(0x4A1DE0,count=400,stop_ret=True,max_bytes=4096))
o.append('\n=== CALLER 0065AB10 FULL ENTRY-TO-RET ===')
o.append(fmt_block(0x65AB10,count=120,stop_ret=True,max_bytes=1024))
o.append('\n=== SENTINEL/NAME ANCHORS (full functions saved in mission_fields_probe.txt) ===')
o.append('005B3760 uses [esi]==-1 -> 0x817474 "<none>", else name table [0x816CAC + id*4].')
o.append('005B3910 scans 32 pointers from 0x816CAC to 0x816D2C via CRT::strcmpi and returns -1 on miss.')
(CARD/'EVIDENCE'/'005B3970_SAVE_PROOF.txt').write_text('\n'.join(o)+'\n',encoding='utf-8')
print('wrote',CARD/'EVIDENCE'/'005B3970_SAVE_PROOF.txt',len('\n'.join(o)))
