// W168 run2: merge fn 0x46CE10, file-open 0x47AE10, INI read 0x525A60, callers via getFunctionContaining.
// @category W168
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;

public class W168Run2 extends GhidraScript {
    Address va(long v){ return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(v); }
    void dumpFn(long t, int cap) throws Exception {
        Address a=va(t);
        Function f=currentProgram.getFunctionManager().getFunctionAt(a);
        if (f==null){ println("=== no exact fn at "+a+" ==="); return; }
        println("=== FN "+a+" "+f.getName()+" size="+f.getBody().getNumAddresses()+" ===");
        DecompInterface di=new DecompInterface(); di.openProgram(currentProgram);
        DecompileResults r=di.decompileFunction(f,120,monitor);
        if(r==null||!r.decompileCompleted()){ println("  decompile FAILED"); return; }
        int k=0;
        for(String ln:r.getDecompiledFunction().getC().split("\n")){
            println("C| "+ln);
            if(++k>cap){ println("C| ...TRUNCATED"); break; }
        }
        println("=== END FN "+a+" ===");
    }
    void dumpContaining(long site, int cap, String label) throws Exception {
        Address a=va(site);
        Function f=currentProgram.getFunctionManager().getFunctionContaining(a);
        println("### site "+a+" ("+label+") containing="+(f==null?"?":f.getEntryPoint()+" "+f.getName()+" size="+f.getBody().getNumAddresses()));
        if(f==null) return;
        DecompInterface di=new DecompInterface(); di.openProgram(currentProgram);
        DecompileResults r=di.decompileFunction(f,120,monitor);
        if(r==null||!r.decompileCompleted()){ println("  decompile FAILED"); return; }
        int k=0;
        for(String ln:r.getDecompiledFunction().getC().split("\n")){
            println("C| "+ln);
            if(++k>cap){ println("C| ...TRUNCATED"); break; }
        }
    }
    void xrefsToFn(long t, String label) throws Exception {
        Address a=va(t);
        println("### CALLERS OF "+label+" @ "+a+" ###");
        ReferenceIterator it=currentProgram.getReferenceManager().getReferencesTo(a);
        int n=0;
        while(it.hasNext()){
            Reference r=it.next();
            Address from=r.getFromAddress();
            Function cf=currentProgram.getFunctionManager().getFunctionContaining(from);
            Instruction ins=currentProgram.getListing().getInstructionContaining(from);
            println("   ref@"+from+" type="+r.getReferenceType()+" in="+(cf==null?"?":cf.getEntryPoint())+" insn="+(ins==null?"?":ins.toString()));
            n++;
        }
        println("   total="+n);
    }
    public void run() throws Exception {
        println("========== MERGE FN ==========");
        dumpFn(0x0046CE10L, 400);
        println("========== FILE OPEN / INI READ ==========");
        dumpFn(0x0047AE10L, 220);
        dumpFn(0x00525A60L, 240);
        println("========== CALLERS OF MERGE FN ==========");
        xrefsToFn(0x0046CE10L, "0x46CE10 MERGE");
        println("========== CALLERS OF ENUM FNS (with containing fn) ==========");
        long[] sites={0x0052C605L,0x0052DF25L,0x0052E0C4L,0x00685609L,0x0052C95CL};
        String[] labels={"caller-site of 52CB90","caller-site of 52CB90","caller-site of 52CB90","caller-site of 52CB90","caller-site of 52CD70"};
        for(int i=0;i<sites.length;i++) dumpContaining(sites[i],100,labels[i]);
        println("========== DONE ==========");
    }
}
