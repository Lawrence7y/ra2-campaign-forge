import os, hashlib, re, json
D='/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/'
BAKD='/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14_real/R17_LEAD_BASELINE/'
A=1
def chk(n,c,x=''):
    global A
    print('  %s %-72s %s'%('PASS' if c else 'FAIL',n,x)); assert c,n; A+=1

CP=D+'check_disc.py'
raw=open(CP,'rb').read()
chk('check_disc.py CR 0', raw.count(b'\r')==0)
s=raw.decode('utf-8')
chk("GATE_VER is 'R139'", "GATE_VER = 'R139'" in s)
old_floors="    142: 3404, 143: 3039,"
chk('floors tail line present', old_floors in s)
# add 144: 4010 = half of 8021 (the new 2.144 body)
new_floors="    142: 3404, 143: 3039, 144: 4010,"
s1=s.replace(old_floors,new_floors)
chk('floors line replaced', s1!=s and new_floors in s1)
chk('144 floor is half of the measured 8021 B body', 4010==8021//2, '8021//2=%d'%(8021//2))
s2=s1.replace("GATE_VER = 'R139'","GATE_VER = 'R140'")
chk('GATE_VER bumped to R140', "GATE_VER = 'R140'" in s2)

# recompute C16_FLOORS_SHA256 the same way the gate does
m=re.search(r'C16_FLOORS = \{(.*?)\n\}', s2, re.S)
body=m.group(1)
pairs=[(int(a),int(b)) for a,b in re.findall(r'(\d+)\s*:\s*(\d+)', body)]
chk('parsed 138 floor pairs (7..144)', len(pairs)==138, str(len(pairs)))
chk('ids are exactly 7..144 with 143 present and 144 added', sorted(k for k,_ in pairs)==list(range(7,145)))
d=dict(pairs)
norm='\n'.join('%d:%d' % (k, d[k]) for k in sorted(d))
newsha=hashlib.sha256(norm.encode()).hexdigest()
print('      recomputed C16_FLOORS_SHA256 = %s' % newsha)
chk('recomputed sha differs from the old pin', newsha!='9091db94ba4c5543c9fca635cc6aad0efea2d8dc475f2bd6e85183f5440ff14b')
s3=re.sub(r"C16_FLOORS_SHA256 = '[0-9a-f]{64}'",
          "C16_FLOORS_SHA256 = '%s'"%newsha, s2, count=1)
chk('C16_FLOORS_SHA256 repinned', newsha in s3)

# DISC_RECHECK row 20 must mirror GATE_VER text verbatim (C12b requires frozen==live on expr)
DR=D+'DISC_RECHECK.tsv'
drraw=open(DR,'rb').read()
chk('DISC_RECHECK exists', len(drraw)>0)
drs=drraw.decode('utf-8')
chk("DISC_RECHECK row 20 carries GATE_VER = 'R139'", "grep=(?m)^GATE_VER = 'R139'" in drs)
drs2=drs.replace("grep=(?m)^GATE_VER = 'R139'","grep=(?m)^GATE_VER = 'R140'")
chk('row 20 synced to R140', "grep=(?m)^GATE_VER = 'R139'" not in drs2 and "grep=(?m)^GATE_VER = 'R140'" in drs2)
chk('only one occurrence changed', drs.count("grep=(?m)^GATE_VER = 'R139'")==1)
newdr=drs2.encode('utf-8')

# C7d fingerprint + FREEZE_SHA256 must be repinned after the .tsv edits
newc7d=hashlib.sha256(newdr).hexdigest()
print('      new DISC_RECHECK sha256 = %s' % newc7d)
DU=D+'DISC_UNVERIFIABLE.tsv'
duraw=open(DU,'rb').read()
dus=duraw.decode('utf-8')
chk("DISC_UNVERIFIABLE row 20 carries GATE_VER = 'R139'", "grep=(?m)^GATE_VER = 'R139'" in dus)
dus2=dus.replace("grep=(?m)^GATE_VER = 'R139'","grep=(?m)^GATE_VER = 'R140'")
chk('unverifiable row 20 synced', "grep=(?m)^GATE_VER = 'R139'" not in dus2)
newdu=dus2.encode('utf-8')
newfreeze=hashlib.sha256(newdu).hexdigest()
print('      new DISC_UNVERIFIABLE sha256 = %s' % newfreeze)

s4=s3.replace("C7_TEXT_SHA256 = '97299336fc04a8703d1b11c20461ac88dfdbd2ed482eb76e216e6f10095c344b'",
              "C7_TEXT_SHA256 = '%s'"%newc7d)
chk('C7_TEXT_SHA256 repinned', newc7d in s4)
s5=s4.replace("FREEZE_SHA256 = '5b9455a0973e679b628f177a818e149c6404b186feac3eb959729c62fbb8ab46'",
              "FREEZE_SHA256 = '%s'"%newfreeze)
chk('FREEZE_SHA256 repinned', newfreeze in s5)
newcp=s5.encode('utf-8')
chk('check_disc.py CR still 0', newcp.count(b'\r')==0)
# the DISC_RECHECK self-describing row must also carry the new C7d constant? check gate expectation
print()
print('  changes: check_disc.py %d -> %d B ; DISC_RECHECK %d -> %d B ; DISC_UNVERIFIABLE %d -> %d B'
      % (len(raw),len(newcp),len(drraw),len(newdr),len(duraw),len(newdu)))

for path,blob,old in ((CP,newcp,raw),(DR,newdr,drraw),(DU,newdu,duraw)):
    bak=BAKD+os.path.basename(path)+'.before_R140_gate_20261126_2108.bak'
    fd=os.open(bak, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o644); os.write(fd,old); os.close(fd)
    chk('backup wx created for %s'%os.path.basename(path), os.path.getsize(bak)==len(old))
    open(path,'wb').write(blob)
    chk('readback %s'%os.path.basename(path), open(path,'rb').read()==blob)
print()
print('ASSERTIONS: %d PASS' % (A-1))
json.dump({'c16':newsha,'c7d':newc7d,'freeze':newfreeze}, open('/home/t628/projects/ra2-campaign-forge/_r140/r141_gate.json','w'), indent=1)
