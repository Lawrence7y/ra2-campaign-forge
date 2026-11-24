// W160: one-shot Ghidra reference/decompile pass for AI-dispatch card.
// @category W160
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.symbol.*;
import ghidra.util.task.*;
import java.util.*;

public class W160Gather extends GhidraScript {
    static String hx(long v){ return String.format("%08X", v); }
    Address addr(long t){ return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(t); }

    public void run() throws Exception {
        println("W160_GATHER_BEGIN");
        println("imageBase = " + currentProgram.getImageBase());

        // 1) xrefs for key addresses (6 channels where applicable)
        long[] xs = { 0x0055B8F0L, 0x0055B960L, 0x0087F778L, 0x0040CB80L, 0x0040CBC0L,
                      0x0055AFB0L, 0x00454DB0L, 0x004C54E0L };
        for (long t : xs) {
            Address a = addr(t);
            ReferenceIterator ri = currentProgram.getReferenceManager().getReferencesTo(a);
            int n=0;
            while (ri.hasNext() && n < 200) { Reference r = ri.next();
                println("XREF_TO " + hx(t) + " <- " + r.getFromAddress() + " type=" + r.getReferenceType() + " src=" + r.getSource()); n++; }
            println("XREF_TO_SUM " + hx(t) + " n=" + n);
            Function cf = currentProgram.getFunctionManager().getFunctionContaining(a);
            println("FUNC_AT " + hx(t) + " = " + (cf==null?"NONE":cf.getEntryPoint()+" size="+cf.getBody().getNumAddresses()));
        }

        // 2) data words at key addresses (absolute operands)
        long[] words = { 0x0055B8F0L, 0x0055B8F0L-4, 0x0055B8F0L-8, 0x0055B8F0L-0x10,
                         0x0055B8F0L-0x20, 0x0055B8F0L+0x30, 0x0055B8F0L+0x70,
                         0x0055B8F0L+0xB0 };
        for (long w : words) {
            try { byte[] b = new byte[4];
                  currentProgram.getMemory().getBytes(addr(w), b);
                  long v=(b[0]&255L)|((b[1]&255L)<<8)|((b[2]&255L)<<16)|((b[3]&255L)<<24);
                  println("WORD " + hx(w) + " = " + hx(v));
            } catch (Exception e) { println("WORD " + hx(w) + " ERR " + e); }
        }

        // 3) decompile 0x55AFB0 and 0x55B8F0 if function exists
        DecompInterface di = new DecompInterface(); di.openProgram(currentProgram);
        long[] ds = { 0x0055AFB0L, 0x0055B8F0L, 0x0040CB80L };
        for (long t : ds) {
            Function f = currentProgram.getFunctionManager().getFunctionContaining(addr(t));
            if (f==null){ println("DECOMP " + hx(t) + " NO_FUNC"); continue; }
            println("=== DECOMP " + hx(t) + " -> " + f.getEntryPoint() + " size=" + f.getBody().getNumAddresses() + " ===");
            DecompileResults r = di.decompileFunction(f, 90, monitor);
            if (r==null || !r.decompileCompleted()){ println("DECOMP_FAIL"); continue; }
            println(r.getDecompiledFunction().getC());
        }

        // 4) scan all instructions in .text for indirect call [X+0x5C]; count by containing function
        AddressSetView textSet = currentProgram.getMemory().getExecuteSet();
        InstructionIterator ii = currentProgram.getListing().getInstructions(textSet, true);
        int n=0, n5c=0; TreeMap<String,Integer> byFn = new TreeMap<String,Integer>();
        while (ii.hasNext()) {
            Instruction in = ii.next(); n++;
            String s = in.toString();
            if (!s.startsWith("CALL")) continue;
            if (!s.contains("+ 0x5c") && !s.contains("+0x5c") && !s.contains("+ 0x5C")) continue;
            n5c++;
            Function f = currentProgram.getFunctionManager().getFunctionContaining(in.getAddress());
            String k = f==null ? "NONE" : f.getEntryPoint().toString();
            byFn.put(k, byFn.getOrDefault(k,0)+1);
            if (n5c<=300) println("SITE " + in.getAddress() + " fn=" + k + " :: " + s);
        }
        println("INSTR_TOTAL " + n);
        println("CALL_5C_TOTAL " + n5c);
        println("CALL_5C_FUNCS " + byFn.size());
        for (Map.Entry<String,Integer> e : byFn.entrySet()) println("FNCOUNT " + e.getKey() + " " + e.getValue());

        println("W160_GATHER_END");
    }
}
