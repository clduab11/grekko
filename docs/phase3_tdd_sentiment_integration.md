# Phase 3: Sentiment Integration TDD Specifications

## Overview

This document provides comprehensive Test-Driven Development (TDD) anchor specifications for the Sentiment Integration System, following London School TDD principles with outside-in development and extensive use of test doubles for social media data ingestion, sentiment analysis, and real-time feed integration.

## Test Categories

### 1. Unit Tests for Core Functions

#### SentimentIntegrationEngine Unit Tests

```python
class TestSentimentIntegrationEngine:
    """Unit tests for SentimentIntegrationEngine core functionality"""
    
    def setup_method(self):
        """Setup test doubles and dependencies"""
        self.mock_config = Mock(spec=SentimentConfig)
        self.mock_event_bus = Mock(spec=EventBus)
        self.mock_aggregator = Mock(spec=SentimentAggregator)
        self.mock_influencer_tracker = Mock(spec=InfluencerTracker)
        self.mock_spam_filter = Mock(spec=SpamFilter)
        self.mock_cache = Mock(spec=SentimentCache)
        
        # Configure mock config
        self.mock_config.sources = [Mock(spec=SourceConfig)]
        self.mock_config.analyzers = [Mock(spec=AnalyzerConfig)]
        self.mock_config.min_data_points = 10
        self.mock_config.min_confidence_threshold = 0.7
        self.mock_config.cache_ttl = 300
        
    def test_engine_initialization_with_valid_config(self):
        """GIVEN valid sentiment configuration
        WHEN SentimentIntegrationEngine is initialized
        THEN engine should initialize with correct dependencies"""
        
        with patch('validate_sentiment_config', return_value=self.mock_config):
            engine = SentimentIntegrationEngine(self.mock_config, self.mock_event_bus)
            
            assert engine.config == self.mock_config
            assert engine.event_bus == self.mock_event_bus
            assert isinstance(engine.sources, dict)
            assert isinstance(engine.analyzers, dict)
    
    def test_engine_initialization_with_invalid_config(self):
        """GIVEN invalid sentiment configuration
        WHEN SentimentIntegrationEngine is initialized
        THEN should raise ConfigurationError"""
        
        with patch('validate_sentiment_config', side_effect=ConfigurationError("Invalid config")):
            with pytest.raises(ConfigurationError):
                SentimentIntegrationEngine(None, self.mock_event_bus)
    
    def test_initialize_sources_success(self):
        """GIVEN valid source configurations
        WHEN initialize_sources is called
        THEN all sources should be registered successfully"""
        
        mock_source = Mock(spec=SentimentSource)
        mock_source.source_id = "test_source"
        mock_source.validate_connection.return_value = True
        
        engine = SentimentIntegrationEngine(self.mock_config, self.mock_event_bus)
        
        with patch.object(engine, '_create_source', return_value=mock_source):
            with patch.object(engine, '_create_analyzer', return_value=Mock()):
                result = engine.initialize_sources()
                
                assert result is True
                assert "test_source" in engine.sources
                self.mock_event_bus.emit.assert_called()
    
    def test_initialize_sources_connection_failure(self):
        """GIVEN source with failed connection
        WHEN initialize_sources is called
        THEN source should not be registered"""
        
        mock_source = Mock(spec=SentimentSource)
        mock_source.validate_connection.return_value = False
        
        engine = SentimentIntegrationEngine(self.mock_config, self.mock_event_bus)
        
        with patch.object(engine, '_create_source', return_value=mock_source):
            with patch.object(engine, '_create_analyzer', return_value=Mock()):
                result = engine.initialize_sources()
                
                assert len(engine.sources) == 0
    
    @pytest.mark.asyncio
    async def test_analyze_token_sentiment_with_cache_hit(self):
        """GIVEN cached sentiment analysis exists
        WHEN analyze_token_sentiment is called
        THEN should return cached result without source calls"""
        
        token_address = "0x123456789abcdef"
        timeframe = "1h"
        
        cached_analysis = Mock(spec=SentimentAnalysis)
        cached_analysis.is_expired.return_value = False
        
        engine = SentimentIntegrationEngine(self.mock_config, self.mock_event_bus)
        engine.cache = self.mock_cache
        
        self.mock_cache.get.return_value = cached_analysis
        
        with patch('validate_token_address', return_value=token_address):
            result = await engine.analyze_token_sentiment(token_address, timeframe)
            
            assert result == cached_analysis
            self.mock_cache.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_token_sentiment_with_cache_miss(self):
        """GIVEN no cached sentiment analysis
        WHEN analyze_token_sentiment is called
        THEN should generate new analysis using sources"""
        
        token_address = "0x123456789abcdef"
        timeframe = "1h"
        
        mock_source = Mock(spec=SentimentSource)
        mock_source.is_active = True
        
        mock_sentiment_data = [Mock(spec=SentimentData)]
        mock_analyzed_data = [Mock(spec=AnalyzedSentimentData)]
        mock_aggregated_sentiment = Mock(spec=SentimentAnalysis)
        
        engine = SentimentIntegrationEngine(self.mock_config, self.mock_event_bus)
        engine.cache = self.mock_cache
        engine.sources = {"test_source": mock_source}
        engine.spam_filter = self.mock_spam_filter
        engine.aggregator = self.mock_aggregator
        engine.influencer_tracker = self.mock_influencer_tracker
        
        self.mock_cache.get.return_value = None
        self.mock_spam_filter.filter_data.return_value = mock_sentiment_data
        self.mock_aggregator.aggregate_sentiment.return_value = mock_aggregated_sentiment
        self.mock_influencer_tracker.calculate_impact.return_value = Mock()
        
        with patch('validate_token_address', return_value=token_address):
            with patch.object(engine, '_collect_sentiment_data', return_value=mock_sentiment_data):
                with patch.object(engine, '_analyze_sentiment', return_value=mock_analyzed_data[0]):
                    with patch.object(engine, '_detect_sentiment_trend', return_value=Mock()):
                        with patch.object(engine, '_generate_sentiment_alerts', return_value=[]):
                            result = await engine.analyze_token_sentiment(token_address, timeframe)
                            
                            assert result == mock_aggregated_sentiment
                            self.mock_aggregator.aggregate_sentiment.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_token_sentiment_invalid_timeframe(self):
        """GIVEN invalid timeframe
        WHEN analyze_token_sentiment is called
        THEN should raise InvalidTimeframeError"""
        
        token_address = "0x123456789abcdef"
        invalid_timeframe = "invalid"
        
        engine = SentimentIntegrationEngine(self.mock_config, self.mock_event_bus)
        
        with patch('validate_token_address', return_value=token_address):
            with patch('SUPPORTED_TIMEFRAMES', ["1h", "4h", "1d"]):
                with pytest.raises(InvalidTimeframeError):
                    await engine.analyze_token_sentiment(token_address, invalid_timeframe)
    
    @pytest.mark.asyncio
    async def test_analyze_token_sentiment_insufficient_data(self):
        """GIVEN insufficient sentiment data
        WHEN analyze_token_sentiment is called
        THEN should raise InsufficientSentimentDataError"""
        
        token_address = "0x123456789abcdef"
        timeframe = "1h"
        
        # Configure minimum data points requirement
        self.mock_config.min_data_points = 10
        
        engine = SentimentIntegrationEngine(self.mock_config, self.mock_event_bus)
        engine.cache = self.mock_cache
        engine.sources = {}  # No sources available
        
        self.mock_cache.get.return_value = None
        
        with patch('validate_token_address', return_value=token_address):
            with pytest.raises(InsufficientSentimentDataError):
                await engine.analyze_token_sentiment(token_address, timeframe)
    
    @pytest.mark.asyncio
    async def test_monitor_viral_content_success(self):
        """GIVEN active sources with viral detection capability
        WHEN monitor_viral_content is called
        THEN should return ranked viral content"""
        
        mock_source = Mock(spec=SentimentSource)
        mock_source.supports_viral_detection.return_value = True
        
        mock_candidate = Mock(spec=ContentCandidate)
        mock_candidate.content_id = "viral_content_1"
        mock_candidate.platform = "twitter"
        mock_candidate.content = "Bitcoin to the moon! #crypto"
        mock_candidate.engagement = Mock()
        
        mock_source.detect_viral_content.return_value = [mock_candidate]
        
        engine = SentimentIntegrationEngine(self.mock_config, self.mock_event_bus)
        engine.sources = {"test_source": mock_source}
        
        with patch.object(engine, '_calculate_virality_score', return_value=85.0):
            with patch.object(engine, '_is_crypto_relevant', return_value=True):
                with patch.object(engine, '_extract_token_mentions', return_value=["BTC"]):
                    result = await engine.monitor_viral_content()
                    
                    assert len(result) == 1
                    assert result[0].virality_score == 85.0
                    assert result[0].platform == "twitter"
    
    @pytest.mark.asyncio
    async def test_monitor_viral_content_source_failure(self):
        """GIVEN source that fails viral detection
        WHEN monitor_viral_content is called
        THEN should continue with other sources and log warning"""
        
        mock_source = Mock(spec=SentimentSource)
        mock_source.supports_viral_detection.return_value = True
        mock_source.detect_viral_content.side_effect = Exception("API Error")
        
        engine = SentimentIntegrationEngine(self.mock_config, self.mock_event_bus)
        engine.sources = {"failing_source": mock_source}
        
        with patch('logger.warning') as mock_logger:
            result = await engine.monitor_viral_content()
            
            assert len(result) == 0
            mock_logger.assert_called_once()
    
    def test_calculate_virality_score(self):
        """GIVEN content with engagement metrics
        WHEN _calculate_virality_score is called
        THEN should return normalized virality score"""
        
        mock_content = Mock(spec=ContentCandidate)
        mock_content.engagement = Mock()
        mock_content.engagement.total_interactions = 1000
        mock_content.reach = 10000
        mock_content.engagement.growth_rate = 0.5
        mock_content.engagement.velocity = 0.3
        
        # Configure weights
#### SentimentSource Unit Tests

```python
class TestSentimentSource:
    """Unit tests for abstract SentimentSource base class"""
    
    def test_source_initialization(self):
        """GIVEN valid source configuration
        WHEN SentimentSource is initialized
        THEN should set correct attributes"""
        
        config = Mock(spec=SourceConfig)
        config.source_id = "test_source"
        config.platform = "twitter"
        config.endpoint = "https://api.twitter.com"
        config.credentials = {"api_key": "test_key"}
        config.rate_limits = Mock(spec=RateLimitConfig)
        config.credibility_score = 0.8
        config.is_active = True
        
        # Create concrete implementation for testing
        class TestSource(SentimentSource):
            async def collect_data(self, query, timeframe, limit):
                pass
            def validate_connection(self):
                return True
        
        source = TestSource(config)
        
        assert source.source_id == "test_source"
        assert source.platform == "twitter"
        assert source.endpoint == "https://api.twitter.com"
        assert source.credibility_score == 0.8
        assert source.is_active is True
    
    def test_supports_viral_detection_with_method(self):
        """GIVEN source with viral detection method
        WHEN supports_viral_detection is called
        THEN should return True"""
        
        class ViralCapableSource(SentimentSource):
            async def collect_data(self, query, timeframe, limit):
                pass
            def validate_connection(self):
                return True
            async def detect_viral_content(self, lookback_period):
                return []
        
        config = Mock(spec=SourceConfig)
        source = ViralCapableSource(config)
        
        assert source.supports_viral_detection() is True
    
    def test_supports_viral_detection_without_method(self):
        """GIVEN source without viral detection method
        WHEN supports_viral_detection is called
        THEN should return False"""
        
        class BasicSource(SentimentSource):
            async def collect_data(self, query, timeframe, limit):
                pass
            def validate_connection(self):
                return True
        
        config = Mock(spec=SourceConfig)
        source = BasicSource(config)
        
        assert source.supports_viral_detection() is False
