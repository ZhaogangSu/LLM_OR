# gurobi_retriever.py
import json
from typing import List, Dict
from collections import defaultdict
import numpy as np

class GurobiExampleRetriever:
    """Retrieve relevant Gurobi examples for OR problems"""
    
    def __init__(self, index_file="gurobi_examples_index.json"):
        with open(index_file, 'r', encoding='utf-8') as f:
            self.examples = json.load(f)
        
        self._build_keyword_index()
        print(f"✓ Loaded {len(self.examples)} Gurobi examples")
    
    def _build_keyword_index(self):
        """Build inverted index for fast search"""
        self.keyword_index = defaultdict(list)
        
        for i, example in enumerate(self.examples):
            # Index by problem type
            for ptype in example['problem_types']:
                self.keyword_index[ptype.lower()].append(i)
            
            # Index by keywords in description
            import re
            words = re.findall(r'\w+', example['description'].lower())
            for word in set(words):
                if len(word) > 3:
                    self.keyword_index[word].append(i)
    
    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search for relevant examples"""
        query_lower = query.lower()
        
        # Extract keywords
        import re
        keywords = re.findall(r'\w+', query_lower)
        keywords = [w for w in keywords if len(w) > 3]
        
        # Score examples
        scores = defaultdict(float)
        for keyword in keywords:
            for idx in self.keyword_index.get(keyword, []):
                scores[idx] += 1.0
        
        # Sort by score
        sorted_examples = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        results = []
        for idx, score in sorted_examples:
            example = self.examples[idx].copy()
            example['relevance_score'] = score
            results.append(example)
        
        return results
    

    def format_for_prompt(self, examples: List[Dict], condensed: bool = False) -> str:
        """
        Format examples for LLM prompt
        
        Args:
            examples: List of example dicts
            condensed: If True, return minimal version for training data
        """
        if not examples:
            return "No relevant Gurobi examples found."
        
        if condensed:
            # CONDENSED VERSION for training data (200-300 tokens total)
            formatted = "Key modeling patterns:\n"
            
            for i, ex in enumerate(examples, 1):
                # Only include: problem type + variable types + key pattern
                formatted += f"- Similar to {ex['name'].replace('_', ' ')}: "
                formatted += f"{', '.join(ex['problem_types'][:2])}\n"
                
                if ex['patterns']['variable_types']:
                    formatted += f"  Variables: {', '.join(ex['patterns']['variable_types'])}\n"
                
                if ex['patterns']['constraint_patterns']:
                    formatted += f"  Pattern: {ex['patterns']['constraint_patterns'][0]}\n"
            
            return formatted
        
        else:
            # ORIGINAL VERBOSE VERSION (for reference, not training)
            formatted = "## Relevant Gurobi Modeling Examples\n\n"
            
            for i, ex in enumerate(examples, 1):
                formatted += f"### Example {i}: {ex['name'].replace('_', ' ').title()}\n\n"
                formatted += f"**Problem Types**: {', '.join(ex['problem_types'])}\n\n"
                formatted += f"**Description**: {ex['description'][:300]}...\n\n"
                
                if ex['patterns']['variable_types']:
                    formatted += f"**Variable Types Used**: {', '.join(ex['patterns']['variable_types'])}\n\n"
                
                if ex['code_blocks']:
                    formatted += "**Example Gurobi Code Pattern**:\n"
                    formatted += f"```python\n{ex['code_blocks'][0][:400]}\n...\n```\n\n"
                
                formatted += "**Key Modeling Patterns**:\n"
                for pattern in ex['patterns']['constraint_patterns'][:2]:
                    formatted += f"- {pattern}\n"
                
                formatted += "\n---\n\n"
            
            return formatted


# Test
if __name__ == "__main__":
    retriever = GurobiExampleRetriever()
    
    # Test search
    query = "production planning with capacity constraints"
    results = retriever.search(query, top_k=3)
    
    print(f"Search results for: '{query}'\n")
    for r in results:
        print(f"  {r['name']}: {r['relevance_score']:.1f}")
    
    print("\n" + "="*70)
    print(retriever.format_for_prompt(results[:2]))