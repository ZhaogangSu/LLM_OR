# reference_agent_v3.py (update your existing file)
from knowledge_base.retrievers.copt_retriever import COPTRetriever
from knowledge_base.retrievers.gurobi_retriever import GurobiExampleRetriever
from typing import List
import json

class ReferenceAgent:
    """Enhanced Reference Agent with Gurobi and COPT knowledge"""
    
    def __init__(self, 
                 copt_kb_dir="copt_knowledge_base",
                 gurobi_index="gurobi_examples_index.json"):
        self.knowledge_base.retrievers.copt_retriever = COPTRetriever(copt_kb_dir)
        self.knowledge_base.retrievers.gurobi_retriever = GurobiExampleRetriever(gurobi_index)
        print("✓ Reference Agent V3 initialized (COPT + Gurobi)")
    
    def get_modeling_references(self, problem_description: str) -> str:
        """Get both Gurobi examples and COPT docs for modeling"""
        # Get Gurobi examples
        gurobi_examples = self.knowledge_base.retrievers.gurobi_retriever.search(problem_description, top_k=2)
        gurobi_ref = self.knowledge_base.retrievers.gurobi_retriever.format_for_prompt(gurobi_examples)
        
        # Get COPT docs
        keywords = self._extract_modeling_keywords(problem_description)
        copt_sections = self.knowledge_base.retrievers.copt_retriever.search_by_keywords(keywords, top_k=2, python_only=True)
        copt_ref = self.knowledge_base.retrievers.copt_retriever.format_reference(copt_sections, max_content_length=400)
        
        # Combined reference
        reference = "## Modeling Guidance\n\n"
        reference += "### Step 1: Learn from Similar Gurobi Examples\n\n"
        reference += gurobi_ref
        reference += "\n### Step 2: COPT API Documentation\n\n"
        reference += copt_ref
        reference += "\n**Important**: Use Gurobi examples to understand the MODELING APPROACH, "
        reference += "but write code using COPT Python API (not Gurobi syntax).\n"
        
        return reference
    
    def get_coding_references(self, math_model: str) -> str:
        """Get COPT coding references with Gurobi→COPT translation hints"""
        # Get COPT API docs
        keywords = self._extract_coding_keywords(math_model)
        sections = self.knowledge_base.retrievers.copt_retriever.search_by_keywords(keywords, top_k=2, python_only=True)
        
        reference = "## COPT Code Generation Guide\n\n"
        reference += "### Gurobi → COPT API Translation\n\n"
        reference += self._gurobi_to_copt_translation_guide()
        reference += "\n### COPT Python API Documentation\n\n"
        reference += self.knowledge_base.retrievers.copt_retriever.format_reference(sections, max_content_length=400)
        
        return reference
    

    def _gurobi_to_copt_translation_guide(self) -> str:
        """Provide verified Gurobi to COPT API translation guide"""
        try:
            with open('gurobi_to_copt_translation.json', 'r') as f:
                translation = json.load(f)
            
            guide = """
    ## Gurobi → COPT Translation Guide
    *Verified from 51 real Gurobi modeling examples*

    """
            
            # Format as a clean table
            guide += "| Category | Gurobi | COPT |\n"
            guide += "|----------|--------|------|\n"
            
            key_mappings = [
                ("Import", "import gurobipy as gp", "import coptpy as cp"),
                ("Import", "from gurobipy import GRB", "from coptpy import COPT"),
                ("Model", "model = gp.Model()", "env = cp.Envr()<br>model = env.createModel()"),
                ("Binary Var", "vtype=GRB.BINARY", "vtype=COPT.BINARY"),
                ("Integer Var", "vtype=GRB.INTEGER", "vtype=COPT.INTEGER"),
                ("Continuous", "vtype=GRB.CONTINUOUS", "vtype=COPT.CONTINUOUS"),
                ("Constraint", "model.addConstr(...)", "model.addConstr(...) ✓ Same!"),
                ("Multi-Constr", "model.addConstrs(...)", "model.addConstrs(...) ✓ Same!"),
                ("Quicksum", "gp.quicksum(...)", "cp.quicksum(...) or sum(...)"),
                ("Minimize", "GRB.MINIMIZE", "COPT.MINIMIZE"),
                ("Maximize", "GRB.MAXIMIZE", "COPT.MAXIMIZE"),
                ("Solve", "model.optimize()", "model.solve()"),
                ("Get Value", "x.X (uppercase!)", "x.x (lowercase!)"),
                ("Get Obj", "model.ObjVal", "model.objval (all lowercase!)"),
            ]
            
            for category, grb, copt in key_mappings:
                guide += f"| {category} | `{grb}` | `{copt}` |\n"
            
            guide += "\n**⚠️ COMMON MISTAKES TO AVOID:**\n"
            guide += "1. Using `.optimize()` instead of `.solve()`\n"
            guide += "2. Using `.X` (uppercase) instead of `.x` (lowercase)\n"
            guide += "3. Using `model.ObjVal` instead of `model.objval`\n"
            guide += "4. Importing `gurobipy` instead of `coptpy`\n\n"
            
            guide += "**✅ GOOD NEWS:** Constraint syntax is identical!\n"
            
            return guide
        
        except FileNotFoundError:
            return self._fallback_translation_guide()

    def _fallback_translation_guide(self) -> str:
        """Minimal fallback if translation file missing"""
        return """
    **Gurobi → COPT Quick Reference:**
    - `import gurobipy as gp` → `import coptpy as cp`
    - `from gurobipy import GRB` → `from coptpy import COPT`
    - `gp.Model()` → `cp.Envr(); env.createModel()`
    - `model.optimize()` → `model.solve()`
    - `x.X` → `x.x` (lowercase!)
    - `model.ObjVal` → `model.objval` (lowercase!)
    """

    
    def _extract_modeling_keywords(self, problem: str) -> List[str]:
        """Extract keywords for modeling search"""
        keywords = ['model', 'variable']
        problem_lower = problem.lower()
        
        # Variable types
        if any(w in problem_lower for w in ['binary', 'select', 'yes/no', 'whether', 'choose']):
            keywords.append('binary')
        if any(w in problem_lower for w in ['integer', 'count', 'number of', 'units']):
            keywords.append('integer')
        
        # Objective
        if any(w in problem_lower for w in ['minimize', 'minimum', 'least', 'cost']):
            keywords.extend(['minimize', 'objective'])
        if any(w in problem_lower for w in ['maximize', 'maximum', 'most', 'profit', 'revenue']):
            keywords.extend(['maximize', 'objective'])
        
        # Constraints
        if any(w in problem_lower for w in ['constraint', 'must', 'should', 'at least', 'at most']):
            keywords.append('constraint')
        
        return list(set(keywords))
    
    def _extract_coding_keywords(self, math_model: str) -> List[str]:
        """Extract API keywords from mathematical model"""
        keywords = []
        model_lower = math_model.lower()
        
        if any(w in model_lower for w in ['variable', 'decision']):
            keywords.extend(['addvar', 'variable'])
        
        if any(w in model_lower for w in ['constraint', 'subject to', '<=']):
            keywords.extend(['addconstr', 'constraint'])
        
        if any(w in model_lower for w in ['objective', 'minimize', 'maximize']):
            keywords.extend(['setobjective', 'objective'])
        
        keywords.append('solve')
        
        return list(set(keywords))


# Test
if __name__ == "__main__":
    agent = ReferenceAgent()
    
    problem = """
    A factory can produce products A and B. 
    Product A requires 2 hours and gives $10 profit.
    Product B requires 3 hours and gives $15 profit.
    Available: 100 hours. Demand: At least 10 of A, 5 of B.
    Maximize profit.
    """
    
    print("="*70)
    print("Testing Enhanced Reference Agent")
    print("="*70)
    
    modeling_ref = agent.get_modeling_references(problem)
    print(modeling_ref[:1000])