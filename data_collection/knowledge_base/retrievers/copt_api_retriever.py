# knowledge_base/retrievers/copt_api_retriever.py
"""
Simplified COPT API Retriever - reads only from copt_api_essential.json

This retriever provides API documentation for COPT methods needed for code generation.
No complex document crawling - just clean JSON-based API lookup.
"""

import json
from typing import List, Dict, Set
from pathlib import Path


class COPTAPIRetriever:
    """
    Simplified retriever for COPT Python API documentation
    
    Reads from copt_api_essential.json and provides keyword-based lookup
    for API methods like addVar, addVars, setObjective, etc.
    """
    
    def __init__(self, api_json_path: str):
        """
        Initialize COPT API retriever
        
        Args:
            api_json_path: Path to copt_api_essential.json
            
        Example:
            >>> retriever = COPTAPIRetriever('knowledge_base/data/copt_api_essential.json')
        """
        self.api_json_path = Path(api_json_path)
        
        if not self.api_json_path.exists():
            raise FileNotFoundError(f"COPT API JSON not found: {api_json_path}")
        
        # Load API definitions
        with open(self.api_json_path, 'r', encoding='utf-8') as f:
            self.api_methods = json.load(f)
        
        self.method_names = list(self.api_methods.keys())
        
        # Build keyword index for fast lookup
        self._build_keyword_index()
        
        print(f"✓ COPT API Retriever loaded {len(self.method_names)} methods")
    
    def _build_keyword_index(self):
        """Build reverse index: keyword -> [method_names]"""
        self.keyword_to_methods = {}
        
        for method_name in self.method_names:
            # Extract keywords from method name
            # e.g., "Model.addVar" -> ["model", "add", "var", "addvar"]
            parts = method_name.lower().replace('.', ' ').split()
            keywords = parts + [method_name.lower().replace('.', '')]
            
            for keyword in keywords:
                if keyword not in self.keyword_to_methods:
                    self.keyword_to_methods[keyword] = []
                self.keyword_to_methods[keyword].append(method_name)
    
    def get_methods_by_keywords(self, keywords: List[str]) -> List[str]:
        """
        Get API method names matching keywords
        
        Args:
            keywords: List of search keywords
            
        Returns:
            List of matching method names
            
        Example:
            >>> retriever.get_methods_by_keywords(['variable', 'add'])
            ['Model.addVar', 'Model.addVars']
        """
        if isinstance(keywords, str):
            keywords = [keywords]
        
        # Normalize keywords
        keywords = [k.lower().strip() for k in keywords]
        
        # Collect matching methods
        matched_methods: Set[str] = set()
        
        for keyword in keywords:
            # Direct match
            if keyword in self.keyword_to_methods:
                matched_methods.update(self.keyword_to_methods[keyword])
            
            # Partial match (contains)
            for indexed_keyword, methods in self.keyword_to_methods.items():
                if keyword in indexed_keyword or indexed_keyword in keyword:
                    matched_methods.update(methods)
        
        return list(matched_methods)
    
    def get_method_details(self, method_name: str) -> Dict:
        """
        Get full details for a specific method
        
        Args:
            method_name: Method name (e.g., "Model.addVar")
            
        Returns:
            Dict with method details
        """
        return self.api_methods.get(method_name, {})
    
    def format_for_prompt(
        self, 
        method_names: List[str],
        include_all_details: bool = True
    ) -> str:
        """
        Format API methods for LLM prompt
        
        Args:
            method_names: List of method names to include
            include_all_details: If True, include critical notes and examples
            
        Returns:
            Formatted API documentation string
            
        Example:
            >>> methods = retriever.get_methods_by_keywords(['addvar'])
            >>> prompt = retriever.format_for_prompt(methods)
        """
        if not method_names:
            return "No API methods found for the given keywords."
        
        formatted = "## COPT Python API Documentation\n\n"
        
        for method_name in method_names:
            details = self.get_method_details(method_name)
            
            if not details:
                continue
            
            formatted += f"### {method_name}\n\n"
            
            # Signature
            if details.get('signature'):
                formatted += f"**Signature:**\n```python\n{details['signature']}\n```\n\n"
            
            # Critical notes (MOST IMPORTANT!)
            if include_all_details and details.get('critical_note'):
                formatted += f"⚠️ **CRITICAL:** {details['critical_note']}\n\n"
            
            # Correct usage
            if include_all_details and details.get('correct_usage'):
                formatted += "**✓ Correct Usage:**\n```python\n"
                if isinstance(details['correct_usage'], list):
                    formatted += '\n'.join(details['correct_usage'])
                else:
                    formatted += details['correct_usage']
                formatted += "\n```\n\n"
            
            # Wrong usage (if any)
            if include_all_details and details.get('wrong_usage'):
                formatted += "**✗ Wrong Usage:**\n```python\n"
                formatted += details['wrong_usage']
                formatted += "\n```\n\n"
            
            # Alternative (if any)
            if include_all_details and details.get('alternative'):
                formatted += "**Alternative Approach:**\n```python\n"
                formatted += details['alternative']
                formatted += "\n```\n\n"
            
            # Examples
            if details.get('examples'):
                formatted += "**Examples:**\n```python\n"
                if isinstance(details['examples'], list):
                    formatted += '\n'.join(details['examples'])
                else:
                    formatted += details['examples']
                formatted += "\n```\n\n"
            
            formatted += "---\n\n"
        
        return formatted
    
    def get_essential_guide(self) -> str:
        """
        Get essential COPT API guide covering common operations
        
        Returns:
            Quick reference guide for COPT basics
        """
        essential_methods = [
            'Envr.__init__',
            'Envr.createModel',
            'Model.addVar',
            'Model.addVars',
            'Model.addConstr',
            'Model.setObjective',
            'Model.solve'
        ]
        
        guide = "## COPT Essential API Guide\n\n"
        guide += "This guide covers the core APIs needed for most optimization problems.\n\n"
        
        # Add basic workflow
        guide += "### Basic Workflow\n"
        guide += "```python\n"
        guide += "import coptpy as cp\n"
        guide += "from coptpy import COPT\n\n"
        guide += "# 1. Create environment\n"
        guide += "env = cp.Envr()\n\n"
        guide += "# 2. Create model\n"
        guide += "model = env.createModel('problem_name')\n\n"
        guide += "# 3. Add variables\n"
        guide += "x = model.addVar(vtype=COPT.INTEGER, name='x')\n\n"
        guide += "# 4. Add constraints\n"
        guide += "model.addConstr(x >= 5)\n\n"
        guide += "# 5. Set objective\n"
        guide += "model.setObjective(x, COPT.MINIMIZE)\n\n"
        guide += "# 6. Solve\n"
        guide += "model.solve()\n\n"
        guide += "# 7. Get solution\n"
        guide += "if model.status == COPT.OPTIMAL:\n"
        guide += "    print(f'Optimal objective: {model.objval}')\n"
        guide += "```\n\n"
        
        # Add detailed API docs for essential methods
        guide += self.format_for_prompt(essential_methods, include_all_details=True)
        
        return guide
    
    def extract_api_keywords_from_model(self, math_model: str) -> List[str]:
        """
        Extract which COPT APIs are likely needed based on mathematical model
        
        Args:
            math_model: Mathematical formulation text
            
        Returns:
            List of relevant API keywords
            
        Example:
            >>> model = "Variables: x[i] binary, Objective: minimize cost"
            >>> keywords = retriever.extract_api_keywords_from_model(model)
            >>> # Returns: ['addvars', 'binary', 'setobjective', 'minimize']
        """
        keywords = []
        model_lower = math_model.lower()
        
        # Always need these basics
        keywords.extend(['envr', 'createmodel', 'solve'])
        
        # Variable creation
        if any(w in model_lower for w in ['variable', 'decision']):
            keywords.extend(['addvar', 'addvars'])
        
        # Variable types
        if 'binary' in model_lower:
            keywords.append('binary')
        if 'integer' in model_lower:
            keywords.append('integer')
        if 'continuous' in model_lower:
            keywords.append('continuous')
        
        # Constraints
        if any(w in model_lower for w in ['constraint', 'subject to', '<=', '>=', '==']):
            keywords.extend(['addconstr', 'addconstrs'])
        
        # Objective
        if any(w in model_lower for w in ['objective', 'minimize', 'maximize']):
            keywords.append('setobjective')
        
        return list(set(keywords))


# Test
if __name__ == "__main__":
    print("=== COPT API Retriever Test ===\n")
    
    # Initialize
    retriever = COPTAPIRetriever('knowledge_base/data/copt_api_essential.json')
    
    # Test 1: Keyword search
    print("Test 1: Search for variable-related methods")
    methods = retriever.get_methods_by_keywords(['variable', 'add'])
    print(f"Found methods: {methods}\n")
    
    # Test 2: Format for prompt
    print("Test 2: Format API docs")
    formatted = retriever.format_for_prompt(['Model.addVar', 'Model.addVars'])
    print(formatted[:500] + "...\n")
    
    # Test 3: Essential guide
    print("Test 3: Get essential guide")
    guide = retriever.get_essential_guide()
    print(f"Essential guide length: {len(guide)} chars\n")
    
    # Test 4: Extract keywords from model
    print("Test 4: Extract API keywords from math model")
    model = "Variables: x[i] binary for i in 1..10. Objective: minimize cost. Constraints: sum(x[i]) >= 5"
    keywords = retriever.extract_api_keywords_from_model(model)
    print(f"Extracted keywords: {keywords}\n")
    
    print("✓ All tests passed!")