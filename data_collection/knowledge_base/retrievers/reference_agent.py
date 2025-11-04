# knowledge_base/retrievers/reference_agent.py
"""
Reference Agent - Simplified version that uses only essential APIs

Provides:
1. Gurobi examples for modeling guidance (unchanged)
2. COPT API essentials from JSON (simplified - no general docs)
"""

from knowledge_base.retrievers.copt_api_retriever import COPTAPIRetriever
from knowledge_base.retrievers.gurobi_retriever import GurobiExampleRetriever
from typing import List
import json


class ReferenceAgent:
    """
    Simplified Reference Agent using only Gurobi examples + COPT API essentials
    
    Removed:
    - General COPT documentation (copt_flat_sections.jsonl)
    - Complex section searching
    - Unnecessary file I/O
    
    Kept:
    - Gurobi modeling examples
    - COPT API essentials (JSON)
    - Translation guide (optional)
    """
    
    def __init__(
        self,
        gurobi_index: str = "knowledge_base/data/gurobi_examples_index.json",
        copt_api_json: str = "knowledge_base/data/copt_api_essential.json",
        translation_guide: str = None
    ):
        """
        Initialize reference agent
        
        Args:
            gurobi_index: Path to Gurobi examples index JSON
            copt_api_json: Path to COPT API essentials JSON
            translation_guide: Optional path to Gurobi→COPT translation guide
            
        Example:
            >>> agent = ReferenceAgent(
            ...     gurobi_index='path/to/gurobi_index.json',
            ...     copt_api_json='path/to/copt_api_essential.json'
            ... )
        """
        # Initialize Gurobi retriever (for modeling examples)
        self.gurobi_retriever = GurobiExampleRetriever(gurobi_index)
        
        # Initialize COPT API retriever (for coding)
        self.copt_api_retriever = COPTAPIRetriever(copt_api_json)
        
        # Load translation guide if provided
        self.translation_guide = None
        if translation_guide:
            try:
                with open(translation_guide, 'r') as f:
                    self.translation_guide = json.load(f)
            except:
                print(f"⚠️  Could not load translation guide from {translation_guide}")
        
        print("✓ Reference Agent initialized (Gurobi + COPT API only)")
    
    def get_modeling_references(
        self, 
        problem_description: str,
        condensed: bool = False  # NEW PARAMETER
    ) -> str:
        """
        Get references for mathematical modeling
        
        Args:
            problem_description: Problem text
            condensed: If True, return condensed version for training data
        """
        # Get relevant Gurobi examples
        gurobi_examples = self.gurobi_retriever.search(
            problem_description, 
            top_k=2
        )
        
        if condensed:
            # CONDENSED VERSION (200-300 tokens total)
            reference = "## Mathematical Modeling Guidance\n\n"
            reference += self.gurobi_retriever.format_for_prompt(
                gurobi_examples, 
                condensed=True  # Use condensed format
            )
            reference += "\nApply these patterns using COPT Python API.\n"
            return reference
        
        else:
            # ORIGINAL VERBOSE VERSION
            reference = "## Mathematical Modeling Guidance\n\n"
            reference += "### Similar Problem Examples\n\n"
            reference += "Learn from these Gurobi modeling examples:\n\n"
            reference += self.gurobi_retriever.format_for_prompt(gurobi_examples)
            
            reference += "\n### Important Note\n"
            reference += "- Use these examples to understand the **modeling approach**\n"
            reference += "- When writing code, use **COPT Python API** (not Gurobi syntax)\n"
            reference += "- Focus on: variable types, constraint structure, objective function\n\n"
            
            return reference


    def get_coding_references(
        self, 
        math_model: str,
        condensed: bool = False  # NEW PARAMETER
    ) -> str:
        """
        Get COPT API references
        
        Args:
            math_model: Mathematical formulation
            condensed: If True, return condensed version
        """
        api_keywords = self.copt_api_retriever.extract_api_keywords_from_model(math_model)
        method_names = self.copt_api_retriever.get_methods_by_keywords(api_keywords)
        
        if condensed:
            # CONDENSED VERSION (150-200 tokens)
            reference = "## COPT API Reference\n\n"
            reference += self.copt_api_retriever.get_essential_guide(condensed=True)
            reference += "\n"
            reference += self.copt_api_retriever.format_for_prompt(
                method_names,
                include_all_details=False,
                condensed=True
            )
            return reference
        
        else:
            # ORIGINAL VERBOSE VERSION
            reference = "## COPT Python API Reference\n\n"
            reference += "### Essential COPT Workflow\n\n"
            reference += self.copt_api_retriever.get_essential_guide()
            
            if method_names:
                reference += "\n### Specific APIs for This Problem\n\n"
                reference += self.copt_api_retriever.format_for_prompt(
                    method_names,
                    include_all_details=True
                )
            
            if self.translation_guide:
                reference += "\n### Gurobi → COPT Translation\n\n"
                reference += self._format_translation_guide()
            
            return reference
        
    def _format_translation_guide(self) -> str:
        """Format Gurobi→COPT translation guide for prompt"""
        if not self.translation_guide:
            return ""
        
        guide = "Common Gurobi→COPT translations:\n\n"
        
        # Key differences
        key_diffs = [
            ('imports', 'Package imports'),
            ('model_creation', 'Model creation'),
            ('solving', 'Solving'),
            ('solution_access', 'Solution access')
        ]
        
        for key, title in key_diffs:
            if key in self.translation_guide:
                section = self.translation_guide[key]
                guide += f"**{title}:**\n"
                guide += f"- Gurobi: `{section['gurobi'][0]}`\n"
                guide += f"- COPT: `{section['copt'][0]}`\n"
                if section.get('notes'):
                    guide += f"- Note: {section['notes']}\n"
                guide += "\n"
        
        return guide
    
    def get_complete_reference(
        self, 
        problem: str,
        math_model: str = None
    ) -> dict[str, str]:
        """
        Get both modeling and coding references
        
        Args:
            problem: Problem description
            math_model: Mathematical model (if available)
            
        Returns:
            Dict with 'modeling' and 'coding' references
        """
        references = {
            'modeling': self.get_modeling_references(problem)
        }
        
        if math_model:
            references['coding'] = self.get_coding_references(math_model)
        
        return references


# Test
if __name__ == "__main__":
    print("=== Reference Agent Test ===\n")
    
    # Initialize
    agent = ReferenceAgent(
        gurobi_index="knowledge_base/data/gurobi_examples_index.json",
        copt_api_json="knowledge_base/data/copt_api_essential.json"
    )
    
    # Test problem
    problem = """
    A factory produces two products A and B.
    Product A requires 2 hours and gives $10 profit.
    Product B requires 3 hours and gives $15 profit.
    Available: 100 hours.
    Maximize profit.
    """
    
    # Test 1: Modeling references
    print("Test 1: Get modeling references")
    modeling_ref = agent.get_modeling_references(problem)
    print(f"✓ Modeling reference length: {len(modeling_ref)} chars\n")
    
    # Test 2: Coding references
    print("Test 2: Get coding references")
    math_model = """
    Variables: x_A, x_B (continuous, non-negative)
    Objective: maximize 10*x_A + 15*x_B
    Constraints:
    - 2*x_A + 3*x_B <= 100 (time)
    """
    coding_ref = agent.get_coding_references(math_model)
    print(f"✓ Coding reference length: {len(coding_ref)} chars\n")
    
    # Test 3: Complete reference
    print("Test 3: Get complete reference")
    complete = agent.get_complete_reference(problem, math_model)
    print(f"✓ Got {len(complete)} reference types\n")
    
    print("✓ All tests passed!")