import requests
from bs4 import BeautifulSoup
import json
import os
from urllib.parse import urljoin, urlparse
from collections import deque
import time

class COPTDocCrawler:
    def __init__(self, base_url, output_dir="copt_knowledge_base"):
        self.base_url = base_url
        self.output_dir = output_dir
        self.visited = set()
        self.doc_structure = []
        
        os.makedirs(output_dir, exist_ok=True)
    
    def is_valid_doc_url(self, url):
        """Check if URL belongs to the documentation"""
        parsed = urlparse(url)
        return (parsed.netloc == urlparse(self.base_url).netloc and 
                '/copt/en-doc/' in url and
                not url.endswith(('.pdf', '.zip', '.png', '.jpg')))
    
    def extract_section_info(self, soup, url):
        """Extract section title, content, and metadata"""
        # Try to find the main content area
        main_content = soup.find('div', class_='document') or soup.find('main') or soup.find('article')
        
        if not main_content:
            main_content = soup.find('body')
        
        # Extract title
        title = soup.find('h1')
        title_text = title.get_text(strip=True) if title else "Unknown Section"
        
        # Extract all text content
        # Remove navigation, footer, etc.
        for element in main_content.find_all(['nav', 'footer', 'script', 'style']):
            element.decompose()
        
        content = main_content.get_text(separator='\n', strip=True)
        
        # Extract code examples
        code_blocks = []
        for code in main_content.find_all(['pre', 'code']):
            code_text = code.get_text(strip=True)
            if len(code_text) > 20:  # Filter out inline code
                code_blocks.append(code_text)
        
        # Extract section hierarchy from breadcrumbs or URL
        breadcrumbs = soup.find('div', class_='breadcrumbs') or soup.find('nav', class_='breadcrumb')
        hierarchy = []
        if breadcrumbs:
            for link in breadcrumbs.find_all('a'):
                hierarchy.append(link.get_text(strip=True))
        
        return {
            'url': url,
            'title': title_text,
            'hierarchy': hierarchy,
            'content': content,
            'code_examples': code_blocks,
            'section_level': len(hierarchy)
        }
    
    def crawl_documentation(self, start_url, max_pages=500):
        """Crawl the documentation site with BFS"""
        queue = deque([start_url])
        self.visited.add(start_url)
        page_count = 0
        
        print(f"Starting to crawl {start_url}")
        
        while queue and page_count < max_pages:
            current_url = queue.popleft()
            page_count += 1
            
            print(f"[{page_count}/{max_pages}] Crawling: {current_url}")
            
            try:
                response = requests.get(current_url, timeout=10)
                response.raise_for_status()
                time.sleep(0.5)  # Be respectful to the server
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract section information
                section_info = self.extract_section_info(soup, current_url)
                self.doc_structure.append(section_info)
                
                # Find all links in the page
                for link in soup.find_all('a', href=True):
                    absolute_url = urljoin(current_url, link['href'])
                    # Remove fragments
                    absolute_url = absolute_url.split('#')[0]
                    
                    if (absolute_url not in self.visited and 
                        self.is_valid_doc_url(absolute_url)):
                        self.visited.add(absolute_url)
                        queue.append(absolute_url)
                
            except Exception as e:
                print(f"Error crawling {current_url}: {e}")
                continue
        
        print(f"\nCrawling complete! Processed {page_count} pages.")
        return self.doc_structure
    
    def build_hierarchical_structure(self):
        """Organize flat list into hierarchical structure"""
        # Sort by URL depth and hierarchy
        sorted_docs = sorted(self.doc_structure, 
                           key=lambda x: (len(x['hierarchy']), x['url']))
        
        # Build tree structure
        tree = {
            'title': 'COPT Documentation Root',
            'children': [],
            'sections': {}
        }
        
        for doc in sorted_docs:
            # Create nested structure based on hierarchy
            current_level = tree
            for i, level_name in enumerate(doc['hierarchy']):
                if level_name not in current_level['sections']:
                    current_level['sections'][level_name] = {
                        'title': level_name,
                        'children': [],
                        'sections': {},
                        'content': None
                    }
                current_level = current_level['sections'][level_name]
            
            # Add the actual content at the leaf
            current_level['content'] = {
                'title': doc['title'],
                'url': doc['url'],
                'text': doc['content'],
                'code_examples': doc['code_examples']
            }
        
        return tree
    
    def save_knowledge_base(self, structure):
        """Save the knowledge base in multiple formats"""
        # 1. Save as JSON
        json_path = os.path.join(self.output_dir, 'copt_knowledge_base.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(structure, f, indent=2, ensure_ascii=False)
        print(f"Saved JSON structure to {json_path}")
        
        # 2. Save flat list for easy searching
        flat_path = os.path.join(self.output_dir, 'copt_flat_sections.jsonl')
        with open(flat_path, 'w', encoding='utf-8') as f:
            for doc in self.doc_structure:
                f.write(json.dumps(doc, ensure_ascii=False) + '\n')
        print(f"Saved flat sections to {flat_path}")
        
        # 3. Save section index for quick lookup
        index = {}
        for doc in self.doc_structure:
            key = doc['title'].lower()
            index[key] = {
                'url': doc['url'],
                'hierarchy': doc['hierarchy'],
                'summary': doc['content'][:200] + '...'
            }
        
        index_path = os.path.join(self.output_dir, 'section_index.json')
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
        print(f"Saved section index to {index_path}")


# Usage
if __name__ == "__main__":
    crawler = COPTDocCrawler(
        base_url="https://guide.coap.online/copt/en-doc/index.html",
        output_dir="copt_knowledge_base"
    )
    
    # Crawl the documentation
    doc_structure = crawler.crawl_documentation(
        start_url="https://guide.coap.online/copt/en-doc/index.html",
        max_pages=500
    )
    
    # Build hierarchical structure
    hierarchical = crawler.build_hierarchical_structure()
    
    # Save in multiple formats
    crawler.save_knowledge_base(hierarchical)
    
    print("\n✓ Knowledge base construction complete!")
    print(f"Total sections: {len(doc_structure)}")