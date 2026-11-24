import sys,io,os,glob
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
files=glob.glob(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\**\coverage.tsv',recursive=True)
for f in sorted(files,key=os.path.getmtime,reverse=True)[:6]:
    print(os.path.getmtime(f),os.path.getsize(f),f)
