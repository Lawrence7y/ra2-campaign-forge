// S17-F1 Channel-2 (Ghidra SLEIGH) independent disassembly dump.
// Run with analyzeHeadless -noanalysis. Reads raw instructions at known VAs.
// @category S17F1
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;

public class S17F1Dump extends GhidraScript {
    void dumpRange(long start, long end, String label) throws Exception {
        println("=== " + label + " [0x" + Long.toHexString(start) + ",0x" + Long.toHexString(end) + ") ===");
        Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(start);
        Address e = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(end);
        int n = 0;
        while (a != null && a.compareTo(e) < 0 && n < 2000) {
            Instruction ins = getInstructionAt(a);
            if (ins == null) {
                // try to disassemble at a (returns boolean success)
                disassemble(a);
                ins = getInstructionAt(a);
            }
            if (ins == null) { println("0x" + a.toString() + "  <no decode>"); a = a.add(1); n++; continue; }
            String bytes = "";
            byte[] bs = ins.getBytes();
            for (byte b : bs) bytes += String.format("%02x", b & 0xff);
            println("0x" + ins.getAddress().toString() + "  " + String.format("%-18s", bytes) + " " + ins.toString());
            a = ins.getAddress().add(ins.getLength());
            n++;
        }
        println("--- end " + label + " (n=" + n + ") ---");
    }

    @Override
    public void run() throws Exception {
        println("IMAGE_BASE=0x" + currentProgram.getImageBase().toString());
        dumpRange(0x67D300L, 0x67D3A0L, "Save_Core head (prologue+first vector)");
        dumpRange(0x67DF00L, 0x67DF40L, "block#1 call site");
        dumpRange(0x67E3A0L, 0x67E440L, "Save_Core tail (block#35+skirmish+ret)");
        dumpRange(0x67FDF0L, 0x67FE70L, "template block fn #1 (full 127B)");
        dumpRange(0x6CF240L, 0x6CF2C0L, "Here_I_Am full");
        dumpRange(0x6CF350L, 0x6CF410L, "Reset (restore pass) full");
        dumpRange(0x55DBCDL, 0x55DC9AL, "gating chain");
        dumpRange(0x83D560L, 0x83D568L, "magic bytes");
        println("### S17F1DUMP DONE");
    }
}
