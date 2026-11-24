import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S21-F1\work")
import ra2 as R
for va in [0x826198,0x8261A8,0x889F64]:
    try:
        print(f"{va:08X} = {R.cstr(va,60)!r}")
    except Exception as e:
        print(f"{va:08X}: ERR (BSS/no raw) - {e}")
# check coverage for specific entries
print("\n=== coverage check ===")
import io
cov=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
targets={'0046CCD0','0046CC90','0046CE10','0046D070','0052CB90','0046CFC0','0046D330','0046D350','00471500','00471520','0046D360','00470C90','0046FC00'}
with open(cov,encoding='utf-8',errors='replace') as f:
    for line in f:
        p=line.rstrip('\n').split('\t')
        if p[0] in targets:
            print('\t'.join(p[:6]))
