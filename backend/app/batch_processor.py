# Batch Research Processor for Large-Scale Research Tasks

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from google import genai
from google.genai import types
import json

logger = logging.getLogger(__name__)

class BatchResearchProcessor:
    """
    Handles large-scale research tasks using Google GenAI Batch API
    for efficient processing of multiple research queries
    """
    
    def __init__(self, client: genai.Client):
        self.client = client
        
    async def process_batch_research(
        self, 
        topics: List[str], 
        research_type: str = "summary"
    ) -> Dict[str, Any]:
        """Process multiple research topics efficiently using Batch API"""
        try:
            # Prepare batch requests
            batch_requests = self._prepare_batch_requests(topics, research_type)
            
            # Submit batch job
            batch_job = await self._submit_batch_job(batch_requests)
            
            # Monitor and retrieve results
            results = await self._monitor_batch_job(batch_job)
            
            return {
                "batch_id": batch_job.name,
                "total_topics": len(topics),
                "results": results,
                "completed_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Batch research processing failed: {e}")
            raise
    
    def _prepare_batch_requests(self, topics: List[str], research_type: str) -> List[Dict[str, Any]]:
        """Prepare individual requests for batch processing"""
        requests = []
        
        for i, topic in enumerate(topics):
            prompt = self._create_research_prompt(topic, research_type)
            
            request = {
                "custom_id": f"research_{i}_{topic[:50]}",
                "method": "POST",
                "url": "/v1/models/gemini-2.5-flash:generateContent",
                "body": {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 2048
                    }
                }
            }
            requests.append(request)
        
        return requests
    
    def _create_research_prompt(self, topic: str, research_type: str) -> str:
        """Create optimized prompt for batch research"""
        prompts = {
            "summary": f"Provide a comprehensive 3-paragraph summary of current developments in: {topic}",
            "trends": f"Analyze the latest trends and future outlook for: {topic}",
            "comparison": f"Compare and contrast different approaches or solutions in: {topic}",
            "deep_dive": f"Provide an in-depth analysis of key aspects and implications of: {topic}"
        }
        
        return prompts.get(research_type, prompts["summary"])
    
    async def _submit_batch_job(self, requests: List[Dict[str, Any]]) -> Any:
        """Submit batch job to Google GenAI Batch API"""
        try:
            # Convert requests to proper batch format
            batch_source = types.BatchJobSource(
                input_uri="data:application/json," + json.dumps({"requests": requests})
            )
            
            # Submit batch job
            batch_job = await self.client.aio.batches.create(
                model="gemini-2.5-flash",
                src=batch_source,
                config=types.CreateBatchJobConfig(
                    display_name=f"Research Batch {datetime.utcnow().isoformat()}"
                )
            )
            
            logger.info(f"Batch job submitted: {batch_job.name}")
            return batch_job
            
        except Exception as e:
            logger.error(f"Failed to submit batch job: {e}")
            raise
    
    async def _monitor_batch_job(self, batch_job: Any, max_wait_time: int = 600) -> List[Dict[str, Any]]:
        """Monitor batch job completion and retrieve results"""
        wait_time = 0
        poll_interval = 30  # Poll every 30 seconds
        
        while wait_time < max_wait_time:
            try:
                # Check job status
                job_status = await self.client.aio.batches.get(
                    name=batch_job.name,
                    config=types.GetBatchJobConfig()
                )
                
                logger.info(f"Batch job status: {job_status.state}")
                
                if job_status.state == "JOB_STATE_SUCCEEDED":
                    # Retrieve results
                    return await self._retrieve_batch_results(job_status)
                elif job_status.state in ["JOB_STATE_FAILED", "JOB_STATE_CANCELLED"]:
                    raise Exception(f"Batch job failed with state: {job_status.state}")
                
                # Wait before next poll
                await asyncio.sleep(poll_interval)
                wait_time += poll_interval
                
            except Exception as e:
                logger.error(f"Error monitoring batch job: {e}")
                raise
        
        raise TimeoutError(f"Batch job did not complete within {max_wait_time} seconds")
    
    async def _retrieve_batch_results(self, job_status: Any) -> List[Dict[str, Any]]:
        """Retrieve and process batch job results"""
        try:
            # Get results from output URI
            output_uri = job_status.output_uri
            
            # For this example, we'll simulate result retrieval
            # In practice, you'd download and parse the results file
            results = []
            
            # Process each result
            for i in range(job_status.request_count):
                result = {
                    "custom_id": f"research_{i}",
                    "content": "Batch result would be processed here",
                    "success": True,
                    "timestamp": datetime.utcnow()
                }
                results.append(result)
            
            logger.info(f"Retrieved {len(results)} batch results")
            return results
            
        except Exception as e:
            logger.error(f"Failed to retrieve batch results: {e}")
            raise