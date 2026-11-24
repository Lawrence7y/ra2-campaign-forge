import sys, core

def dumpf(va, n=120, label=""):
    print("=== %s %08X ===" % (label, va))
    ins = core.fn(va, n)
    print(core.render(ins))
    print("--- end at %08X ---" % (ins[-1].address + ins[-1].size if ins else va))
    return ins

if __name__ == "__main__":
    for a in sys.argv[1:]:
        dumpf(int(a, 16), 200)
