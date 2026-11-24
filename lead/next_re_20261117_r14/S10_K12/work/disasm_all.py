
import sys,hashlib,datetime,csv
from pathlib import Path
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K12\work')
import re_lib as R
L=[]
def log(s=''): L.append(str(s))

log('S10_K12 RECHECK 2: FUNCTIONS + CALL SITES + CALLEES')
log('TIME='+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat())
log('EXE_SHA256='+hashlib.sha256(R.EXE.read_bytes()).hexdigest().upper())
log('TOOLS=Python3.12.10 capstone5.0.7(skipdata=True)+pefile2024.8.26')

log('\n=== VTABLE MAP (vt=0x7EB058) ===')
vt=0x7EB058
for off in [0x5c,0x174,0x1e8,0x288,0x320+0x1e0,0x3c8,0x480,0x500,0x53c,0x558]:
    log(f'vt+0x{off:X} @ {vt+off:08X} = {R.u32(vt+off):08X}')
# correct slots
for off,nm in [(0x5c,'slot23'),(0x3c8,'slot242'),(0x500,'slot320'),(0x53c,'slot335'),(0x558,'slot342'),(0x480,'slot288'),(0x1e8,'slot93ish')]:
    log(f'vt+0x{off:03X} ({nm}) @ {vt+off:08X} = {R.u32(vt+off):08X}')

def dump(va,size,label):
    log('\n=== '+label+' @ '+f'{va:08X}'+' size='+str(size)+' ===')
    log(R.dis(va,size))
    log('POST='+R.read(va+size,16).hex().upper())

# The 5 candidate functions
for a,sz,label in [(0x51D6F0,1013,'ROW1 0051D6F0 slot342'),
                   (0x51DAF0,223,'ROW2 0051DAF0 slot320'),
                   (0x51B1F0,347,'ROW3 0051B1F0 slot242'),
                   (0x51BAB0,1239,'ROW4 0051BAB0 slot23'),
                   (0x522340,393,'ROW5 00522340 slot335')]:
    dump(a,sz,label)

# External callees (proven)
for a,sz,label in [(0x4D55C0,39,'CALLEE StopMoving 004D55C0 [proved]'),
                   (0x65C7E0,173,'CALLEE RandomRanged 0065C7E0 [proved]'),
                   (0x5B3A00,15,'CALLEE 005B3A00 table-accessor [未证 S12]')]:
    dump(a,sz,label)

# External callers with call sites to slots 0x3c8 / 0x500 / 0x5c / 0x53c
# full dump of small ones
for a,sz,label in [(0x51F330,168,'EXT_CALLER 0051F330 slot266 (has call@51F39D to v+3c8)'),
                   (0x51F6E0,281,'EXT_CALLER 0051F6E0 slot143 (has call@51F7AF to v+3c8)'),
                   (0x521760,90,'CALLER 00521760 slot58 -> v+558')]:
    dump(a,sz,label)

# context windows around external call sites for slots 0x500 and 0x5c and 0x53c
def ctx(site,before=24,after=8):
    log('\n--- CTX '+f'{site:08X}'+' (raw bytes around) ---')
    va=site-before
    log(R.dis(va,before+after))

for site in [0x5180FE,0x51A6CA,0x51ABD1,0x520946,   # slot500 callers
             0x51F39D,0x51F7AF,                     # slot3c8 callers
             0x4DAEF3,0x51BB7A,                     # slot5c
             0x4D473A,0x4D4E6A,0x4D54D2,0x6FAB74]: # slot53c
    ctx(site)

out=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K12\EVIDENCE\DISASM_ALL.txt'
Path(out).write_text('\n'.join(L)+'\n','utf-8',newline='\n')
print('WROTE',out,'lines',len(L))
