# Live Research Session for Interactive Research with Voice/Video

import asyncio
from datetime import datetime
import logging
from typing import Optional, Dict, Any, AsyncGenerator, List
from google import genai
from google.genai import types
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LiveResearchSession:
    """
    Interactive research sessions using Google GenAI Live API
    Supports voice, video, and text-based collaborative research
    """
    
    def __init__(self, client: genai.Client):
        """Initialize the live research session"""
        logger.info(f"Initializing live research session with client: {client}")
        self.client = client
        self.active_session = None
        self.session_context = {
        }   
        logger.info(f"Live research session context initialized: {self.session_context}")
    async def start_live_research_session(
        self, 
        research_topic: str,
        modalities: List[str] = ["TEXT", "AUDIO"],
        system_instructions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Start an interactive research session"""
        logger.info(f"Starting live research session for topic: {research_topic} with modalities: {modalities}")
        try:
            # Configure session
            config = {
                "response_modalities": modalities,
                "system_instruction": system_instructions or [
                    "You are an expert research assistant.",
                    "Help users explore topics through interactive dialogue.",
                    "Ask clarifying questions and provide detailed insights.",
                    "Maintain context throughout the research session."
                ]
            }
            
            # Start Live API session
            self.active_session = await self.client.aio.live.connect(
                model="gemini-2.5-flash-preview-native-audio-dialog",
                config=types.LiveConnectConfig(**config)
            )
            
            # Initialize session context
            self.session_context = {
                "topic": research_topic,
                "started_at": datetime.utcnow(),
                "interactions": [],
                "key_findings": [],
                "questions_explored": []
            }
            
            # Send initial research prompt
            await self._send_initial_prompt(research_topic)

            logger.info(f"Live research session started for topic: {research_topic}")
        
            return {
                "session_id": id(self.active_session),
                "topic": research_topic,
                "status": "active",
                "modalities": modalities
            }
        except Exception as e:
            logger.error(f"Failed to start live research session: {e}")
            raise

    async def _send_initial_prompt(self, research_topic: str):
        """Send initial research prompt to the session"""
        prompt = f"""
        You are an expert research assistant conducting an interactive research session on the topic: "{research_topic}"
        
        """
        
        await self.active_session.send_message(prompt)
        
        logger.info(f"Initial research prompt sent to session for topic: {research_topic}")
        
    async def _handle_message(self, message: types.Message):
        """Handle incoming messages from the session"""
        logger.info(f"Received message from session: {message.content}")
        
        # Process message content
        content = message.content
        if content:
            self.session_context["interactions"].append({
                "role": "user",
                "content": content,
                "timestamp": datetime.utcnow()
            })
            
            # Generate response
            response = await self._generate_response(content)
            await self.active_session.send_message(response)
            
            logger.info(f"Response sent to session: {response}")
            
    async def _generate_response(self, content: str) -> str:
        """Generate a response to the user's message"""
        prompt = f"""
        Generate a response to the following user message:
        {content}

        Provide detailed insights and recommendations based on the research topic.
        """
        
        response = await self.client.aio.models.generate_content(
            model="gemini-2.5-flash-preview-native-audio-dialog",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                top_p=0.8,
                max_output_tokens=1024,
                response_mime_type="text/plain",
            )
        )
        
        return response.text if response.text else ""
        
    async def _end_session(self):
        """End the live research session"""
        if self.active_session:
            await self.active_session.disconnect()
            logger.info("Live research session ended")
            return {
                "status": "ended",
                "session_id": id(self.active_session)
            }
        else:
            logger.warning("No active session to end")
            return {
                "status": "inactive",
                "session_id": None
            }