```

### 2. Social Media Data Ingestion Tests

#### TwitterSentimentSource Integration Tests

```python
class TestTwitterSentimentSource:
    """Tests for Twitter-specific sentiment data collection"""
    
    def setup_method(self):
        """Setup Twitter source configuration and mocks"""
        self.mock_config = Mock(spec=TwitterSourceConfig)
        self.mock_config.source_id = "twitter_source"
        self.mock_config.platform = "twitter"
        self.mock_config.credentials = {
            "api_key": "test_key",
            "api_secret": "test_secret",
            "access_token": "test_token",
            "access_token_secret": "test_token_secret"
        }
        self.mock_config.rate_limits = Mock()
        self.mock_config.credibility_score = 0.9
        self.mock_config.is_active = True
        
        self.mock_twitter_client = Mock()
    
    @pytest.mark.asyncio
    async def test_collect_data_success(self):
        """GIVEN valid query and timeframe
        WHEN collect_data is called
        THEN should return formatted sentiment data"""
        
        # Mock tweet data
        mock_tweet = Mock()
        mock_tweet.id = "tweet_123"
        mock_tweet.text = "Bitcoin is looking bullish! #BTC"
        mock_tweet.author_id = "user_456"
        mock_tweet.created_at = datetime.utcnow()
        mock_tweet.public_metrics = Mock()
        mock_tweet.public_metrics.like_count = 100
        mock_tweet.public_metrics.retweet_count = 50
        mock_tweet.public_metrics.reply_count = 25
        mock_tweet.public_metrics.impression_count = 10000
        mock_tweet.data = {"raw": "data"}
        
        self.mock_twitter_client.search_tweets.return_value = [mock_tweet]
        
        source = TwitterSentimentSource(self.mock_config)
        
        with patch.object(source, '_create_twitter_client', return_value=self.mock_twitter_client):
            with patch.object(source, '_build_twitter_query', return_value="bitcoin"):
                with patch.object(source, '_get_author_credibility', return_value=0.8):
                    result = await source.collect_data("bitcoin", "1h", 100)
                    
                    assert len(result) == 1
                    assert result[0].data_id == "tweet_123"
                    assert result[0].content == "Bitcoin is looking bullish! #BTC"
                    assert result[0].engagement.likes == 100
                    assert result[0].engagement.retweets == 50
    
    @pytest.mark.asyncio
    async def test_collect_data_api_error(self):
        """GIVEN Twitter API error
        WHEN collect_data is called
        THEN should raise SentimentCollectionError"""
        
        self.mock_twitter_client.search_tweets.side_effect = TwitterAPIError("Rate limit exceeded")
        
        source = TwitterSentimentSource(self.mock_config)
        
        with patch.object(source, '_create_twitter_client', return_value=self.mock_twitter_client):
            with patch.object(source, '_build_twitter_query', return_value="bitcoin"):
                with pytest.raises(SentimentCollectionError):
                    await source.collect_data("bitcoin", "1h", 100)
    
    @pytest.mark.asyncio
    async def test_detect_viral_content_success(self):
        """GIVEN trending crypto topics
        WHEN detect_viral_content is called
        THEN should return viral content candidates"""
        
        # Mock trending topic
        mock_topic = Mock()
        mock_topic.name = "Bitcoin"
        
        # Mock viral tweet
        mock_viral_tweet = Mock()
        mock_viral_tweet.id = "viral_123"
        mock_viral_tweet.text = "BREAKING: Bitcoin hits new ATH! 🚀"
        mock_viral_tweet.public_metrics = Mock()
        mock_viral_tweet.public_metrics.retweet_count = 1000
        mock_viral_tweet.public_metrics.like_count = 5000
        
        self.mock_twitter_client.get_trending_topics.return_value = [mock_topic]
        self.mock_twitter_client.search_tweets.return_value = [mock_viral_tweet]
        
        source = TwitterSentimentSource(self.mock_config)
        
        with patch.object(source, '_create_twitter_client', return_value=self.mock_twitter_client):
            with patch.object(source, '_is_crypto_trending_topic', return_value=True):
                with patch.object(source, '_calculate_twitter_engagement', return_value=Mock()):
                    result = await source.detect_viral_content(24)
                    
                    assert len(result) == 1
                    assert result[0].content_id == "viral_123"
                    assert result[0].platform == "twitter"
    
    def test_validate_connection_success(self):
        """GIVEN valid Twitter API credentials
        WHEN validate_connection is called
        THEN should return True"""
        
        self.mock_twitter_client.get_me.return_value = {"id": "user_123"}
        
        source = TwitterSentimentSource(self.mock_config)
        
        with patch.object(source, '_create_twitter_client', return_value=self.mock_twitter_client):
            result = source.validate_connection()
            
            assert result is True
    
    def test_validate_connection_failure(self):
        """GIVEN invalid Twitter API credentials
        WHEN validate_connection is called
        THEN should return False"""
        
        self.mock_twitter_client.get_me.side_effect = Exception("Authentication failed")
        
        source = TwitterSentimentSource(self.mock_config)
        
        with patch.object(source, '_create_twitter_client', return_value=self.mock_twitter_client):
            result = source.validate_connection()
            
            assert result is False
