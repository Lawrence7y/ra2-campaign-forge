# -*- coding: utf-8 -*-
"""Q5: can '件数与字节必须同时给出' be machine-checked? Test a concrete linter on F24 statement."""
import csv, io, json, os, re
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
OUT  = os.path.join(BASE, r'R17_R94_T4_AUDIT53\analysis4.json')
with io.open(os.path.join(BASE,r'R17_R93_FACTINDEX_V527\FACT_INDEX.tsv'), encoding='utf-8', newline='') as f:
    fi = list(csv.reader(f, delimiter='\t'))
f24 = [r for r in fi if r[0].strip()=='F24'][0]
stmt = f24[1]

# canonical corpus-value registry (count -> bytes) drawn from F24/§2.53 themselves
CANON = {4413:744172839, 4518:724479859, 3786:714228639, 627:29944200,
         732:10251220, 24723:1589964358, 24478:1558495337, 14548:548531103,
         378:100948978, 18712:0}

def fmt(n): return format(n, ',')
def has_bytes(sent, b):
    return (fmt(b) in sent) or (str(b) in sent)

# check 1: canonical pair co-occurrence in the SAME sentence (。；\n delimiters)
sentences = [s for s in re.split(r'[。；\n]', stmt) if s.strip()]
violations_same_sentence = []
for i,sent in enumerate(sentences):
    for m in re.finditer(r'(\d[\d,]*)\s*(?:件|文件)', sent):
        c = int(m.group(1).replace(',',''))
        if c in CANON and CANON[c] and not has_bytes(sent, CANON[c]):
            violations_same_sentence.append({'sent_idx':i,'count':c,'expected_bytes':CANON[c],'sent_tail':sent[-90:]})

# check 2: pair present ANYWHERE in statement (the lead's actual constraint for the canonical value)
pair_4413 = has_bytes(stmt,744172839) and ('4,413' in stmt or '4413' in stmt)
pair_4518 = has_bytes(stmt,724479859) and ('4,518' in stmt or '4518' in stmt)

# check 3: does any bare "N 件/文件" appear with NO ' B' within a window of 60 chars?
bare=[]
for m in re.finditer(r'(\d[\d,]*)\s*(?:件|文件)', stmt):
    c=int(m.group(1).replace(',',''))
    window=stmt[m.start():m.start()+80]
    if ' B' not in window:
        bare.append({'count':c,'context':stmt[max(0,m.start()-30):m.start()+70]})

res={
 'statement_len':len(stmt),
 'check1_same_sentence_pairs':{
    'n_sentences':len(sentences),
    'n_violations':len(violations_same_sentence),
    'violations':violations_same_sentence[:10],
    'verdict':'FAIL' if violations_same_sentence else 'PASS',
 },
 'check2_canonical_pair_anywhere':{
    'new_4413_744172839':pair_4413,
    'old_4518_724479859':pair_4518,
    'verdict':'PASS' if (pair_4413 and pair_4518) else 'FAIL',
 },
 'check3_bare_counts_no_B_in_80char_window':{
    'n':len(bare),'samples':bare[:8],
 },
 'conclusion':'Check2 (canonical pair anywhere) is cleanly executable and passes on current F24. '
              'Check1 (every count paired in same sentence) is executable but FAILS on component prose '
              '(3,786 件 / 732 件 in the 口径 clause) -- so a naive "every 件 must have B" rule is too strict; '
              'must scope to a canonical value registry.',
}
with io.open(OUT,'w',encoding='utf-8') as f: json.dump(res,f,ensure_ascii=False,indent=2)
print('OK',OUT)
