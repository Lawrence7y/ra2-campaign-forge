"""Channel B: full .text linear sweep (skipdata=True), save cache to work/sweep.json."""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))
import s08lib as L

t0=time.time()
b=L.Bin()
sw=L.sweep_text(b)
out=os.path.join(os.path.dirname(__file__),'sweep.json')
L.save_sweep(sw,out)
print('saved',out)
print('meta',sw['meta'])
print('elapsed %.1fs'%(time.time()-t0))
