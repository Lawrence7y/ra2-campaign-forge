// S18-F1 Channel-2 (Ghidra SLEIGH) independent disassembly dump.
// Run with analyzeHeadless -noanalysis. Reads raw instructions at known VAs.
// @category S18F1
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;

public class S18F1Dump extends GhidraScript {
    void dumpRange(long start, long end, String label) throws Exception {
        println("=== " + label + " [0x" + Long.toHexString(start) + ",0x" + Long.toHexString(end) + ") ===");
        Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(start);
        Address e = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(end);
        int n = 0;
        while (a != null && a.compareTo(e) < 0 && n < 3000) {
            Instruction ins = getInstructionAt(a);
            if (ins == null) {
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
        dumpRange(0x71F8C0L, 0x71F930L, "TEventClass ctor");
        dumpRange(0x4C6CB0L, 0x4C6CE0L, "Exec dispatch prologue");
        dumpRange(0x4C8114L, 0x4C81C8L, "jump table 46 dwords");
        dumpRange(0x64C380L, 0x64C410L, "Queue_ValidateExec head");
        dumpRange(0x64C8B0L, 0x64C930L, "Queue exec call site 0x64C911");
        dumpRange(0x64DAB0L, 0x64DB60L, "Frame CRC head");
        dumpRange(0x64DE40L, 0x64DE80L, "Frame CRC tail");
        dumpRange(0x4C6AE0L, 0x4C6B60L, "FillEvent_Place full");
        dumpRange(0x55DE20L, 0x55DE90L, "MainLogicFrame tail + CurrentFrame++");
        dumpRange(0x48CE70L, 0x48CEB0L, "GameRunner ordering");
        println("### S18F1DUMP DONE");
    }
}