```

### 3. Sentiment Scoring and Calibration Tests

#### SentimentAggregator Unit Tests

```python
class TestSentimentAggregator:
    """Tests for sentiment aggregation across multiple sources"""
    
    def setup_method(self):
        """Setup aggregator configuration and test data"""
        self.mock_config = Mock(spec=AggregationConfig)
        self.mock_config.source_weights = {
            "twitter": 1.0,
            "reddit": 0.8,
            "news": 1.2
        }
        self.mock_config.time_decay_factor = 0.1
        
        self.aggregator = SentimentAggregator(self.mock_config)
    
    @pytest.mark.asyncio
    async def test_aggregate_sentiment_success(self):
        """GIVEN analyzed sentiment data from multiple sources
        WHEN aggregate_sentiment is called
        THEN should return weighted aggregated sentiment"""
        
        # Create test data from different sources
        twitter_data = AnalyzedSentimentData(
            data_id="twitter_1",
            source_id="twitter",
            content="Bitcoin is bullish!",
            sentiment_score=0.8,
            confidence=0.9,
            processed_at=datetime.utcnow()
        )
        
        reddit_data = AnalyzedSentimentData(
            data_id="reddit_1",
            source_id="reddit",
            content="BTC looking good",
            sentiment_score=0.7,
            confidence=0.8,
            processed_at=datetime.utcnow()
        )
        
        analyzed_data = [twitter_data, reddit_data]
        
        with patch.object(self.aggregator, '_calculate_sentiment_trend', return_value=Mock()):
            with patch.object(self.aggregator, '_calculate_sentiment_momentum', return_value=0.6):
                with patch.object(self.aggregator, '_calculate_data_quality', return_value=0.85):
                    result = await self.aggregator.aggregate_sentiment(
                        analyzed_data, "1h", "0x123"
                    )
                    
                    assert isinstance(result, SentimentAnalysis)
                    assert result.token_address == "0x123"
                    assert result.timeframe == "1h"
                    assert 0 <= result.aggregated_sentiment <= 1
                    assert len(result.sources) == 2
    
    def test_calculate_source_sentiment_with_time_decay(self):
        """GIVEN sentiment data points with different timestamps
        WHEN _calculate_source_sentiment is called
        THEN should apply time decay weighting"""
        
        current_time = datetime.utcnow()
        old_time = current_time - timedelta(hours=2)
        
        # Recent data point
        recent_data = AnalyzedSentimentData(
            data_id="recent_1",
            source_id="twitter",
            sentiment_score=0.8,
            confidence=0.9,
            processed_at=current_time
        )
        
        # Older data point
        old_data = AnalyzedSentimentData(
            data_id="old_1",
            source_id="twitter",
            sentiment_score=0.2,
            confidence=0.8,
            processed_at=old_time
        )
        
        data_points = [recent_data, old_data]
        
        result = self.aggregator._calculate_source_sentiment(data_points)
        
        # Recent data should have more weight, so sentiment should be closer to 0.8
        assert result.score > 0.5
        assert result.confidence > 0
        assert result.data_points == 2
    
    def test_calculate_source_sentiment_empty_data(self):
        """GIVEN empty data points list
        WHEN _calculate_source_sentiment is called
        THEN should return zero sentiment with zero confidence"""
        
        result = self.aggregator._calculate_source_sentiment([])
        
        assert result.score == 0
        assert result.confidence == 0
        assert result.data_points == 0
