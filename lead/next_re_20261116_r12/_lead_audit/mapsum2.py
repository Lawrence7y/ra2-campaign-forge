base=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W110_crash\out"
p1=base+r"\_archive_range1\trip_range1_r1\installed_inputs\RA2F_M1.MAP"
p2=base+r"\_archive_c2\trip_c2_near_r1\installed_inputs\RA2F_M1.MAP"
a=open(p1,'rb').read(); b=open(p2,'rb').read()
print('len a=%d b=%d  diff=%+d' % (len(a),len(b),len(b)-len(a)))
# 用 difflib 找差异块
import difflib
sa=a.decode('latin-1','replace'); sb=b.decode('latin-1','replace')
sm=difflib.SequenceMatcher(None, sa, sb, autojunk=False)
n=0
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': continue
    n+=1
    if n<=8:
        print('%-8s a[%d:%d]=%r  b[%d:%d]=%r' % (tag,i1,i2,sa[i1:i2][:120],j1,j2,sb[j1:j2][:120]))
print('total diff blocks =', n)
