# Core logic for the research agent using Google GenAI SDK (Latest)

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta, timezone
import json

from google import genai
from google.genai import types
import requests

from .schemas import ResearchRequest, ResearchResult, Reference

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiResearchAgent:
    """
    Advanced research agent using Google GenAI SDK (Latest) with best practices:
    - Unified client interface
    - Context caching for efficiency
    - Streaming responses
    - Enhanced error handling
    - Latest Gemini 2.5 Flash model support
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Gemini Research Agent with new SDK"""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Initialize the unified GenAI client
        self.client = genai.Client(api_key=self.api_key)
        
        # Model configuration for research use case
        self.model_name = "gemini-2.5-flash"  # Latest Gemini 2.0 Flash model
        self.generation_config = types.GenerateContentConfig(
            temperature=0.3,  # Lower for more deterministic research
            top_p=0.8,
            top_k=40,
            max_output_tokens=8192,
            response_mime_type="text/plain",
        )
        
        # Safety settings for research use case
        self.safety_settings = [
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            ),
        ]
        
        # Context management for efficiency
        self.cached_context = None
        self.cache_expiry = None
        
    async def conduct_research(self, request: ResearchRequest) -> ResearchResult:
        """
        Main research method implementing the full pipeline with Gemini AI
        """
        try:
            logger.info(f"Starting research for topic: {request.topic}")
            
            # Use comprehensive academic search from helpers
            from .gemini_helpers import AcademicGeminiHelpers
            search_results = await AcademicGeminiHelpers.comprehensive_academic_search(
                self.client, self.model_name, request.topic, 
                email=getattr(request, 'email', None)
            )
            
            # Extract sources from search results
            raw_sources = []
            for paper in search_results.get('arxiv_papers', []):
                raw_sources.append({
                    'title': paper.get('title', ''),
                    'url': paper.get('url', ''),
                    'snippet': paper.get('abstract', '')[:500],
                    'source': 'arxiv'
                })
            for paper in search_results.get('pubmed_papers', []):
                raw_sources.append({
                    'title': paper.get('title', ''),
                    'url': paper.get('url', ''),
                    'snippet': paper.get('abstract', '')[:500],
                    'source': 'pubmed'
                })
            for result in search_results.get('grounding_results', []):
                raw_sources.append({
                    'title': result.get('title', ''),
                    'url': result.get('url', ''),
                    'snippet': result.get('text', '')[:500],
                    'source': 'web'
                })
            
            # Process and analyze content with Gemini
            processed_content = await self._process_content_with_gemini(
                raw_sources, request.topic, request.output_format
            )
            
            # Step 4: Generate final research output
            research_output = await self._generate_research_output(
                processed_content, request
            )
            
            # Step 5: Extract references
            references = self._extract_references(raw_sources)
            
            result = ResearchResult(
                topic=request.topic,
                content=research_output,
                references=references,
                output_format=request.output_format,
                generated_at=datetime.utcnow(),
                word_count=len(research_output.split()),
                confidence_score=0.85  # Could be calculated based on source quality
            )
            
            logger.info(f"Research completed for topic: {request.topic}")
            return result
            
        except Exception as e:
            logger.error(f"Research failed for topic {request.topic}: {str(e)}")
            raise
    
    async def _generate_search_queries(self, topic: str) -> List[str]:
        """Generate optimized search queries using Gemini"""
        from .gemini_helpers import AcademicGeminiHelpers
        return await AcademicGeminiHelpers.generate_academic_search_queries(self.client, self.model_name, topic)
    
    async def _gather_information(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Gather information from multiple sources"""
        from .gemini_helpers import AcademicGeminiHelpers
        return await AcademicGeminiHelpers.gather_information(queries)
    
    async def _process_content_with_gemini(
        self, 
        sources: List[Dict[str, Any]], 
        topic: str, 
        output_format: str
    ) -> str:
        """Process and analyze gathered content using Gemini"""
        
        # Prepare context from sources
        context_parts = []
        for i, source in enumerate(sources[:20], 1):  # Limit to 20 sources
            context_parts.append(f"""
Source {i}:
Title: {source.get('title', 'Unknown')}
URL: {source.get('url', 'N/A')}
Content: {source.get('snippet', 'No content available')}
---""")
        
        context_to_use = "\n".join(context_parts)
        
        analysis_prompt = f"""You are a research analyst. Analyze the provided sources about "{topic}" and create a comprehensive research synthesis.

IMPORTANT: You MUST use ONLY the information from the provided sources below. Do NOT use your general knowledge or training data.

Sources and Content:
{context_to_use}

Analysis Requirements:
- Extract key facts, findings, and insights ONLY from the provided sources
- Identify recent developments and breakthroughs mentioned in the sources
- Note any conflicting information between sources
- Assess the credibility and recency of each source
- Highlight specific technologies, standards, protocols, or research findings mentioned
- Focus on concrete examples and specific implementations discussed in the sources

If the provided sources do not contain sufficient information about "{topic}", explicitly state this limitation.

Provide a detailed analysis that synthesizes the source material for a {output_format} format output."""
        
        try:
            # Use streaming for large analysis tasks
            response = await self._generate_content_async(analysis_prompt, use_streaming=True)
            return response
        except Exception as e:
            logger.error(f"Content processing failed: {e}")
            # Fallback without streaming
            return await self._generate_content_async(analysis_prompt, use_streaming=False)
    
    async def _generate_research_output(
        self, 
        processed_content: str, 
        request: ResearchRequest
    ) -> str:
        """Generate final research output in requested format"""
        
        format_instructions = {
            "bullets": """
            Format as bullet points:
            - Use clear, concise bullet points
            - Organize by main themes/categories
            - Include sub-bullets for details
            - Maximum 15-20 main points
            """,
            "full_report": """
            Format as a comprehensive report:
            - Executive summary (2-3 sentences)
            - Main sections with clear headings
            - Detailed analysis with supporting evidence
            - Conclusions and implications
            - 1000-2000 words total
            """
        }
        
        prompt = f"""
        Create a comprehensive research output about "{request.topic}" based on the following analysis:
        
        {processed_content}
        
        {format_instructions.get(request.output_format, format_instructions["bullets"])}
        
        Additional requirements:
        - Ensure accuracy and factual correctness
        - Use professional, clear language
        - Include specific examples and data where available
        - Maintain objectivity and balance
        - Focus on the most important and relevant information
        """
        
        try:
            response = await self._generate_content_async(prompt)
            return response
        except Exception as e:
            logger.error(f"Research output generation failed: {e}")
            raise
    
    async def _generate_content_async(
        self, 
        prompt: str, 
        use_streaming: bool = False
    ) -> str:
        """Generate content asynchronously using new SDK patterns"""
        try:
            # Use direct API call - no request wrapper needed
            
            if use_streaming:
                # Use streaming for large responses
                response_stream = await self.client.aio.models.generate_content_stream(
                    model=self.model_name,
                    contents=prompt,
                    config=self.generation_config
                )
                content_parts = []
                async for chunk in response_stream:
                    if chunk.text:
                        content_parts.append(chunk.text)
                return "".join(content_parts)
            else:
                # Use standard generation
                response = await self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=self.generation_config
                )
                return response.text if response.text else ""
                    
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            # Retry with reduced parameters
            try:
                reduced_config = types.GenerateContentConfig(
                    temperature=0.3,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=4096,  # Reduced
                    response_mime_type="text/plain",
                )
                
                response = await self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=reduced_config
                )
                return response.text if response.text else ""
                    
            except Exception as retry_e:
                logger.error(f"Retry also failed: {retry_e}")
                raise e
    
    def _is_cache_valid(self) -> bool:
        """Check if cached context is still valid"""
        if not self.cached_context or not self.cache_expiry:
            return False
        return datetime.now(timezone.utc) < self.cache_expiry
    
    async def _create_cached_context(self, content: str) -> bool:
        """Create a cached context for efficient token usage using helpers"""
        from .gemini_helpers import AcademicGeminiHelpers
        
        try:
            cache_data = await AcademicGeminiHelpers.create_cached_context(
                self.client, content, self.model_name
            )
            if cache_data:
                self.cached_context = cache_data["content"]
                self.cache_expiry = cache_data["expires_at"]
                return True
            return False
        except Exception as e:
            logger.warning(f"Failed to cache context: {e}")
            return False
    
    def _extract_references(self, sources: List[Dict[str, Any]]) -> List[Reference]:
        """Extract and format references from sources"""
        from .gemini_helpers import AcademicGeminiHelpers
        
        # Separate sources by type
        arxiv_papers = [s for s in sources if s.get('source') == 'arxiv']
        pubmed_papers = [s for s in sources if s.get('source') == 'pubmed']
        grounding_results = [s for s in sources if s.get('source') == 'web']
        
        return AcademicGeminiHelpers.extract_academic_references(
            arxiv_papers, pubmed_papers, grounding_results
        )

# Factory function for creating the agent
def create_research_agent() -> GeminiResearchAgent:
    """Factory function to create a research agent instance"""
    return GeminiResearchAgent() 