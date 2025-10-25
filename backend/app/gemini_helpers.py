# Updated Gemini Helpers - Academic APIs and Google Grounding Only

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import xml.etree.ElementTree as ET
import arxiv
from Bio import Entrez
from google import genai
from google.genai import types

from .schemas import Reference

logger = logging.getLogger(__name__)

class AcademicGeminiHelpers:
    """
    Helper methods focused on academic research using:
    - arXiv API for computer science, physics, mathematics
    - PubMed API for biomedical and life sciences
    - Google Grounding with Search for authoritative web sources
    - No web scraping or unreliable sources
    """
    
    @staticmethod
    async def generate_academic_search_queries(
        client: genai.Client, 
        model_name: str, 
        topic: str
    ) -> Dict[str, List[str]]:
        """Generate optimized search queries for different academic databases"""
        current_year = datetime.now().year
        prompt = f"""You must generate search queries for the EXACT topic provided: "{topic}"

IMPORTANT: The queries must be directly related to "{topic}" and not about unrelated subjects.

First, determine which databases are most relevant:
- Use arXiv ONLY if "{topic}" is about computer science, physics, mathematics, or engineering
- Use PubMed if "{topic}" is about medicine, biology, health, life sciences, or clinical research
- Always use Web search for comprehensive coverage

Create 3 search queries for each RELEVANT database. If a database is not relevant to "{topic}", write "NOT APPLICABLE" for that section.

For time-sensitive topics, include the current year ({current_year}) or recent years in queries to find the latest research.

Format your response exactly as:
arXiv:
[query 1 about {topic} OR "NOT APPLICABLE"]
[query 2 about {topic} OR "NOT APPLICABLE"]
[query 3 about {topic} OR "NOT APPLICABLE"]

PubMed:
[query 1 about {topic}]
[query 2 about {topic}]
[query 3 about {topic}]

Web:
[query 1 about {topic}]
[query 2 about {topic}]
[query 3 about {topic}]

Example for topic "diabetes treatment":
arXiv:
NOT APPLICABLE
NOT APPLICABLE
NOT APPLICABLE

PubMed:
diabetes mellitus treatment guidelines
type 2 diabetes pharmacological interventions
diabetes management insulin therapy

Web:
latest developments diabetes treatment
diabetes treatment clinical trials {current_year}
diabetes medication new research"""
        
        try:
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    top_p=0.8,
                    max_output_tokens=1024,
                    response_mime_type="text/plain",
                )
            )
            
            if response.text:
                return AcademicGeminiHelpers._parse_query_response(response.text, topic)
            else:
                raise ValueError("No content generated")
                
        except Exception as e:
            logger.error(f"Failed to generate academic search queries: {e}")
            # Fallback to basic queries
            return {
                "arxiv": [topic, f"{topic} recent", f"{topic} algorithm"],
                "pubmed": [topic, f"{topic} clinical", f"{topic} research"],
                "web": [topic, f"{topic} trends", f"{topic} industry"]
            }
    
    @staticmethod
    def _parse_query_response(response_text: str, topic: str) -> Dict[str, List[str]]:
        """Parse the query response into structured format"""
        queries = {"arxiv": [], "pubmed": [], "web": []}
        current_section = None
        
        logger.info(f"Parsing query response for topic: {topic}")
        
        for line in response_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            if line.lower().startswith('arxiv:'):
                current_section = "arxiv"
            elif line.lower().startswith('pubmed:'):
                current_section = "pubmed"
            elif line.lower().startswith('web:') or line.lower().startswith('google'):
                current_section = "web"
            elif current_section and not line.startswith('[') and not line.endswith(']'):
                # Clean up the query
                query = line.strip('- ').strip()
                # Skip "NOT APPLICABLE" entries
                if query and len(query) > 3 and "not applicable" not in query.lower():
                    queries[current_section].append(query)
                    logger.info(f"Added {current_section} query: {query}")
        
        # Only add fallback for web search, not for specialized databases
        # arXiv and PubMed should only be searched if relevant
        if not queries.get("web"):
            queries["web"] = [topic]  # Fallback to topic itself for web search
        
        logger.info(f"Final query counts - arXiv: {len(queries.get('arxiv', []))}, PubMed: {len(queries.get('pubmed', []))}, Web: {len(queries.get('web', []))}")
        
        return queries
    
    @staticmethod
    async def search_arxiv_papers(
        query: str, 
        max_results: int = 10,
        sort_by: str = "submittedDate",
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search arXiv for academic papers"""
        try:
            logger.info(f"Searching arXiv for: {query}")
            
            # Create arXiv client
            client = arxiv.Client()
            
            # Add category filter if specified
            search_query = query
            if category:
                search_query = f"cat:{category} AND {query}"
            
            # Configure sort criteria
            sort_criteria = {
                "relevance": arxiv.SortCriterion.Relevance,
                "submittedDate": arxiv.SortCriterion.SubmittedDate,
                "lastUpdatedDate": arxiv.SortCriterion.LastUpdatedDate
            }
            
            # Create search
            search = arxiv.Search(
                query=search_query,
                max_results=max_results,
                sort_by=sort_criteria.get(sort_by, arxiv.SortCriterion.SubmittedDate),
                sort_order=arxiv.SortOrder.Descending
            )
            
            # Execute search in thread pool
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
                    "primary_category": paper.primary_category,
                    "source": "arXiv",
                    "doi": getattr(paper, 'doi', None),
                    "comment": getattr(paper, 'comment', None)
                }
                arxiv_papers.append(paper_data)
                logger.info(f"Found arXiv paper: {paper.title[:50]}...")
            
            return arxiv_papers
            
        except Exception as e:
            logger.error(f"arXiv search failed: {e}")
            return []
    
    @staticmethod
    async def search_pubmed_papers(
        query: str,
        max_results: int = 10,
        sort: str = "relevance",
        date_range: Optional[str] = None,
        email: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search PubMed for biomedical papers"""
        if not email:
            logger.warning("No email provided for PubMed API - this may limit functionality")
            return []
        
        try:
            logger.info(f"Searching PubMed for: {query}")
            
            # Set email for Entrez
            Entrez.email = email
            
            # Prepare search query with date filter if specified
            search_query = query
            if date_range:
                if ":" in date_range:
                    start_year, end_year = date_range.split(":")
                    search_query += f" AND {start_year}:{end_year}[dp]"
                elif date_range == "last_5_years":
                    current_year = datetime.now().year
                    start_year = current_year - 5
                    search_query += f" AND {start_year}:{current_year}[dp]"
            
            # Run search in thread pool
            loop = asyncio.get_event_loop()
            
            def search_and_fetch():
                # Search PubMed
                search_handle = Entrez.esearch(
                    db="pubmed",
                    term=search_query,
                    retmax=max_results,
                    sort=sort
                )
                search_results = Entrez.read(search_handle)
                search_handle.close()
                
                if not search_results["IdList"]:
                    return []
                
                # Fetch detailed information
                ids = search_results["IdList"]
                fetch_handle = Entrez.efetch(
                    db="pubmed",
                    id=",".join(ids),
                    rettype="xml",
                    retmode="text"
                )
                xml_data = fetch_handle.read()
                fetch_handle.close()
                
                return xml_data
            
            xml_data = await loop.run_in_executor(None, search_and_fetch)
            
            if not xml_data:
                return []
            
            # Parse XML results
            pubmed_papers = AcademicGeminiHelpers._parse_pubmed_xml(xml_data)
            logger.info(f"Found {len(pubmed_papers)} PubMed papers")
            return pubmed_papers
            
        except Exception as e:
            logger.error(f"PubMed search failed: {e}")
            return []
    
    @staticmethod
    def _parse_pubmed_xml(xml_data: str) -> List[Dict[str, Any]]:
        """Parse PubMed XML response into structured data"""
        try:
            root = ET.fromstring(xml_data)
            papers = []
            
            for article in root.findall(".//PubmedArticle"):
                try:
                    # Extract title
                    title_elem = article.find(".//ArticleTitle")
                    title = title_elem.text if title_elem is not None else "No title"
                    
                    # Extract abstract (handle multiple AbstractText elements)
                    abstract_parts = []
                    for abstract_elem in article.findall(".//AbstractText"):
                        if abstract_elem.text:
                            # Include label if available
                            label = abstract_elem.get("Label", "")
                            text = abstract_elem.text
                            if label:
                                abstract_parts.append(f"{label}: {text}")
                            else:
                                abstract_parts.append(text)
                    
                    abstract = " ".join(abstract_parts) if abstract_parts else "No abstract available"
                    
                    # Extract authors
                    authors = []
                    for author in article.findall(".//Author"):
                        last_name_elem = author.find("LastName")
                        first_name_elem = author.find("ForeName")
                        initials_elem = author.find("Initials")
                        
                        if last_name_elem is not None:
                            name_parts = [last_name_elem.text]
                            if first_name_elem is not None:
                                name_parts.insert(0, first_name_elem.text)
                            elif initials_elem is not None:
                                name_parts.insert(0, initials_elem.text)
                            authors.append(" ".join(name_parts))
                    
                    # Extract publication date
                    pub_date_elem = article.find(".//PubDate")
                    pub_year = None
                    pub_month = None
                    if pub_date_elem is not None:
                        year_elem = pub_date_elem.find("Year")
                        month_elem = pub_date_elem.find("Month")
                        pub_year = year_elem.text if year_elem is not None else None
                        pub_month = month_elem.text if month_elem is not None else None
                    
                    # Extract PMID
                    pmid_elem = article.find(".//PMID")
                    pmid = pmid_elem.text if pmid_elem is not None else None
                    
                    # Extract DOI
                    doi = None
                    for article_id in article.findall(".//ArticleId"):
                        if article_id.get("IdType") == "doi":
                            doi = article_id.text
                            break
                    
                    # Extract journal information
                    journal_elem = article.find(".//Journal/Title")
                    journal_title = journal_elem.text if journal_elem is not None else None
                    
                    if not journal_title:
                        journal_elem = article.find(".//Journal/ISOAbbreviation")
                        journal_title = journal_elem.text if journal_elem is not None else "Unknown journal"
                    
                    # Extract keywords
                    keywords = []
                    for keyword in article.findall(".//Keyword"):
                        if keyword.text:
                            keywords.append(keyword.text)
                    
                    # Extract MeSH terms
                    mesh_terms = []
                    for mesh in article.findall(".//MeshHeading/DescriptorName"):
                        if mesh.text:
                            mesh_terms.append(mesh.text)
                    
                    paper_data = {
                        "title": title,
                        "authors": authors,
                        "abstract": abstract,
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
                        "pmid": pmid,
                        "doi": doi,
                        "journal": journal_title,
                        "published_year": pub_year,
                        "published_month": pub_month,
                        "keywords": keywords,
                        "mesh_terms": mesh_terms[:5],  # Limit to first 5 MeSH terms
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
    
    @staticmethod
    async def search_with_google_grounding(
        client: genai.Client,
        model_name: str,
        query: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Use Google Grounding with Search for authoritative web information"""
        try:
            logger.info(f"Using Google Grounding for: {query}")
            
            # Create comprehensive grounding query
            grounding_prompt = f"""
            Research the topic: {query}
            
            {f"Additional context: {context}" if context else ""}
            
            Please provide comprehensive information including:
            - Recent developments and breakthroughs
            - Current market trends and statistics
            - Expert opinions and analysis
            - Industry reports and government data
            - Regulatory or policy changes
            - Future outlook and implications
            
            Use Google Search to find the most authoritative and recent sources.
            Prioritize information from:
            - Government agencies and official statistics
            - Academic institutions and research centers
            - Industry reports from reputable organizations
            - News from established media outlets
            - Professional associations and standards bodies
            """
            
            # Use Gemini with Google Search grounding
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=grounding_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    top_p=0.8,
                    max_output_tokens=4096,
                    response_mime_type="text/plain",
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            
            result = {
                "content": response.text if response.text else "",
                "sources": [],
                "grounding_metadata": None,
                "search_quality": "high"
            }
            
            # Extract grounding metadata if available
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata'):
                    result["grounding_metadata"] = candidate.grounding_metadata
                    
                    # NEW: Extract from grounding_chunks (the actual search results)
                    if hasattr(candidate.grounding_metadata, 'grounding_chunks'):
                        for chunk in candidate.grounding_metadata.grounding_chunks:
                            if hasattr(chunk, 'web'):
                                web = chunk.web
                                source_info = {
                                    "title": getattr(web, 'title', 'Unknown'),
                                    "url": getattr(web, 'uri', ''),
                                    "snippet": response.text[:300] if response.text else ''  # Use response text as snippet
                                }
                                result["sources"].append(source_info)
                                logger.info(f"Found web source: {source_info['title']} - {source_info['url']}")
                    
                    # Fallback: Try search_entry_point for older API versions
                    elif hasattr(candidate.grounding_metadata, 'search_entry_point'):
                        search_entry = candidate.grounding_metadata.search_entry_point
                        if hasattr(search_entry, 'rendered_content'):
                            for content in search_entry.rendered_content:
                                if hasattr(content, 'source'):
                                    source_info = {
                                        "title": getattr(content.source, 'title', 'Unknown'),
                                        "url": getattr(content.source, 'url', ''),
                                        "snippet": getattr(content, 'text', '')[:200]
                                    }
                                    result["sources"].append(source_info)
            
            logger.info(f"Google Grounding found {len(result['sources'])} sources")
            return result
            
        except Exception as e:
            logger.error(f"Google Grounding search failed: {e}")
            return {
                "content": f"Google Grounding search failed: {str(e)}",
                "sources": [],
                "grounding_metadata": None,
                "search_quality": "failed"
            }
    
    @staticmethod
    async def comprehensive_academic_search(
        client: genai.Client,
        model_name: str,
        topic: str,
        email: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform comprehensive search across all academic sources"""
        try:
            logger.info(f"Starting comprehensive academic search for: {topic}")
            
            # Generate optimized queries
            queries = await AcademicGeminiHelpers.generate_academic_search_queries(
                client, model_name, topic
            )
            
            logger.info(f"Generated queries - arXiv: {len(queries.get('arxiv', []))}, PubMed: {len(queries.get('pubmed', []))}, Web: {len(queries.get('web', []))}")
            
            # Search arXiv only if we have queries
            arxiv_results = []
            arxiv_queries_used = queries.get("arxiv", [])[:2]
            if arxiv_queries_used:
                logger.info(f"Searching arXiv with queries: {arxiv_queries_used}")
                for query in arxiv_queries_used:
                    papers = await AcademicGeminiHelpers.search_arxiv_papers(query, max_results=5)
                    logger.info(f"arXiv query '{query}' returned {len(papers)} papers")
                    arxiv_results.extend(papers)
                    await asyncio.sleep(1)  # Rate limiting
            else:
                logger.info("No arXiv queries generated - skipping arXiv search")
            
            # Search PubMed
            pubmed_results = []
            if email:
                pubmed_queries_used = queries.get("pubmed", [])[:2]
                if pubmed_queries_used:
                    logger.info(f"Searching PubMed with queries: {pubmed_queries_used}")
                for query in pubmed_queries_used:
                    papers = await AcademicGeminiHelpers.search_pubmed_papers(
                        query, max_results=5, email=email
                    )
                    logger.info(f"PubMed query '{query}' returned {len(papers)} papers")
                    pubmed_results.extend(papers)
                    await asyncio.sleep(1)  # Rate limiting
            else:
                logger.warning("No email provided for PubMed search - skipping PubMed")
            
            # Search with Google Grounding
            grounding_results = []
            for query in queries.get("web", [])[:2]:
                result = await AcademicGeminiHelpers.search_with_google_grounding(
                    client, model_name, query, context=topic
                )
                grounding_results.append(result)
                await asyncio.sleep(1)  # Rate limiting
            
            # Remove duplicates
            arxiv_results = AcademicGeminiHelpers._remove_duplicate_papers(arxiv_results)
            pubmed_results = AcademicGeminiHelpers._remove_duplicate_papers(pubmed_results)
            
            comprehensive_results = {
                "topic": topic,
                "arxiv_papers": arxiv_results,
                "pubmed_papers": pubmed_results,
                "grounding_results": grounding_results,
                "total_academic_papers": len(arxiv_results) + len(pubmed_results),
                "total_web_sources": sum(len(r.get("sources", [])) for r in grounding_results),
                "search_queries_used": queries,
                "timestamp": datetime.utcnow()
            }
            
            logger.info(f"Comprehensive search completed: {comprehensive_results['total_academic_papers']} papers, {comprehensive_results['total_web_sources']} web sources")
            return comprehensive_results
            
        except Exception as e:
            logger.error(f"Comprehensive academic search failed: {e}")
            raise
    
    @staticmethod
    def _remove_duplicate_papers(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate papers based on title and DOI"""
        if not papers:
            return papers
        
        unique_papers = []
        seen_identifiers = set()
        
        for paper in papers:
            # Create identifier based on title and DOI
            title = (paper.get("title") or "").lower().strip()
            doi = (paper.get("doi") or "").lower().strip()
            pmid = paper.get("pmid") or ""
            
            # Create unique identifier
            if doi:
                identifier = f"doi:{doi}"
            elif pmid:
                identifier = f"pmid:{pmid}"
            else:
                identifier = f"title:{title[:50]}"  # Use first 50 chars of title
            
            if identifier not in seen_identifiers:
                seen_identifiers.add(identifier)
                unique_papers.append(paper)
        
        return unique_papers
    
    @staticmethod
    def extract_academic_references(
        arxiv_papers: List[Dict[str, Any]],
        pubmed_papers: List[Dict[str, Any]],
        grounding_results: List[Dict[str, Any]]
    ) -> List[Reference]:
        """Extract references from all academic sources"""
        references = []
        
        # Extract from arXiv papers
        for paper in arxiv_papers:
            authors_str = ", ".join(paper.get("authors", [])[:3])
            if len(paper.get("authors", [])) > 3:
                authors_str += " et al."
            
            snippet = f"arXiv preprint by {authors_str}. "
            snippet += f"Categories: {', '.join(paper.get('categories', [])[:2])}. "
            snippet += f"Abstract: {paper.get('abstract', '')[:150]}..."
            
            ref = Reference(
                title=paper.get("title", "Unknown title"),
                url=paper.get("url", ""),
                accessed_date=datetime.now(timezone.utc),
                snippet=snippet,
                source_type="arxiv"
            )
            references.append(ref)
        
        # Extract from PubMed papers
        for paper in pubmed_papers:
            authors_str = ", ".join(paper.get("authors", [])[:3])
            if len(paper.get("authors", [])) > 3:
                authors_str += " et al."
            
            snippet = f"Published in {paper.get('journal', 'Unknown journal')}"
            if paper.get("published_year"):
                snippet += f" ({paper['published_year']})"
            snippet += f". Authors: {authors_str}. "
            if paper.get("mesh_terms"):
                snippet += f"MeSH terms: {', '.join(paper['mesh_terms'][:3])}. "
            snippet += f"Abstract: {paper.get('abstract', '')[:150]}..."
            
            ref = Reference(
                title=paper.get("title", "Unknown title"),
                url=paper.get("url", ""),
                accessed_date=datetime.now(timezone.utc),
                snippet=snippet,
                source_type="pubmed"
            )
            references.append(ref)
        
        # Extract from grounding results  
        for result in grounding_results:
            for source in result.get("sources", []):
                # Extract domain/publisher from URL
                url = source.get("url", "")
                publisher = "Unknown"
                if url:
                    try:
                        from urllib.parse import urlparse
                        parsed = urlparse(url)
                        publisher = parsed.netloc.replace('www.', '')
                    except:
                        pass
                
                # Create snippet with publisher info
                snippet = f"Published on {publisher}. "
                snippet += source.get('snippet', 'No snippet available')[:200]
                
                ref = Reference(
                    title=source.get("title", "Unknown title"),
                    url=url,
                    accessed_date=datetime.now(timezone.utc),
                    snippet=snippet,
                    source_type="web"
                )
                references.append(ref)
        
        return references[:25]  # Limit to 25 references
    
    @staticmethod
    async def create_research_synthesis(
        client: genai.Client,
        model_name: str,
        comprehensive_results: Dict[str, Any],
        output_format: str = "full_report"
    ) -> str:
        """Create a synthesis of all research sources"""
        
        # Prepare academic summary
        academic_summary = AcademicGeminiHelpers._create_comprehensive_summary(comprehensive_results)
        
        synthesis_prompt = f"""
        Create a comprehensive research synthesis for the topic: "{comprehensive_results['topic']}"
        
        ACADEMIC AND WEB SOURCES:
        {academic_summary}
        
        SYNTHESIS REQUIREMENTS:
        1. Integrate findings from peer-reviewed sources (arXiv, PubMed)
        2. Incorporate current information from authoritative web sources
        3. Identify relationships, patterns, and conflicts between sources
        4. Highlight recent developments and breakthroughs
        5. Assess the quality and credibility of different source types
        6. Note any limitations or gaps in the available research
        7. Provide evidence-based conclusions and implications
        
        OUTPUT FORMAT: {output_format}
        
        Focus on accuracy, proper attribution, and maintaining academic rigor while being accessible.
        """
        
        response = await client.aio.models.generate_content(
            model=model_name,
            contents=synthesis_prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                top_p=0.8,
                max_output_tokens=6144,
                response_mime_type="text/plain",
            )
        )
        
        return response.text if response.text else "Synthesis generation failed"
    
    @staticmethod
    def _create_comprehensive_summary(results: Dict[str, Any]) -> str:
        """Create a comprehensive summary of all research results"""
        summary_parts = []
        
        # arXiv papers summary
        arxiv_papers = results.get("arxiv_papers", [])
        if arxiv_papers:
            summary_parts.append(f"=== arXiv Papers ({len(arxiv_papers)} found) ===")
            for i, paper in enumerate(arxiv_papers[:5], 1):  # Top 5
                summary_parts.append(f"\n{i}. {paper.get('title', 'No title')}")
                summary_parts.append(f"   Authors: {', '.join(paper.get('authors', [])[:3])}")
                summary_parts.append(f"   Published: {paper.get('published', 'Unknown date')}")
                summary_parts.append(f"   Categories: {', '.join(paper.get('categories', []))}")
                summary_parts.append(f"   Abstract: {paper.get('abstract', '')[:200]}...")
                summary_parts.append(f"   URL: {paper.get('url', '')}")
        
        # PubMed papers summary
        pubmed_papers = results.get("pubmed_papers", [])
        if pubmed_papers:
            summary_parts.append(f"\n=== PubMed Papers ({len(pubmed_papers)} found) ===")
            for i, paper in enumerate(pubmed_papers[:5], 1):  # Top 5
                summary_parts.append(f"\n{i}. {paper.get('title', 'No title')}")
                summary_parts.append(f"   Authors: {', '.join(paper.get('authors', [])[:3])}")
                summary_parts.append(f"   Journal: {paper.get('journal', 'Unknown')}")
                summary_parts.append(f"   Year: {paper.get('published_year', 'Unknown')}")
                if paper.get('mesh_terms'):
                    summary_parts.append(f"   MeSH Terms: {', '.join(paper['mesh_terms'][:3])}")
                summary_parts.append(f"   Abstract: {paper.get('abstract', '')[:200]}...")
                if paper.get('url'):
                    summary_parts.append(f"   URL: {paper['url']}")
        
        # Grounding results summary
        grounding_results = results.get("grounding_results", [])
        if grounding_results:
            summary_parts.append(f"\n=== Web Sources via Google Search ===")
            for i, result in enumerate(grounding_results, 1):
                summary_parts.append(f"\nSearch {i} Results:")
                summary_parts.append(f"Content: {result.get('content', '')[:300]}...")
                
                sources = result.get("sources", [])
                if sources:
                    summary_parts.append(f"Sources found: {len(sources)}")
                    for j, source in enumerate(sources[:3], 1):  # Top 3 sources per search
                        summary_parts.append(f"  {j}. {source.get('title', 'No title')}")
                        summary_parts.append(f"     URL: {source.get('url', '')}")
                        summary_parts.append(f"     Snippet: {source.get('snippet', '')[:100]}...")
        
        if not summary_parts:
            return "No academic or web sources found for this topic."
        
        return "\n".join(summary_parts)