```

### 4. Real-time Feed Integration Tests

#### Real-time Data Processing Tests

```python
class TestRealTimeFeedIntegration:
    """Tests for real-time sentiment feed processing"""
    
    def setup_method(self):
        """Setup real-time feed components"""
        self.mock_config = Mock(spec=SentimentConfig)
        self.mock_event_bus = Mock(spec=EventBus)
        self.mock_stream_processor = Mock(spec=StreamProcessor)
        
    @pytest.mark.asyncio
    async def test_real_time_sentiment_stream_processing(self):
        """GIVEN real-time sentiment data stream
        WHEN data is processed
        THEN should emit sentiment events in real-time"""
        
        # Mock streaming data
        stream_data = [
            {
                "platform": "twitter",
                "content": "Bitcoin pump incoming! 🚀",
                "timestamp": datetime.utcnow(),
                "author": "crypto_trader_123"
            },
            {
                "platform": "reddit",
                "content": "BTC analysis: very bullish signals",
                "timestamp": datetime.utcnow(),
                "author": "reddit_user_456"
            }
        ]
        
        engine = SentimentIntegrationEngine(self.mock_config, self.mock_event_bus)
        
        # Mock real-time processing
        with patch.object(engine, '_process_stream_data') as mock_process:
            mock_process.return_value = Mock(spec=SentimentAnalysis)
            
            for data in stream_data:
                await engine._process_real_time_data(data)
            
            # Should process each data point
            assert mock_process.call_count == len(stream_data)
            
            # Should emit events for processed data
            assert self.mock_event_bus.emit.call_count >= len(stream_data)
    
    @pytest.mark.asyncio
    async def test_rate_limiting_compliance(self):
        """GIVEN rate-limited API sources
        WHEN multiple requests are made
        THEN should respect rate limits and implement backoff"""
        
        mock_source = Mock(spec=SentimentSource)
        mock_rate_limiter = Mock(spec=RateLimiter)
        mock_source.rate_limiter = mock_rate_limiter
        
        # Simulate rate limit exceeded
        mock_rate_limiter.acquire.side_effect = [
            None,  # First request succeeds
            RateLimitExceededError("Rate limit exceeded"),  # Second fails
            None   # Third succeeds after backoff
        ]
        
        engine = SentimentIntegrationEngine(self.mock_config, self.mock_event_bus)
        
        with patch.object(engine, '_collect_sentiment_data') as mock_collect:
            mock_collect.side_effect = [
                [Mock()],  # Success
                SentimentCollectionError("Rate limit exceeded"),  # Failure
                [Mock()]   # Success after backoff
            ]
            
            # Should handle rate limiting gracefully
            results = []
            for i in range(3):
                try:
                    result = await engine._collect_sentiment_data(mock_source, "0x123", "1h")
                    results.append(result)
                except SentimentCollectionError:
                    # Expected for rate-limited request
                    pass
            
            # Should have 2 successful results
            assert len(results) == 2
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self):
        """GIVEN source failures during real-time processing
        WHEN errors occur
        THEN should handle gracefully and continue processing"""
        
        mock_sources = {
            "twitter": Mock(spec=SentimentSource),
            "reddit": Mock(spec=SentimentSource),
            "news": Mock(spec=SentimentSource)
        }
        
        # Configure one source to fail
        mock_sources["twitter"].collect_data.side_effect = Exception("API Error")
        mock_sources["reddit"].collect_data.return_value = [Mock()]
        mock_sources["news"].collect_data.return_value = [Mock()]
        
        engine = SentimentIntegrationEngine(self.mock_config, self.mock_event_bus)
        engine.sources = mock_sources
        
        with patch('logger.warning') as mock_logger:
            # Should continue processing despite one source failure
            result = await engine._collect_all_sentiment_data("0x123", "1h")
            
            # Should have data from 2 working sources
            assert len(result) >= 2
            
            # Should log the error
            mock_logger.assert_called()
