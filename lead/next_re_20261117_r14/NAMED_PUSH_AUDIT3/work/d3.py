from core import *

def show(lo, hi, title):
    print("=== %s [%08X,%08X) ===" % (title, lo, hi))
    for l in dis_lines(lo, hi):
        print(l)
    print()

show(0x00747180, 0x00747210, "region A around 007471C1")
show(0x00747290, 0x00747340, "region B around 007472CF/007472F8")
show(0x00748000, 0x00748080, "region C around 0074803F")
