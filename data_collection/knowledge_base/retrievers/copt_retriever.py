# copt_retriever.py
import json
import re
from typing import List, Dict
from collections import defaultdict
import numpy as np

class COPTRetriever:
    """Improved retriever with Python API focus"""
    
    def __init__(self, kb_dir="knowledge_base/data/copt_knowledge_base"):
        self.kb_dir = kb_dir
        self.sections = self._load_sections()
        self._filter_python_sections()
        self._build_keyword_index()
        print(f"✓ Loaded {len(self.sections)} sections ({len(self.python_sections)} Python-specific)")
    
    def _load_sections(self):
        """Load all sections"""
        sections = []
        # FIX: Construct the correct file path
        jsonl_file = f"{self.kb_dir}/copt_flat_sections.jsonl"
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                sections.append(json.loads(line))
        return sections
    
    def _filter_python_sections(self):
        """Identify Python-specific sections"""
        self.python_sections = []
        self.other_sections = []
        
        python_indicators = [
            'python api', 'pyapi', '.py', 'import coptpy',
            'model.addvar', 'model.addconstr', 'env.createmodel'
        ]
        
        for i, section in enumerate(self.sections):
            url_lower = section['url'].lower()
            title_lower = section['title'].lower()
            content_lower = section['content'].lower()
            
            # Check if this is Python-related
            is_python = (
                'pyapi' in url_lower or
                'python' in title_lower or
                any(indicator in content_lower for indicator in python_indicators) or
                any(code for code in section['code_examples'] 
                    if 'import coptpy' in code or 'from coptpy' in code)
            )
            
            if is_python:
                self.python_sections.append(i)
            else:
                self.other_sections.append(i)
    
    def _build_keyword_index(self):
        """Build inverted index for fast keyword search"""
        self.keyword_index = defaultdict(list)
        
        # Index Python sections with higher priority
        for i in self.python_sections:
            section = self.sections[i]
            text = f"{section['title']} {section['content']}".lower()
            words = re.findall(r'\w+', text)
            
            for word in set(words):
                if len(word) > 2:
                    self.keyword_index[word].append(i)
        
        # Also index other sections but mark them
        for i in self.other_sections:
            section = self.sections[i]
            text = f"{section['title']} {section['content']}".lower()
            words = re.findall(r'\w+', text)
            
            for word in set(words):
                if len(word) > 2 and i not in self.keyword_index[word]:
                    self.keyword_index[word].append(i)
    
    def search_by_keywords(self, keywords: List[str], 
                          top_k: int = 5, 
                          python_only: bool = True) -> List[Dict]:
        """Search with improved scoring and Python filtering"""
        if isinstance(keywords, str):
            keywords = [keywords]
        
        keywords = [k.lower() for k in keywords]
        section_scores = defaultdict(float)
        
        for keyword in keywords:
            matching_sections = self.keyword_index.get(keyword, [])
            idf = np.log(len(self.sections) / (len(matching_sections) + 1))
            
            for section_idx in matching_sections:
                section = self.sections[section_idx]
                text = f"{section['title']} {section['content']}".lower()
                tf = text.count(keyword)
                
                # Base score
                score = tf * idf
                
                # Boost Python sections significantly
                if section_idx in self.python_sections:
                    score *= 5.0
                
                # Boost if keyword in title
                if keyword in section['title'].lower():
                    score *= 3.0
                
                # Boost if has relevant code examples
                if section['code_examples']:
                    # Check if code examples contain the keyword
                    relevant_code = sum(1 for code in section['code_examples'] 
                                      if keyword in code.lower())
                    if relevant_code > 0:
                        score *= (1 + relevant_code * 0.5)
                
                # Penalize overly long sections (too generic)
                if len(section['content']) > 10000:
                    score *= 0.3
                
                # Penalize sections with too many code examples (API reference dumps)
                if len(section['code_examples']) > 100:
                    score *= 0.2
                
                section_scores[section_idx] += score
        
        # Filter Python only if requested
        if python_only:
            section_scores = {k: v for k, v in section_scores.items() 
                            if k in self.python_sections}
        
        # Sort and return top_k
        sorted_sections = sorted(section_scores.items(), 
                                key=lambda x: x[1], 
                                reverse=True)[:top_k]
        
        results = []
        for section_idx, score in sorted_sections:
            section = self.sections[section_idx].copy()
            section['relevance_score'] = score
            section['is_python'] = section_idx in self.python_sections
            results.append(section)
        
        return results
    
    def format_reference(self, sections: List[Dict], 
                        max_content_length: int = 800) -> str:
        """Format retrieved sections as concise reference"""
        if not sections:
            return "No relevant references found."
        
        reference_text = "## COPT Python API References\n\n"
        
        for i, section in enumerate(sections, 1):
            reference_text += f"### Reference {i}: {section['title']}\n"
            reference_text += f"**Relevance**: {section['relevance_score']:.1f} | "
            reference_text += f"**Python API**: {'Yes' if section.get('is_python') else 'No'}\n\n"
            
            # Add truncated content
            content = section['content']
            if len(content) > max_content_length:
                content = content[:max_content_length] + "...\n"
            reference_text += f"{content}\n\n"
            
            # Add most relevant code examples (max 3)
            if section['code_examples']:
                reference_text += "**Code Examples:**\n"
                relevant_codes = [code for code in section['code_examples'] 
                                if 20 < len(code) < 500][:3]
                for code in relevant_codes:
                    reference_text += f"```python\n{code}\n```\n"
            
            reference_text += "\n---\n\n"
        
        return reference_text
    
# Test
if __name__ == "__main__":
    retriever = COPTRetriever()
    
    print("="*70)
    print("Test 1: Get methods for variable creation")
    print("="*70)
    methods = retriever.get_methods_by_keywords(['variable', 'addvars'])
    print(f"Found methods: {methods}\n")
    
    formatted = retriever.format_for_prompt(methods, include_all_details=False)
    print(formatted)
    
    print("\n" + "="*70)
    print("Test 2: Essential API Guide")
    print("="*70)
    print(retriever.get_essential_api_guide())