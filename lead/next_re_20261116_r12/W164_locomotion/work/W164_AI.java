// W164: Dump AI functions + all their call instructions (direct and indirect via vtable).
// Decompile FootClass::AI and subclass AIs; find Locomotor virtual calls.
// @category W164
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.mem.*;
import java.util.*;

public class W164_AI extends GhidraScript {
    long[] targets = { 0x004DA530L, 0x007360C0L, 0x0051BAB0L, 0x00414BB0L, 0x0043FB20L, 0x004666E0L };

    String cAt(long a) {
        try { return Integer.toHexString(currentProgram.getMemory().getInt(currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(a))); }
        catch (Exception e) { return "?"; }
    }

    public void run() throws Exception {
        DecompInterface di = new DecompInterface(); di.openProgram(currentProgram);
        for (long t : targets) {
            Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(t);
            Function f = currentProgram.getFunctionManager().getFunctionContaining(a);
            if (f == null) { println("=== NO FUNCTION at " + a + " ==="); continue; }
            println("================================================================");
            println("=== FN entry=" + f.getEntryPoint() + " name=" + f.getName() + " size=" + f.getBody().getNumAddresses() + " ===");
            // list all CALL instructions with operand strings, dedup by (addr,bytes)
            int nc=0;
            InstructionIterator ii = currentProgram.getListing().getInstructions(f.getBody(), true);
            while (ii.hasNext()) {
                Instruction ins = ii.next();
                String mn = ins.getMnemonicString();
                if (mn.startsWith("CALL") || mn.equals("call")) {
                    String ops = ins.toString();
                    println("  CALL@" + ins.getAddress() + ": " + ops);
                    nc++;
                }
            }
            println("  total CALL instrs = " + nc);
            // decompile (limit lines)
            DecompileResults r = di.decompileFunction(f, 90, monitor);
            if (r != null && r.decompileCompleted()) {
                println("--- DECOMPILE ---");
                String c = r.getDecompiledFunction().getC();
                int k=0;
                for (String ln : c.split("\n")) { println("C| "+ln); if (++k>200){println("C| ...TRUNC");break;} }
            } else println("--- decompile failed ---");
            println();
        }
    }
}
