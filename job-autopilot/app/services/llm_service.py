from typing import Optional, Dict, Any, List
import httpx
from app.config import settings
from loguru import logger
from sqlmodel import Session
from app.database import engine
from app.models import Setting


def get_db_setting(key: str, default: str = "") -> str:
    """Get setting value from database"""
    try:
        with Session(engine) as session:
            setting = session.query(Setting).filter(Setting.key == key).first()
            return setting.value if setting else default
    except Exception:
        # Fallback to env settings if DB is not available
        return default


class LLMService:
    """Сервис для работы с LLM (OpenAI-compatible API)."""
    
    def __init__(self, session: Optional[Session] = None):
        # Try to get settings from DB first, fallback to env
        self.api_key = get_db_setting("LLM_API_KEY", settings.LLM_API_KEY or "")
        self.base_url = get_db_setting("LLM_BASE_URL", settings.LLM_BASE_URL or "https://api.openai.com/v1")
        self.model = get_db_setting("LLM_MODEL", settings.LLM_MODEL or "gpt-4o")
        self.temperature = 0.2
        self.max_tokens = 4000
    
    def is_configured(self) -> bool:
        """Проверить, настроен ли LLM."""
        return bool(self.api_key and self.base_url)
    
    async def _make_request(
        self,
        messages: List[Dict[str, str]],
        response_format: str = "text"
    ) -> Optional[Dict[str, Any]]:
        """Выполнить запрос к LLM API."""
        if not self.is_configured():
            logger.warning("LLM not configured (API key or base URL missing)")
            return None
        
        # Check if using Google AI Studio (Gemini)
        is_gemini = "generativelanguage.googleapis.com" in self.base_url
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if is_gemini:
            # Gemini API format - API key as query parameter
            payload = {
                "contents": [{
                    "parts": [{
                        "text": f"{messages[0]['content']}\n\n{messages[1]['content']}"
                    }]
                }],
                "generationConfig": {
                    "temperature": self.temperature,
                    "maxOutputTokens": self.max_tokens
                }
            }
            
            if response_format == "json":
                payload["generationConfig"]["responseMimeType"] = "application/json"
            
            # Gemini endpoint includes model in the path, API key as query param
            url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        else:
            # OpenAI-compatible format - API key in Authorization header
            headers["Authorization"] = f"Bearer {self.api_key}"
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            
            if response_format == "json":
                payload["response_format"] = {"type": "json_object"}
            
            url = f"{self.base_url}/chat/completions"
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                # Parse Gemini response format
                if is_gemini:
                    if "candidates" in data and len(data["candidates"]) > 0:
                        content = data["candidates"][0]["content"]["parts"][0]["text"]
                        # Wrap in OpenAI-like structure for compatibility
                        return {
                            "choices": [{
                                "message": {"content": content}
                            }]
                        }
                    return None
                
                return data
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM API HTTP error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            return None
    
    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> Optional[str]:
        """Сгенерировать текст."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        result = await self._make_request(messages)
        if result and "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        return None
    
    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> Optional[Dict[str, Any]]:
        """Сгенерировать JSON ответ."""
        import json
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        result = await self._make_request(messages, response_format="json")
        if result and "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM JSON response: {e}")
                # Retry once
                retry_result = await self._make_request([
                    {"role": "system", "content": "Return ONLY valid JSON, no other text."},
                    {"role": "user", "content": user_prompt}
                ], response_format="json")
                if retry_result and "choices" in retry_result:
                    try:
                        return json.loads(retry_result["choices"][0]["message"]["content"])
                    except:
                        pass
                return None
        return None
    
    async def classify_vacancy(
        self,
        vacancy_data: Dict[str, Any],
        filter_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Классифицировать вакансию через LLM."""
        system_prompt = """You are a job vacancy classifier. Analyze the vacancy and determine if it matches the candidate profile.
Return strict JSON only with the following structure:
{
  "match": true,
  "score": 0-100,
  "remote": true/false,
  "grade": "junior|middle|senior|lead|unknown",
  "is_golang": true/false,
  "backend_focus": 0.0-1.0,
  "reasons": ["reason1", "reason2"],
  "red_flags": ["flag1", "flag2"]
}"""
        
        user_prompt = f"""Vacancy data:
Title: {vacancy_data.get('title', '')}
Company: {vacancy_data.get('company', '')}
Description: {vacancy_data.get('description_text', '')}

Filter config:
{filter_config}

Classify this vacancy."""
        
        result = await self.generate_json(system_prompt, user_prompt)
        if result:
            return result
        
        # Default fallback
        return {
            "match": True,
            "score": 50,
            "remote": vacancy_data.get("remote"),
            "grade": "unknown",
            "is_golang": False,
            "backend_focus": 0.5,
            "reasons": [],
            "red_flags": []
        }
    
    async def generate_application(
        self,
        profile_context: str,
        cv_text: str,
        constraints: str,
        vacancy_data: Dict[str, Any],
        questions: Optional[List[Dict[str, str]]] = None
    ) -> Optional[Dict[str, Any]]:
        """Сгенерировать сопроводительное письмо и ответы на вопросы."""
        system_prompt = """You are generating a job application. Use only the candidate context provided.
Do not invent facts. If required information is missing, mark can_answer=false.
Return strict JSON only:
{
  "cover_letter_short": "string",
  "cover_letter_medium": "string",
  "answers": [
    {
      "question": "string",
      "answer": "string",
      "can_answer": true/false,
      "confidence": 0.0-1.0
    }
  ],
  "risk_notes": []
}"""
        
        questions_text = ""
        if questions:
            questions_text = "\nQuestions to answer:\n" + "\n".join([f"- {q.get('question', '')}" for q in questions])
        
        user_prompt = f"""Candidate context:
{profile_context}

CV:
{cv_text}

Constraints:
{constraints}

Vacancy:
Title: {vacancy_data.get('title', '')}
Company: {vacancy_data.get('company', '')}
Description: {vacancy_data.get('description_text', '')}
{questions_text}

Generate application materials."""
        
        return await self.generate_json(system_prompt, user_prompt)
    
    async def generate_outreach(
        self,
        profile_context: str,
        vacancy_data: Dict[str, Any],
        contact_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Сгенерировать outreach сообщение для контакта."""
        system_prompt = """You are generating a direct outreach message to a recruiter or hiring contact.
Use only candidate context and vacancy data. Do not invent facts.
Keep it short, polite and direct.
Return strict JSON only:
{
  "subject": "string or null",
  "message": "string",
  "should_attach_cv": true/false
}"""
        
        user_prompt = f"""Candidate context:
{profile_context}

Vacancy:
Title: {vacancy_data.get('title', '')}
Company: {vacancy_data.get('company', '')}
Description: {vacancy_data.get('description_text', '')}

Contact:
Name: {contact_data.get('person_name', '')}
Role: {contact_data.get('role_hint', '')}
Type: {contact_data.get('contact_type', '')}

Generate outreach message."""
        
        return await self.generate_json(system_prompt, user_prompt)
    
    async def classify_hr_message(
        self,
        message_text: str
    ) -> Optional[Dict[str, Any]]:
        """Классифицировать входящее сообщение как HR или нет."""
        system_prompt = """You are classifying an incoming message.
Determine whether it looks like a recruiter / HR / hiring outreach.
Return strict JSON only:
{
  "is_hr_message": true/false,
  "confidence": 0.0-1.0,
  "intent": "job_outreach|recruiter_follow_up|unknown",
  "asks_resume": true/false,
  "asks_experience": true/false,
  "asks_salary": true/false,
  "summary": "string"
}"""
        
        user_prompt = f"""Message:
{message_text}

Classify this message."""
        
        return await self.generate_json(system_prompt, user_prompt)
    
    async def parse_telegram_post(
        self,
        post_text: str
    ) -> Optional[Dict[str, Any]]:
        """Распарсить Telegram пост и извлечь данные о вакансии."""
        system_prompt = """You are a vacancy parser for Telegram posts.
Analyze the post and extract structured data.
Return strict JSON only:
{
  "is_vacancy": true/false,
  "title": "string or null",
  "company": "string or null",
  "grade": "junior|middle|senior|lead|unknown",
  "remote": true/false,
  "stack": [],
  "description": "string - full vacancy description text from the post",
  "contact_tg": "string or null - Telegram username/handle (e.g. @username or just username)",
  "contact_email": "string or null - email address",
  "apply_url": "string or null - application URL, but NOT hh.ru links (exclude any hh.ru URLs)",
  "salary_text": "string or null",
  "reasons": []
}

Important rules:
- Extract the full description text from the post
- For contacts: extract Telegram handles (starting with @ or just usernames), email addresses
- For apply_url: extract any application links EXCEPT hh.ru links (hh.ru vacancies are processed by a separate agent)
- If multiple contacts exist, pick the most relevant one for each type
- Mark is_vacancy=false if this is not a job posting"""
        
        user_prompt = f"""Telegram post:
{post_text}

Extract vacancy data."""
        
        return await self.generate_json(system_prompt, user_prompt)
