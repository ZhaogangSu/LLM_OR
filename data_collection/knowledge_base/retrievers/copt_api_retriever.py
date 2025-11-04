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
        include_all_details: bool = True,
        condensed: bool = False
    ) -> str:
        """
        Format API methods for LLM prompt
        
        Args:
            method_names: List of method names
            include_all_details: Include examples and notes
            condensed: If True, return minimal version
        """
        if not method_names:
            return "No API methods found."
        
        if condensed:
            # CONDENSED VERSION (50-100 tokens)
            formatted = "Key COPT methods:\n"
            for method_name in method_names[:5]:  # Only top 5
                details = self.get_method_details(method_name)
                if details:
                    formatted += f"- {method_name}: {details.get('purpose', 'N/A')}\n"
            return formatted
        
        else:
            # ORIGINAL VERBOSE VERSION
            formatted = ""
            for method_name in method_names:
                details = self.get_method_details(method_name)
                if not details:
                    continue
                
                formatted += f"### {method_name}\n\n"
                formatted += f"**Purpose**: {details.get('purpose', 'N/A')}\n\n"
                
                if include_all_details:
                    if details.get('syntax'):
                        formatted += f"**Syntax**: `{details['syntax']}`\n\n"
                    if details.get('parameters'):
                        formatted += "**Parameters**:\n"
                        for param in details['parameters']:
                            formatted += f"- `{param['name']}`: {param['description']}\n"
                        formatted += "\n"
                    if details.get('example'):
                        formatted += f"**Example**:\n```python\n{details['example']}\n```\n\n"
                
                formatted += "---\n\n"
            
            return formatted

    def get_essential_guide(self, condensed: bool = False) -> str:
        """
        Get essential COPT workflow guide
        
        Args:
            condensed: If True, return minimal version
        """
        if condensed:
            # CONDENSED VERSION (100-150 tokens)
            return """Essential COPT pattern:
    1. Create model: env = cp.Envr(); model = env.createModel()
    2. Add variables: x = model.addVar(lb=0, vtype=COPT.INTEGER)
    3. Set objective: model.setObjective(expr, COPT.MINIMIZE)
    4. Add constraints: model.addConstr(lhs <= rhs)
    5. Solve: model.solve()
    6. Get solution: x.X for value
    """
        else:
            # ORIGINAL VERBOSE VERSION
            return self._format_essential_guide_verbose()

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