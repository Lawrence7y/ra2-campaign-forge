import sys,io,json
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
BASE=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_DIRECT'
d=json.load(open(BASE+r'\EVIDENCE\direct_analysis.json',encoding='utf-8'))
v=json.load(open(BASE+r'\EVIDENCE\vref_analysis.json',encoding='utf-8'))
results=d['results']
with open(BASE+r'\VIRTUAL_SKIPPED.tsv','w',encoding='utf-8',newline='') as f:
    f.write('entry\tname\tone_line_semantics\tgrade\tevidence_path\trdata_dword_refs\t环123(盘上既有)\t环4状态\t本卡处置\n')
    for i,r in enumerate(results):
        refs=v[i].get('dword_refs',{}); rdata=refs.get('.rdata',0)
        e123='盘上[静态推断]: entry在atlas(环1); name来自vt/rdata(环2); semantics='+r['semantics'][:60]+'(环3)'
        f.write('%s\t%s\t%s\t%s\t%s\t%d\t%s\t无direct call(全.text E8边界扫0命中,raw E8弱扫0命中),仅虚表可达\t保留[静态推断],不升格\n'%(
            r['entry'],r['name'],r['semantics'],r['grade'],r['evidence'],rdata,e123))
print('VIRTUAL_SKIPPED.tsv rows',len(results))
