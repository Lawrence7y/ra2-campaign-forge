// W164: focused disassembly around 0x4DAEF3 in FootClass::AI + full decompile
// @category W164
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;

public class W164_Focus extends GhidraScript {
    public void run() throws Exception {
        AddressFactory af = currentProgram.getAddressFactory();
        Address base = af.getDefaultAddressSpace().getAddress(0x004DA530L);
        // disassemble window 0x4DAE80..0x4DAF40
        Address st = af.getDefaultAddressSpace().getAddress(0x004DAE80L);
        Address en = af.getDefaultAddressSpace().getAddress(0x004DAF40L);
        println("=== DISASM 0x4DAE80..0x4DAF40 ===");
        InstructionIterator ii = currentProgram.getListing().getInstructions(new ghidra.program.model.address.AddressSet(st,en), true);
        while (ii.hasNext()) { Instruction ins = ii.next(); println("  "+ins.getAddress()+": "+ins.toString()); }
        // full decompile of FootClass AI
        Function f = currentProgram.getFunctionManager().getFunctionContaining(base);
        DecompInterface di = new DecompInterface(); di.openProgram(currentProgram);
        DecompileResults r = di.decompileFunction(f, 120, monitor);
        if (r != null && r.decompileCompleted()) {
            println("=== FULL DECOMPILE 0x4DA530 ===");
            for (String ln : r.getDecompiledFunction().getC().split("\n")) println("C| "+ln);
        }
    }
}
