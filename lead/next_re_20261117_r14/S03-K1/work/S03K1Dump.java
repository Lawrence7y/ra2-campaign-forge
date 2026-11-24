// S03-K1 Channel-B independent disassembly via Ghidra SLEIGH (no capstone).
// Run with analyzeHeadless -noanalysis. Reads raw instructions at known VAs.
// @category S03K1
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;

public class S03K1Dump extends GhidraScript {
    void dumpRange(long start, long end, String label) throws Exception {
        println("=== " + label + " [0x" + Long.toHexString(start) + ",0x" + Long.toHexString(end) + ") ===");
        Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(start);
        Address e = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(end);
        int n = 0;
        while (a != null && a.compareTo(e) < 0 && n < 3000) {
            Instruction ins = getInstructionAt(a);
            if (ins == null) { disassemble(a); ins = getInstructionAt(a); }
            if (ins == null) { println("0x" + a.toString() + "  <no decode>"); a = a.add(1); n++; continue; }
            String bytes = "";
            for (byte bb : ins.getBytes()) bytes += String.format("%02x", bb & 0xff);
            println("0x" + ins.getAddress().toString() + "  " + String.format("%-20s", bytes) + " " + ins.toString());
            a = ins.getAddress().add(ins.getLength());
            n++;
        }
        println("--- end " + label + " (n=" + n + ") ---");
    }
    @Override
    public void run() throws Exception {
        println("IMAGE_BASE=0x" + currentProgram.getImageBase().toString());
        // MixFileClass ctor: zero-init + numFiles*12 allocation + tail-insert
        dumpRange(0x5B3C20L, 0x5B3C55L, "MixCtor zero-init+vft");
        dumpRange(0x5B3D75L, 0x5B3DBAL, "MixCtor numFiles*12 alloc (entry size)");
        dumpRange(0x5B3DDEL, 0x5B3E01L, "MixCtor dataStart+tail-insert");
        // hash function core loop
        dumpRange(0x4A1E75L, 0x4A1EA5L, "CRC32 inner loop (init/poly/final)");
        // Find binary search + 12-byte stride
        dumpRange(0x5B44CBL, 0x5B4506L, "Find binary search 12B stride");
        // CCFileClass ctor
        dumpRange(0x4739F0L, 0x473A20L, "CCFileCtor head");
        // vtable slot 12 (candidate GetSize)
        dumpRange(0x473AE0L, 0x473B10L, "CCFile v[12] 473AE0");
        println("### S03K1DUMP DONE");
    }
}
