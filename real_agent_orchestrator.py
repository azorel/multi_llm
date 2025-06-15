
import os
import random
import time
from typing import Dict, List, Optional, Tuple

from anthropic import Anthropic
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

class ProviderLoadBalancer:
    def __init__(self):
        self.providers = {
            'anthropic': 0.5,
            'gemini': 0.5
        }
        
        self.fallback_provider = 'anthropic'
        self._validate_weights()

    def _validate_weights(self):
        total = sum(self.providers.values())
        if not (0.99 <= total <= 1.01):  # Allow small float imprecision
            raise ValueError(f"Provider weights must sum to 1.0, got {total}")

    def get_provider(self) -> str:
        r = random.random()
        cumulative = 0
        for provider, weight in self.providers.items():
            cumulative += weight
            if r <= cumulative:
                return provider
        return self.fallback_provider

class RealAgent:
    def __init__(
        self,
        agent_name: str,
        agent_role: str,
        anthropic_api_key: str,
        google_api_key: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ):
        self.agent_name = agent_name
        self.agent_role = agent_role
        self.anthropic_api_key = anthropic_api_key
        self.google_api_key = google_api_key
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        self.provider_lb = ProviderLoadBalancer()
        self.conversation_history: List[Dict] = []
        
        self._init_all_llm_clients()

    def _init_all_llm_clients(self):
        # Initialize Anthropic client
        self.anthropic_client = Anthropic(api_key=self.anthropic_api_key)
        
        # Initialize Google Gemini client
        genai.configure(api_key=self.google_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-pro')

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(5)
    )
    def execute_task(self, task: str) -> Tuple[str, Dict]:
        provider = self.provider_lb.get_provider()
        
        try:
            if provider == 'anthropic':
                completion = self.anthropic_client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=[
                        {
                            "role": "system",
                            "content": f"{self.system_prompt}\nYou are {self.agent_name}, a {self.agent_role}."
                        },
                        {
                            "role": "user",
                            "content": task
                        }
                    ]
                )
                response = completion.content[0].text
                
            elif provider == 'gemini':
                prompt = f"{self.system_prompt}\nYou are {self.agent_name}, a {self.agent_role}.\n\nTask: {task}"
                completion = self.gemini_model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=self.temperature,
                        max_output_tokens=self.max_tokens
                    )
                )
                response = completion.text
                
            else:
                raise ValueError(f"Unknown provider: {provider}")

            self.conversation_history.append({
                "role": "user",
                "content": task
            })
            self.conversation_history.append({
                "role": "assistant", 
                "content": response
            })

            return response, {"provider": provider}

        except Exception as e:
            if provider != self.provider_lb.fallback_provider:
                # Try fallback provider
                return self.execute_task(task)
            else:
                raise e

    def get_conversation_history(self) -> List[Dict]:
        return self.conversation_history