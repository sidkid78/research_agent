#!/usr/bin/env python3
"""Test ArXiv integration"""

import asyncio
from app.gemini_helpers import GeminiHelpers

async def test_arxiv_search():
    """Test ArXiv search functionality"""
    
    # Test quantum computing topic
    topic = "quantum computing cybersecurity"
    
    print(f"🔬 Testing ArXiv search for: {topic}")
    
    try:
        papers = await GeminiHelpers.search_arxiv_papers(topic, max_results=3)
        
        print(f"✅ Found {len(papers)} ArXiv papers")
        
        for i, paper in enumerate(papers, 1):
            print(f"\n📄 Paper {i}:")
            print(f"   Title: {paper['title'][:80]}...")
            print(f"   Authors: {paper.get('authors', 'N/A')}")
            print(f"   Published: {paper.get('published', 'N/A')}")
            print(f"   Categories: {paper.get('categories', 'N/A')}")
            print(f"   URL: {paper['url']}")
            print(f"   Abstract length: {len(paper.get('content', ''))} chars")
        
        return True
        
    except Exception as e:
        print(f"❌ ArXiv search failed: {e}")
        return False

async def test_combined_search():
    """Test combined ArXiv + web search"""
    
    queries = ["quantum cryptography", "post-quantum security"]
    
    print(f"\n🔍 Testing combined search with queries: {queries}")
    
    try:
        all_sources = await GeminiHelpers.gather_information(queries)
        
        arxiv_count = len([s for s in all_sources if s.get('publisher') == 'arXiv'])
        web_count = len(all_sources) - arxiv_count
        
        print(f"✅ Total sources: {len(all_sources)}")
        print(f"   📚 ArXiv papers: {arxiv_count}")
        print(f"   🌐 Web sources: {web_count}")
        
        # Show a few examples
        for i, source in enumerate(all_sources[:3], 1):
            source_type = "📚 ArXiv" if source.get('publisher') == 'arXiv' else "🌐 Web"
            print(f"\n{source_type} Source {i}:")
            print(f"   Title: {source['title'][:60]}...")
            print(f"   Content length: {len(source.get('content', ''))} chars")
        
        return True
        
    except Exception as e:
        print(f"❌ Combined search failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🧪 Testing ArXiv Integration")
    print("=" * 50)
    
    test1 = await test_arxiv_search()
    test2 = await test_combined_search()
    
    if test1 and test2:
        print("\n🎉 All ArXiv tests passed!")
    else:
        print("\n💥 Some tests failed")

if __name__ == "__main__":
    asyncio.run(main())
