# knowledge_base/builders/extract_copt_essential_v2.py
"""
Extract essential COPT API methods - FIXED VERSION
"""

import re
import json
from bs4 import BeautifulSoup

ESSENTIAL_METHODS = {
    'Model.addVar': 'model-addvar',
    'Model.addVars': 'model-addvars',
    'Model.addConstr': 'model-addconstr',
    'Model.addConstrs': 'model-addconstrs',
    'Model.setObjective': 'model-setobjective',
    'Model.solve': 'model-solve',
    'Envr.__init__': 'envr',
    'Envr.createModel': 'envr-createmodel',
}

def extract_essential_methods(html_file):
    """Extract only the essential methods with complete information"""
    
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    methods = {}
    
    for method_name, section_id in ESSENTIAL_METHODS.items():
        print(f"Extracting: {method_name}...")
        
        section = soup.find('section', id=section_id)
        if not section:
            print(f"  ⚠️  Section not found: {section_id}")
            continue
        
        method_info = extract_method_info_v2(section, method_name)
        
        if method_info:
            methods[method_name] = method_info
            print(f"  ✓ Signature: {method_info['signature'][:50]}...")
            print(f"  ✓ Parameters: {len(method_info['parameters'])}")
            print(f"  ✓ Examples: {len(method_info['examples'])}")
        else:
            print(f"  ❌ Failed to extract")
    
    return methods

def extract_method_info_v2(section, method_name):
    """Extract complete method info with better parsing"""
    
    info = {
        'method_name': method_name,
        'signature': '',
        'description': '',
        'parameters': {},
        'returns': '',
        'examples': []
    }
    
    # Strategy: Walk through the section linearly
    # Structure is: <p><strong>Section</strong></p> followed by <blockquote>content</blockquote>
    
    current_section = None
    
    for element in section.descendants:
        # Check if this is a section header
        if element.name == 'strong':
            current_section = element.get_text().strip()
            continue
        
        # Process based on current section
        if current_section == 'Synopsis' and element.name == 'code':
            if not info['signature']:  # Only take first one
                info['signature'] = element.get_text().strip()
        
        elif current_section == 'Description' and element.name == 'p':
            # Get description text (avoid nested blockquotes)
            if element.parent.name == 'blockquote' and not info['description']:
                info['description'] = element.get_text().strip()
        
        elif current_section == 'Arguments':
            # Will handle separately
            pass
    
    # Extract parameters separately (more reliable)
    info['parameters'] = extract_parameters_v2(section)
    
    # Extract returns
    info['returns'] = extract_returns(section)
    
    # Extract examples and DEDUPLICATE
    all_examples = extract_examples_v2(section)
    info['examples'] = list(dict.fromkeys(all_examples))  # Remove duplicates while preserving order
    
    return info if info['signature'] else None

def extract_parameters_v2(section):
    """Extract parameters more reliably"""
    params = {}
    
    # Find the Arguments paragraph
    for p in section.find_all('p'):
        strong = p.find('strong')
        if strong and strong.get_text().strip() == 'Arguments':
            # Found Arguments section
            # Parameters are in the next blockquote
            next_bq = p.find_next_sibling('blockquote')
            if next_bq:
                # Each parameter is: <p><code>name</code></p> followed by <blockquote><p>desc</p></blockquote>
                param_elements = next_bq.find_all('p', recursive=False)
                
                for param_p in param_elements:
                    code = param_p.find('code')
                    if code:
                        param_name = code.get_text().strip()
                        
                        # Find description in next blockquote
                        desc_bq = param_p.find_next_sibling('blockquote')
                        if desc_bq:
                            desc_p = desc_bq.find('p')
                            if desc_p:
                                params[param_name] = desc_p.get_text().strip()
            break
    
    return params

def extract_returns(section):
    """Extract return value"""
    for p in section.find_all('p'):
        strong = p.find('strong')
        if strong and 'Return' in strong.get_text():
            # Found Returns/Return value section
            next_bq = p.find_next_sibling('blockquote')
            if next_bq:
                desc_p = next_bq.find('p')
                if desc_p:
                    return desc_p.get_text().strip()
    return ''

