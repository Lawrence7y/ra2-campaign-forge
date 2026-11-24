import sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
cov=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
raw=open(cov,'rb').read()
lines=raw.split(b'\n')
# header bytes
print('header bytes',repr(lines[0][:80]))
# for first 3 data rows show grade field (field index 4) raw bytes
for ln in lines[1:5]:
    parts=ln.split(b'\t')
    if len(parts)>=5:
        print('grade raw bytes:',repr(parts[4]), ' entry',parts[0])
# try encodings on the grade bytes
g=lines[1].split(b'\t')[4]
for enc in ['utf-8','gbk','gb18030','big5','cp936','latin-1']:
    try: print(enc, repr(g.decode(enc)))
    except Exception as e: print(enc,'ERR',str(e)[:50])
