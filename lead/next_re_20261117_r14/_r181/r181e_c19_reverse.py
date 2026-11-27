import hashlib, io, os, shutil, subprocess, sys, tempfile
ROOT='/home/t628/projects/ra2-campaign-forge'; TIER=os.path.join(ROOT,'lead','next_re_20261117_r14')
GATE=os.path.join(TIER,'check_disc.py')
PTR=os.path.join(TIER,'FACT_INDEX_CURRENT.md')
fails=[]
def ck(n,c,d=''):
    print(('  PASS  ' if c else '  FAIL  ')+n+(('  '+str(d)) if d else ''))
    if not c: fails.append(n)
def run_in_mirror(mutate):
    """镜像整个 ROOT 的相关子树（只软链），在镜像内施加 mutate，跑生产的 check_disc（软链副本）。"""
    tmpd=tempfile.mkdtemp(prefix='r181neg_')
    try:
        sbox=os.path.join(tmpd,'lead','next_re_20261117_r14'); os.makedirs(sbox)
        for n in sorted(os.listdir(TIER)):
            p=os.path.join(TIER,n)
            if n=='check_disc.py': continue
            os.symlink(p,os.path.join(sbox,n))
        os.symlink(os.path.join(ROOT,'lead','GOAL_THREE_TARGETS_20261018.md'),
                   os.path.join(tmpd,'lead','GOAL_THREE_TARGETS_20261018.md'))
        os.makedirs(os.path.join(tmpd,'_r160'))
        os.symlink(os.path.join(ROOT,'_r160','facts_floors.py'),os.path.join(tmpd,'_r160','facts_floors.py'))
        shutil.copy2(GATE, os.path.join(sbox,'check_disc.py'))
        mutate(tmpd, sbox)
        env=dict(os.environ); env['PYTHONDONTWRITEBYTECODE']='1'
        p=subprocess.run([sys.executable,os.path.join(sbox,'check_disc.py')],
                         capture_output=True,text=True,cwd=sbox,env=env,timeout=300)
        o=p.stdout+p.stderr
        fs=[l.strip() for l in o.split('\n') if l.strip().startswith('FAIL')]
        return p.returncode, fs, o
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)

print('--- 基线（无改动）：确认 C19 在镜像里绿 ---')
rc,fs,o = run_in_mirror(lambda t,s: None)
# S-675：首版 N0 断言「无改动时 FAIL 0」⇒ 假 FAIL。镜像里 id 31 的产物用相对路径，
# 软链镜像下 FILE_MISSING 是**镜像环境**造成的（旧版同样 3 条），不是 C19 造成的。
# 正确判据是差分：无改动时 FAIL 集合里不得出现任何 C19 条目。
ck('N0 无改动时 FAIL 集合不含任何 C19 条目', not [f for f in fs if 'C19' in f],
   (rc, [f[:60] for f in fs]))
ck('N0b 无改动时 C19 ok 行在场', 'C19 fact-layer link: ok(' in o)

print('--- 反向 1：指针 sha 末位改坏 ⇒ C19 必须 FAIL ---')
def m1(t,s):
    txt=io.open(os.path.join(s,'FACT_INDEX_CURRENT.md'),encoding='utf-8',newline='').read()
    import re
    m=re.search(r'\| sha256 \| ([0-9a-f]{64}) \|', txt)
    bad=m.group(1)[:-1]+('0' if m.group(1)[-1]!='0' else '1')
    os.unlink(os.path.join(s,'FACT_INDEX_CURRENT.md'))
    io.open(os.path.join(s,'FACT_INDEX_CURRENT.md'),'w',encoding='utf-8',newline='').write(
        txt.replace(m.group(1),bad))
rc1,fs1,o1 = run_in_mirror(m1)
ck('N1 指针 sha 末位改坏 ⇒ exit 1', rc1==1, rc1)
ck('N2 ⇒ 出现 C19 pointer sha FAIL', any('C19 pointer sha' in f for f in fs1), [f[:90] for f in fs1])

print('--- 反向 2：指针字节数改坏 ⇒ C19 必须 FAIL ---')
def m2(t,s):
    txt=io.open(os.path.join(s,'FACT_INDEX_CURRENT.md'),encoding='utf-8',newline='').read()
    os.unlink(os.path.join(s,'FACT_INDEX_CURRENT.md'))
    io.open(os.path.join(s,'FACT_INDEX_CURRENT.md'),'w',encoding='utf-8',newline='').write(
        txt.replace('| 字节数 | 133310 |','| 字节数 | 133311 |'))
rc2,fs2,o2 = run_in_mirror(m2)
ck('N3 指针字节数改坏 ⇒ exit 1', rc2==1, rc2)
ck('N4 ⇒ 出现 C19 pointer bytes FAIL', any('C19 pointer bytes' in f for f in fs2), len(fs2))