```

### 5. Multi-source Sentiment Aggregation Tests

#### Cross-platform Sentiment Validation Tests

```python
class TestMultiSourceSentimentAggregation:
    """Tests for aggregating sentiment across multiple platforms"""
    
    def setup_method(self):
        """Setup multi-source test environment"""
        self.mock_config = Mock(spec=SentimentConfig)
        self.mock_event_bus = Mock(spec=EventBus)
        
        # Configure source weights
        self.mock_config.source_weights = {
            "twitter": 1.0,
            "reddit": 0.8,
            "telegram": 0.6,
            "news": 1.2
        }
        
    @pytest.mark.asyncio
    async def test_weighted_sentiment_aggregation(self):
        """GIVEN sentiment data from multiple sources with different weights
        WHEN sentiment is aggregated
        THEN should apply correct source weights"""
        
        # Create sentiment data with different scores
        sentiment_data = [
            AnalyzedSentimentData(
                source_id="twitter",
                sentiment_score=0.8,  # Positive
                confidence=0.9
            ),
            AnalyzedSentimentData(
                source_id="reddit", 
                sentiment_score=0.3,  # Negative
                confidence=0.7
            ),
            AnalyzedSentimentData(
                source_id="news",
                sentiment_score=0.9,  # Very positive
                confidence=0.95
            )
        ]
        
        aggregator = SentimentAggregator(self.mock_config)
        
        with patch.object(aggregator, '_calculate_sentiment_trend', return_value=Mock()):
            with patch.object(aggregator, '_calculate_sentiment_momentum', return_value=0.5):
                with patch.object(aggregator, '_calculate_data_quality', return_value=0.8):
                    result = await aggregator.aggregate_sentiment(sentiment_data, "1h", "0x123")
                    
                    # News has highest weight (1.2), so should pull sentiment up
                    # Expected: (0.8*1.0 + 0.3*0.8 + 0.9*1.2) / (1.0 + 0.8 + 1.2) = 0.72
                    assert result.aggregated_sentiment > 0.6
                    assert result.aggregated_sentiment < 0.8
    
    @pytest.mark.asyncio
    async def test_sentiment_confidence_weighting(self):
        """GIVEN sentiment data with varying confidence levels
        WHEN sentiment is aggregated
        THEN should weight by confidence scores"""
        
        # High confidence positive sentiment
        high_confidence_data = AnalyzedSentimentData(
            source_id="news",
            sentiment_score=0.9,
            confidence=0.95,
            processed_at=datetime.utcnow()
        )
        
        # Low confidence negative sentiment
        low_confidence_data = AnalyzedSentimentData(
            source_id="twitter",
            sentiment_score=0.2,
            confidence=0.3,
            processed_at=datetime.utcnow()
        )
        
        aggregator = SentimentAggregator(self.mock_config)
        
        result = aggregator._calculate_source_sentiment([high_confidence_data, low_confidence_data])
        
        # High confidence data should dominate
        assert result.score > 0.7
        assert result.confidence > 0.6
    
    @pytest.mark.asyncio
    async def test_sentiment_trend_detection(self):
        """GIVEN historical sentiment data
        WHEN trend is calculated
        THEN should detect sentiment direction and momentum"""
        
        # Create time series of sentiment data showing upward trend
        base_time = datetime.utcnow()
        trend_data = []
        
        for i in range(5):
            data_point = AnalyzedSentimentData(
                source_id="twitter",
                sentiment_score=0.3 + (i * 0.15),  # Increasing from 0.3 to 0.9
                confidence=0.8,
                processed_at=base_time - timedelta(hours=4-i)
            )
            trend_data.append(data_point)
        
        aggregator = SentimentAggregator(self.mock_config)
        
        trend = await aggregator._calculate_sentiment_trend(trend_data, "4h")
        
        assert trend.direction == "BULLISH"
        assert trend.strength > 0.5
        assert trend.momentum > 0
    
    def test_data_quality_assessment(self):
        """GIVEN sentiment data with varying quality indicators
        WHEN data quality is assessed
        THEN should return appropriate quality score"""
        
        # High quality data
        high_quality_data = [
            AnalyzedSentimentData(
                source_id="news",
                confidence=0.95,
                author_credibility=0.9,
                processed_at=datetime.utcnow()
            ),
            AnalyzedSentimentData(
                source_id="twitter",
                confidence=0.85,
                author_credibility=0.8,
                processed_at=datetime.utcnow()
            )
        ]
        
        # Low quality data
        low_quality_data = [
            AnalyzedSentimentData(
                source_id="unknown",
                confidence=0.4,
                author_credibility=0.2,
                processed_at=datetime.utcnow() - timedelta(hours=6)  # Stale
            )
        ]
        
        aggregator = SentimentAggregator(self.mock_config)
        
        high_quality_score = aggregator._calculate_data_quality(high_quality_data)
        low_quality_score = aggregator._calculate_data_quality(low_quality_data)
        
        assert high_quality_score > 0.8
        assert low_quality_score < 0.5
        assert high_quality_score > low_quality_score
