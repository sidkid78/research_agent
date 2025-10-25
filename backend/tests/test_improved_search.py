#!/usr/bin/env python3
"""Test the improved search and content extraction"""

import asyncio
import os
from app.agent import create_research_agent
from app.schemas import ResearchRequest

async def test_improved_search():
    """Test if the improved search generates better, more relevant content"""
    try:
        print("🧪 Testing improved search capabilities...")
        
        # Create agent
        agent = create_research_agent()
        print("✅ Agent created successfully")
        
        # Test with a specific, technical topic
        request = ResearchRequest(
            topic="Latest quantum key distribution protocols for secure communications 2024",
            output_format="bullets"
        )
        
        print(f"🔍 Testing with topic: {request.topic}")
        
        # Check if we have API key
        if not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
            print("⚠️  No API key found - testing search queries only")
            
            # Test just the query generation
            queries = await agent._generate_search_queries(request.topic)
            print(f"✅ Generated {len(queries)} search queries:")
            for i, query in enumerate(queries, 1):
                print(f"   {i}. {query}")
            
            # Test information gathering (without API key, will use fallback)
            sources = await agent._gather_information(queries[:3])  # Test with first 3 queries
            print(f"✅ Gathered {len(sources)} sources")
            
            for i, source in enumerate(sources[:3], 1):
                print(f"   Source {i}: {source.get('title', 'No title')[:60]}...")
                print(f"   URL: {source.get('url', 'No URL')}")
                print(f"   Content length: {len(source.get('content', ''))} chars")
                print()
            
        else:
            print("🚀 API key found - running full research test")
            
            # Run full research
            result = await agent.conduct_research(request)
            
            print("✅ Research completed!")
            print(f"📊 Topic: {result.topic}")
            print(f"📝 Content length: {len(result.content)} characters")
            print(f"📚 References: {len(result.references)}")
            print(f"🎯 Confidence: {result.confidence_score:.1%}")
            print(f"💪 Word count: {result.word_count}")
            
            # Show first few lines of content
            lines = result.content.split('\n')[:5]
            print("📄 Content preview:")
            for line in lines:
                if line.strip():
                    print(f"   {line.strip()}")
            
            # Show references
            print("📖 References:")
            for i, ref in enumerate(result.references[:3], 1):
                print(f"   {i}. {ref.title[:60]}...")
                print(f"      {ref.url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_improved_search())
    print("\n" + "="*60)
    if success:
        print("🎉 Improved search test completed successfully!")
    else:
        print("💥 Improved search test failed!")

