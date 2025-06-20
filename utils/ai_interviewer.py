"""
AI Interviewer using ElevenLabs Conversational AI
This class manages agent creation and session logging for the web widget.
This version uses a universal fix to be compatible with all SDK versions.
"""

import os
import json
import logging
from datetime import datetime

from elevenlabs.client import ElevenLabs
# NOTE: The problematic 'APIError' import has been completely removed.

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AIInterviewer:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv('ELEVENLABS_API_KEY')
        if not self.api_key:
            raise ValueError("Missing ElevenLabs API key. Set ELEVENLABS_API_KEY environment variable.")
        self.client = ElevenLabs(api_key=self.api_key)
        self.interview_sessions: dict[str, dict] = {}

    def create_interview_agent(
        self,
        agent_name: str = "PersonaFit Interviewer",
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",
        model_id: str = "eleven_turbo_v2",
        job_description: str | None = None
    ) -> str:
        prompt = (
            """
Key guidelines:
-Greet the user first and make sure you just ask 3 questions and interview should end in 1 minute .
-You are PersonaFit Interviewer, an AI focused on assessing psychological
-You are a professional AI voice interviewer conducting natural, conversational interviews. Your role is to have meaningful conversations with candidates to assess their experience, skills, and fit for the role.
- Start by greeting the candidate warmly and asking them to introduce themselves
- Listen actively to everything the candidate shares
- Ask thoughtful follow-up questions based on their responses
- Keep the conversation natural and engaging
- Focus on understanding their experience, motivations, and problem-solving approach
- Do NOT ask predetermined or scripted questions
- Let the conversation flow naturally based on what they tell you

Your tone should be:
- Professional yet conversational
- Genuinely curious and interested
- Respectful and encouraging
- Clear and easy to understand

Assessment areas to explore naturally:
- Their background and experience
- Problem-solving approach and examples
- Communication skills and clarity of thought
- Motivations and career goals
- How they handle challenges and feedback
- Technical skills relevant to the role
- Cultural fit and working style

Remember: This is a conversation, not an interrogation. Build rapport and make the candidate feel comfortable while gathering meaningful insights about their capabilities.
"""
        )
        if job_description:
            prompt += f"\n\nThis interview is for a role with the following context:\n{job_description}\n"

        conversation_config = {
            "language": "en",
            "agent": {"prompt": {"prompt": prompt}},
            "tts": {"voice_id": voice_id, "model_id": model_id}
        }
        
        platform_settings = {"max_duration_seconds": 1800}
        
        try:
            agent = self.client.conversational_ai.agents.create(
                name=agent_name,
                conversation_config=conversation_config,
                platform_settings=platform_settings
            )
            logger.info(f"Successfully created agent: {agent.agent_id}")
            return agent.agent_id
        except Exception as e:
            # Catching the general Exception will handle any API or other errors.
            logger.error(f"An error occurred while creating an ElevenLabs agent: {e}")
            raise

    def start_interview_session(
        self,
        agent_id: str,
        candidate_name: str
    ) -> dict[str, any]:
        session_id = f"interview_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{candidate_name.replace(' ', '_')}"
        
        self.interview_sessions[session_id] = {
            "session_id": session_id,
            "agent_id": agent_id,
            "candidate_name": candidate_name,
            "start_time": datetime.now().isoformat(),
            "status": "active",
            "conversation_history": []
        }
        logger.info(f"Backend session logged: {session_id} for candidate '{candidate_name}'")
        return self.interview_sessions[session_id]

    def end_interview_session(self, session_id: str) -> dict[str, any]:
        info = self.interview_sessions.get(session_id)
        if not info:
            logger.warning(f"Attempted to end a session that was not found: {session_id}")
            raise ValueError(f"Session not found: {session_id}")
        
        info["end_time"] = datetime.now().isoformat()
        info["status"] = "completed"
        
        try:
            # This part is for logging/history and won't crash the main app if it fails.
            history_items = self.client.history.get_by_agent(agent_id=info['agent_id'])

            # ... additional logic to parse history could go here ...
            logger.info(f"History for agent {info['agent_id']} checked.")
        except Exception as e:
            logger.warning(f"Could not fetch conversation history for session {session_id}: {e}")
        
        logger.info(f"Backend session completed: {session_id}")
        return info

    def get_available_voices(self) -> list[dict]:
        try:
            resp = self.client.voices.get_all()
            return [{"voice_id": v.voice_id, "name": v.name, "category": v.category} for v in resp.voices]
        except Exception as e:
            logger.error(f"An error occurred while retrieving ElevenLabs voices: {e}")
            return [] 