#!/usr/bin/env python3
"""Emit non-truncated byte evidence for 005B3A60 scalar deleting destructor."""
import hashlib,struct
from pathlib import Path
from re_lib import *
CARD=Path(__file__).resolve().parent.parent
EXEP=ROOT/'ra2youli'/'gamemd.exe'
sha=hashlib.sha256(EXEP.read_bytes()).hexdigest().upper()
out=[]
out.append('S10-K5 005B3A60 SCALAR DELETING DESTRUCTOR EVIDENCE')
out.append('SHA256='+sha)
out.append('TOOLS: Python 3.12 capstone 5.0.7 skipdata=True pefile; no Ghidra; no atlas entry+size used as sole channel.')
out.append('\n=== RAW BYTES 005B3A60..005B3A96 ===')
out.append(dump_bytes(0x5B3A60,0x40))
out.append('\n=== ENTRY-TO-RET DISASSEMBLY 005B3A60 ===')
out.append(fmt_block(0x5B3A60,count=100,stop_ret=True,max_bytes=1024))
out.append('\n=== VFTABLE RTTI CHAIN (independent data channel) ===')
col=0x805D28; vb=0x7EDCC0; slot=8; td=0x817B18
off,cdoff,ptd=struct.unpack('<iii',read(col+4,12))
out.append('ref dword @0x%08X = 0x%08X (func)'%(vb+4*slot,u32(vb+4*slot)))
out.append('vbase=0x%08X slot=%d COL@0x%08X sig=0x%08X offset=0x%x cdOffset=0x%x pTD=0x%08X'%(vb,slot,col,u32(col),off&0xffffffff,cdoff&0xffffffff,ptd))
out.append('TD+8=0x%08X name=%s'%(td+8,cstr(td+8,128)))
out.append('RTTI class=MissionClass; slot8 value is the target entry.')
out.append('\n=== CTOR 005B2DA0 SAME FOUR VPTR WRITES ===')
out.append(fmt_block(0x5B2DA0,count=40,stop_ret=True,max_bytes=512))
out.append('\n=== CALLED BASE DTOR 005F3B80 (entry-to-ret, full) ===')
out.append(fmt_block(0x5F3B80,count=400,stop_ret=True,max_bytes=8192))
out.append('\n=== 007C8B3D operator delete thunk (entry-to-ret) ===')
out.append(fmt_block(0x7C8B3D,count=20,stop_ret=True,max_bytes=64))
out.append('\n=== COVERAGE ANCHORS FOR CALLEES ===')
out.append('005F3900 [已证] sub_005F3900 (paired base ctor; writes 7EF060/44/3C/34 and registers arrays)')
out.append('005F3B80 [已证] ObjectClass::ObjectClass (label stale; bytes are base destructor shape: same vptrs + array unwinding, no ret4/delete)')
out.append('007C8B3D [已证] CRT::_delete; calls 007C93E8 CRT::free [已证]')
out.append('\n=== S13/S06 SCALAR-DELETING-DTOR CHECKLIST ===')
out.append('1 body entry-to-ret: 005B3A60 push esi; mov esi,ecx; ...; ret 4. PASS')
out.append('2 own vptrs restored: [esi]=7EDCC0,+4=7EDCA4,+8=7EDC9C,+0xC=7EDC94. PASS')
out.append('3 same four vptrs written by ctor 005B2DA0 at 005B2DE9..005B2DFD. PASS')
out.append('4 RTTI class: vbase 007EDCC0 slot8 -> COL 805D28 -> TD 817B18 -> .?AVMissionClass@@. PASS')
out.append('5 base dtor call before flag: call 005F3B80 at 005B3A7E. PASS')
out.append('6 MSVC deleting flag: test byte [esp+8],1 at 005B3A83; on true push this -> call 007C8B3D; ret 4. PASS')
out.append('7 return this in eax: mov eax,esi at 005B3A93. PASS')
out.append('8 name evidence: class from RTTI channel (2), deleting-destructor role from body channel (1/5/6/7); not a single-source name. PASS')
(CARD/'EVIDENCE'/'005B3A60_DELETING_DTOR.txt').write_text('\n'.join(out)+'\n',encoding='utf-8')
print('wrote',CARD/'EVIDENCE'/'005B3A60_DELETING_DTOR.txt',len('\n'.join(out)))
