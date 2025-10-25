#!/usr/bin/env python3
"""Debug content extraction"""

import asyncio
from app.gemini_helpers import GeminiHelpers

async def test_content_extraction():
    """Test if we can extract content from search results"""
    
    # Test with some common sites
    test_urls = [
        "https://www.nist.gov/topics/cybersecurity",
        "https://en.wikipedia.org/wiki/Quantum_cryptography",
        "https://www.ibm.com/quantum",
    ]
    
    for url in test_urls:
        print(f"\n🔍 Testing: {url}")
        content = await GeminiHelpers.fetch_url_content(url)
        if content:
            print(f"✅ Extracted {len(content)} characters")
            print(f"Preview: {content[:200]}...")
        else:
            print("❌ Failed to extract content")

if __name__ == "__main__":
    asyncio.run(test_content_extraction())
