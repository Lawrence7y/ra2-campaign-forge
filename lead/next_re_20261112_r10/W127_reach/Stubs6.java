// W127: exact entry/exit semantics of the 6 routines that receive [0x887368] as `this`.
// Needed before writing any guard stub: a stub must preserve (a) return value,
// (b) `ret N` stack cleanup. @category W127
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import java.util.*;

public class Stubs6 extends GhidraScript {
    static final long[] FNS = { 0x007241A0L, 0x00724520L, 0x00724530L,
                                0x00724540L, 0x00724580L, 0x00724730L };

    public void run() throws Exception {
        FunctionManager fm = currentProgram.getFunctionManager();
        AddressSpace as = currentProgram.getAddressFactory().getDefaultAddressSpace();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        for (long va : FNS) {
            Address a = as.getAddress(va);
            Function f = fm.getFunctionAt(a);
            if (f == null) f = fm.getFunctionContaining(a);
            println("");
            println("=================================================");
            println("FN 0x" + Long.toHexString(va) + "  "
                    + (f == null ? "<NOT A FUNCTION>" :
                       ("size=" + f.getBody().getNumAddresses()
                        + "  end=" + f.getBody().getMaxAddress())));
            if (f == null) continue;

            // decompiled signature line
            DecompileResults r = di.decompileFunction(f, 90, monitor);
            if (r != null && r.decompileCompleted()) {
                String[] ls = r.getDecompiledFunction().getC().split("\n");
                for (String ln : ls) {
                    if (ln.contains("(") && ln.contains("FUN_")) { println("SIG: " + ln); break; }
                }
            }

            // first 12 instructions
            println("-- prologue --");
            InstructionIterator it = currentProgram.getListing().getInstructions(f.getBody(), true);
            int k = 0;
            while (it.hasNext() && k < 12) {
                Instruction in = it.next();
                println(String.format("   %08x  %-24s %s %s", in.getAddress().getOffset(),
                        bytes(in), in.getMnemonicString(), ops(in)));
                k++;
            }

            // every ret, with the preceding 3 instructions for context
            println("-- exits --");
            it = currentProgram.getListing().getInstructions(f.getBody(), true);
            while (it.hasNext()) {
                Instruction in = it.next();
                String m = in.getMnemonicString();
                if (!m.startsWith("ret") && !m.startsWith("RET")) continue;
                println(String.format("   RET @%08x  %s %s", in.getAddress().getOffset(),
                        bytes(in), ops(in)));
                // look back
                Instruction p = in.getPrevious();
                int n = 0;
                while (p != null && n < 3) {
                    println(String.format("        <- %08x  %s %s",
                            p.getAddress().getOffset(), p.getMnemonicString(), ops(p)));
                    p = p.getPrevious();
                    n++;
                }
            }
        }
    }

    String bytes(Instruction in) {
        try { return in.getBytes().toString().replace(" ", ""); } catch (Exception e) { return ""; }
    }

    String ops(Instruction in) {
        StringBuilder sb = new StringBuilder();
        int n = in.getNumOperands();
        for (int i = 0; i < n; i++) {
            if (i > 0) sb.append(",");
            try { sb.append(in.getDefaultOperandRepresentation(i)); } catch (Exception e) { }
        }
        return sb.toString();
    }
}