```

## Test Execution Framework

### Pytest Configuration

```python
# conftest.py
import pytest
import asyncio
from unittest.mock import Mock
from datetime import datetime, timedelta
from src.sentiment_integration.engine import SentimentIntegrationEngine
from src.sentiment_integration.config import SentimentConfig

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_sentiment_config():
    """Provide mock sentiment configuration for tests"""
    config = Mock(spec=SentimentConfig)
    config.sources = []
    config.analyzers = []
    config.min_data_points = 5
    config.min_confidence_threshold = 0.6
    config.cache_ttl = 300
    config.viral_detection_window = 24
    config.max_viral_alerts = 10
    return config

@pytest.fixture
def mock_event_bus():
    """Provide mock event bus for tests"""
    return Mock()

@pytest.fixture
def sentiment_engine(mock_sentiment_config, mock_event_bus):
    """Provide configured sentiment engine for tests"""
    return SentimentIntegrationEngine(mock_sentiment_config, mock_event_bus)

@pytest.fixture
def sample_tweet_data():
    """Provide sample Twitter data for tests"""
    return {
        "id": "tweet_123",
        "text": "Bitcoin is looking bullish! #BTC #crypto",
        "author_id": "user_456",
        "created_at": datetime.utcnow(),
        "public_metrics": {
            "like_count": 100,
            "retweet_count": 50,
            "reply_count": 25,
            "impression_count": 10000
        }
    }

