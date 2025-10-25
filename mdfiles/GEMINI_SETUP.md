# Google Gemini AI Integration Setup Guide

## Overview

Your research agent now uses Google's Gemini AI with the latest best practices including:

- **Context Caching** for efficient token usage
- **2M Context Window** with Gemini 1.5 Pro
- **Async Operations** for better performance
- **Robust Error Handling** with retry mechanisms
- **Safety Settings** configured for research use cases

## Setup Instructions

### 1. Get Your Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key

### 2. Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# backend/.env
GEMINI_API_KEY=your_api_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/research_agent
DEBUG=True
LOG_LEVEL=INFO
```

### 3. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## Key Features Implemented

### 1. Context Caching (Latest Feature)

The agent implements Google's context caching to:
- Reduce token usage by up to 50%
- Speed up response times
- Cache frequently used research contexts for 1 hour

```python
# Automatic context caching for research sources
cached_model = await GeminiHelpers.create_cached_context(content, model_name)
```

### 2. Optimized Model Configuration

```python
generation_config = {
    "temperature": 0.3,        # Lower for deterministic research
    "top_p": 0.8,             # Balanced creativity
    "top_k": 40,              # Focused vocabulary
    "max_output_tokens": 8192, # Large output capacity
}
```

### 3. Safety Settings

Configured for research use case:
- Allows academic and factual content
- Blocks harmful or inappropriate content
- Maintains research integrity

### 4. Multi-Stage Research Pipeline

1. **Query Generation**: Gemini generates optimized search queries
2. **Information Gathering**: Web scraping from multiple sources
3. **Content Analysis**: Gemini analyzes and synthesizes information
4. **Output Generation**: Formats results as bullets or full report

## Usage Examples

### Basic Research Request

```python
from app.agent import create_research_agent
from app.schemas import ResearchRequest

agent = create_research_agent()

request = ResearchRequest(
    topic="Latest developments in quantum computing",
    output_format="full_report",
    deadline=None
)

result = await agent.conduct_research(request)
print(result.content)
```

### With Context Caching Benefits

The agent automatically:
- Caches research context for similar topics
- Reuses cached content for faster responses
- Reduces API costs through efficient token usage

## Error Handling

The implementation includes:

1. **Retry Mechanisms**: Automatic retry with reduced parameters
2. **Fallback Strategies**: Graceful degradation when features fail
3. **Comprehensive Logging**: Detailed error tracking
4. **Rate Limiting**: Prevents API quota exhaustion

## Performance Optimizations

### Context Window Utilization

- **2M Token Context**: Processes extensive source material
- **Smart Chunking**: Efficiently manages large documents
- **Source Prioritization**: Focuses on most relevant content

### Async Operations

```python
# All operations are async for better performance
search_queries = await self._generate_search_queries(topic)
raw_sources = await self._gather_information(search_queries)
processed_content = await self._process_content_with_gemini(sources)
```

## Best Practices Implemented

### 1. Secure API Key Management
- Environment variable storage
- No hardcoded keys in source code
- Server-side implementation only

### 2. Efficient Prompt Engineering
- Structured prompts for better results
- Format-specific instructions
- Context-aware generation

### 3. Content Processing
- Multi-source information gathering
- Credibility assessment
- Fact-checking and verification

### 4. Output Optimization
- Format-specific generation (bullets vs full report)
- Word count management
- Reference extraction and formatting

## Monitoring and Logging

The agent provides comprehensive logging:

```python
logger.info(f"Starting research for topic: {request.topic}")
logger.info(f"Research completed for topic: {request.topic}")
logger.error(f"Research failed: {error_message}")
```

## Cost Optimization

### Context Caching Benefits

- **Token Savings**: Up to 50% reduction in token usage
- **Speed Improvement**: Faster response times
- **Automatic Management**: Cache expiry and renewal

### Efficient Resource Usage

- Rate limiting prevents quota exhaustion
- Smart content chunking reduces unnecessary tokens
- Fallback mechanisms prevent failed requests

## Next Steps

1. **Set up your API key** in the environment variables
2. **Test the basic functionality** with a simple research request
3. **Monitor performance** through the logging system
4. **Customize safety settings** if needed for your use case

## Troubleshooting

### Common Issues

1. **API Key Not Found**: Ensure `GEMINI_API_KEY` is set in `.env`
2. **Rate Limiting**: The agent includes automatic rate limiting
3. **Context Too Large**: Automatic chunking handles large content
4. **Safety Blocks**: Adjust safety settings if needed

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This setup gives you a production-ready research agent with the latest Gemini AI capabilities and best practices!

