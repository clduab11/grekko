"""
Trading agent implementation for the Grekko platform.

This module implements the TradingAgent class, which provides an interface
to language models and manages the communication, prompt formatting, and
response handling.
"""
import logging
import json
import asyncio
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum

from ...utils.logger import get_logger
from ...utils.metrics import track_latency
from ...utils.credentials_manager import CredentialsManager

class ModelProvider(Enum):
    """Supported language model providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    COHERE = "cohere"
    LLAMA = "llama"
    CUSTOM = "custom"

class TradingAgent:
    """
    Trading agent powered by a language model.
    
    This class provides an interface to various language models and handles
    prompt construction, API communication, and response parsing. It is designed
    to be used by the LLM Ensemble and other components that need LLM capabilities.
    
    Attributes:
        name (str): Name of the agent
        model_provider (ModelProvider): Provider of the language model
        model_name (str): Name of the specific model to use
        system_prompt (str): System prompt to use for the model
        max_tokens (int): Maximum number of tokens for model responses
        temperature (float): Temperature parameter for model sampling
        logger (logging.Logger): Logger for agent events
    """
    
    def __init__(self, 
                 name: str,
                 model_provider: Union[str, ModelProvider] = ModelProvider.ANTHROPIC,
                 model_name: str = "claude-3-5-sonnet",
                 system_prompt: str = "You are a helpful trading assistant.",
                 max_tokens: int = 2000,
                 temperature: float = 0.7):
        """
        Initialize the trading agent.
        
        Args:
            name (str): Name of the agent
            model_provider (Union[str, ModelProvider]): Provider of the language model
            model_name (str): Name of the specific model to use
            system_prompt (str): System prompt to use for the model
            max_tokens (int): Maximum number of tokens for model responses
            temperature (float): Temperature parameter for model sampling
        """
        self.name = name
        
        # Convert string to enum if needed
        if isinstance(model_provider, str):
            try:
                self.model_provider = ModelProvider(model_provider)
            except ValueError:
                self.model_provider = ModelProvider.CUSTOM
        else:
            self.model_provider = model_provider
            
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Initialize logger
        self.logger = get_logger(f'agent.{name}')
        self.logger.info(f"Initialized trading agent '{name}' with {model_provider} {model_name}")
        
        # Initialize API clients
        self._init_clients()
        
        # Metrics tracking
        self.metrics = {
            "total_calls": 0,
            "total_tokens": 0,
            "avg_latency": 0.0,
            "errors": 0
        }
    
    def _init_clients(self) -> None:
        """Initialize API clients for language model providers."""
        credentials = CredentialsManager()
        self.api_keys = {}
        
        try:
            if self.model_provider == ModelProvider.ANTHROPIC:
                self.api_keys["anthropic"] = credentials.get_credential("anthropic_api_key")
                
                # Lazy import to avoid dependency issues
                try:
                    from anthropic import Anthropic
                    self.client = Anthropic(api_key=self.api_keys["anthropic"])
                except ImportError:
                    self.logger.error("Anthropic Python SDK not installed. Run 'pip install anthropic'")
                    self.client = None
                
            elif self.model_provider == ModelProvider.OPENAI:
                self.api_keys["openai"] = credentials.get_credential("openai_api_key")
                
                # Lazy import to avoid dependency issues
                try:
                    from openai import AsyncOpenAI
                    self.client = AsyncOpenAI(api_key=self.api_keys["openai"])
                except ImportError:
                    self.logger.error("OpenAI Python SDK not installed. Run 'pip install openai'")
                    self.client = None
                
            elif self.model_provider == ModelProvider.COHERE:
                self.api_keys["cohere"] = credentials.get_credential("cohere_api_key")
                
                # Lazy import to avoid dependency issues
                try:
                    import cohere
                    self.client = cohere.Client(self.api_keys["cohere"])
                except ImportError:
                    self.logger.error("Cohere Python SDK not installed. Run 'pip install cohere'")
                    self.client = None
                
            elif self.model_provider == ModelProvider.LLAMA:
                # Local Llama models don't need API keys
                self.client = "local"  # Placeholder for local implementation
                
            else:
                self.logger.warning(f"Unsupported model provider: {self.model_provider}")
                self.client = None
                
        except Exception as e:
            self.logger.error(f"Error initializing API client: {str(e)}")
            self.client = None
    
    @track_latency("trading_agent_generate")
    async def generate(self, prompt: str) -> str:
        """
        Generate a response from the language model.
        
        Args:
            prompt (str): The prompt to send to the model
            
        Returns:
            str: The model's response
        """
        if not self.client:
            self._init_clients()
            if not self.client:
                error_msg = "No language model client available"
                self.logger.error(error_msg)
                return f"Error: {error_msg}"
        
        self.metrics["total_calls"] += 1
        start_time = time.time()
        
        try:
            if self.model_provider == ModelProvider.ANTHROPIC:
                response = await self._generate_anthropic(prompt)
            elif self.model_provider == ModelProvider.OPENAI:
                response = await self._generate_openai(prompt)
            elif self.model_provider == ModelProvider.COHERE:
                response = await self._generate_cohere(prompt)
            elif self.model_provider == ModelProvider.LLAMA:
                response = await self._generate_llama(prompt)
            else:
                response = "Unsupported model provider"
                
            # Update metrics
            duration = time.time() - start_time
            self._update_metrics(duration)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            self.metrics["errors"] += 1
            return f"Error: {str(e)}"
    
    async def _generate_anthropic(self, prompt: str) -> str:
        """
        Generate a response using Anthropic's Claude.
        
        Args:
            prompt (str): The prompt to send to Claude
            
        Returns:
            str: Claude's response
        """
        try:
            message = await self.client.messages.create(
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Update token metrics
            self.metrics["total_tokens"] += message.usage.input_tokens + message.usage.output_tokens
            
            return message.content[0].text
        except Exception as e:
            self.logger.error(f"Anthropic API error: {str(e)}")
            raise
    
    async def _generate_openai(self, prompt: str) -> str:
        """
        Generate a response using OpenAI's GPT models.
        
        Args:
            prompt (str): The prompt to send to GPT
            
        Returns:
            str: GPT's response
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Update token metrics
            self.metrics["total_tokens"] += response.usage.total_tokens
            
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"OpenAI API error: {str(e)}")
            raise
    
    async def _generate_cohere(self, prompt: str) -> str:
        """
        Generate a response using Cohere models.
        
        Args:
            prompt (str): The prompt to send to Cohere
            
        Returns:
            str: Cohere's response
        """
        try:
            # Cohere's Python client is not async, so we use run_in_executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.generate(
                    model=self.model_name,
                    prompt=f"{self.system_prompt}\n\n{prompt}",
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
            )
            
            # Cohere doesn't always provide token metrics
            if hasattr(response, 'total_tokens'):
                self.metrics["total_tokens"] += response.total_tokens
            
            return response.generations[0].text
        except Exception as e:
            self.logger.error(f"Cohere API error: {str(e)}")
            raise
    
    async def _generate_llama(self, prompt: str) -> str:
        """
        Generate a response using local Llama models.
        
        Args:
            prompt (str): The prompt to send to Llama
            
        Returns:
            str: Llama's response
        """
        try:
            # Local Llama implementation
            # This is a placeholder - actual implementation would depend on the specific
            # Llama deployment being used (e.g., llama.cpp, llama-cpp-python, etc.)
            self.logger.warning("Local Llama generation not fully implemented")
            
            # Example implementation using llama-cpp-python's HTTP server
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:8000/completion",
                    json={
                        "prompt": f"{self.system_prompt}\n\n{prompt}",
                        "max_tokens": self.max_tokens,
                        "temperature": self.temperature,
                    },
                ) as response:
                    result = await response.json()
                    return result["content"]
                    
        except Exception as e:
            self.logger.error(f"Llama generation error: {str(e)}")
            raise
    
    def _update_metrics(self, duration: float) -> None:
        """
        Update agent metrics.
        
        Args:
            duration (float): Duration of the last API call in seconds
        """
        # Update average latency using a running average
        if self.metrics["total_calls"] == 1:
            self.metrics["avg_latency"] = duration
        else:
            self.metrics["avg_latency"] = (
                (self.metrics["avg_latency"] * (self.metrics["total_calls"] - 1) + duration) / 
                self.metrics["total_calls"]
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get the agent's performance metrics.
        
        Returns:
            Dict[str, Any]: The agent's metrics
        """
        return dict(self.metrics)
    
    def estimate_cost(self) -> Dict[str, float]:
        """
        Estimate the cost of API calls made by this agent.
        
        Returns:
            Dict[str, float]: Cost estimates in USD
        """
        # Cost per 1000 tokens (approximate as of 2024)
        cost_per_1k = {
            "claude-3-opus": (15.0, 75.0),  # (input, output)
            "claude-3-sonnet": (3.0, 15.0),
            "claude-3-haiku": (0.25, 1.25),
            "claude-3-5-sonnet": (3.0, 15.0),
            "gpt-4-turbo": (10.0, 30.0),
            "gpt-4": (10.0, 30.0),
            "gpt-3.5-turbo": (0.5, 1.5)
        }
        
        # Default cost for unknown models
        default_cost = (5.0, 15.0)
        
        # Get cost rates for this model
        input_cost, output_cost = cost_per_1k.get(self.model_name, default_cost)
        
        # Estimate costs assuming a 1:3 input to output token ratio
        total_tokens = self.metrics["total_tokens"]
        input_tokens = total_tokens * 0.25
        output_tokens = total_tokens * 0.75
        
        input_cost_usd = (input_tokens / 1000) * input_cost
        output_cost_usd = (output_tokens / 1000) * output_cost
        total_cost_usd = input_cost_usd + output_cost_usd
        
        return {
            "input_cost_usd": input_cost_usd,
            "output_cost_usd": output_cost_usd,
            "total_cost_usd": total_cost_usd,
            "estimated_tokens": total_tokens
        }