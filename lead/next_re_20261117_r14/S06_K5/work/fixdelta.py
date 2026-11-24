
import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import k5_lib as K
CARD=K.CARD
sem=("CellClass::SpreadTiberiumToNeighbor: one stack bool arg (force). If force==0 gate chain: byte0 of RulesClass ptr loaded from [0xA8B230] & 0x80 != 0; "
     "overlay type [cell+0x44] -> typeIndex via 0x5FDD20 (>=0); cell density [cell+0x11E] > typeIndex/2; cell [cell+0x11C]==0; "
     "type float [type+0xA0] >= 1e-5 (f168e388b5f8e43e); cell dword [cell+0xE4]==0. "
     "force!=0 bypasses gates and maps typeIndex -1 to 0. Then 8-neighbor loop (ebx=0..7, dir word-pair table 0x89F688, GetCell 0x5657A0, canSpread 0x4838E0) "
     "finds first acceptable neighbor and calls IncreaseTiberium(typeIndex,3) @0x4838C0 push 3 + 0x4838C5 call 0x487190; "
     "returns the callee al (NOT hardcoded true); all gate/no-neighbor fail paths return 0.")
p=CARD/'coverage_delta.tsv'
with p.open('w',encoding='utf-8',newline='') as f:
    f.write('\t'.join(['00483780','S06','CellClass::SpreadTiberiumToNeighbor',sem,'[已证]','EVIDENCE/growth_neighbors_proof.txt'])+'\n')
print("delta rewritten with precise rules deref")
print(p.read_text(encoding='utf-8'))
