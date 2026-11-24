// W156 final: refs to the two instance-array objects; operator new/delete identity; remaining vtable methods.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.util.*;

public class W156Final extends GhidraScript {
    AddressFactory af; FunctionManager fm; ReferenceManager rm; DecompInterface di;
    void refsTo(long addr, String label) throws Exception {
        Address a = af.getDefaultAddressSpace().getAddress(addr);
        println("=== REFS to " + label + " " + a + " ===");
        ReferenceIterator it = rm.getReferencesTo(a);
        TreeSet<String> s = new TreeSet<String>();
        int n=0;
        while (it.hasNext()) {
            Reference r = it.next();
            RefType rt = r.getReferenceType();
            Function f = fm.getFunctionContaining(r.getFromAddress());
            String fn = (f==null)?"NOFUNC":f.getEntryPoint().toString();
            String k = rt.isWrite()?"W":(rt.isRead()?"R":(rt.isCall()?"C":"D"));
            s.add("  " + k + " " + fn + " @" + r.getFromAddress());
            n++;
        }
        println("  total=" + n);
        for (String x : s) println(x);
    }
    void decomp(long addr) throws Exception {
        Address a = af.getDefaultAddressSpace().getAddress(addr);
        Function f = fm.getFunctionAt(a); if (f==null) f=fm.getFunctionContaining(a);
        println("--- DECOMP " + a + " size=" + (f==null?-1:f.getBody().getNumAddresses()) + " ---");
        if (f==null) return;
        DecompileResults res = di.decompileFunction(f,60,monitor);
        if (res==null||!res.decompileCompleted()){println("  FAILED");return;}
        String[] L = res.getDecompiledFunction().getC().split("\n");
        int k=0; for(String ln:L){println("C| "+ln); if(++k>60){println("C| ...");break;}}
    }
    public void run() throws Exception {
        af=currentProgram.getAddressFactory(); fm=currentProgram.getFunctionManager();
        rm=currentProgram.getReferenceManager(); di=new DecompInterface(); di.openProgram(currentProgram);
        // array object bases
        refsTo(0x00A8EB40L,"BldArray.obj");
        refsTo(0x00B0F640L,"AbsArray.obj");
        // remaining dynamicvector methods (slot1, 10)
        decomp(0x004E9460L);
        decomp(0x004E94A0L);
        decomp(0x004EF5D0L);
        // find any function named operator new/delete via symbol table
        println("=== SYMBOLS operator/new/delete ===");
        SymbolIterator si = currentProgram.getSymbolTable().getAllSymbols(true);
        int ns=0;
        while (si.hasNext() && ns<40) {
            Symbol sy = si.next();
            String nm = sy.getName();
            if (nm.toLowerCase().contains("operator") || nm.toLowerCase().contains("_new") || nm.toLowerCase().contains("_del")) {
                println("  " + nm + " @ " + sy.getAddress() + " type=" + sy.getSymbolType());
                ns++;
            }
        }
        println("W156Final DONE");
    }
}
