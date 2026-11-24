# 19 capstone 5.0.7 op.index self-check

capstone 5.0.7 x86: operand has NO .index attribute; mem index is op.mem.index (no index => int 0, NOT None).
This card uses raw-byte E8+rel32 (not operand-None filtering), so the trap does not apply to the scan; self-check still performed.

known-positive: E8 10 00 00 00 @ 0x500000 -> call 0x500015 ; size=5
  op.type=2 hasattr(op,'index')=False
target check 0x500000+5+0x10=0x500015 -> PASS
call [eax] (FF 10): op.mem.index=0 (int 0) ; op.index attr=False
