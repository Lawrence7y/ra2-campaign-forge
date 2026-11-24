"""全 .text 单遍线扫索引（skipdata=True），供回溯/调用者统计使用"""
import pickle, sys
import rt
from rt import im

TEXT_START = 0x401000
TEXT_END = 0x7E038D

def build():
    insns = []
    for i in im.dis(TEXT_START, (TEXT_END-TEXT_START)//1 + 1, stop_ret=False):
        if i.address >= TEXT_END:
            break
        insns.append((i.address, i.size, i.mnemonic, i.op_str, i.bytes.hex()))
    return insns

if __name__ == "__main__":
    insns = build()
    print("insns:", len(insns), "first", hex(insns[0][0]), "last", hex(insns[-1][0]))
    pickle.dump(insns, open("text_index.pkl","wb"))
    # 统计
    from collections import Counter
    c = Counter(i[2] for i in insns)
    print("top mnemonics:", c.most_common(12))
    print(".byte(raw) count:", c.get(".byte", 0))