def extract_examples_v2(section):
    """Extract all code examples from section"""
    examples = []
    
    # Find all highlight-python divs
    for div in section.find_all('div', class_='highlight-python'):
        pre = div.find('pre')
        if pre:
            code = pre.get_text().strip()
            if code and len(code) > 5:
                examples.append(code)
    
    return examples

def add_critical_notes(methods):
    """Add critical usage notes"""
    
    if 'Model.addVar' in methods:
        methods['Model.addVar'].update({
            'critical_note': '✓ ACCEPTS "name" parameter. Use for single named variables.',
            'correct_usage': [
                "x = model.addVar(vtype=COPT.INTEGER, name='x')",
                "S = model.addVar(vtype=COPT.CONTINUOUS, name='S')"
            ]
        })
    
    if 'Model.addVars' in methods:
        methods['Model.addVars'].update({
            'critical_note': '✗ Does NOT accept "name" parameter! Only accepts "nameprefix".',
            'correct_usage': [
                "# Unnamed (auto-generated names)",
                "x = model.addVars(4, vtype=COPT.INTEGER)  # Creates x[0], x[1], x[2], x[3]",
                "",
                "# With prefix",
                "x = model.addVars(4, vtype=COPT.INTEGER, nameprefix='x')  # Creates x0, x1, x2, x3"
            ],
            'wrong_usage': "x = model.addVars(4, name='x')  # ERROR: unexpected keyword 'name'",
            'alternative': "# For custom names, use dict comprehension:\nx = {i: model.addVar(vtype=COPT.INTEGER, name=f'x_{i}') for i in range(4)}"
        })
    
    if 'Model.solve' in methods:
        methods['Model.solve'].update({
            'critical_note': 'Always check model.status == COPT.OPTIMAL before accessing solution.',
            'correct_usage': [
                "model.solve()",
                "if model.status == COPT.OPTIMAL:",
                "    print(f'Optimal objective: {model.objval}')"
            ]
        })
    
    if 'Envr.createModel' in methods:
        methods['Envr.createModel'].update({
            'critical_note': 'COPT requires Envr() first, unlike Gurobi which uses gp.Model() directly.',
            'correct_usage': [
                "env = cp.Envr()",
                "model = env.createModel('problem_name')"
            ]
        })
    
    return methods

if __name__ == "__main__":
    html_file = '/home/szg/Su/LLM_OR/Python API Reference — Cardinal Optimizer (COPT) User~Guide, Ver8.0.html'
    
    print("="*70)
    print("Extracting Essential COPT API Methods (v2)")
    print("="*70)
    print()
    
    methods = extract_essential_methods(html_file)
    
    if not methods:
        print("\n❌ No methods extracted!")
    else:
        # Add critical notes
        methods = add_critical_notes(methods)
        
        # Add URLs
        for method_name in methods:
            section_id = ESSENTIAL_METHODS[method_name]
            methods[method_name]['url'] = f"https://guide.coap.online/copt/en-doc/pyapiref.html#{section_id}"
        
        # Save to file
        output_file = '../data/copt_knowledge_base/copt_api_essential.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(methods, f, indent=2, ensure_ascii=False)
        
        print()
        print("="*70)
        print("SUMMARY")
        print("="*70)
        print(f"✓ Extracted: {len(methods)}/{len(ESSENTIAL_METHODS)} methods")
        print(f"✓ Saved to: {output_file}")
        print()
        
        # Show details
        print("Method Details:")
        print("-"*70)
        for method_name, info in methods.items():
            print(f"\n{method_name}:")
            print(f"  Signature: {info['signature'][:80]}")
            print(f"  Params: {list(info['parameters'].keys())}")
            print(f"  Examples: {len(info['examples'])} (deduplicated)")
            if info.get('critical_note'):
                print(f"  ⚠️  {info['critical_note']}")