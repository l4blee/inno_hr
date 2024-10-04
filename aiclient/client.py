import json
import logging
from openai import AsyncOpenAI

from .utils import GPTResponse
from database import Users

logger = logging.getLogger('aiclient')

class OpenAIClient:
    def __init__(self, token: str, model: str, instruction: str) -> None:
        self._client = AsyncOpenAI(api_key=token)
        self._model = model
        self._context_base = [{'role': 'system', 'content': instruction}]

        logger.info('Initialized OpenAI client...')

    async def get_response(self, prompt: str, user: Users) -> GPTResponse:
        context = json.loads(user.context) if user.use_context else []

        context.append({'role': 'user', 'content': prompt})

        res = await self._client.chat.completions.create(
            model=self._model,
            messages=self._context_base 
                     + [{'role': 'system', 'content': f'Также учитывай следующие требования вакансии: {user.candidate_requirements}'}] 
                     + context,
            max_tokens=user.tokens_left,
            temperature=0.6
        )

        gpt_response = GPTResponse(
            content=res.choices[0].message.content,
            tokens_total=res.usage.total_tokens,
            tokens_completion=res.usage.completion_tokens
        )
        
        if user.use_context:
            user.context = json.dumps(context)
            user.context_used += gpt_response.tokens_total 

        user.tokens_left -= gpt_response.tokens_completion

        return gpt_response
