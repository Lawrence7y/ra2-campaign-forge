"""W161 Q3: interval-style resolvability of the 0.65 ms/bullet slope.

INPUTS are the PUBLISHED numbers (R12_FACTS §8.1 / R11_COMMON §3.5) - we do NOT
recompute the regression; we only re-express it against the quantization/step floor.
No p-values / no confidence intervals / no 'significant' (project rule).
"""
import os
OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\W161_bulletcost\EVIDENCE"

# published bucket medians (R12_FACTS §8.1), bin width 25
bmins=[0,25,50,75,100]; bmaxs=[24,49,74,99,124]
bmids=[12,37,62,87,112]
ms=[32.00,33.01,38.55,59.43,85.33]

PUBLISHED_SLOPE=0.6496   # ms/frame per bullet, bullets>=30, n=60
PUBLISHED_RMSE=10.73     # ms
MONO_QUANT=15.625        # ms, t_monotonic quantization
STEP_LO,STEP_HI=25.30,50.40  # 2:1 ms/frame step
STEP_DIFF=STEP_HI-STEP_LO
COMPRESS=0.546           # high-bullet dynamic range is 54.6% of truth (median -45.4%)

def lsq(xs,ys):
    n=len(xs); mx=sum(xs)/n; my=sum(ys)/n
    num=sum((x-mx)*(y-my) for x,y in zip(xs,ys))
    den=sum((x-mx)**2 for x in xs)
    return num/den, my-(num/den)*mx

print("=== 1. bucket medians -> local slopes (bin width 25 bullets) ===")
print("bin        midpoint  ms/frame   jump vs prev   local slope (ms/bullet)")
prev=None
loc=[]
for lo,hi,mid,m in zip(bmins,bmaxs,bmids,ms):
    if prev is None:
        print("  %3d-%3d     %3d      %6.2f       -              -"%(lo,hi,mid,m))
    else:
        j=m-prev; s=j/25.0; loc.append(s)
        print("  %3d-%3d     %3d      %6.2f     %+6.2f         %+6.3f"%(lo,hi,mid,m,j,s))
    prev=m
print("  local-slope range: %.3f .. %.3f  (%.0fx spread)"%(min(loc),max(loc),max(loc)/min(loc)))

print("\n=== 2. whole-range and sub-range least-squares slopes on the 5 bucket medians ===")
s_all,i_all=lsq(bmids,ms)
print("  all 5 bins        : slope=%.4f intercept=%.2f"%(s_all,i_all))
s_ge25,i_ge25=lsq(bmids[1:],ms[1:])
print("  bins b>=25 (4 bins): slope=%.4f intercept=%.2f"%(s_ge25,i_ge25))
s_ge50,i_ge50=lsq(bmids[2:],ms[2:])
print("  bins b>=50 (3 bins): slope=%.4f intercept=%.2f"%(s_ge50,i_ge50))
s_end=(ms[-1]-ms[0])/(bmids[-1]-bmids[0])
print("  endpoint 0->112    : slope=%.4f"%s_end)
print("  PUBLISHED fit (b>=30,n=60): slope=%.4f, RMSE=%.2f"%(PUBLISHED_SLOPE,PUBLISHED_RMSE))
print("  => all of %.4f / %.4f / %.4f / %.4f / %.4f are consistent descriptions of the same staircase"%
      (s_all,s_ge25,s_ge50,s_end,PUBLISHED_SLOPE))

print("\n=== 3. signal size vs measurement floors (x-span ~ 95 bullets for b>=30) ===")
SPAN=125-30
signal=PUBLISHED_SLOPE*SPAN
print("  fitted signal over %d bullets: 0.6496 * %d = %.1f ms/frame"%(SPAN,SPAN,signal))
print("  t_monotonic quantum  = %.3f ms  -> signal = %.2f quanta; per bullet = %.2f%% of a quantum"%
      (MONO_QUANT,signal/MONO_QUANT,100*PUBLISHED_SLOPE/MONO_QUANT))
print("  2:1 step size        = %.2f ms  -> signal = %.2f steps;  per bullet = %.2f%% of a step"%
      (STEP_DIFF,signal/STEP_DIFF,100*PUBLISHED_SLOPE/STEP_DIFF))
print("  RMSE                 = %.2f ms  -> per-point scatter = %.2f of a 2:1 step"%(PUBLISHED_RMSE,PUBLISHED_RMSE/STEP_DIFF))
print("  noise-equivalent slope bandwidth = RMSE/span = %.2f/%d = %.3f ms/bullet"%(PUBLISHED_RMSE,SPAN,PUBLISHED_RMSE/SPAN))
print("  quantum-equivalent slope         = 15.625/span = %.3f ms/bullet"%(MONO_QUANT/SPAN))
print("  step-equivalent slope            = 25.10/span  = %.3f ms/bullet"%(STEP_DIFF/SPAN))

print("\n=== 4. duty-cycle reinterpretation of the slope ===")
print("  if ms/frame is a mixture of %.2f and %.2f ms frames, one bullet changes the"%(STEP_LO,STEP_HI))
print("  slow-frame fraction by 0.6496/%.2f = %.2f%% (per bullet), i.e. ~%.0f bullets flip one full step."%
      (STEP_DIFF,100*PUBLISHED_SLOPE/STEP_DIFF,STEP_DIFF/PUBLISHED_SLOPE))

print("\n=== 5. quantization-compression correction (R12_FACTS §8.1) ===")
print("  high-bullet measured range is %.1f%% of truth -> true slope there ~= %.4f/%.3f = %.3f ms/bullet"%
      (100*COMPRESS,PUBLISHED_SLOPE,COMPRESS,PUBLISHED_SLOPE/COMPRESS))
print("  corrected local slopes at high end: %.3f/%.3f=%.3f and %.3f/%.3f=%.3f"%
      (loc[-2],COMPRESS,loc[-2]/COMPRESS,loc[-1],COMPRESS,loc[-1]/COMPRESS))

print("\n=== 6. verdict quantities ===")
print("  local slope consistent with data: %.3f .. %.3f ms/bullet (measured)"%(min(loc),max(loc)))
print("  compression-corrected high end : up to ~%.3f ms/bullet"%(max(loc)/COMPRESS))
print("  the single fitted 0.6496 lies inside this band and is not separable from it.")

with open(os.path.join(OUT,"Q3_resolvability.txt"),"w",encoding="utf-8") as f:
    f.write("Q3 derivations from published numbers (see console output / this script)\n")
