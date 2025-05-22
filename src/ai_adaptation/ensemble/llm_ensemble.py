"""
LLM Ensemble implementation for the Grekko trading platform.

This module implements the Multi-Model LLM Strategy Ensemble that leverages
multiple language models to enhance trading strategy selection, risk assessment,
and market analysis.
"""
import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from datetime import datetime

from ...utils.logger import get_logger
from ...utils.metrics import track_latency
from ..agent.trading_agent import TradingAgent


class ModelType(Enum):
    """Types of models in the LLM ensemble."""
    META = "meta"  # Orchestrator
    TECHNICAL = "technical"  # Technical analysis
    REGIME = "regime"  # Market regime
    SENTIMENT = "sentiment"  # Sentiment analysis
    RISK = "risk"  # Risk assessment


class LLMEnsemble:
    """
    Multi-Model LLM Strategy Ensemble for enhanced trading decisions.
    
    This class implements an ensemble of specialized language models that
    collaborate to analyze market conditions, select optimal strategies,
    and assess trading risks. Each model focuses on a specific aspect of
    market analysis, and the meta-model orchestrates the ensemble.
    
    Attributes:
        config (Dict[str, Any]): Configuration for the ensemble
        meta_model (TradingAgent): Orchestrator model
        technical_model (TradingAgent): Technical analysis model
        regime_model (TradingAgent): Market regime model
        sentiment_model (TradingAgent): Sentiment analysis model
        risk_model (TradingAgent): Risk assessment model
        model_weights (Dict[str, float]): Contribution weights for each model
        cache (Dict[str, Any]): Cache for recent analyses
        logger (logging.Logger): Logger for ensemble events
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the LLM ensemble.
        
        Args:
            config (Dict[str, Any]): Configuration parameters for the ensemble
        """
        self.config = config
        self.logger = get_logger('llm_ensemble')
        self.logger.info("Initializing LLM Ensemble with %d models", 
                         len(config.get('models', {})))
        
        # Initialize model weights (default equal weighting)
        self.model_weights = config.get('model_weights', {
            ModelType.TECHNICAL.value: 0.25,
            ModelType.REGIME.value: 0.25,
            ModelType.SENTIMENT.value: 0.25,
            ModelType.RISK.value: 0.25
        })
        
        # Initialize models
        self._init_models()
        
        # Initialize cache
        self.cache = {}
        self.cache_ttl = config.get('cache_ttl', 300)  # 5 minutes default
        
        # Performance tracking
        self.performance_metrics = {
            "calls": 0,
            "cache_hits": 0,
            "avg_latency": 0,
            "model_contributions": {model.value: 0 for model in ModelType},
            "success_rate": 0
        }
    
    def _init_models(self) -> None:
        """Initialize all models in the ensemble."""
        models_config = self.config.get('models', {})
        
        # Initialize meta model (orchestrator)
        meta_config = models_config.get(ModelType.META.value, {})
        self.meta_model = TradingAgent(
            name="meta_orchestrator",
            model_provider=meta_config.get('provider', 'anthropic'),
            model_name=meta_config.get('model_name', 'claude-3-5-sonnet'),
            system_prompt=self._load_prompt('meta_system_prompt'),
            max_tokens=meta_config.get('max_tokens', 4000)
        )
        
        # Initialize technical analysis model
        tech_config = models_config.get(ModelType.TECHNICAL.value, {})
        self.technical_model = TradingAgent(
            name="technical_analysis",
            model_provider=tech_config.get('provider', 'openai'),
            model_name=tech_config.get('model_name', 'gpt-4'),
            system_prompt=self._load_prompt('technical_system_prompt'),
            max_tokens=tech_config.get('max_tokens', 2000)
        )
        
        # Initialize market regime model
        regime_config = models_config.get(ModelType.REGIME.value, {})
        self.regime_model = TradingAgent(
            name="market_regime",
            model_provider=regime_config.get('provider', 'anthropic'),
            model_name=regime_config.get('model_name', 'claude-3-opus'),
            system_prompt=self._load_prompt('regime_system_prompt'),
            max_tokens=regime_config.get('max_tokens', 2000)
        )
        
        # Initialize sentiment model
        sentiment_config = models_config.get(ModelType.SENTIMENT.value, {})
        self.sentiment_model = TradingAgent(
            name="sentiment_analysis",
            model_provider=sentiment_config.get('provider', 'anthropic'),
            model_name=sentiment_config.get('model_name', 'claude-3-5-sonnet'),
            system_prompt=self._load_prompt('sentiment_system_prompt'),
            max_tokens=sentiment_config.get('max_tokens', 2000)
        )
        
        # Initialize risk model
        risk_config = models_config.get(ModelType.RISK.value, {})
        self.risk_model = TradingAgent(
            name="risk_assessment",
            model_provider=risk_config.get('provider', 'openai'),
            model_name=risk_config.get('model_name', 'gpt-4'),
            system_prompt=self._load_prompt('risk_system_prompt'),
            max_tokens=risk_config.get('max_tokens', 2000)
        )
    
    def _load_prompt(self, prompt_name: str) -> str:
        """
        Load a prompt template from the prompts directory.
        
        Args:
            prompt_name (str): Name of the prompt template
            
        Returns:
            str: The prompt template text
        """
        try:
            prompt_path = f"config/prompts/{prompt_name}.txt"
            with open(prompt_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            self.logger.warning(f"Prompt template {prompt_name} not found, using default")
            return self._get_default_prompt(prompt_name)
    
    def _get_default_prompt(self, prompt_name: str) -> str:
        """
        Get a default prompt template for the specified name.
        
        Args:
            prompt_name (str): Name of the prompt template
            
        Returns:
            str: Default prompt template text
        """
        default_prompts = {
            "meta_system_prompt": """You are the orchestrator for a trading AI ensemble. Your role is to coordinate the analysis from multiple specialized models, resolve conflicts, and produce a unified trading recommendation. You should weigh each model's input based on its historical performance and current market conditions.""",
            
            "technical_system_prompt": """You are a technical analysis specialist for a trading AI. Analyze price patterns, indicators, and chart formations to identify potential trading signals. Focus only on technical aspects of the market, not fundamentals or sentiment.""",
            
            "regime_system_prompt": """You are a market regime specialist for a trading AI. Your job is to identify the current market regime (trending, ranging, volatile) and recommend appropriate strategies for this regime. Consider macro conditions and market structure in your analysis.""",
            
            "sentiment_system_prompt": """You are a sentiment analysis specialist for a trading AI. Analyze market sentiment from news, social media, and on-chain metrics. Identify extreme sentiment conditions and sentiment shifts that might affect trading decisions.""",
            
            "risk_system_prompt": """You are a risk assessment specialist for a trading AI. Evaluate potential trades for risk exposure, correlation with existing positions, and portfolio impact. Recommend position sizing and risk management strategies."""
        }
        
        return default_prompts.get(prompt_name, "You are a trading assistant. Provide analysis and recommendations based on market data.")
    
    @track_latency("llm_ensemble_analyze")
    async def analyze(self, 
                    market_data: Dict[str, Any],
                    current_positions: Optional[List[Dict[str, Any]]] = None,
                    market_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform a comprehensive analysis using the LLM ensemble.
        
        Args:
            market_data (Dict[str, Any]): Current market data
            current_positions (Optional[List[Dict[str, Any]]]): Current portfolio positions
            market_state (Optional[Dict[str, Any]]): Additional market state information
            
        Returns:
            Dict[str, Any]: Ensemble analysis and recommendations
        """
        self.performance_metrics["calls"] += 1
        
        # Check cache for recent identical analysis
        cache_key = self._generate_cache_key(market_data, current_positions, market_state)
        cached_result = self._check_cache(cache_key)
        if cached_result:
            self.performance_metrics["cache_hits"] += 1
            return cached_result
        
        # Prepare analysis context
        context = self._prepare_context(market_data, current_positions, market_state)
        
        # Run specialized models in parallel
        tasks = [
            self._run_technical_analysis(context),
            self._run_regime_analysis(context),
            self._run_sentiment_analysis(context),
            self._run_risk_analysis(context)
        ]
        
        model_results = await asyncio.gather(*tasks)
        technical_analysis, regime_analysis, sentiment_analysis, risk_analysis = model_results
        
        # Combine model outputs with meta-model
        ensemble_result = await self._orchestrate_ensemble(
            context,
            technical_analysis,
            regime_analysis,
            sentiment_analysis,
            risk_analysis
        )
        
        # Cache the result
        self._update_cache(cache_key, ensemble_result)
        
        return ensemble_result
    
    async def assess_risk(self,
                         trade_signal: Dict[str, Any],
                         market_data: Dict[str, Any],
                         current_positions: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Assess the risk of a potential trade using the risk model.
        
        Args:
            trade_signal (Dict[str, Any]): The trading signal to evaluate
            market_data (Dict[str, Any]): Current market data
            current_positions (Optional[List[Dict[str, Any]]]): Current portfolio positions
            
        Returns:
            Dict[str, Any]: Risk assessment results
        """
        # Prepare the risk assessment context
        context = {
            "trade_signal": trade_signal,
            "market_data": market_data,
            "current_positions": current_positions or [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Format the prompt for risk assessment
        prompt = f"""
        Please assess the risk of the following potential trade:
        
        ## Trade Signal
        ```json
        {json.dumps(trade_signal, indent=2)}
        ```
        
        ## Current Market Data
        ```json
        {json.dumps(market_data, indent=2)}
        ```
        
        ## Current Portfolio Positions
        ```json
        {json.dumps(current_positions or [], indent=2)}
        ```
        
        Provide a comprehensive risk assessment including:
        1. Overall risk score (0-10 scale)
        2. Position sizing recommendation
        3. Correlation with existing positions
        4. Specific risk factors
        5. Recommended risk mitigation strategies
        
        Format your response as a JSON object.
        """
        
        # Get risk assessment from the risk model
        risk_response = await self.risk_model.generate(prompt)
        
        try:
            # Extract JSON from response
            risk_assessment = self._extract_json(risk_response)
            
            # Add metadata
            risk_assessment["timestamp"] = datetime.now().isoformat()
            risk_assessment["model"] = self.risk_model.model_name
            
            return risk_assessment
        except Exception as e:
            self.logger.error(f"Error extracting risk assessment JSON: {str(e)}")
            # Return a basic risk assessment
            return {
                "risk_score": 5,
                "position_sizing": {"max_position_pct": 0.02},
                "error": "Failed to parse model output",
                "timestamp": datetime.now().isoformat()
            }
    
    def _prepare_context(self, 
                        market_data: Dict[str, Any],
                        current_positions: Optional[List[Dict[str, Any]]],
                        market_state: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Prepare the analysis context for all models.
        
        Args:
            market_data (Dict[str, Any]): Current market data
            current_positions (Optional[List[Dict[str, Any]]]): Current portfolio positions
            market_state (Optional[Dict[str, Any]]): Additional market state information
            
        Returns:
            Dict[str, Any]: Prepared context
        """
        return {
            "market_data": market_data,
            "current_positions": current_positions or [],
            "market_state": market_state or {},
            "timestamp": datetime.now().isoformat()
        }
    
    async def _run_technical_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run technical analysis using the technical model.
        
        Args:
            context (Dict[str, Any]): Analysis context
            
        Returns:
            Dict[str, Any]: Technical analysis results
        """
        market_data = context["market_data"]
        
        prompt = f"""
        Please analyze the following market data from a technical analysis perspective:
        
        ```json
        {json.dumps(market_data, indent=2)}
        ```
        
        Provide a technical analysis including:
        1. Identified chart patterns
        2. Key support and resistance levels
        3. Technical indicator readings (RSI, MACD, etc.)
        4. Trend strength and direction
        5. Technical trading signals (entry/exit points)
        
        Format your response as a JSON object.
        """
        
        response = await self.technical_model.generate(prompt)
        
        try:
            analysis = self._extract_json(response)
            analysis["model_type"] = ModelType.TECHNICAL.value
            analysis["timestamp"] = datetime.now().isoformat()
            return analysis
        except Exception as e:
            self.logger.error(f"Error in technical analysis: {str(e)}")
            return {
                "model_type": ModelType.TECHNICAL.value,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _run_regime_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run market regime analysis using the regime model.
        
        Args:
            context (Dict[str, Any]): Analysis context
            
        Returns:
            Dict[str, Any]: Market regime analysis results
        """
        market_data = context["market_data"]
        market_state = context["market_state"]
        
        prompt = f"""
        Please analyze the following market data to identify the current market regime:
        
        ## Market Data
        ```json
        {json.dumps(market_data, indent=2)}
        ```
        
        ## Market State
        ```json
        {json.dumps(market_state, indent=2)}
        ```
        
        Provide a market regime analysis including:
        1. Current market regime classification (trending, ranging, volatile)
        2. Confidence in the classification
        3. Signs of potential regime change
        4. Recommended strategies for this regime
        5. Key metrics supporting your classification
        
        Format your response as a JSON object.
        """
        
        response = await self.regime_model.generate(prompt)
        
        try:
            analysis = self._extract_json(response)
            analysis["model_type"] = ModelType.REGIME.value
            analysis["timestamp"] = datetime.now().isoformat()
            return analysis
        except Exception as e:
            self.logger.error(f"Error in regime analysis: {str(e)}")
            return {
                "model_type": ModelType.REGIME.value,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _run_sentiment_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run sentiment analysis using the sentiment model.
        
        Args:
            context (Dict[str, Any]): Analysis context
            
        Returns:
            Dict[str, Any]: Sentiment analysis results
        """
        market_data = context["market_data"]
        
        prompt = f"""
        Please analyze the sentiment for the following market:
        
        ```json
        {json.dumps(market_data, indent=2)}
        ```
        
        Provide a sentiment analysis including:
        1. Overall market sentiment (bullish, bearish, neutral)
        2. Sentiment extremes detection (fear/greed)
        3. Recent sentiment changes
        4. News and social media impact
        5. On-chain sentiment indicators (if applicable)
        
        Format your response as a JSON object.
        """
        
        response = await self.sentiment_model.generate(prompt)
        
        try:
            analysis = self._extract_json(response)
            analysis["model_type"] = ModelType.SENTIMENT.value
            analysis["timestamp"] = datetime.now().isoformat()
            return analysis
        except Exception as e:
            self.logger.error(f"Error in sentiment analysis: {str(e)}")
            return {
                "model_type": ModelType.SENTIMENT.value,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _run_risk_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run risk analysis using the risk model.
        
        Args:
            context (Dict[str, Any]): Analysis context
            
        Returns:
            Dict[str, Any]: Risk analysis results
        """
        market_data = context["market_data"]
        current_positions = context["current_positions"]
        
        prompt = f"""
        Please analyze the risk factors for the following market and portfolio:
        
        ## Market Data
        ```json
        {json.dumps(market_data, indent=2)}
        ```
        
        ## Current Positions
        ```json
        {json.dumps(current_positions, indent=2)}
        ```
        
        Provide a risk analysis including:
        1. Overall market risk level
        2. Specific risk factors
        3. Portfolio concentration risk
        4. Correlation risks
        5. Recommended risk management strategies
        
        Format your response as a JSON object.
        """
        
        response = await self.risk_model.generate(prompt)
        
        try:
            analysis = self._extract_json(response)
            analysis["model_type"] = ModelType.RISK.value
            analysis["timestamp"] = datetime.now().isoformat()
            return analysis
        except Exception as e:
            self.logger.error(f"Error in risk analysis: {str(e)}")
            return {
                "model_type": ModelType.RISK.value,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _orchestrate_ensemble(self,
                                  context: Dict[str, Any],
                                  technical_analysis: Dict[str, Any],
                                  regime_analysis: Dict[str, Any],
                                  sentiment_analysis: Dict[str, Any],
                                  risk_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrate the ensemble using the meta-model.
        
        Args:
            context (Dict[str, Any]): Analysis context
            technical_analysis (Dict[str, Any]): Technical analysis results
            regime_analysis (Dict[str, Any]): Market regime analysis results
            sentiment_analysis (Dict[str, Any]): Sentiment analysis results
            risk_analysis (Dict[str, Any]): Risk analysis results
            
        Returns:
            Dict[str, Any]: Orchestrated ensemble results
        """
        # Format the prompt for the meta-model
        prompt = f"""
        Please analyze and synthesize the following model outputs into a cohesive trading recommendation:
        
        ## Context
        Market: {context["market_data"].get("symbol", "Unknown")}
        Timestamp: {context["timestamp"]}
        
        ## Technical Analysis Model Output
        ```json
        {json.dumps(technical_analysis, indent=2)}
        ```
        
        ## Market Regime Model Output
        ```json
        {json.dumps(regime_analysis, indent=2)}
        ```
        
        ## Sentiment Analysis Model Output
        ```json
        {json.dumps(sentiment_analysis, indent=2)}
        ```
        
        ## Risk Analysis Model Output
        ```json
        {json.dumps(risk_analysis, indent=2)}
        ```
        
        Please provide a synthesized analysis including:
        1. Overall market assessment
        2. Trading recommendation (buy, sell, hold)
        3. Confidence level (0-1)
        4. Entry, target, and stop levels (if applicable)
        5. Position sizing recommendation
        6. Time horizon
        7. Key contributing factors from each model
        8. Areas of disagreement between models and your resolution
        
        Format your response as a JSON object.
        """
        
        meta_response = await self.meta_model.generate(prompt)
        
        try:
            # Extract JSON from response
            ensemble_result = self._extract_json(meta_response)
            
            # Add metadata
            ensemble_result["model_outputs"] = {
                "technical": technical_analysis,
                "regime": regime_analysis,
                "sentiment": sentiment_analysis,
                "risk": risk_analysis
            }
            ensemble_result["timestamp"] = datetime.now().isoformat()
            ensemble_result["model_weights"] = self.model_weights
            
            return ensemble_result
        except Exception as e:
            self.logger.error(f"Error in ensemble orchestration: {str(e)}")
            # Return a basic result with the individual model outputs
            return {
                "error": f"Failed to orchestrate ensemble: {str(e)}",
                "model_outputs": {
                    "technical": technical_analysis,
                    "regime": regime_analysis,
                    "sentiment": sentiment_analysis,
                    "risk": risk_analysis
                },
                "timestamp": datetime.now().isoformat(),
                "model_weights": self.model_weights
            }
    
    def _generate_cache_key(self,
                           market_data: Dict[str, Any],
                           current_positions: Optional[List[Dict[str, Any]]],
                           market_state: Optional[Dict[str, Any]]) -> str:
        """
        Generate a cache key for the given inputs.
        
        Args:
            market_data (Dict[str, Any]): Market data
            current_positions (Optional[List[Dict[str, Any]]]): Current positions
            market_state (Optional[Dict[str, Any]]): Market state
            
        Returns:
            str: Cache key
        """
        # Use relevant parts of the input to generate a cache key
        key_data = {
            "symbol": market_data.get("symbol"),
            "last_price": market_data.get("last"),
            "timestamp": market_data.get("timestamp"),
            "positions_hash": hash(str(current_positions)) if current_positions else None,
            "state_hash": hash(str(market_state)) if market_state else None
        }
        
        return json.dumps(key_data)
    
    def _check_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Check if a cached result exists and is valid.
        
        Args:
            cache_key (str): Cache key to check
            
        Returns:
            Optional[Dict[str, Any]]: Cached result or None
        """
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            cache_time = datetime.fromisoformat(cache_entry["timestamp"])
            now = datetime.now()
            
            # Check if cache is still valid
            if (now - cache_time).total_seconds() < self.cache_ttl:
                return cache_entry["result"]
        
        return None
    
    def _update_cache(self, cache_key: str, result: Dict[str, Any]) -> None:
        """
        Update the cache with a new result.
        
        Args:
            cache_key (str): Cache key
            result (Dict[str, Any]): Result to cache
        """
        self.cache[cache_key] = {
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        # Prune cache if it gets too large
        if len(self.cache) > self.config.get('max_cache_size', 100):
            # Remove oldest entries
            sorted_keys = sorted(
                self.cache.keys(),
                key=lambda k: datetime.fromisoformat(self.cache[k]["timestamp"])
            )
            for key in sorted_keys[:len(sorted_keys) // 2]:  # Remove half of the entries
                del self.cache[key]
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        Extract a JSON object from text.
        
        Args:
            text (str): Text containing JSON
            
        Returns:
            Dict[str, Any]: Extracted JSON object
        """
        try:
            # Look for JSON block in markdown
            if "```json" in text:
                json_block = text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_block)
            
            # Look for JSON object between curly braces
            if "{" in text and "}" in text:
                json_text = text[text.find("{"):text.rfind("}") + 1]
                return json.loads(json_text)
            
            # Try to parse the whole text as JSON
            return json.loads(text)
        except Exception as e:
            self.logger.error(f"Failed to extract JSON: {str(e)}")
            raise
    
    def update_model_weights(self, new_weights: Dict[str, float]) -> None:
        """
        Update the weights of models in the ensemble.
        
        Args:
            new_weights (Dict[str, float]): New weights for each model
        """
        # Validate weights
        total = sum(new_weights.values())
        if abs(total - 1.0) > 0.01:  # Allow small rounding errors
            self.logger.warning(f"Model weights sum to {total}, normalizing to 1.0")
            # Normalize weights to sum to 1.0
            for model in new_weights:
                new_weights[model] = new_weights[model] / total
        
        self.model_weights = new_weights
        self.logger.info(f"Updated model weights: {self.model_weights}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the ensemble.
        
        Returns:
            Dict[str, Any]: Performance metrics
        """
        return dict(self.performance_metrics)