@pytest.fixture
def sample_sentiment_data():
    """Provide sample analyzed sentiment data for tests"""
    return [
        AnalyzedSentimentData(
            data_id="data_1",
            source_id="twitter",
            content="Bitcoin to the moon!",
            sentiment_score=0.8,
            confidence=0.9,
            processed_at=datetime.utcnow()
        ),
        AnalyzedSentimentData(
            data_id="data_2", 
            source_id="reddit",
            content="BTC looking bearish",
            sentiment_score=0.2,
            confidence=0.7,
            processed_at=datetime.utcnow()
        )
    ]
```

### Test Execution Commands

```bash
# Run all sentiment integration tests
pytest tests/test_sentiment_integration/ -v

# Run specific test categories
pytest tests/test_sentiment_integration/test_unit.py -v
pytest tests/test_sentiment_integration/test_integration.py -v
pytest tests/test_sentiment_integration/test_real_time.py -v
pytest tests/test_sentiment_integration/test_aggregation.py -v

# Run with coverage
pytest tests/test_sentiment_integration/ --cov=src.sentiment_integration --cov-report=html

# Run real-time processing tests
pytest tests/test_sentiment_integration/test_real_time.py -m realtime

# Run social media integration tests
pytest tests/test_sentiment_integration/test_social_media.py -m social_media

