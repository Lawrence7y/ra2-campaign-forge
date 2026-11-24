"""逐行落盘 11 个 entry 的函数体 + 机器提取关键指令（独立实现）"""
import sys, re
import rt
from rt import im, IB

ENTRIES = ["006C5210","006C5390","006C5510","006C5690","006C5810","006C5990",
           "006C5B10","006C5C90","006C5E10","006C5F90","006C6110"]

def body(entry):
    va = int(entry, 16)
    insns = list(im.dis(va, 300, stop_ret=False))
    # 函数边界：遇到 ret 且其后紧跟 nop 填充 => 函数结束
    for k, i in enumerate(insns):
        if i.mnemonic.startswith("ret"):
            nxt = insns[k+1:k+3]
            if nxt and all(x.mnemonic == "nop" for x in nxt):
                return insns[:k+1]
    return insns

def main():
    for e in ENTRIES:
        insns = body(e)
        lines = [f"# entry {e}  len={insns[-1].address+insns[-1].size-int(e,16)} bytes  insns={len(insns)}", ""]
        for i in insns:
            lines.append(f"{i.address:08X}  {i.bytes.hex():<22} {i.mnemonic:<7} {i.op_str}")
        open(f"body_{e}.txt","w",encoding="utf-8").write("\n".join(lines)+"\n")
        print(f"--- {e} ({len(insns)} insns) ---")
        for i in insns:
            print(f"{i.address:08X}  {i.bytes.hex():<22} {i.mnemonic:<7} {i.op_str}")
        print()

if __name__ == "__main__":
    main()
