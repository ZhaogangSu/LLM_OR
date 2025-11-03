# extract_gurobi_patterns.py
import json
import re
from collections import Counter

def analyze_gurobi_code_patterns(index_file="gurobi_examples_index.json"):
    """Extract actual Gurobi API patterns from indexed examples"""
    
    with open(index_file, 'r') as f:
        examples = json.load(f)
    
    print("="*70)
    print("GUROBI API PATTERN ANALYSIS")
    print("="*70)
    
    all_patterns = {
        'imports': Counter(),
        'model_creation': Counter(),
        'variable_creation': Counter(),
        'constraint_addition': Counter(),
        'objective_setting': Counter(),
        'solving': Counter(),
        'solution_access': Counter()
    }
    
    for example in examples:
        for code_block in example['code_blocks']:
            code = str(code_block)
            
            # Import patterns
            imports = re.findall(r'import\s+\w+.*', code)
            all_patterns['imports'].update(imports)
            
            # Model creation
            model_creates = re.findall(r'(\w+\s*=\s*gp\.Model\(.*?\))', code)
            all_patterns['model_creation'].update(model_creates)
            
            # Variable creation
            var_creates = re.findall(r'\.addVar\([^)]+\)', code)
            all_patterns['variable_creation'].update(var_creates[:5])  # Sample
            
            # Constraints
            constr_adds = re.findall(r'\.addConstr[s]?\([^)]+\)', code)
            all_patterns['constraint_addition'].update(constr_adds[:3])
            
            # Objective
            obj_sets = re.findall(r'\.setObjective\([^)]+\)', code)
            all_patterns['objective_setting'].update(obj_sets[:3])
            
            # Solving
            solves = re.findall(r'\.(optimize|solve)\(\)', code)
            all_patterns['solving'].update(solves)
            
            # Solution access
            sol_access = re.findall(r'\.(X|ObjVal|objVal)', code)
            all_patterns['solution_access'].update(sol_access)
    
    # Print results
    print("\n📦 Import Patterns (top 5):")
    for pattern, count in all_patterns['imports'].most_common(5):
        print(f"  {pattern} ({count}x)")
    
    print("\n🏗️  Model Creation Patterns (top 3):")
    for pattern, count in all_patterns['model_creation'].most_common(3):
        print(f"  {pattern} ({count}x)")
    
    print("\n📊 Variable Creation Patterns (top 5):")
    for pattern, count in all_patterns['variable_creation'].most_common(5):
        print(f"  {pattern[:60]}... ({count}x)")
    
    print("\n🔗 Constraint Patterns (top 5):")
    for pattern, count in all_patterns['constraint_addition'].most_common(5):
        print(f"  {pattern[:60]}... ({count}x)")
    
    print("\n🎯 Objective Setting Patterns (top 3):")
    for pattern, count in all_patterns['objective_setting'].most_common(3):
        print(f"  {pattern[:60]}... ({count}x)")
    
    print("\n⚙️  Solving Patterns:")
    for pattern, count in all_patterns['solving'].most_common(3):
        print(f"  .{pattern}() ({count}x)")
    
    print("\n📈 Solution Access Patterns:")
    for pattern, count in all_patterns['solution_access'].most_common(5):
        print(f"  .{pattern} ({count}x)")
    
    print("\n" + "="*70)
    
    # Save detailed analysis
    with open('gurobi_patterns_analysis.json', 'w') as f:
        json.dump({
            'imports': dict(all_patterns['imports'].most_common(10)),
            'model_creation': dict(all_patterns['model_creation'].most_common(5)),
            'variable_creation': dict(all_patterns['variable_creation'].most_common(10)),
            'constraint_addition': dict(all_patterns['constraint_addition'].most_common(10)),
            'objective_setting': dict(all_patterns['objective_setting'].most_common(5)),
            'solving': dict(all_patterns['solving'].most_common(5)),
            'solution_access': dict(all_patterns['solution_access'].most_common(5))
        }, f, indent=2)
    
    print("✓ Detailed analysis saved to gurobi_patterns_analysis.json")

if __name__ == "__main__":
    analyze_gurobi_code_patterns()