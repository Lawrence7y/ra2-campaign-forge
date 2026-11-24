// W155: batched Ghidra cross-check. One run, all outputs to stdout (redirected by caller).
// @category W155
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.util.*;

public class W155All extends GhidraScript {
    Address addr(long v) { return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(v); }
    String hex(Address a) { return a==null?"-":a.toString(); }

    int backEdges(Function f) {
        int n=0;
        if (f==null) return 0;
        InstructionIterator it = currentProgram.getListing().getInstructions(f.getBody(), true);
        while (it.hasNext()) {
            Instruction ins = it.next();
            String m = ins.getMnemonicString();
            if (!(m.startsWith("j") || m.startsWith("loop"))) continue;
            Object[] ops = ins.getOpObjects(0);
            for (Object o : ops) {
                if (o instanceof Address) {
                    Address t=(Address)o;
                    if (t.compareTo(ins.getAddress())<=0) { n++; break; }
                }
            }
        }
        return n;
    }

    void describe(long v) {
        Address a=addr(v);
        Function f=currentProgram.getFunctionManager().getFunctionAt(a);
        Function c=currentProgram.getFunctionManager().getFunctionContaining(a);
        println("== describe 0x"+Long.toHexString(v)+" ==");
        println("  functionAt="+(f==null?"NONE":f.getName()+"@"+f.getEntryPoint()+" size="+f.getBody().getNumAddresses()));
        println("  containing="+(c==null?"NONE":c.getName()+"@"+c.getEntryPoint()+" size="+c.getBody().getNumAddresses()));
        if (f!=null) {
            println("  nInstr="+countInstr(f)+" backEdges="+backEdges(f));
            Set<String> callers=new TreeSet<String>();
            for (Function cf : f.getCallingFunctions(monitor)) callers.add(hex(cf.getEntryPoint()));
            println("  callers("+callers.size()+")="+callers);
            Set<String> callees=new TreeSet<String>();
            InstructionIterator it=currentProgram.getListing().getInstructions(f.getBody(),true);
            while(it.hasNext()){
                Instruction ins=it.next();
                if(!ins.getFlowType().isCall()) continue;
                Reference[] ri=currentProgram.getReferenceManager().getReferencesFrom(ins.getAddress());
                for(Reference r:ri){
                    if(r.getReferenceType().isCall()) callees.add(hex(r.getToAddress()));
                }
            }
            println("  directCallees("+callees.size()+")="+callees);
        }
        // references TO exact address
        int nref=0;
        ReferenceIterator refs=currentProgram.getReferenceManager().getReferencesTo(a);
        while(refs.hasNext()){
            Reference r=refs.next(); nref++;
            if(nref<=40) println("  refTo["+nref+"] from="+hex(r.getFromAddress())+" type="+r.getReferenceType()+" to="+hex(r.getToAddress()));
        }
        println("  refToCount="+nref);
    }

    int countInstr(Function f){
        int n=0; InstructionIterator it=currentProgram.getListing().getInstructions(f.getBody(),true);
        while(it.hasNext()){it.next();n++;} return n;
    }

    void dumpIns(long lo, long hi) throws Exception {
        println("== instructions ["+Long.toHexString(lo)+","+Long.toHexString(hi)+") ==");
        InstructionIterator it=currentProgram.getListing().getInstructions(addr(lo),true);
        while(it.hasNext()){
            Instruction ins=it.next();
            if(ins.getAddress().compareTo(addr(hi))>=0) break;
            String mark="";
            String s=ins.toString();
            byte[] bs=ins.getBytes();
            StringBuilder bh=new StringBuilder();
            for(byte b:bs) bh.append(String.format("%02x",b&0xff));
            if(s.contains("0x5c") || s.contains("0x98")) mark=" <<<";
            println("  "+hex(ins.getAddress())+"  "+bh+"  "+s+mark);
        }
    }

    void decomp(long v, int maxlines) {
        Address a=addr(v);
        Function f=currentProgram.getFunctionManager().getFunctionAt(a);
        if(f==null) f=currentProgram.getFunctionManager().getFunctionContaining(a);
        println("== decompile 0x"+Long.toHexString(v)+" ==");
        if(f==null){println("  NO FUNCTION");return;}
        DecompInterface di=new DecompInterface(); di.openProgram(currentProgram);
        DecompileResults r=di.decompileFunction(f,90,monitor);
        if(r==null||!r.decompileCompleted()){println("  FAILED");return;}
        String[] ls=r.getDecompiledFunction().getC().split("\n");
        println("  lines="+ls.length);
        for(int i=0;i<Math.min(ls.length,maxlines);i++) println("C| "+ls[i]);
        if(ls.length>maxlines) println("C| ...");
    }

    void bulletCheck() throws Exception {
        println("== BULLET 0x4666E0 / W151 recheck ==");
        Function f=currentProgram.getFunctionManager().getFunctionAt(addr(0x4666E0L));
        if(f==null){println("  NO FUNCTION");return;}
        println("  entry="+f.getEntryPoint()+" size="+f.getBody().getNumAddresses()+" nInstr="+countInstr(f)+" backEdges="+backEdges(f));
        TreeSet<String> callees=new TreeSet<String>();
        InstructionIterator it=currentProgram.getListing().getInstructions(f.getBody(),true);
        while(it.hasNext()){
            Instruction ins=it.next();
            if(!ins.getFlowType().isCall()) continue;
            Reference[] ri=currentProgram.getReferenceManager().getReferencesFrom(ins.getAddress());
            for(Reference r:ri){
                if(r.getReferenceType().isCall()) callees.add(hex(r.getToAddress()));
            }
        }
        println("  directCalleeAddrs="+callees.size());
        int nfn=0, nzero=0;
        for(String s:callees){
            Address ca=currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(s);
            Function cf=currentProgram.getFunctionManager().getFunctionAt(ca);
            int be=(cf==null?-1:backEdges(cf));
            if(cf!=null){nfn++; if(be==0)nzero++;}
            println("    callee "+s+" func="+(cf==null?"NONE":cf.getName())+" size="+(cf==null?-1:cf.getBody().getNumAddresses())+" backEdges="+be);
        }
        println("  callees_with_function="+nfn+" with_backEdges_zero="+nzero);
    }

    public void run() throws Exception {
        println("W155ALL start imageBase="+currentProgram.getImageBase());
        describe(0x55B8F0L);
        describe(0x55B960L);
        describe(0x55AFB0L);
        describe(0x55D360L);
        describe(0x48CCC0L);
        dumpIns(0x55B8E1L,0x55BAA0L);
        decomp(0x55B8F0L,100);
        bulletCheck();
        println("W155ALL done");
    }
}
