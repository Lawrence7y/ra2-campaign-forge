"""Generate byte-level claims (VA = HEXBYTES) from gamemd.exe and verify round-trip."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import s08lib as L
b=L.Bin()
# (VA, expected hex, note) -- all from capstone dumps in EVIDENCE
CLAIMS=[
 (0x5863C5,'c1e009','谓词idx计算 shl eax,9 (=512)'),
 (0x5863CC,'3d00000400','边界 cmp eax,0x40000 (512*512)'),
 (0x5863D3,'8b1524f98700','格数组基址 mov edx,[0x87F924]'),
 (0x5863D9,'8b0482','stride4 mov eax,[edx+eax*4]'),
 (0x5863F2,'f6812c01000008','Shroud判据 test byte [ecx+0x12C],8'),
 (0x58652E,'8b883c010000','Fog判据 mov ecx,[eax+0x13C]'),
 (0x586534,'85c9','Fog判据 test ecx,ecx'),
 (0x5865E0,'32c0','stub xor al,al'),
 (0x5865E2,'c20400','stub ret 4'),
 (0x48799B,'e8c0e90f00','CellClass::IsShrouded调0x586360前 mov ecx,0x87F7E8于0x48798E'),
 (0x4A98E6,'8b852c010000','写探索位 mov eax,[ebp+0x12C]'),
 (0x4A98EC,'0c08','or al,8 (cf_Explored)'),
 (0x4A990F,'888520010000','mov [ebp+0x120],al'),
 (0x4A9924,'0c10','or al,0x10 (cf_Mapped)'),
 (0x4A9947,'888521010000','mov [ebp+0x121],al'),
 (0x6D8724,'8b8040010000','mov eax,[eax+0x140]'),
 (0x6D872A,'a803','test al,3'),
 (0x480207,'888620010000','Draw写 mov [esi+0x120],al'),
 (0x480230,'e8abedffff','call 0x47EFE0 黑幕层'),
 ( (0x48022E),'8bce','mov ecx,esi 黑幕层this'),
 (0x47F01F,'f6c51074','FogOfWar位门 test ch,0x10 / je 0x47F02F'),
 (0x65715C,'8a86d9140000','雷达脏门1 mov al,[esi+0x14d9]'),
 (0x6571A3,'8b866c120000','雷达脏门4 mov eax,[esi+0x126c]'),
 (0x6571AD,'8b8634120000','雷达脏门5 mov eax,[esi+0x1234]'),
 (0x6571C3,'0f84a9060000','全无脏 je 0x657872 早退'),
 (0x6574C3,'e888e7ffff','增量DrawCell call 0x655C50'),
 (0x657520,'e82be7ffff','脏点DrawCell call 0x655C50'),
 (0x657D77,'e8d4deffff','全量DrawCell call 0x655C50'),
 (0x6529D0,'899e1c120000','ctor 写 Surface字段 mov [esi+0x121C],ebx'),
 (0x6529FB,'899e3c120000','ctor 写地形色缓存 mov [esi+0x123C],ebx'),
 (0x508F60,'',''),  # placeholder removed below
]
CLAIMS=[c for c in CLAIMS if c[1]]
out=[]
ok=0; bad=0
for va,hx,note in CLAIMS:
    actual=b.read(va,len(hx)//2).hex()
    status='OK' if actual==hx else 'MISMATCH'
    if status=='OK': ok+=1
    else: bad+=1
    out.append('0x%08X  %-24s %-24s %-8s %s'%(va,hx,actual,status,note))
p=os.path.join(os.path.dirname(__file__),'..','EVIDENCE','E14_claims.txt')
with open(p,'w',encoding='utf-8') as f:
    f.write('; S08-K1 byte claims (expected = actual from read-only gamemd.exe)\n')
    f.write('\n'.join(out)+'\n')
    f.write('TOTAL %d  OK=%d  MISMATCH=%d\n'%(len(CLAIMS),ok,bad))
print('\n'.join(out))
print('TOTAL %d OK=%d MISMATCH=%d'%(len(CLAIMS),ok,bad))
