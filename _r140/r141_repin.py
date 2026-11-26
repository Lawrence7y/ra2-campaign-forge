import os, hashlib, re, json, io
D='/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/'
BAKD='/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14_real/R17_LEAD_BASELINE/'
A=1
def chk(n,c,x=''):
    global A
    print('  %s %-72s %s'%('PASS' if c else 'FAIL',n,x)); assert c,n; A+=1

CP=D+'check_disc.py'; DR=D+'DISC_RECHECK.tsv'; DU=D+'DISC_UNVERIFIABLE.tsv'
cpr=open(CP,'rb').read(); drr=open(DR,'rb').read(); dur=open(DU,'rb').read()
chk('all three CR-free', cpr.count(b'\r')==0 and drr.count(b'\r')==0 and dur.count(b'\r')==0)
chk("GATE_VER already R140 (from the previous step)", b"GATE_VER = 'R140'" in cpr)
chk("DISC_RECHECK row20 already R140", b"grep=(?m)^GATE_VER = 'R140'" in drr)
chk("DISC_UNVERIFIABLE row20 already R140", b"grep=(?m)^GATE_VER = 'R140'" in dur)

# recompute C7d exactly as the gate does: rows from DISC_RECHECK, blob = id\tcol5\tcol6
def parse_rows(blob):
    txt=blob.decode('utf-8')
    out=[]
    for ln in txt.split('\n'):
        if not ln.strip(): continue
        r=ln.split('\t')
        out.append(r)
    return out
rows=parse_rows(drr)
hdr=rows[0]
chk('header has 7 columns', len(hdr)==7, str(len(hdr)))
data=[r for r in rows[1:] if len(r)==7]
chk('31 data rows', len(data)==31, str(len(data)))
blob='\n'.join('%s\t%s\t%s'%(r[0],r[4].strip(),r[5].strip()) for r in data)
newc7d=hashlib.sha256(blob.encode('utf-8')).hexdigest()
print('      C7d (id,col5,col6) normalized sha256 = %s' % newc7d)
row20=[r for r in data if r[0]=='20']
chk('exactly one row id 20', len(row20)==1)
h20=hashlib.sha256(('%s\t%s\t%s'%(row20[0][0],row20[0][4].strip(),row20[0][5].strip())).encode('utf-8')).hexdigest()
print('      row 20 sha256 = %s' % h20)
old_row20_sha='85e65454f57cc13731c68010c77a1d2021bb429a862afb12c9829e85b7e2f9e9'
chk('row 20 sha actually changed (its col6 text changed)', h20!=old_row20_sha)

newcp=cpr.decode('utf-8')
chk('old C7_TEXT_SHA256 value present', "C7_TEXT_SHA256 = 'f493f64cfdd8ef688e18f31b527762ac88fe75f9a734091b88daca1706f60483'" in newcp)
newcp=newcp.replace("C7_TEXT_SHA256 = 'f493f64cfdd8ef688e18f31b527762ac88fe75f9a734091b88daca1706f60483'",
                    "C7_TEXT_SHA256 = '%s'"%newc7d)
chk('C7_TEXT_SHA256 repinned to the normalized value', newc7d in newcp)
chk('old row-20 pin present', "'20': '%s'"%old_row20_sha in newcp)
newcp=newcp.replace("'20': '%s'"%old_row20_sha, "'20': '%s'"%h20)
chk('C7_ROW_SHA["20"] repinned', "'20': '%s'"%h20 in newcp)
chk('no other row sha touched', newcp.count("'21': 'ad68a5c24394fb293c08dd336283e9c1ffe7c56ca052349b69c4bdf6be0f80ff'")==1)
newcpr=newcp.encode('utf-8')
chk('check_disc.py still CR-free', newcpr.count(b'\r')==0)

for path,blobn,old in ((CP,newcpr,cpr),):
    bak=BAKD+os.path.basename(path)+'.before_R140_repin_20261126_2112.bak'
    fd=os.open(bak, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o644); os.write(fd,old); os.close(fd)
    chk('backup wx created', os.path.getsize(bak)==len(old))
    open(path,'wb').write(blobn)
    chk('readback identical', open(path,'rb').read()==blobn)
print()
print('check_disc.py: %d -> %d B' % (len(cpr),len(newcpr)))
print('ASSERTIONS: %d PASS' % (A-1))
json.dump({'c7d':newc7d,'row20':h20}, open('/home/t628/projects/ra2-campaign-forge/_r140/r141_repin.json','w'), indent=1)
