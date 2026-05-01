# services/llm_services.py => defines the LLMService class which is responsible for interacting with the language model (LM Studio in this case). It has a method to generate responses based on a system prompt and user message. 
# This service layer isolates the LM logic from the API routes, making it easier to swap out the model provider or test the agent core without relying on the actual LM """

import httpx
import logging

logger = logging.getLogger(__name__)

## Service layer isolates LM logic from API routes.
# Makes model provider swappable and easier to test.
class LLMService :
    def __init__(self, base_url, model, api_key=None) :
          self.base_url = base_url
          self.model = model
          self.api_key = api_key

      
    async def generate(self, system_prompt, user_message=None) :
      messages = []

      if user_message :
        messages.append({"role" : "system", "content": system_prompt})
        messages.append({"role" : "user", "content": user_message})

      else :
        messages.append({"role" : "user", "content": system_prompt})

      payload = {
        "model" : self.model,
        "messages" : messages,
        "temperature" : 0.4,
        "max_tokens" : 300
    }
      headers = {}
      if self.api_key:
          headers["Authorization"] = f"Bearer {self.api_key}"

      async with httpx.AsyncClient(timeout=120.0) as client :
        response = await client.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload,
            headers=headers,
        )

        response.raise_for_status() 
        data = response.json()
        
        logger.debug("LM response received. choices=%s", len(data.get("choices", [])))
        
        return data["choices"][0]["message"]["content"].strip()

    async def converse(self, user_message: str) -> str:
      return await self.generate(
          system_prompt="""You are RUX, a helpful AI personal assistant.
          Answer conversationally and helpfully. Never return JSON.""",
          user_message=user_message
      )