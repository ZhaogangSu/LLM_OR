# inspect_knowledge.py
import json
from collections import Counter

def inspect_knowledge_base(kb_dir="copt_knowledge_base"):
    """Inspect the collected knowledge base"""
    
    print("=" * 60)
    print("COPT Knowledge Base Inspection")
    print("=" * 60)
    
    # Load flat sections
    with open(f"{kb_dir}/copt_flat_sections.jsonl", 'r', encoding='utf-8') as f:
        sections = [json.loads(line) for line in f]
    
    print(f"\n📊 Total Sections: {len(sections)}")
    
    # Analyze hierarchy levels
    levels = [s['section_level'] for s in sections]
    print(f"\n📈 Hierarchy Levels:")
    for level, count in sorted(Counter(levels).items()):
        print(f"  Level {level}: {count} sections")
    
    # Show section categories
    print(f"\n📚 Top-level Categories:")
    top_level = [s for s in sections if s['section_level'] <= 1]
    for i, section in enumerate(top_level[:20], 1):
        print(f"  {i}. {section['title']}")
    
    # Analyze content statistics
    total_content = sum(len(s['content']) for s in sections)
    total_code = sum(len(s['code_examples']) for s in sections)
    
    print(f"\n📝 Content Statistics:")
    print(f"  Total text: {total_content:,} characters")
    print(f"  Average per section: {total_content // len(sections):,} chars")
    print(f"  Total code examples: {total_code}")
    print(f"  Sections with code: {sum(1 for s in sections if s['code_examples'])}")
    
    # Show example sections with code
    print(f"\n💻 Sample Sections with Code Examples:")
    sections_with_code = [s for s in sections if s['code_examples']][:5]
    for section in sections_with_code:
        print(f"\n  Title: {section['title']}")
        print(f"  URL: {section['url']}")
        print(f"  Code examples: {len(section['code_examples'])}")
        if section['code_examples']:
            print(f"  First example preview: {section['code_examples'][0][:100]}...")
    
    # Check for key topics
    print(f"\n🔍 Key Topics Coverage:")
    key_topics = ['variable', 'constraint', 'objective', 'solve', 'model', 
                  'parameter', 'callback', 'solution', 'optimization']
    for topic in key_topics:
        count = sum(1 for s in sections if topic.lower() in s['content'].lower())
        print(f"  '{topic}': found in {count} sections")
    
    return sections

if __name__ == "__main__":
    sections = inspect_knowledge_base()