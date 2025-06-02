import os
import json
import logging
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AIScreening:
    _model = None # Class-level variable to store the model instance
    _api_key_configured = False

    def __init__(self):
        """Initializes the AI Screening module."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logging.warning("GEMINI_API_KEY is not set. AI Screening features will be disabled.")
            self._api_key_configured = False
            return

        try:
            genai.configure(api_key=api_key)
            # Test a small model list call to confirm API key is working
            # This is a light-weight way to check connectivity without making full content generation calls.
            # However, for production, you might want to wrap actual generation calls in try-except for robust handling.
            list(genai.list_models()) # Attempt to list models
            self._api_key_configured = True
            logging.info("Gemini API configured successfully for AI Screening.")
        except Exception as e:
            logging.error(f"Failed to configure Gemini API for AI Screening: {e}")
            self._api_key_configured = False

    @property
    def ai_available(self):
        return self._api_key_configured

    def _get_model(self):
        """Returns the GenerativeModel instance, creating it if necessary."""
        if not self.ai_available:
            return None
        if self._model is None:
            try:
                self._model = genai.GenerativeModel('gemini-2.0')
                logging.info("Gemini-pro model initialized.")
            except Exception as e:
                logging.error(f"Failed to initialize Gemini-pro model: {e}")
                return None
        return self._model

    def _safe_generate_content(self, prompt, timeout=120):
        """
        Safely generates content using the Gemini model with error handling and retry logic.
        Includes safety settings.
        """
        model = self._get_model()
        if not model:
            logging.error("AI model not available.")
            return None

        try:
            response = model.generate_content(
                prompt,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                },
                request_options={"timeout": timeout}
            )
            # Raise an exception if the content was blocked
            if not response._result.candidates:
                if response._result.prompt_feedback and response._result.prompt_feedback.block_reason:
                    logging.warning(f"Prompt blocked by safety settings: {response._result.prompt_feedback.block_reason}")
                    return None # Or raise a specific error
                logging.warning("No candidates generated in AI response.")
                return None

            return response.text

        except genai.types.BlockedPromptException as e:
            logging.error(f"Gemini API: Prompt blocked by safety settings - {e}")
            return None
        except genai.types.BlockedResponseException as e:
            logging.error(f"Gemini API: Response blocked by safety settings - {e}")
            return None
        except genai.core.exceptions.GoogleGenerativeAIException as e:
            logging.error(f"Gemini API error during content generation: {e}")
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred during AI content generation: {e}")
            return None

    @staticmethod
    def _extract_json_from_response(text):
        """
        Extracts and parses a JSON string from a potentially markdown-wrapped text.
        """
        if not text:
            return None

        # Attempt to find JSON within markdown code blocks
        if "```json" in text:
            try:
                json_string = text.split("```json", 1)[1].split("```", 1)[0].strip()
                return json.loads(json_string)
            except (IndexError, json.JSONDecodeError) as e:
                logging.warning(f"Failed to parse JSON from ```json block: {e}")
        elif "```" in text:
            try:
                json_string = text.split("```", 1)[1].split("```", 1)[0].strip()
                return json.loads(json_string)
            except (IndexError, json.JSONDecodeError) as e:
                logging.warning(f"Failed to parse JSON from generic ``` block: {e}")

        # Fallback: try to parse the entire text as JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logging.warning(f"Failed to parse entire text as JSON: {e}")

        return None

    def generate_background_check(self, candidate_profile, job_description):
        """
        Generate background check assessment using Gemini API.
        
        Args:
            candidate_profile (dict): The candidate's profile data
            job_description (str): The job description text
            
        Returns:
            dict: Background check results in JSON format or a default error response.
        """
        if not self.ai_available:
            logging.warning("AI not available. Returning default background check response.")
            return {
                "verificationAssessment": "AI service is currently unavailable.",
                "riskScore": 5,
                "areasForVerification": ["AI service not configured or failed to initialize."]
            }

        background_check_prompt = f"""
        You are an AI recruitment assistant tasked with performing a background verification assessment based on a candidate's profile and a job description.

        Analyze the following candidate profile:
        {json.dumps(candidate_profile, indent=2)}

        Consider the following job description (if provided):
        {job_description if job_description else "No specific job description provided. Base your analysis on general career progression and consistency."}

        Provide a concise background verification assessment. Identify any potential inconsistencies, significant gaps, or red flags in the candidate's background that are relevant to a professional role. If no specific job description is provided, analyze for general career consistency, common discrepancies, and overall profile strength.

        Based on your assessment, provide:
        1.  A numeric risk assessment score from 1 to 10, where 1 indicates the lowest risk (highly consistent, no red flags) and 10 indicates the highest risk (significant inconsistencies, major red flags).
        2.  A list of specific areas (use short, clear phrases) that would benefit from further human verification or closer examination (e.g., "Employment dates mismatch", "Missing educational details", "Unexplained gaps in work history"). If no specific areas are identified, include the phrase "No specific areas identified".

        Your response MUST be ONLY a JSON object. Do not include any introductory or concluding text, markdown formatting (like ```json), or conversational phrases. The JSON object must strictly follow this structure:
        {{
            "verificationAssessment": "[Your concise assessment here]",
            "riskScore": [Your numeric score from 1-10],
            "areasForVerification": ["Area 1", "Area 2", ...]
        }}
        """

        response_text = self._safe_generate_content(background_check_prompt)
        background_check_data = self._extract_json_from_response(response_text)

        if background_check_data and isinstance(background_check_data.get("riskScore"), int) and \
           isinstance(background_check_data.get("verificationAssessment"), str) and \
           isinstance(background_check_data.get("areasForVerification"), list):
            logging.info("Successfully generated background check.")
            return background_check_data
        else:
            logging.error("Failed to parse valid JSON for background check or received incomplete data.")
            logging.debug(f"Raw AI response: {response_text}")
            return {
                "verificationAssessment": "Could not generate assessment due to an issue with AI response. Please try again.",
                "riskScore": 5,
                "areasForVerification": ["Error parsing AI response"]
            }

    def generate_prescreening_questions(self, candidate_profile, job_description):
        """
        Generate pre-screening questions using Gemini API.
        
        Args:
            candidate_profile (dict): The candidate's profile data
            job_description (str): The job description text
            
        Returns:
            dict: Generated pre-screening questions in JSON format or a default error response.
        """
        if not self.ai_available:
            logging.warning("AI not available. Returning default pre-screening questions.")
            return {
                "questions": [
                    {
                        "question": "AI service is currently unavailable.",
                        "purpose": "Technical issue",
                        "whatToLookFor": "AI service not configured or failed to initialize."
                    }
                ]
            }

        questions_prompt = f"""
        You are an AI recruitment assistant tasked with generating targeted pre-screening questions for a candidate based on their profile and a job description.

        Based on this candidate profile:
        {json.dumps(candidate_profile, indent=2)}

        And this job description (if provided):
        {job_description if job_description else "No specific job description provided. Generate general behavioral and skill-based questions."}

        Generate exactly 5 targeted pre-screening questions that would help assess this candidate's fit for the role. For each question, also provide its purpose and what to look for in the candidate's answer.

        The questions should:
        - Aim to verify key skills, experience, and achievements mentioned in their profile.
        - Address any potential gaps or areas requiring clarification (if applicable).
        - Assess relevant soft skills (e.g., teamwork, problem-solving, communication, leadership).
        - Evaluate technical knowledge or past project experience relevant to the position.
        - Be open-ended to encourage detailed responses.

        Your response MUST be ONLY a JSON object. Do not include any introductory or concluding text, markdown formatting (like ```json), or conversational phrases. The JSON object must strictly follow this structure:
        {{
            "questions": [
                {{
                    "question": "[Your question text]",
                    "purpose": "[Concise purpose of the question]",
                    "whatToLookFor": "[Key points or behaviors to listen for]"
                }},
                // ... 4 more question objects ...
            ]
        }}
        """

        response_text = self._safe_generate_content(questions_prompt)
        questions_data = self._extract_json_from_response(response_text)

        if questions_data and isinstance(questions_data.get("questions"), list):
            # Basic validation for each question object
            if all(isinstance(q, dict) and 'question' in q and 'purpose' in q and 'whatToLookFor' in q for q in questions_data['questions']):
                logging.info("Successfully generated pre-screening questions.")
                return questions_data
            else:
                logging.error("Generated questions list contains invalid objects.")
                logging.debug(f"Raw AI response: {response_text}")
                return {
                    "questions": [
                        {
                            "question": "Failed to generate valid questions due to AI response structure.",
                            "purpose": "Data validation issue",
                            "whatToLookFor": "N/A"
                        }
                    ]
                }
        else:
            logging.error("Failed to parse valid JSON for pre-screening questions or received incomplete data.")
            logging.debug(f"Raw AI response: {response_text}")
            return {
                "questions": [
                    {
                        "question": "Could not generate questions due to an issue with AI response. Please try again.",
                        "purpose": "Error parsing AI response",
                        "whatToLookFor": "N/A"
                    }
                ]
            }

# You might want to initialize AIScreening once in your app.py if you reuse it
# For example, in app.py:
# ai_screening_instance = AIScreening()
# Then use ai_screening_instance.generate_background_check
# For this specific app structure where methods are called directly, it works,
# but if AIScreening needs to maintain state (like an API key configuration check),
# it's better to instantiate it.

# If you prefer to keep it static-like and check availability inside methods,
# you would instantiate it inside app.py's global scope:
# from utils.ai_screening import AIScreening
# ai_screening_tool = AIScreening() # This will run the __init__ and set _api_key_configured
# And then change calls in app.py from AIScreening.generate_background_check to ai_screening_tool.generate_background_check