# Run performance tests
pytest tests/test_sentiment_integration/test_performance.py -m performance
```

---

*This TDD specification provides comprehensive test coverage for the Sentiment Integration System, ensuring robust validation of social media data ingestion, sentiment scoring accuracy, real-time feed integration, multi-source aggregation, and error handling for production-ready AI trading systems.*
        self.mock_config.engagement_weight = 0.4
        self.mock_config.growth_weight = 0.3
        self.mock_config.velocity_weight = 0.3
        
        engine = SentimentIntegrationEngine(self.mock_config, self.mock_event_bus)
        
        score = engine._calculate_virality_score(mock_content)
        
        # Score should be between 0 and 100
        assert 0 <= score <= 100
        assert isinstance(score, float)
    
    def test_is_crypto_relevant_with_keywords(self):
        """GIVEN content with crypto keywords
        WHEN _is_crypto_relevant is called
        THEN should return True for relevant content"""
        
        crypto_content = "Bitcoin price surge! BTC to the moon #cryptocurrency"
        
        self.mock_config.crypto_keywords = ["bitcoin", "btc", "cryptocurrency"]
        self.mock_config.token_patterns = [r'\$[A-Z]{3,5}', r'#crypto']
        self.mock_config.min_relevance_matches = 2
        
        engine = SentimentIntegrationEngine(self.mock_config, self.mock_event_bus)
        
        result = engine._is_crypto_relevant(crypto_content)
        
        assert result is True
    
    def test_is_crypto_relevant_insufficient_matches(self):
        """GIVEN content with insufficient crypto relevance
        WHEN _is_crypto_relevant is called
        THEN should return False"""
        
        non_crypto_content = "Weather is nice today"
        
        self.mock_config.crypto_keywords = ["bitcoin", "btc", "cryptocurrency"]
        self.mock_config.token_patterns = [r'\$[A-Z]{3,5}']
        self.mock_config.min_relevance_matches = 2
        
        engine = SentimentIntegrationEngine(self.mock_config, self.mock_event_bus)
        
        result = engine._is_crypto_relevant(non_crypto_content)
        
        assert result is False