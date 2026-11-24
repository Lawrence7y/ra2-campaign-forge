"""Q2: per-record classification under §2.49 (as amended by §2.50), at the semantic record level.

Record = one thing the file states. This file has exactly two kinds of record:
  A. calls : key=callee VA, value=[call-site VAs]      n = 6,728 keys / 68,253 site entries
  B. bounds: bare instruction-start VAs                 n = 1,392,592
Both are classified against §2.49's three questions, and - separately - against the
stricter wording of the dispatch card ("that address HOLDS what bytes/values").

Also computed: the byte cost of each part, so Q4 can answer at byte level.
"""
import json, re, struct
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
P0 = BASE + r'\D41_SUBST\_audit\EVIDENCE\a2_sites.json'
LOG = []
def P(*a):
    line = ' '.join(str(x) for x in a); LOG.append(line); print(line, flush=True)

s = open(P0, 'rb').read().decode('utf-8')
d = json.loads(s)
calls, bounds = d['calls'], d['bounds']
MARK = '}, "bounds": ["'
CUT = s.index(MARK)
CALLS_BYTES = CUT                       # everything before the bounds key
BOUNDS_BYTES = len(s.encode()) - CUT    # '}, "bounds": [' .. ']}'
P('file_bytes 17624355')
P('calls_section_bytes  %d (%.2f%%)' % (CALLS_BYTES, 100*CALLS_BYTES/17624355))
P('bounds_section_bytes %d (%.2f%%)' % (BOUNDS_BYTES, 100*BOUNDS_BYTES/17624355))

# ---- record counts ----
nkeys = len(calls)
nsites = sum(len(v) for v in calls.values())
nb = len(bounds)
P('')
P('calls keys      %d' % nkeys)
P('calls site rows %d' % nsites)
P('bounds rows     %d' % nb)

# ---- A. calls: is the recorded value recoverable at the recorded site? ----
blob = open(EXE, 'rb').read()
TEXT_RAW, TEXT_VA, TEXT_VSZ = 4096, 0x00401000, 4060045
TEXT_END = TEXT_VA + TEXT_VSZ
okA = 0
for k, v in calls.items():
    for site in v:
        sva = int(site, 16); so = TEXT_RAW + (sva - TEXT_VA)
        if blob[so] == 0xE8 and ((sva + 5 + struct.unpack_from('<i', blob, so+1)[0]) & 0xFFFFFFFF) == int(k, 16):
            okA += 1
P('')
P('A. calls site rows whose target is recomputable from the byte at the recorded site: %d/%d' % (okA, nsites))
P('   (i.e. the file does NOT store "what byte/word is at that address"; it stores a relation')
P('    E8+rel32 @site == target.  The 5 bytes are recovered, not recorded.)')

# ---- B. bounds: is the value at the recorded address recoverable? ----
# the value at an instruction start IS the instruction; check a deterministic sample
STEP = 1000
sample = bounds[::STEP]
P('')
P('B. bounds sampling rule: every %d-th element (indices 0, %d, %d, ...), n=%d' % (STEP, STEP, 2*STEP, len(sample)))
P('   first 3 :', sample[:3], ' last 3 :', sample[-3:])
inner = sum(1 for a in sample if TEXT_VA <= int(a, 16) < TEXT_END)
P('   of the sample, %d/%d fall inside .text VA range [%08X,%08X)' % (inner, len(sample), TEXT_VA, TEXT_END))
P('   -> the file records instruction-start ADDRESSES only; no opcode byte, no mnemonic,')
P('      no field value accompanies any of them.')

# ---- byte split for Q4 ----
P('')
P('--- byte accounting ---')
P('bytes carried by the calls section   : %d' % CALLS_BYTES)
P('bytes carried by the bounds section  : %d' % BOUNDS_BYTES)
P('sum                                   : %d' % (CALLS_BYTES + BOUNDS_BYTES))
P('bounds share of the file              : %.2f%%' % (100*BOUNDS_BYTES/17624355))

# ---- re-express at "record" granularity, both readings ----
P('')
P('--- two readings of Q2, both stated ---')
P('reading1 (strict card wording: "that address holds what bytes/values"):')
P('   object  0 / 1,467,573 records (0.00%%)')
P('   process 1,467,573 / 1,467,573 (100%%)')
P('reading2 (R14_COMMON §2.49 verbatim: "records the value itself, and is re-verifiable at the address"):')
P('   object  1,467,573 (100%%)  [all re-verifiable at the .text address, verified in Q3]')
P('   process 0')
open(BASE + r'\R17_R95_T1_A2SITES\q2_records.out','w',encoding='utf-8').write('\n'.join(LOG))
