// W170 (R13) — one-shot Ghidra: decompile mode-2 slot callees, +0x81 writers, 0x7014A0;
// and independently scan all instructions for byte-size [reg+0x81] operands (channel B).
// @category W170
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.lang.*;
import java.util.*;
import java.util.regex.*;

public class W170Dump extends GhidraScript {
    static final long[] TARGETS = {
        0x0043F180L, // BuildingClass slot73 (context)
        0x00705D70L, // mode2 slot +0x1E4
        0x005F6960L, // mode2 slot +0x1BC
        0x00456F80L, // mode2 slot +0x464
        0x0041BF40L, // mode2 slot +0x160
        0x0070E360L, // helper called in mode2
        0x0043FB20L, // BuildingClass self-calls slot73 mode2 at 0x43FDEB
        0x007014A0L, // TechnoClass slot245 relocation
        0x0070D4A0L, // reset related objects
        0x005F5850L, // predicate (hard veto +0x81)
        0x0044EBF0L, // BuildingClass slot? 11 writes +0x81
        0x0044EB60L, // orphan save/set/restore +0x81
        0x005F4D30L, // BulletClass slot53 sets +0x81=1
        0x005F4EC0L, // BulletClass slot54 sets +0x81=0/1
        0x00543780L, // sets +0x81=0
        0x00543A10L, // sets +0x81=0
        0x00543A40L, // sets +0x81=1
        0x00543B10L, // sets +0x81=1
        0x006F4A70L, // TechnoClass slot73 calls predicate
        0x004238B0L, // tiny wrapper calls predicate
        0x004666C0L, // tiny wrapper calls predicate
        0x0062D6F0L, // tiny wrapper calls predicate
        0x0071BFB0L  // TerrainClass slot73 calls predicate
    };

    void dumpC(DecompInterface di, long t, int maxLines) throws Exception {
        Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(t);
        Function f = currentProgram.getFunctionManager().getFunctionContaining(a);
        if (f == null) { println("=== @"+a+" NO FUNCTION ==="); return; }
        println("=== @"+a+" FN "+f.getEntryPoint()+" name="+f.getName()+" size="+f.getBody().getNumAddresses()+" ===");
        DecompileResults r = di.decompileFunction(f, 90, monitor);
        if (r == null || !r.decompileCompleted()) { println("  (decompile failed)"); return; }
        String c = r.getDecompiledFunction().getC();
        String[] lines = c.split("\n");
        println("  C lines="+lines.length);
        int shown = 0;
        for (String ln : lines) {
            println("C| "+ln);
            if (++shown >= maxLines) { println("C| ...(cap "+maxLines+")"); break; }
        }
        println("");
    }

    public void run() throws Exception {
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        println("W170 decompile start; imageBase="+currentProgram.getImageBase());
        for (long t : TARGETS) {
            try { dumpC(di, t, 260); }
            catch (Exception e) { println("=== @"+Long.toHexString(t)+" ERR "+e); }
        }

        // ---- channel B: independent scan for byte-size [..+0x81] operands ----
        println("===== CHANNEL B: Ghidra instruction scan byte [+0x81] =====");
        Pattern pDisp = Pattern.compile("0x81\\]");
        int nInsn=0, nHit=0, nWrite=0, nRead=0, nStack=0;
        ArrayList<String> hitsObj = new ArrayList<String>();
        ArrayList<String> hitsStack = new ArrayList<String>();
        InstructionIterator it = currentProgram.getListing().getInstructions(true);
        while (it.hasNext()) {
            Instruction ins = it.next();
            nInsn++;
            String s = ins.toString();
            if (s == null) continue;
            String low = s.toLowerCase();
            if (!low.contains("byte ptr")) continue;
            if (!pDisp.matcher(low).find()) continue;
            // exclude pure stack locals [esp+0x81] / [ebp+0x81]
            boolean stack = low.contains("esp + 0x81") || low.contains("ebp + 0x81")
                          || low.contains("esp+0x81") || low.contains("ebp+0x81");
            boolean isWrite = low.indexOf("byte ptr") < low.indexOf(",");
            // crude: if "byte ptr" appears before first comma => destination
            if (stack) { nStack++; hitsStack.add(String.format("%s  %s", ins.getAddress(), s)); continue; }
            nHit++;
            if (isWrite) nWrite++; else nRead++;
            Function f = currentProgram.getFunctionManager().getFunctionContaining(ins.getAddress());
            String fn = (f==null)?"NOFN":(f.getEntryPoint().toString()+" "+f.getName());
            hitsObj.add(String.format("%s  %-60s  %s  %s", ins.getAddress(), s, isWrite?"W":"R", fn));
        }
        println(String.format("insns=%d hitsObj=%d write=%d read=%d stackExcluded=%d", nInsn, nHit, nWrite, nRead, nStack));
        println("--- obj hits ---");
        for (String h : hitsObj) println(h);
        println("--- stack hits (first 40) ---");
        for (int i=0;i<Math.min(40,hitsStack.size());i++) println(hitsStack.get(i));
        println("W170 DONE");
    }
}