print('--- 反向 3：指针版本目录改坏 ⇒ C19 必须 FAIL（这条是 gate_runner 没有的）---')
def m3(t,s):
    txt=io.open(os.path.join(s,'FACT_INDEX_CURRENT.md'),encoding='utf-8',newline='').read()
    os.unlink(os.path.join(s,'FACT_INDEX_CURRENT.md'))
    io.open(os.path.join(s,'FACT_INDEX_CURRENT.md'),'w',encoding='utf-8',newline='').write(
        txt.replace('R17_R131_FACTINDEX_V563','R17_R131_FACTINDEX_V562'))
rc3,fs3,o3 = run_in_mirror(m3)
ck('N5 版本目录改坏 ⇒ exit 1', rc3==1, rc3)
# S-683：N6 的断言过窄。v2 改为从指针「相对路径」解析靶子后，把整个指针里的 V563 换成
# V562 会先撞上「相对路径不存在」这条（更早、更正确的失败点），而不是「目录字段不一致」。
# 真正只改目录字段、保留正确相对路径的工况由 T1a 覆盖（那里两版都报 version dir）。
ck('N6 ⇒ 出现 C19 相对路径/版本目录 FAIL（任一即可，v2 会先报相对路径不存在）',
   any(('C19 pointer version dir' in f) or ('C19 pointer relative path' in f) for f in fs3),
   [f[:80] for f in fs3 if 'C19' in f][:2])

print('--- 反向 4：指针文件删除 ⇒ C19 必须 FAIL（不得跳过）---')
def m4(t,s):
    os.unlink(os.path.join(s,'FACT_INDEX_CURRENT.md'))
rc4,fs4,o4 = run_in_mirror(m4)
ck('N7 指针删除 ⇒ exit 1', rc4==1, rc4)
ck('N8 ⇒ 出现 C19 pointer file missing FAIL', any('C19 pointer file missing' in f for f in fs4), len(fs4))

print('--- 反向 5：台账改 1 字节 ⇒ C19 必须 FAIL（事实层常量与实物脱钩）---')
def m5(t,s):
    p=os.path.join(s,'R17_R131_FACTINDEX_V563')
    os.unlink(p); shutil.copytree(os.path.join(TIER,'R17_R131_FACTINDEX_V563'), p)
    f=os.path.join(p,'FACT_INDEX.tsv')
    b=bytearray(open(f,'rb').read()); b[200]=(b[200]+1)%256
    open(f,'wb').write(bytes(b))
rc5,fs5,o5 = run_in_mirror(m5)
ck('N9 台账改 1 字节 ⇒ exit 1', rc5==1, rc5)
ck('N10 ⇒ 出现 C19 facts CUR_SHA256 FAIL', any('C19 facts CUR_SHA256' in f for f in fs5), len(fs5))

print('--- 反向 6：facts_floors.py 的 CUR_SHA256 与现盘脱钩 ⇒ C19 必须 FAIL ---')
def m6(t,s):
    p=os.path.join(t,'_r160','facts_floors.py')
    os.unlink(p)
    txt=io.open(os.path.join(ROOT,'_r160','facts_floors.py'),encoding='utf-8',newline='').read()
    io.open(p,'w',encoding='utf-8',newline='').write(
        txt.replace("CUR_SHA256 = '28423e7928d8414216b6a09f8ea56ef60d484dbd121cf9e5d673ffc3bc45db46'",
                    "CUR_SHA256 = '0000000000000000000000000000000000000000000000000000000000000000'"))
rc6,fs6,o6 = run_in_mirror(m6)
ck('N11 facts 常量脱钩 ⇒ exit 1', rc6==1, rc6)
ck('N12 ⇒ 出现 C19 facts CUR_SHA256 FAIL', any('C19 facts CUR_SHA256' in f for f in fs6), len(fs6))

print('--- 反向 7：facts_floors.py 文件删除 ⇒ C19 必须 FAIL ---')
def m7(t,s):
    os.unlink(os.path.join(t,'_r160','facts_floors.py'))
rc7,fs7,o7 = run_in_mirror(m7)
ck('N13 facts_floors 删除 ⇒ exit 1', rc7==1, rc7)
ck('N14 ⇒ 出现 C19 facts_floors.py missing FAIL', any('C19 facts_floors.py missing' in f for f in fs7), len(fs7))

print('--- 汇总 ---')
print('PASS=%d FAIL=%d' % (0,0) if False else 'FAILs=%d' % len(fails))
if fails: print(repr(fails)); sys.exit(1)
print('[exit 0]')
