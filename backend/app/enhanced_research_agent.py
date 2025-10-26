"""
Enhanced Research Agent with Academic APIs and Google Grounding

This module provides a comprehensive research agent that integrates multiple academic
and web-based sources to conduct thorough research on any given topic.

Key Features:
- arXiv API integration for computer science, physics, and mathematics papers
- PubMed API integration for biomedical and life sciences literature
- Google Grounding with Search for authoritative web information
- Intelligent source selection based on topic analysis
- Comprehensive synthesis of academic and web sources
- Proper citation and reference management

The agent uses Google's Gemini models for analysis, synthesis, and content generation,
ensuring high-quality research outputs with proper academic rigor.
"""

import os
import asyncio
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from collections import Counter
import logging
import xml.etree.ElementTree as ET

from google import genai
from google.genai import types
from google.genai.errors import APIError
from google.genai.types import Type
from Bio import Entrez
import arxiv

from .schemas import ResearchRequest, ResearchResult, Reference

logger = logging.getLogger(__name__)

class EnhancedResearchAgent:
    """
    Enhanced research agent using academic APIs and Google Grounding.
    
    This agent conducts comprehensive research by:
    - Searching arXiv for computer science, physics, mathematics papers
    - Searching PubMed for biomedical and life sciences literature
    - Using Google Grounding with Search for web-based information
    - Synthesizing information from multiple authoritative sources
    
    The agent prioritizes peer-reviewed academic sources and uses AI-powered
    analysis to determine the best research strategy for each topic.
    
    Attributes:
        api_key (str): Google Gemini API key for AI operations
        email (str): Email address for PubMed API access
        client (genai.Client): Google GenAI client instance
        models (dict): Configuration for different Gemini models
        generation_config (types.GenerateContentConfig): AI generation settings
        research_functions (list): Function definitions for research operations
        cache (dict): Cache for API results to reduce redundant calls
    """
    
    def __init__(self, api_key: Optional[str] = None, email: Optional[str] = None):
        """
        Initialize the enhanced research agent with API keys and configuration.
        
        Args:
            api_key (Optional[str]): Google Gemini API key. If not provided,
                will attempt to read from GEMINI_API_KEY environment variable.
            email (Optional[str]): Email address for PubMed API access. If not
                provided, will attempt to read from RESEARCH_EMAIL environment
                variable. Required for full PubMed functionality.
        
        Raises:
            ValueError: If GEMINI_API_KEY is not provided and not found in
                environment variables.
        """
        logger.info(f"Initializing enhanced research agent with API key: {api_key} and email: {email}") 
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(f"GEMINI_API_KEY environment variable is required: {self.api_key}")
        
        # Initialize GenAI client
        logger.info(f"Initializing GenAI client with API key: {self.api_key}") 
        self.client = genai.Client(api_key=self.api_key)
        logger.info(f"GenAI client initialized") 
        
        # Configure Entrez for PubMed (email required for API access)
        self.email = email or os.getenv("RESEARCH_EMAIL")
        if self.email:
            logger.info(f"PubMed email set to: {self.email}") 
            Entrez.email = self.email
        else:
            logger.warning(f"No email provided for PubMed API - some features may be limited: {self.email}")
        
        # Model configurations
        self.models = {
            "fast": "gemini-2.5-flash",
            "premium": "gemini-2.5-pro",
            "grounding": "gemini-2.5-flash"  # Model that supports grounding
        }
        logger.info(f"Model configurations set to: {self.models}") 
        # Generation config with system instructions
        self.generation_config = types.GenerateContentConfig(
            temperature=0.3,
            top_p=0.8,
            top_k=40,
            max_output_tokens=8192,
            response_mime_type="text/plain",
            thinking_config=types.ThinkingConfig(
                thinking_budget=0
            ),
            system_instruction=[
                "You are a professional academic research analyst.",
                "Prioritize peer-reviewed sources and authoritative academic content.",
                "Always cite sources accurately with DOIs when available.",
                "Focus on recent developments and established research findings.",
                "Note any limitations or conflicts in the research literature."
            ]
        )

        # Create seperate config for premium model (thinking required)
        self.premium_generation_config = types.GenerateContentConfig(
            temperature=0.3,
            top_p=0.8,
            top_k=40,
            max_output_tokens=8192,
            response_mime_type="text/plain",
            thinking_config=types.ThinkingConfig(
                thinking_budget=128
            ),
            system_instruction=[
                "You are a professional academic research analyst.",
                "Prioritize peer-reviewed sources and authoritative academic content.",
                "Always cite sources accurately with DOIs when available.",
                "Focus on recent developments and established research findings.",
                "Note any limitations or conflicts in the research literature."
            ]
        )
        logger.info(f"Generation config set to: {self.generation_config}") 
        # Research function definitions for function calling
        logger.info(f"Research function definitions set to: {self.research_functions}") 
        self.research_functions = [
            {
                "name": "search_arxiv_papers",
                "description": "Search arXiv for academic papers in computer science, physics, mathematics, and related fields",
                "parameters": {
                    "type": Type.OBJECT,
                    "properties": {
                        "query": {"type": Type.STRING, "description": "Search query for arXiv papers", "required": True},
                        "max_results": {"type": Type.INTEGER, "description": "Maximum number of results (default: 10)", "required": False},
                        "sort_by": {"type": Type.STRING, "description": "Sort criteria: relevance, lastUpdatedDate, submittedDate", "required": False},
                        "category": {"type": Type.STRING, "description": "arXiv category (e.g., cs.AI, physics.comp-ph)", "required": False}
                    },
                    "required": [Type.STRING, "query"]
                }
            },
            {
                "name": "search_pubmed_papers",
                "description": "Search PubMed for biomedical and life sciences literature",
                "parameters": {
                    "type": Type.OBJECT,
                    "properties": {
                        "query": {"type": Type.STRING, "description": "Search query for PubMed papers", "required": True},
                        "max_results": {"type": Type.INTEGER, "description": "Maximum number of results (default: 10)", "required": False},
                        "sort": {"type": Type.STRING, "description": "Sort order: relevance, pub_date, first_author", "required": False},
                        "date_range": {"type": Type.STRING, "description": "Date range like '2020:2024' or 'last_5_years'", "required": False}
                    },
                    "required": [Type.STRING, "query"]
                }
            },
            {
                "name": "google_grounding_search",
                "description": "Use Google's Grounding with Search for authoritative web information",
                "parameters": {
                    "type": Type.OBJECT,
                    "properties": {
                        "query": {"type": Type.STRING, "description": "Search query for Google grounding", "required": True},
                        "context": {"type": Type.STRING, "description": "Additional context for the search", "required": False}
                    },
                    "required": [Type.STRING, "query"]
                }
            }
        ]
        
        # Cache for API results
        logger.info(f"Cache initialized") 
        self.cache = {}
        
        # Enhanced stop words for better keyword extraction
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 
            'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'what', 'which', 'who', 'when', 'where', 'why', 'how', 'all', 'each',
            'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such',
            'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
            'very', 'just', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'under', 'again', 'further',
            'then', 'once'
        }
        
        # Domain-specific important terms that should be preserved
        self.important_terms = {
            'ai', 'ml', 'deep learning', 'neural network', 'machine learning',
            'quantum', 'covid', 'cancer', 'gene', 'protein', 'dna', 'rna',
            'algorithm', 'model', 'data', 'analysis', 'research', 'study',
            'treatment', 'therapy', 'diagnosis', 'clinical', 'trial'
        }

    def _select_model(self, task_complexity: str = "medium") -> tuple[str, types.GenerateContentConfig]:
        """Select appropriate model and config based on task complexity"""
        if task_complexity == "high":
            return self.models["premium"], self.premium_generation_config
        else:
            return self.models["fast"], self.generation_config

    async def _call_gemini_safely(self, model: str, contents: str, config: types.GenerateContentConfig) -> str:
        """Wrapper for safe Gemini API calls with error handling"""
        try:
            response = await self.client.aio.models.generate_content(
                model=model,
                contents=contents,
                config=config 
            )

            if not response.text:
                logger.warning("Empty response from Gemini API")
                return ""

            return response.text

        except APIError as e:
            logger.error(f"Gemini API Error {e.code}: {e.message}")
            raise 
        except Exception as e:
            logger.error(f"Unexpected error calling Gemini: {e}")
            raise
        
    async def conduct_research(self, request: ResearchRequest) -> ResearchResult:
        """
        Conduct comprehensive research on a given topic using multiple sources.
        
        This is the main entry point for research operations. It orchestrates the
        entire research process including topic analysis, source gathering, synthesis,
        and final output generation.
        
        Args:
            request (ResearchRequest): Research request containing the topic,
                output format preferences, and other configuration options.
        
        Returns:
            ResearchResult: Comprehensive research result including synthesized
                content, references, metadata, and confidence score.
        
        Raises:
            Exception: If research fails at any stage. The error is logged and
                re-raised for handling by the caller.
        
        Process:
            1. Analyze the research topic to determine optimal strategy
            2. Gather information from academic sources (arXiv, PubMed)
            3. Obtain additional context using Google Grounding
            4. Synthesize all information into coherent research
            5. Generate final formatted output
            6. Extract and organize references
        """
        try:
            logger.info(f"Starting academic research for: {request.topic}")
            # Step 1: Analyze topic and determine research strategy
            research_plan = await self._analyze_research_topic(request.topic)
            logger.info(f"Research plan: {research_plan}") 
            # Step 2: Gather information from academic sources
            academic_data = await self._gather_academic_sources(research_plan, request.topic)
            logger.info(f"Academic data: {academic_data}") 
            # Step 3: Use Google Grounding for additional context
            grounding_data = await self._get_grounding_information(request.topic, academic_data)
            logger.info(f"Grounding data: {grounding_data}") 
            # Step 4: Synthesize all information
            synthesis = await self._synthesize_research_data(
                academic_data, grounding_data, request.topic, request.output_format
            )
            logger.info(f"Synthesis: {synthesis}") 
            # Step 5: Generate final output
            final_content = await self._generate_final_output(synthesis, request)
            
            # Extract references from all sources
            references = self._extract_all_references(academic_data, grounding_data)
            
            result = ResearchResult(
                topic=request.topic,
                content=final_content,
                references=references,
                output_format=request.output_format,
                generated_at=datetime.utcnow(),
                word_count=len(final_content.split()),
                confidence_score=self._calculate_confidence_score(academic_data, grounding_data)
            )
            
            logger.info(f"Academic research completed for: {request.topic}")
            return result
            
        except Exception as e:
            logger.error(f"Research failed for topic {request.topic}: {str(e)}")
            raise
    
    async def _analyze_research_topic(self, topic: str) -> Dict[str, Any]:
        """
        Analyze the research topic to determine the optimal search strategy.
        
        Uses AI to understand the topic's domain, identify relevant academic
        disciplines, and determine which sources will be most valuable.
        
        Args:
            topic (str): The research topic to analyze.
        
        Returns:
            Dict[str, Any]: Research plan containing:
                - analysis (str): Detailed analysis of the topic
                - prioritize_arxiv (bool): Whether to prioritize arXiv searches
                - prioritize_pubmed (bool): Whether to prioritize PubMed searches
                - use_grounding (bool): Whether to use Google Grounding
                - search_terms (List[str]): Optimized search terms for queries
        """
        analysis_prompt = f"""
        Analyze this research topic and determine the best search strategy: "{topic}"
        
        Consider:
        1. What academic disciplines are most relevant?
        2. Is this primarily a STEM topic (good for arXiv) or biomedical (good for PubMed)?
        3. What specific search terms would be most effective?
        4. What recent developments should we focus on?
        5. What additional context from web sources would be valuable?
        
        Provide a structured analysis with recommended search terms and sources.
        Format your response as JSON with the following structure:
        {{
            "disciplines": ["list", "of", "relevant", "disciplines"],
            "is_stem": true/false,
            "is_biomedical": true/false,
            "recommended_search_terms": ["term1", "term2", "term3"],
            "focus_areas": ["area1", "area2"],
            "analysis_summary": "brief summary of the topic and research strategy"
        }}
        """
        
        response = await self.client.aio.models.generate_content(
            model=self.models["fast"],
            contents=analysis_prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                top_p=0.8,
                top_k=40,
                max_output_tokens=2048,
                response_mime_type="application/json",
                system_instruction=[
                    "You are a professional academic research analyst.",
                    "Provide structured JSON responses for research planning.",
                    "Be precise and analytical in your assessments."
                ]
            )
        )
        
        # Parse the structured JSON response
        import json
        try:
            analysis_data = json.loads(response.text)
            logger.info(f"Structured analysis data: {analysis_data}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse analysis JSON: {e}")
            # Fallback to basic analysis
            analysis_data = {
                "disciplines": [],
                "is_stem": False,
                "is_biomedical": False,
                "recommended_search_terms": [],
                "focus_areas": [],
                "analysis_summary": response.text
            }
        
        # Extract structured fields with fallbacks
        is_stem = analysis_data.get("is_stem", False)
        is_biomedical = analysis_data.get("is_biomedical", False)
        
        # If AI didn't determine, use keyword-based fallback
        if not is_stem and not is_biomedical:
            is_stem = any(term in topic.lower() for term in [
                'computer', 'ai', 'machine learning', 'physics', 'mathematics', 
                'engineering', 'algorithm', 'quantum', 'neural network'
            ])
            is_biomedical = any(term in topic.lower() for term in [
                'medical', 'health', 'disease', 'drug', 'clinical', 'biology',
                'genetics', 'medicine', 'therapeutic', 'diagnosis'
            ])
        
        logger.info(f"Is STEM: {is_stem}, Is biomedical: {is_biomedical}")
        
        # Use AI-recommended search terms or extract from topic
        search_terms = analysis_data.get("recommended_search_terms", [])
        if not search_terms:
            search_terms = self._extract_search_terms(topic)
        
        return {
            "analysis": analysis_data.get("analysis_summary", response.text),
            "disciplines": analysis_data.get("disciplines", []),
            "focus_areas": analysis_data.get("focus_areas", []),
            "prioritize_arxiv": is_stem,
            "prioritize_pubmed": is_biomedical,
            "use_grounding": True,  # Always use grounding for additional context
            "search_terms": search_terms
        }
        
    
    def _extract_search_terms(self, topic: str) -> List[str]:
        """
        Extract key search terms from the research topic using enhanced NLP techniques.
        
        Performs advanced NLP processing to identify important keywords and
        create effective search queries for academic databases. Uses multiple
        strategies including:
        - Stop word removal
        - N-gram extraction (bigrams, trigrams)
        - Term frequency analysis
        - Domain-specific term preservation
        - Phrase detection
        
        Args:
            topic (str): The research topic to extract terms from.
        
        Returns:
            List[str]: List of optimized search terms including the full topic,
                important phrases, and key concepts ranked by relevance.
        """
        logger.info(f"Extracting search terms from: {topic}")
        
        # Normalize the topic
        normalized_topic = topic.lower().strip()
        
        # Tokenize into words
        words = re.findall(r'\b[a-z]+\b', normalized_topic)
        logger.info(f"Tokenized words: {words}")
        
        # Extract single keywords (excluding stop words)
        keywords = [word for word in words if word not in self.stop_words and len(word) > 2]
        logger.info(f"Filtered keywords: {keywords}")
        
        # Extract bigrams (two-word phrases)
        bigrams = []
        for i in range(len(words) - 1):
            if words[i] not in self.stop_words or words[i+1] not in self.stop_words:
                bigram = f"{words[i]} {words[i+1]}"
                # Keep bigram if it contains at least one non-stop word
                if words[i] not in self.stop_words or words[i+1] not in self.stop_words:
                    bigrams.append(bigram)
        logger.info(f"Extracted bigrams: {bigrams}")
        
        # Extract trigrams (three-word phrases)
        trigrams = []
        for i in range(len(words) - 2):
            # Keep trigram if it contains at least one important word
            if any(words[j] not in self.stop_words for j in range(i, i+3)):
                trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
                trigrams.append(trigram)
        logger.info(f"Extracted trigrams: {trigrams}")
        
        # Identify important domain-specific phrases
        important_phrases = []
        for term in self.important_terms:
            if term in normalized_topic:
                important_phrases.append(term)
        logger.info(f"Important domain phrases: {important_phrases}")
        
        # Calculate term importance using frequency and position
        term_scores = {}
        
        # Score single keywords
        for i, word in enumerate(keywords):
            # Earlier words get higher scores
            position_score = 1.0 / (i + 1)
            # Check if word appears in important terms
            importance_bonus = 2.0 if word in self.important_terms else 1.0
            term_scores[word] = position_score * importance_bonus
        
        # Score bigrams and trigrams
        for bigram in bigrams:
            if any(important in bigram for important in self.important_terms):
                term_scores[bigram] = 1.5
            else:
                term_scores[bigram] = 1.0
        
        for trigram in trigrams:
            if any(important in trigram for important in self.important_terms):
                term_scores[trigram] = 2.0
            else:
                term_scores[trigram] = 0.8
        
        # Sort terms by score
        ranked_terms = sorted(term_scores.items(), key=lambda x: x[1], reverse=True)
        logger.info(f"Ranked terms: {ranked_terms[:10]}")
        
        # Build search term list
        search_terms = [topic]  # Always include full topic
        
        # Add important domain phrases first
        search_terms.extend(important_phrases)
        
        # Add top-ranked terms
        for term, score in ranked_terms[:5]:
            if term not in search_terms:
                search_terms.append(term)
        
        # Add focused variations
        if len(keywords) >= 3:
            # First 3 keywords
            focused_term = ' '.join(keywords[:3])
            if focused_term not in search_terms:
                search_terms.append(focused_term)
        
        if len(keywords) >= 2:
            # Last 2 keywords (often contain specific focus)
            focused_term = ' '.join(keywords[-2:])
            if focused_term not in search_terms:
                search_terms.append(focused_term)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_search_terms = []
        for term in search_terms:
            if term not in seen:
                seen.add(term)
                unique_search_terms.append(term)
        
        logger.info(f"Final search terms: {unique_search_terms}")
        return unique_search_terms
    
    async def _gather_academic_sources(self, research_plan: Dict[str, Any], topic: str) -> Dict[str, Any]:
        """
        Gather information from academic sources based on the research plan.
        
        Searches arXiv and PubMed databases according to the research strategy,
        collecting relevant papers and their metadata.
        
        Args:
            research_plan (Dict[str, Any]): Research plan from topic analysis
                containing search strategy and terms.
            topic (str): The research topic being investigated.
        
        Returns:
            Dict[str, Any]: Academic data containing:
                - arxiv_papers (List[Dict]): Papers from arXiv
                - pubmed_papers (List[Dict]): Papers from PubMed
                - total_papers (int): Total number of papers found
                - search_terms_used (List[str]): Search terms that were used
        """
        logger.info(f"Gathering academic sources for: {topic}") 
        academic_data = {
            "arxiv_papers": [],
            "pubmed_papers": [],
            "total_papers": 0,
            "search_terms_used": research_plan["search_terms"]
        }
        
        search_terms = research_plan["search_terms"]
        logger.info(f"Search terms: {search_terms}") 
        # Search arXiv if relevant
        if research_plan["prioritize_arxiv"]:
            for term in search_terms:
                try:
                    arxiv_results = await self._search_arxiv_enhanced(term, max_results=5)
                    academic_data["arxiv_papers"].extend(arxiv_results)
                    await asyncio.sleep(1)  # Rate limiting
                except Exception as e:
                    logger.warning(f"arXiv search failed for '{term}': {e}")
        
        # Search PubMed if relevant
        if research_plan["prioritize_pubmed"] and self.email:
            for term in search_terms:
                try:
                    pubmed_results = await self._search_pubmed_enhanced(term, max_results=5)
                    academic_data["pubmed_papers"].extend(pubmed_results)
                    await asyncio.sleep(1)  # Rate limiting
                except Exception as e:
                    logger.warning(f"PubMed search failed for '{term}': {e}")
        logger.info(f"PubMed search failed for '{term}': {e}") 
        # Remove duplicates and calculate totals
        academic_data["arxiv_papers"] = self._remove_duplicate_papers(academic_data["arxiv_papers"])
        academic_data["pubmed_papers"] = self._remove_duplicate_papers(academic_data["pubmed_papers"])
        academic_data["total_papers"] = len(academic_data["arxiv_papers"]) + len(academic_data["pubmed_papers"])
        logger.info(f"Academic data: {academic_data}") 
        logger.info(f"Found {academic_data['total_papers']} academic papers ({len(academic_data['arxiv_papers'])} arXiv, {len(academic_data['pubmed_papers'])} PubMed)")
        
        return academic_data
    
    async def _search_arxiv_enhanced(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Enhanced arXiv search with better error handling and data extraction.
        
        Searches the arXiv database for academic papers matching the query,
        extracting comprehensive metadata for each result.
        
        Args:
            query (str): Search query for arXiv.
            max_results (int, optional): Maximum number of results to return.
                Defaults to 10.
        
        Returns:
            List[Dict[str, Any]]: List of paper dictionaries containing title,
                authors, abstract, URLs, publication dates, categories, and DOI.
        """
        try:
            # Create arXiv client
            client = arxiv.Client()
            
            # Construct search
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            # Execute search in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            papers = await loop.run_in_executor(None, lambda: list(client.results(search)))
            
            # Process results
            arxiv_papers = []
            for paper in papers:
                paper_data = {
                    "title": paper.title,
                    "authors": [author.name for author in paper.authors],
                    "abstract": paper.summary,
                    "url": paper.entry_id,
                    "pdf_url": paper.pdf_url,
                    "published": paper.published.isoformat() if paper.published else None,
                    "updated": paper.updated.isoformat() if paper.updated else None,
                    "categories": paper.categories,
                    "source": "arXiv",
                    "doi": getattr(paper, 'doi', None),
                    "primary_category": paper.primary_category
                }
                arxiv_papers.append(paper_data)
            
            return arxiv_papers
            
        except Exception as e:
            logger.error(f"arXiv search failed: {e}")
            return []
    
    async def _search_pubmed_enhanced(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Enhanced PubMed search using Entrez API.
        
        Searches the PubMed database for biomedical literature, extracting
        detailed metadata including abstracts, authors, and publication info.
        
        Args:
            query (str): Search query for PubMed.
            max_results (int, optional): Maximum number of results to return.
                Defaults to 10.
        
        Returns:
            List[Dict[str, Any]]: List of paper dictionaries containing title,
                authors, abstract, PMID, DOI, journal, and publication year.
        
        Note:
            Requires email to be configured for PubMed API access.
        """
        if not self.email:
            logger.warning("No email configured for PubMed API")
            return []
        
        try:
            # Run PubMed search in thread pool
            loop = asyncio.get_event_loop()
            
            def search_pubmed():
                # Search PubMed
                handle = Entrez.esearch(
                    db="pubmed",
                    term=query,
                    retmax=max_results,
                    sort="relevance"
                )
                search_results = Entrez.read(handle)
                handle.close()
                
                if not search_results["IdList"]:
                    return []
                
                # Fetch detailed information
                ids = search_results["IdList"]
                handle = Entrez.efetch(
                    db="pubmed",
                    id=",".join(ids),
                    rettype="xml",
                    retmode="text"
                )
                xml_data = handle.read()
                handle.close()
                
                return xml_data
            
            xml_data = await loop.run_in_executor(None, search_pubmed)
            
            if not xml_data:
                return []
            
            # Parse XML results
            pubmed_papers = self._parse_pubmed_xml(xml_data)
            return pubmed_papers
            
        except Exception as e:
            logger.error(f"PubMed search failed: {e}")
            return []
    
    def _parse_pubmed_xml(self, xml_data: str) -> List[Dict[str, Any]]:
        """
        Parse PubMed XML response into structured data.
        
        Extracts paper metadata from PubMed's XML format, handling various
        edge cases and missing fields gracefully.
        
        Args:
            xml_data (str): Raw XML data from PubMed API.
        
        Returns:
            List[Dict[str, Any]]: List of parsed paper dictionaries with
                standardized fields.
        """
        try:
            root = ET.fromstring(xml_data)
            papers = []
            
            for article in root.findall(".//PubmedArticle"):
                try:
                    # Extract basic information
                    title_elem = article.find(".//ArticleTitle")
                    title = title_elem.text if title_elem is not None else "No title"
                    
                    # Extract abstract
                    abstract_elem = article.find(".//AbstractText")
                    abstract = abstract_elem.text if abstract_elem is not None else "No abstract available"
                    
                    # Extract authors
                    authors = []
                    for author in article.findall(".//Author"):
                        last_name = author.find("LastName")
                        first_name = author.find("ForeName")
                        if last_name is not None and first_name is not None:
                            authors.append(f"{first_name.text} {last_name.text}")
                    
                    # Extract publication date
                    pub_date = article.find(".//PubDate")
                    pub_year = pub_date.find("Year").text if pub_date is not None and pub_date.find("Year") is not None else None
                    
                    # Extract PMID
                    pmid_elem = article.find(".//PMID")
                    pmid = pmid_elem.text if pmid_elem is not None else None
                    
                    # Extract DOI
                    doi = None
                    for article_id in article.findall(".//ArticleId"):
                        if article_id.get("IdType") == "doi":
                            doi = article_id.text
                            break
                    
                    # Extract journal
                    journal_elem = article.find(".//Journal/Title")
                    journal = journal_elem.text if journal_elem is not None else "Unknown journal"
                    
                    paper_data = {
                        "title": title,
                        "authors": authors,
                        "abstract": abstract,
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
                        "pmid": pmid,
                        "doi": doi,
                        "journal": journal,
                        "published_year": pub_year,
                        "source": "PubMed"
                    }
                    papers.append(paper_data)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse PubMed article: {e}")
                    continue
            
            return papers
            
        except Exception as e:
            logger.error(f"Failed to parse PubMed XML: {e}")
            return []
    
    async def _get_grounding_information(self, topic: str, academic_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use Google Grounding with Search for additional authoritative information.
        
        Leverages Google's Grounding API to find current web-based information
        that complements the academic sources, focusing on recent developments,
        industry perspectives, and practical applications.
        
        Args:
            topic (str): The research topic.
            academic_data (Dict[str, Any]): Previously gathered academic data
                to inform the grounding search.
        
        Returns:
            Dict[str, Any]: Grounding data containing:
                - content (str): Generated content with grounded information
                - grounding_metadata (list): Metadata about sources used
                - sources_found (int): Number of web sources found
        """
        try:
            # Create grounding query based on topic and academic findings
            grounding_query = f"""
            Provide comprehensive information about: {topic}
            
            Focus on:
            - Recent developments and news
            - Industry perspectives and applications
            - Government policies and regulations
            - Market trends and statistics
            - Expert opinions and commentary
            
            Please use Google Search to find authoritative sources and provide current information.
            """
            
            # Use Gemini with Grounding enabled
            response = await self.client.aio.models.generate_content(
                model=self.models["grounding"],
                contents=grounding_query,
                config=self.generation_config,
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
            
            grounding_data = {
                "content": response.text,
                "grounding_metadata": [],
                "sources_found": 0
            }
            
            # Extract grounding metadata if available
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata'):
                    grounding_data["grounding_metadata"] = candidate.grounding_metadata
                    grounding_data["sources_found"] = len(candidate.grounding_metadata.get("search_entry_point", {}).get("rendered_content", []))
            
            logger.info(f"Google Grounding found {grounding_data['sources_found']} sources")
            return grounding_data
            
        except Exception as e:
            logger.error(f"Google Grounding search failed: {e}")
            return {"content": "", "grounding_metadata": [], "sources_found": 0}
    
    async def _synthesize_research_data(
        self, 
        academic_data: Dict[str, Any], 
        grounding_data: Dict[str, Any], 
        topic: str, 
        output_format: str
    ) -> str:
        """
        Synthesize academic and grounding data into comprehensive research.
        
        Integrates findings from academic papers and web sources, identifying
        complementary information, conflicts, and key insights. Uses AI to
        create a coherent synthesis that maintains academic rigor.
        
        Args:
            academic_data (Dict[str, Any]): Data from academic sources.
            grounding_data (Dict[str, Any]): Data from Google Grounding.
            topic (str): The research topic.
            output_format (str): Desired output format (bullets or full_report).
        
        Returns:
            str: Synthesized research content ready for final formatting.
        """
        
        # Prepare academic sources summary
        academic_summary = self._create_academic_summary(academic_data)
        
        synthesis_prompt = f"""
        Synthesize comprehensive research about: "{topic}"
        
        ACADEMIC SOURCES SUMMARY:
        {academic_summary}
        
        CURRENT INFORMATION FROM GOOGLE SEARCH:
        {grounding_data.get('content', 'No additional web information available.')}
        
        Please create a synthesis that:
        1. Integrates findings from peer-reviewed academic sources
        2. Incorporates current developments from web sources
        3. Identifies any conflicts or complementary information
        4. Highlights recent breakthroughs or changes
        5. Notes the quality and recency of sources
        6. Provides evidence-based conclusions
        
        Focus on accuracy, cite sources appropriately, and note any limitations.
        Format for: {output_format}
        """
        
        response = await self.client.aio.models.generate_content(
            model=self.models["premium"],  # Use premium model for synthesis
            contents=synthesis_prompt,
            config=self.generation_config
        )
        
        return response.text
    
    def _create_academic_summary(self, academic_data: Dict[str, Any]) -> str:
        """
        Create a summary of academic sources for synthesis.
        
        Formats academic papers into a readable summary that can be used
        in the synthesis prompt, including key metadata and abstracts.
        
        Args:
            academic_data (Dict[str, Any]): Academic data containing papers
                from arXiv and PubMed.
        
        Returns:
            str: Formatted summary of academic sources.
        """
        summary_parts = []
        
        # Summarize arXiv papers
        if academic_data["arxiv_papers"]:
            summary_parts.append(f"arXiv Papers ({len(academic_data['arxiv_papers'])} found):")
            for paper in academic_data["arxiv_papers"][:5]:  # Limit to top 5
                summary_parts.append(f"- {paper['title']} ({paper.get('published', 'Unknown date')})")
                summary_parts.append(f"  Abstract: {paper['abstract'][:200]}...")
                summary_parts.append(f"  URL: {paper['url']}")
        
        # Summarize PubMed papers
        if academic_data["pubmed_papers"]:
            summary_parts.append(f"\nPubMed Papers ({len(academic_data['pubmed_papers'])} found):")
            for paper in academic_data["pubmed_papers"][:5]:  # Limit to top 5
                summary_parts.append(f"- {paper['title']} ({paper.get('published_year', 'Unknown year')})")
                summary_parts.append(f"  Journal: {paper.get('journal', 'Unknown')}")
                summary_parts.append(f"  Abstract: {paper['abstract'][:200]}...")
                if paper.get('url'):
                    summary_parts.append(f"  URL: {paper['url']}")
        
        if not summary_parts:
            return "No academic papers found for this topic."
        
        return "\n".join(summary_parts)
    
    async def _generate_final_output(self, synthesis: str, request: ResearchRequest) -> str:
        """
        Generate the final formatted research output.
        
        Takes the synthesized research and formats it according to the
        requested output format (bullets or full report), applying
        appropriate structure and academic writing standards.
        
        Args:
            synthesis (str): Synthesized research content.
            request (ResearchRequest): Original research request with
                formatting preferences.
        
        Returns:
            str: Final formatted research output ready for delivery.
        """
        format_instructions = {
            "bullets": """
            Format as comprehensive bullet points:
            - Use clear, hierarchical bullet structure
            - Include academic citations in [Author, Year] format
            - Add confidence indicators where appropriate
            - Maximum 20 main points with detailed sub-points
            - Include a brief methodology note about sources used
            """,
            "full_report": """
            Format as a professional academic research report:
            - Executive Summary (3-4 sentences)
            - Literature Review (academic sources)
            - Current Developments (web sources)
            - Key Findings and Analysis
            - Limitations and Future Research Directions
            - Conclusions
            - References section
            - 2000-4000 words total
            """
        }
        
        output_prompt = f"""
        Create a comprehensive research output about "{request.topic}" based on this synthesis:
        
        {synthesis}
        
        {format_instructions.get(request.output_format, format_instructions["bullets"])}
        
        Requirements:
        - Use professional academic writing style
        - Include proper citations for all claims
        - Note the quality and type of sources (peer-reviewed vs. web)
        - Maintain objectivity and note uncertainties
        - Prioritize recent findings and developments
        """
        
        output_text = await self._call_gemini_safely(
            model=self.models["fast"],
            contents=output_prompt,
            config=self.generation_config 
        )
        return output_text
    
    def _remove_duplicate_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate papers based on title similarity.
        
        Deduplicates papers by comparing normalized titles, keeping only
        the first occurrence of each unique paper.
        
        Args:
            papers (List[Dict[str, Any]]): List of paper dictionaries.
        
        Returns:
            List[Dict[str, Any]]: Deduplicated list of papers.
        """
        if not papers:
            return papers
        
        unique_papers = []
        seen_titles = set()
        
        for paper in papers:
            title = paper.get("title", "").lower().strip()
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_papers.append(paper)
        
        return unique_papers
    
    def _extract_all_references(self, academic_data: Dict[str, Any], grounding_data: Dict[str, Any]) -> List[Reference]:
        """
        Extract references from all sources.
        
        Collects and formats references from academic papers and web sources
        into a standardized Reference format for citation purposes.
        
        Args:
            academic_data (Dict[str, Any]): Academic papers data.
            grounding_data (Dict[str, Any]): Grounding sources data.
        
        Returns:
            List[Reference]: List of Reference objects, limited to 20 most
                relevant sources.
        """
        references = []
        
        # Extract from arXiv papers
        for paper in academic_data.get("arxiv_papers", []):
            ref = Reference(
                title=paper["title"],
                url=paper["url"],
                accessed_date=datetime.now(timezone.utc),
                snippet=f"arXiv paper by {', '.join(paper['authors'][:3])}. Categories: {', '.join(paper['categories'])}. Abstract: {paper['abstract'][:200]}..."
            )
            references.append(ref)
        
        # Extract from PubMed papers
        for paper in academic_data.get("pubmed_papers", []):
            ref = Reference(
                title=paper["title"],
                url=paper.get("url", f"PMID: {paper.get('pmid', 'Unknown')}"),
                accessed_date=datetime.now(timezone.utc),
                snippet=f"PubMed paper in {paper.get('journal', 'Unknown journal')} ({paper.get('published_year', 'Unknown year')}). Authors: {', '.join(paper['authors'][:3])}. Abstract: {paper['abstract'][:200]}..."
            )
            references.append(ref)
        
        # Extract from grounding metadata
        grounding_metadata = grounding_data.get("grounding_metadata", [])
        if grounding_metadata:
            # Process grounding sources (implementation depends on actual metadata structure)
            for source in grounding_metadata:
                if isinstance(source, dict) and source.get("url") and source.get("title"):
                    ref = Reference(
                        title=source["title"],
                        url=source["url"],
                        accessed_date=datetime.now(timezone.utc),
                        snippet=f"Web source via Google Search: {source.get('snippet', 'No snippet available')}"
                    )
                    references.append(ref)
        
        return references[:20]  # Limit to 20 references
    
    def _calculate_confidence_score(self, academic_data: Dict[str, Any], grounding_data: Dict[str, Any]) -> float:
        """
        Calculate confidence score based on source quality and quantity.
        
        Computes a confidence score (0.0 to 1.0) based on the number and
        quality of sources found. Academic papers receive higher weight
        than web sources, with PubMed papers weighted highest.
        
        Args:
            academic_data (Dict[str, Any]): Academic papers data.
            grounding_data (Dict[str, Any]): Grounding sources data.
        
        Returns:
            float: Confidence score between 0.0 and 1.0, where higher
                values indicate more comprehensive source coverage.
        """
        score = 0.5  # Base score
        
        # Add points for academic papers
        arxiv_count = len(academic_data.get("arxiv_papers", []))
        pubmed_count = len(academic_data.get("pubmed_papers", []))
        
        score += min(arxiv_count * 0.1, 0.3)  # Up to 0.3 for arXiv papers
        score += min(pubmed_count * 0.15, 0.3)  # Up to 0.3 for PubMed papers (higher weight)
        
        # Add points for grounding sources
        grounding_sources = grounding_data.get("sources_found", 0)
        score += min(grounding_sources * 0.05, 0.2)  # Up to 0.2 for web sources
        logger.info(f"Confidence score: {score}") 
        return min(score, 1.0)  # Cap at 1.0

# Factory function
def create_enhanced_research_agent(email: Optional[str] = None) -> EnhancedResearchAgent:
    """
    Create an enhanced research agent instance.
    
    Factory function for creating a properly configured EnhancedResearchAgent.
    
    Args:
        email (Optional[str]): Email address for PubMed API access. If not
            provided, will attempt to read from RESEARCH_EMAIL environment
            variable.
    
    Returns:
        EnhancedResearchAgent: Configured research agent instance ready to
            conduct research.
    """
    logger.info(f"Creating enhanced research agent with email: {email}") 
    agent = EnhancedResearchAgent(email=email)
    logger.info(f"Enhanced research agent created") 
    return agent