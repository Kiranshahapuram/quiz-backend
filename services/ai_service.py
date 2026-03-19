import json
import httpx
from django.conf import settings

class AIServiceError(Exception):
    pass

class AIRateLimitError(Exception):
    pass

class AIService:
    @staticmethod
    def _mock_generate(topic, difficulty, count):
        return [
            {
                "body": f"Mock Question {i+1} on {topic} ({difficulty})",
                "options": [
                    {"body": "Correct Option", "is_correct": True},
                    {"body": "Wrong Option 1", "is_correct": False},
                    {"body": "Wrong Option 2", "is_correct": False},
                    {"body": "Wrong Option 3", "is_correct": False},
                ],
                "explanation": "This is a mock explanation."
            }
            for i in range(count)
        ]

    @classmethod
    def generate_questions(cls, topic, difficulty, count):
        groq_key = getattr(settings, 'GROQ_API_KEY', '')
        gemini_key = getattr(settings, 'GEMINI_API_KEY', '')
        
        prompt = f"""
        Generate a quiz about '{topic}' with difficulty '{difficulty}'.
        I need exactly {count} multiple choice questions.
        For each question, provide 4 options where EXACTLY ONE is correct.
        
        Output MUST be pure JSON matching this exact schema:
        {{
            "questions": [
                {{
                    "body": "Question text here",
                    "options": [
                        {{"body": "Option text here", "is_correct": true}},
                        {{"body": "Wrong option text", "is_correct": false}},
                        {{"body": "Another wrong option", "is_correct": false}},
                        {{"body": "Last wrong option", "is_correct": false}}
                    ],
                    "explanation": "Explanation for the correct answer"
                }}
            ]
        }}
        Output ONLY the raw JSON object.
        """

        if groq_key and not groq_key.startswith('your_'):
            return cls._generate_via_groq(groq_key, prompt, count)
        elif gemini_key and not gemini_key.startswith('AIza'):
            # Using your new logic for Gemini 2.0/2.5
            return cls._generate_via_gemini(gemini_key, prompt, count)
        else:
            return cls._mock_generate(topic, difficulty, count)

    @classmethod
    def _generate_via_groq(cls, api_key, prompt, count):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are a quiz generator that outputs ONLY JSON."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.5
        }
        
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, headers=headers, json=payload)
                if response.status_code == 429:
                    raise AIRateLimitError("Groq rate limit exceeded")
                if response.status_code != 200:
                    raise AIServiceError(f"Groq API Error: {response.text}")
                
                result = response.json()
                text_result = result['choices'][0]['message']['content']
                return cls._parse_and_validate(text_result, count)
        except Exception as e:
            raise AIServiceError(str(e))

    @classmethod
    def _generate_via_gemini(cls, api_key, prompt, count):
        # Using the v1beta endpoint with 2.0-flash as it was the most promise-yielding
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json"}
        }
        
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, json=payload)
                if response.status_code == 429:
                    raise AIRateLimitError("Gemini rate limit exceeded")
                if response.status_code != 200:
                    raise AIServiceError(f"Gemini API Error: {response.text}")
                    
                data = response.json()
                text_result = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return cls._parse_and_validate(text_result, count)
        except Exception as e:
            raise AIServiceError(str(e))

    @classmethod
    def _parse_and_validate(cls, text_result, count):
        if not text_result:
            raise AIServiceError("Empty response from AI")
            
        # Clean up markdown if AI ignored the instructions
        if "```json" in text_result:
            text_result = text_result.split("```json")[-1].split("```")[0].strip()
        elif "```" in text_result:
            text_result = text_result.split("```")[-1].split("```")[0].strip()

        try:
            parsed = json.loads(text_result)
            questions = parsed.get("questions", [])
            
            if len(questions) != count:
                 # Try to find questions if they are at top level
                 if isinstance(parsed, list):
                     questions = parsed
                 else:
                     raise AIServiceError(f"Expected {count} questions, got {len(questions)}")
            
            for q in questions:
                correct_count = sum(1 for opt in q.get('options', []) if opt.get('is_correct'))
                if correct_count != 1:
                    raise AIServiceError("Invalid options: Must have exactly 1 correct option per question")
                    
            return questions
        except json.JSONDecodeError:
            raise AIServiceError("Failed to parse JSON from AI")
