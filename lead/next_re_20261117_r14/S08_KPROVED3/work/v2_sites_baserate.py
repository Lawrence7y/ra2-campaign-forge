import sys, struct, random
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S08_KPROVED2\_audit\scripts')
from peutil import PE
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
p = PE(EXE)
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True; md.skipdata = True
text = [s for s in p.sections if s['name']=='.text'][0]
code = p.read(text['va'], text['vsz'])

print('=== CTOR SITES: context around each 007E44F4 install ===')
for va, tag in [(0x457BE2,'ctor A (00457BFD)'),(0x483A40,'ctor B (00483A61)'),
                (0x486AD2,'ctor C (00486AF2)'),(0x4D0740,'static init (004D076D/004D079E)')]:
    print('--- %s @ %08X ---' % (tag, va))
    for ins in md.disasm(p.read(va, 0x50), va):
        mark = ' <<<' if ins.address in (0x457BFD,0x483A61,0x486AF2,0x4D076D,0x4D079E) else ''
        print('  %08X  %-20s %-8s %s%s' % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, mark))
    print()

print('=== direct E8/E9 rel32 call/jmp target == 0045A640 (instruction-boundary, full .text sweep) ===')
TGT = 0x45A640
nins = 0; hits = []
for ins in md.disasm(code, text['va']):
    nins += 1
    if ins.mnemonic in ('call','jmp') and ins.operands and ins.operands[0].type == 2:
        if (ins.address + ins.size + (ins.operands[0].imm & 0xFFFFFFFF)) & 0xFFFFFFFF == TGT:
            hits.append((ins.address, ins.mnemonic, ins.bytes.hex()))
print('scanned %d instructions; direct call/jmp hits to 0045A640: %d' % (nins, len(hits)))
for h in hits: print('   %08X %s %s' % h)

print()
print('=== BASE RATE: S08 static pool n=19, seed 20261119, 2000 draws ===')
# Pool = 19 originally-[静态推断] rows (13 remaining + 6 already merged)
pool = ['0040D250','0045A070','0045A0A0','0045A0C0','0045A640','0045A680','0045AB00',
        '0045AB50','0045AC00','0045AC30','0045AC70','0045AC90','004D24A0','004D2510',
        '004D27B0','004D27D0','004D2810','004D2910','0045A730']
# strict ③b (D-42 合同闭合: guard chain / falsifiable error / >=10-field shape / complete loop I/O)
strict = {'0045A640','0045A680','0045A730','0045AB50','0045AC30','004D24A0','004D2510','004D27D0','004D2810'}
# loose ③b (D-42 宽松: body has any outgoing call, direct or indirect) -- from FEATURES.tsv
loose = {'0045A070','0045A680','0045AB00','0045AB50','0045AC00','0045AC90',
         '004D24A0','004D2510','004D2810','004D2910'}
print('pool n=%d, strict-3b=%d (%.2f%%), loose-3b=%d (%.2f%%)' %
      (len(pool), len(strict), 100*len(strict)/len(pool), len(loose), 100*len(loose)/len(pool)))
print('strict-only: %s' % sorted(strict-loose))
print('loose-only : %s' % sorted(loose-strict))
print('both       : %s' % sorted(strict & loose))

for N in (1, 8):
    rnd = random.Random(20261119)
    n_all_strict = 0; n_all_loose = 0; sum_strict = 0; sum_loose = 0
    TRIALS = 2000
    for _ in range(TRIALS):
        draw = rnd.sample(pool, N)
        ns = sum(1 for x in draw if x in strict)
        nl = sum(1 for x in draw if x in loose)
        sum_strict += ns; sum_loose += nl
        if ns == N: n_all_strict += 1
        if nl == N: n_all_loose += 1
    print('N=%d TRIALS=%d seed=20261119: mean_strict=%.4f mean_loose=%.4f  P(all strict)=%.6f P(all loose)=%.6f' %
          (N, TRIALS, sum_strict/TRIALS, sum_loose/TRIALS, n_all_strict/TRIALS, n_all_loose/TRIALS))
from math import comb
print('exact N=1: P(all strict)=%d/%d=%.6f ; P(all loose)=%d/%d=%.6f' %
      (len(strict),len(pool),len(strict)/len(pool),len(loose),len(pool),len(loose)/len(pool)))
print('exact N=8: P(all strict)=C(%d,8)/C(%d,8)=%.3e ; P(all loose)=C(%d,8)/C(%d,8)=%.3e' %
      (len(strict),len(pool),comb(len(strict),8)/comb(len(pool),8),len(loose),len(pool),comb(len(loose),8)/comb(len(pool),8)))
