# build_gurobi_kb.py
import os
import json
import re
from pathlib import Path

class GurobiExampleIndexer:
    """Index Gurobi modeling examples for retrieval"""
    
    def __init__(self, examples_root="gurobi_modeling_examples/modeling-examples-master"):
        self.examples_root = examples_root
        self.examples = []
    
    def extract_notebook_content(self, notebook_path):
        """Extract text and code from Jupyter notebook"""
        try:
            with open(notebook_path, 'r', encoding='utf-8') as f:
                nb = json.load(f)
            
            text_content = []
            code_blocks = []
            
            for cell in nb.get('cells', []):
                if cell['cell_type'] == 'markdown':
                    text_content.append(''.join(cell['source']))
                elif cell['cell_type'] == 'code':
                    code = ''.join(cell['source'])
                    code_blocks.append(code)
            
            return {
                'text': '\n\n'.join(text_content),
                'code': code_blocks
            }
        except Exception as e:
            print(f"Error reading {notebook_path}: {e}")
            return {'text': '', 'code': []}
    
    def extract_readme(self, readme_path):
        """Extract README content"""
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return ""
    
    def identify_problem_type(self, text, code):
        """Identify optimization problem type from content"""
        text_lower = text.lower()
        code_str = '\n'.join(code).lower()
        
        problem_types = []
        
        # Linear Programming
        if any(kw in text_lower for kw in ['linear program', 'lp problem', 'linear optimization']):
            problem_types.append('Linear Programming')
        
        # Integer Programming
        if any(kw in text_lower or kw in code_str for kw in ['integer', 'binary', 'gurobi.binary', 'vtype=gurobi.integer']):
            problem_types.append('Integer Programming')
        
        # Network Flow
        if any(kw in text_lower for kw in ['network flow', 'transportation', 'assignment', 'routing']):
            problem_types.append('Network Flow')
        
        # Scheduling
        if any(kw in text_lower for kw in ['schedul', 'roster', 'workforce']):
            problem_types.append('Scheduling')
        
        # Facility Location
        if any(kw in text_lower for kw in ['facility location', 'site selection', 'warehouse']):
            problem_types.append('Facility Location')
        
        # Production Planning
        if any(kw in text_lower for kw in ['production', 'manufacturing', 'capacity']):
            problem_types.append('Production Planning')
        
        # Portfolio Optimization
        if any(kw in text_lower for kw in ['portfolio', 'investment', 'asset']):
            problem_types.append('Portfolio Optimization')
        
        # Supply Chain
        if any(kw in text_lower for kw in ['supply chain', 'logistics', 'inventory']):
            problem_types.append('Supply Chain')
        
        return problem_types if problem_types else ['General Optimization']
    
    def extract_gurobi_patterns(self, code_blocks):
        """Extract common Gurobi modeling patterns"""
        patterns = {
            'variable_types': set(),
            'constraint_patterns': [],
            'objective_patterns': []
        }
        
        for code in code_blocks:
            # Variable types
            if 'GRB.BINARY' in code or 'vtype=GRB.BINARY' in code:
                patterns['variable_types'].add('binary')
            if 'GRB.INTEGER' in code or 'vtype=GRB.INTEGER' in code:
                patterns['variable_types'].add('integer')
            if 'GRB.CONTINUOUS' in code:
                patterns['variable_types'].add('continuous')
            
            # Constraint patterns
            if 'quicksum' in code.lower():
                patterns['constraint_patterns'].append('Uses quicksum for summations')
            if 'addConstrs' in code:
                patterns['constraint_patterns'].append('Uses addConstrs for multiple constraints')
            
            # Objective patterns
            if 'setObjective' in code:
                if 'GRB.MINIMIZE' in code:
                    patterns['objective_patterns'].append('minimize')
                if 'GRB.MAXIMIZE' in code:
                    patterns['objective_patterns'].append('maximize')
        
        return patterns
    
    def index_examples(self):
        """Index all Gurobi examples"""
        print("Indexing Gurobi modeling examples...")
        
        examples_path = Path(self.examples_root)
        
        # Find all example directories
        for example_dir in examples_path.iterdir():
            if not example_dir.is_dir() or example_dir.name.startswith(('_', '.')):
                continue
            
            print(f"  Processing: {example_dir.name}")
            
            # Find notebook and README
            notebooks = list(example_dir.glob('*.ipynb'))
            readme = example_dir / 'README.md'
            
            if not notebooks:
                continue
            
            # Process main notebook
            notebook_path = notebooks[0]
            content = self.extract_notebook_content(notebook_path)
            readme_text = self.extract_readme(readme) if readme.exists() else ""
            
            # Identify problem type
            full_text = content['text'] + '\n' + readme_text
            problem_types = self.identify_problem_type(full_text, content['code'])
            
            # Extract patterns
            patterns = self.extract_gurobi_patterns(content['code'])
            
            # Create index entry
            example_entry = {
                'name': example_dir.name,
                'path': str(notebook_path),
                'problem_types': problem_types,
                'description': readme_text[:500] if readme_text else content['text'][:500],
                'code_blocks': content['code'][:5],  # First 5 code blocks
                'patterns': {
                    'variable_types': list(patterns['variable_types']),
                    'constraint_patterns': patterns['constraint_patterns'][:3],
                    'objective_patterns': patterns['objective_patterns']
                },
                'full_text': full_text[:2000]  # For search
            }
            
            self.examples.append(example_entry)
        
        print(f"\n✓ Indexed {len(self.examples)} examples")
        return self.examples
    
    def save_index(self, output_file="gurobi_examples_index.json"):
        """Save index to file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.examples, f, indent=2, ensure_ascii=False)
        print(f"✓ Index saved to {output_file}")


# Run indexing
if __name__ == "__main__":
    indexer = GurobiExampleIndexer()
    indexer.index_examples()
    indexer.save_index()