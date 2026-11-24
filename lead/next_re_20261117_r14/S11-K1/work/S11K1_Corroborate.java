// S11-K1 Ghidra corroboration: decompile factory 0x41C250, CLSID reg site, and 0x4DA877 context.
// Runs -noanalysis (project already analyzed).
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.app.decompiler.*;

public class S11K1_Corroborate extends GhidraScript {
    void dumpDecomp(String label, long va) throws Exception {
        Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(va);
        Function f = getFunctionContaining(a);
        println("===== " + label + " @ " + Long.toHexString(va) + " =====");
        if (f == null) { println("NO FUNCTION"); return; }
        println("FUNCTION " + f.getName() + " entry=" + f.getEntryPoint() + " max=" + f.getBody().getMaxAddress());
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        DecompileResults r = di.decompileFunction(f, 60, monitor);
        if (r.decompileCompleted()) {
            println(r.getDecompiledFunction().getC());
        } else {
            println("DECOMP FAILED: " + r.getErrorMessage());
        }
    }
    @Override
    public void run() throws Exception {
        dumpDecomp("CreateInstance factory", 0x41C250L);
        dumpDecomp("CLSID registration fn", 0x6BD15CL);
        // 0x4DA877 context: list instructions around it
        println("===== 0x4DA877 context =====");
        Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(0x4DA86EL);
        for (int i=0;i<12;i++) {
            Instruction ins = getInstructionAt(a);
            if (ins == null) { println("null at " + a); break; }
            println(ins.getAddress() + "  " + ins.toString());
            Address next = ins.getAddress().add(ins.getLength());
            a = next;
            if (a == null) break;
        }
    }
}
