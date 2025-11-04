# knowledge_base/retrievers/reference_agent.py
from knowledge_base.retrievers.copt_retriever import COPTRetriever
from knowledge_base.retrievers.gurobi_retriever import GurobiExampleRetriever
from knowledge_base.retrievers.copt_retriever import COPTRetriever
from typing import List
import json

class ReferenceAgent:
    """Enhanced Reference Agent with Gurobi, COPT docs, and COPT API essentials"""
    
    def __init__(self,
                 copt_kb_dir="knowledge_base/data/copt_knowledge_base",
                 gurobi_index="knowledge_base/data/gurobi_examples_index.json",
                 copt_api_json="knowledge_base/data/copt_knowledge_base/copt_api_essential.json"):
        # FIX: Pass correct parameters to each retriever
        self.copt_retriever = COPTRetriever(copt_kb_dir)  # Directory for general docs
        self.gurobi_retriever = GurobiExampleRetriever(gurobi_index)  # Index file
        self.copt_api_retriever = COPTRetriever(copt_api_json)  # JSON file for API
        print("✓ Reference Agent V4 initialized (Gurobi + COPT + API Essentials)")
    
    def get_modeling_references(self, problem_description: str) -> str:
        """Get references for modeling"""
        # Get Gurobi examples
        gurobi_examples = self.gurobi_retriever.search(problem_description, top_k=2)
        gurobi_ref = self.gurobi_retriever.format_for_prompt(gurobi_examples)

        # Get COPT docs
        keywords = self._extract_modeling_keywords(problem_description)
        copt_sections = self.copt_retriever.search_by_keywords(keywords, top_k=2, python_only=True)
        copt_ref = self.copt_retriever.format_reference(copt_sections, max_content_length=400)
        
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
        """Get COPT coding references with API essentials"""
        # Extract what APIs are needed based on math model
        api_keywords = self._extract_api_keywords(math_model)
        
        # Get essential API docs for these keywords
        method_names = self.copt_api_retriever.get_methods_by_keywords(api_keywords)
        api_docs = self.copt_api_retriever.format_for_prompt(method_names, include_all_details=False)
        
        # Get essential guide
        essential_guide = self.copt_api_retriever.get_essential_api_guide()
        
        # Also get general COPT docs (less important now)
        keywords = self._extract_coding_keywords(math_model)
        sections = self.copt_retriever.search_by_keywords(keywords, top_k=1, python_only=True)
        general_docs = self.copt_retriever.format_reference(sections, max_content_length=300)

        # Combine with API essentials FIRST (most important)
        reference = "## COPT Code Generation Guide\n\n"
        reference += essential_guide
        reference += "\n### Specific API Documentation for This Problem\n\n"
        reference += api_docs
        reference += "\n### Additional COPT Documentation\n\n"
        reference += general_docs
        
        return reference
    
    def _extract_api_keywords(self, math_model: str) -> List[str]:
        """Extract which COPT APIs are needed from math model"""
        keywords = []
        model_lower = math_model.lower()
        
        # Always need these basics
        keywords.extend(['envr', 'model', 'solve'])
        
        # Variable types
        if any(w in model_lower for w in ['variable', 'decision']):
            keywords.extend(['addvar', 'addvars', 'variable'])
        
        if any(w in model_lower for w in ['binary', 'integer', 'continuous']):
            keywords.append('variable')
        
        # Constraints
        if any(w in model_lower for w in ['constraint', 'subject to', '<=', '>=']):
            keywords.extend(['addconstr', 'constraint'])
        
        # Objective
        if any(w in model_lower for w in ['objective', 'minimize', 'maximize']):
            keywords.extend(['objective', 'setobjective'])
        
        return list(set(keywords))
    
    def _extract_modeling_keywords(self, problem: str) -> List[str]:
        """Extract keywords for modeling search"""
        keywords = ['model', 'variable']
        problem_lower = problem.lower()
        
        if any(w in problem_lower for w in ['binary', 'select', 'yes/no', 'whether', 'choose']):
            keywords.append('binary')
        if any(w in problem_lower for w in ['integer', 'count', 'number of', 'units']):
            keywords.append('integer')
        
        if any(w in problem_lower for w in ['minimize', 'minimum', 'least', 'cost']):
            keywords.extend(['minimize', 'objective'])
        if any(w in problem_lower for w in ['maximize', 'maximum', 'most', 'profit', 'revenue']):
            keywords.extend(['maximize', 'objective'])
        
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