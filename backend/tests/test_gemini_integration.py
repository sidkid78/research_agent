#!/usr/bin/env python3
"""
Test script for Google Gemini AI integration
This script tests the research agent without requiring a full API key setup
"""

import asyncio
import os
from datetime import datetime, timezone
from app.schemas import ResearchRequest
from app.agent import GeminiResearchAgent
from dotenv import load_dotenv

load_dotenv()

async def test_agent_initialization():
    """Test that the agent can be initialized properly"""
    print("🧪 Testing Gemini Agent Initialization...")
    
    try:
        # Test without API key (should raise ValueError)
        try:
            # Clear environment variable for this test
            old_key = os.environ.get("GEMINI_API_KEY")
            if "GEMINI_API_KEY" in os.environ:
                del os.environ["GEMINI_API_KEY"]
            
            agent = GeminiResearchAgent(api_key=None)
            print("❌ Agent should require API key")
            return False
        except ValueError as e:
            print(f"✅ Correctly requires API key: {e}")
        finally:
            # Restore environment variable if it existed
            if old_key:
                os.environ["GEMINI_API_KEY"] = old_key
        
        # Test with dummy API key (for structure testing)
        agent = GeminiResearchAgent(api_key=os.getenv("GEMINI_API_KEY"))
        print("✅ Agent initialized with proper structure")
        
        # Test agent configuration
        assert agent.model_name == "gemini-2.5-flash"
        assert agent.generation_config.temperature == 0.3
        assert agent.generation_config.max_output_tokens == 8192
        print("✅ Agent configuration is correct")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return False

def test_schemas():
    """Test that schemas are properly defined"""
    print("\n🧪 Testing Schema Definitions...")
    
    try:
        from app.schemas import ResearchRequest, ResearchResult, Reference
        
        # Test ResearchRequest
        request = ResearchRequest(
            topic="Test topic",
            output_format="bullets"
        )
        print("✅ ResearchRequest schema works")
        
        # Test Reference
        ref = Reference(
            title="Test Reference",
            url="https://example.com",
            accessed_date=datetime.now(timezone.utc),
            snippet="Test snippet"
        )
        print("✅ Reference schema works")
        
        # Test ResearchResult
        result = ResearchResult(
            topic="Test topic",
            content="Test content",
            references=[ref],
            output_format="bullets",
            generated_at=datetime.now(timezone.utc),
            word_count=2,
            confidence_score=0.85
        )
        print("✅ ResearchResult schema works")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        return False

def test_helper_functions():
    """Test helper functions"""
    print("\n🧪 Testing Helper Functions...")
    
    try:
        from app.gemini_helpers import GeminiHelpers
        
        # Test context preparation
        sources = [
            {
                'title': 'Test Source',
                'url': 'https://example.com',
                'content': 'Test content for the source'
            }
        ]
        
        context = GeminiHelpers.prepare_research_context(sources, "test topic")
        assert "Research Topic: test topic" in context
        assert "Test Source" in context
        print("✅ Context preparation works")
        
        # Test reference extraction
        references = GeminiHelpers.extract_references(sources)
        assert len(references) == 1
        assert references[0].title == "Test Source"
        print("✅ Reference extraction works")
        
        return True
        
    except Exception as e:
        print(f"❌ Helper function test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Gemini Integration Tests\n")
    
    tests = [
        test_schemas(),
        test_helper_functions(),
        await test_agent_initialization(),
    ]
    
    passed = sum(tests)
    total = len(tests)
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Gemini integration is ready.")
        print("\n📋 Next Steps:")
        print("1. Set up your GEMINI_API_KEY environment variable")
        print("2. Get your API key from: https://aistudio.google.com/app/apikey")
        print("3. Test with a real research request")
        print("4. Check the GEMINI_SETUP.md file for detailed instructions")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())
