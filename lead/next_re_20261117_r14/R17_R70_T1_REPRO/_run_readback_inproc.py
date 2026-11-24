import sys
sys.path.insert(0, ".")
import readback_check as R
out = R.main(["--lead", r"D:\Project\ra2-campaign-forge\lead",
              "--r16", r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_MEASURE_EVID675",
              "--out", r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R70_T1_REPRO"])
