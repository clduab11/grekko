# Phase 3: Sentiment Integration Engine - Pseudocode Specification

## Overview

The Sentiment Integration Engine provides real-time social media analysis, news sentiment tracking, influencer monitoring, and community pulse analysis for crypto market sentiment intelligence.

## Module: SentimentIntegrationEngine

```python
class SentimentIntegrationEngine:
    """
    Central coordinator for sentiment analysis across multiple platforms
    Aggregates and analyzes sentiment data for trading insights
    """
    
    def __init__(self, config: SentimentConfig, event_bus: EventBus):
        # TEST: Engine initializes with valid configuration
        self.config = validate_sentiment_config(config)
        self.event_bus = event_bus
        self.sources = {}
        self.analyzers = {}
        self.aggregator = SentimentAggregator(config.aggregation_settings)
        self.influencer_tracker = InfluencerTracker(config.influencer_settings)
        self.spam_filter = SpamFilter(config.spam_detection)
        self.cache = SentimentCache(config.cache_settings)
        
    def initialize_sources(self) -> bool:
        """Initialize all sentiment data sources"""
        # TEST: All configured sources initialize successfully
        try:
            for source_config in self.config.sources:
                source = self._create_source(source_config)
                # TEST: Source validation checks API connectivity
                if source.validate_connection():
                    self.sources[source.source_id] = source
                    # TEST: Source registration emits event
                    self.event_bus.emit(SentimentSourceRegistered(source.source_id))
                else:
                    # TEST: Failed source initialization logs warning
                    logger.warning(f"Failed to initialize source: {source_config.platform}")
            
            # TEST: NLP analyzers initialize correctly
            for analyzer_config in self.config.analyzers:
                analyzer = self._create_analyzer(analyzer_config)
                self.analyzers[analyzer.analyzer_id] = analyzer
            
            return len(self.sources) > 0 and len(self.analyzers) > 0
        except Exception as e:
            # TEST: Initialization errors are handled gracefully
            logger.error(f"Sentiment engine initialization failed: {e}")
            return False
    
    async def analyze_token_sentiment(self, token_address: str, timeframe: str = "1h") -> SentimentAnalysis:
        """
        Analyze sentiment for specific token across all sources
        Returns aggregated sentiment with confidence metrics
        """
        # TEST: Token address validation
        validated_address = validate_token_address(token_address)
        
        # TEST: Timeframe validation
        if timeframe not in SUPPORTED_TIMEFRAMES:
            raise InvalidTimeframeError(f"Unsupported timeframe: {timeframe}")
        
        # TEST: Cache check for recent analysis
        cache_key = f"sentiment:{validated_address}:{timeframe}"
        cached_analysis = await self.cache.get(cache_key)
        if cached_analysis and not cached_analysis.is_expired():
            return cached_analysis
        
        # TEST: Parallel sentiment collection from all sources
        sentiment_tasks = []
        for source in self.sources.values():
            if source.is_active:
                task = self._collect_sentiment_data(source, validated_address, timeframe)
                sentiment_tasks.append(task)
        
        # TEST: Sentiment data collection with timeout handling
        sentiment_data = []
        completed_tasks = await asyncio.gather(*sentiment_tasks, return_exceptions=True)
        
        for i, result in enumerate(completed_tasks):
            if isinstance(result, Exception):
                # TEST: Individual source failures don't break analysis
                logger.warning(f"Source {list(self.sources.keys())[i]} failed: {result}")
                continue
            sentiment_data.extend(result)
        
        # TEST: Minimum data requirement validation
        if len(sentiment_data) < self.config.min_data_points:
            raise InsufficientSentimentDataError("Not enough sentiment data collected")
        
        # TEST: Spam filtering removes low-quality content
        filtered_data = await self.spam_filter.filter_data(sentiment_data)
        
        # TEST: Sentiment analysis processing
        analyzed_data = []
        for data_point in filtered_data:
            try:
                # TEST: NLP analysis with confidence scoring
                analysis = await self._analyze_sentiment(data_point)
                analyzed_data.append(analysis)
            except Exception as e:
                # TEST: Individual analysis failures are logged and skipped
                logger.debug(f"Sentiment analysis failed for data point: {e}")
                continue
        
        # TEST: Sentiment aggregation across sources
        aggregated_sentiment = await self.aggregator.aggregate_sentiment(
            analyzed_data, 
            timeframe,
            validated_address
        )
        
        # TEST: Influencer impact calculation
        influencer_impact = await self.influencer_tracker.calculate_impact(
            analyzed_data,
            validated_address
        )
        aggregated_sentiment.influencer_impact = influencer_impact
        
        # TEST: Trend detection and momentum calculation
        sentiment_trend = await self._detect_sentiment_trend(
            validated_address,
            aggregated_sentiment,
            timeframe
        )
        aggregated_sentiment.trend = sentiment_trend
        
        # TEST: Alert generation for significant changes
        alerts = await self._generate_sentiment_alerts(
            validated_address,
            aggregated_sentiment
        )
        aggregated_sentiment.alerts = alerts
        
        # TEST: Cache storage with appropriate TTL
        await self.cache.set(cache_key, aggregated_sentiment, ttl=self.config.cache_ttl)
        
        # TEST: Sentiment analysis event emission
        self.event_bus.emit(SentimentAnalysisCompleted(
            token_address=validated_address,
            sentiment_score=aggregated_sentiment.aggregated_sentiment,
            trend=sentiment_trend.direction
        ))
        
        return aggregated_sentiment
    
    async def monitor_viral_content(self) -> List[ViralContent]:
        """
        Monitor for viral content across platforms
        Detects trending topics and rapid engagement growth
        """
        # TEST: Viral content detection across all active sources
        viral_candidates = []
        
        for source in self.sources.values():
            if source.supports_viral_detection():
                try:
                    # TEST: Platform-specific viral detection
                    candidates = await source.detect_viral_content(
                        lookback_period=self.config.viral_detection_window
                    )
                    viral_candidates.extend(candidates)
                except Exception as e:
                    # TEST: Viral detection errors don't break monitoring
                    logger.warning(f"Viral detection failed for {source.platform}: {e}")
                    continue
        
        # TEST: Viral content scoring and ranking
        scored_content = []
        for candidate in viral_candidates:
            # TEST: Virality score calculation
            virality_score = self._calculate_virality_score(candidate)
            
            # TEST: Crypto relevance filtering
            if self._is_crypto_relevant(candidate.content):
                scored_content.append(ViralContent(
                    content_id=candidate.content_id,
                    platform=candidate.platform,
                    content=candidate.content,
                    virality_score=virality_score,
                    engagement_metrics=candidate.engagement,
                    token_mentions=self._extract_token_mentions(candidate.content),
                    detected_at=datetime.utcnow()
                ))
        
        # TEST: Content ranking by virality score
        ranked_content = sorted(scored_content, key=lambda x: x.virality_score, reverse=True)
        
        # TEST: Viral content event emission
        for content in ranked_content[:self.config.max_viral_alerts]:
            self.event_bus.emit(ViralContentDetected(
                content_id=content.content_id,
                platform=content.platform,
                virality_score=content.virality_score,
                token_mentions=content.token_mentions
            ))
        
        return ranked_content
    
    async def track_influencer_activity(self, influencer_ids: List[str]) -> List[InfluencerActivity]:
        """
        Track specific influencers for market-relevant activity
        Monitors posts, engagement, and sentiment impact
        """
        # TEST: Influencer ID validation
        validated_ids = [id for id in influencer_ids if self._is_valid_influencer_id(id)]
        
        if not validated_ids:
            raise InvalidInfluencerIdsError("No valid influencer IDs provided")
        
        # TEST: Parallel influencer activity tracking
        activity_data = []
        for influencer_id in validated_ids:
            try:
                # TEST: Recent activity retrieval
                recent_activity = await self._get_influencer_activity(
                    influencer_id,
                    lookback_hours=self.config.influencer_tracking_window
                )
                
                # TEST: Activity analysis and scoring
                for activity in recent_activity:
                    analyzed_activity = await self._analyze_influencer_activity(activity)
                    activity_data.append(analyzed_activity)
                    
            except Exception as e:
                # TEST: Individual influencer tracking errors are logged
                logger.warning(f"Failed to track influencer {influencer_id}: {e}")
                continue
        
        # TEST: Activity filtering for crypto relevance
        crypto_relevant_activity = [
            activity for activity in activity_data
            if self._is_crypto_relevant(activity.content)
        ]
        
        # TEST: Impact scoring based on historical accuracy
        for activity in crypto_relevant_activity:
            # TEST: Historical accuracy lookup
            historical_accuracy = await self.influencer_tracker.get_accuracy_score(
                activity.influencer_id
            )
            
            # TEST: Impact calculation with accuracy weighting
            activity.impact_score = self._calculate_impact_score(
                activity.engagement_metrics,
                historical_accuracy,
                activity.sentiment_score
            )
        
        return crypto_relevant_activity
    
    async def _collect_sentiment_data(self, source: SentimentSource, token_address: str, timeframe: str) -> List[SentimentData]:
        """Collect sentiment data from specific source"""
        # TEST: Rate limiting compliance
        await source.rate_limiter.acquire()
        
        try:
            # TEST: Platform-specific data collection
            raw_data = await source.collect_data(
                query=self._build_search_query(token_address),
                timeframe=timeframe,
                limit=self.config.max_data_per_source
            )
            
            # TEST: Data validation and cleaning
            validated_data = []
            for data_point in raw_data:
                if self._validate_data_point(data_point):
                    cleaned_data = self._clean_data_point(data_point)
                    validated_data.append(cleaned_data)
            
            return validated_data
            
        except RateLimitExceededError:
            # TEST: Rate limit handling with backoff
            await asyncio.sleep(source.backoff_delay)
            raise SentimentCollectionError(f"Rate limit exceeded for {source.platform}")
        except Exception as e:
            # TEST: Collection errors are wrapped appropriately
            raise SentimentCollectionError(f"Data collection failed for {source.platform}: {e}")
    
    async def _analyze_sentiment(self, data_point: SentimentData) -> AnalyzedSentimentData:
        """Analyze sentiment of individual data point"""
        # TEST: Analyzer selection based on content type
        analyzer = self._select_analyzer(data_point.content_type)
        
        try:
            # TEST: NLP sentiment analysis
            sentiment_result = await analyzer.analyze(data_point.content)
            
            # TEST: Confidence validation
            if sentiment_result.confidence < self.config.min_confidence_threshold:
                raise LowConfidenceError("Sentiment confidence below threshold")
            
            # TEST: Analyzed data creation
            return AnalyzedSentimentData(
                data_id=data_point.data_id,
                source_id=data_point.source_id,
                content=data_point.content,
                author=data_point.author,
                sentiment=sentiment_result.sentiment,
                sentiment_score=sentiment_result.score,
                confidence=sentiment_result.confidence,
                entities=sentiment_result.entities,
                keywords=sentiment_result.keywords,
                processed_at=datetime.utcnow()
            )
            
        except Exception as e:
            # TEST: Analysis errors are logged and re-raised
            logger.error(f"Sentiment analysis failed: {e}")
            raise SentimentAnalysisError(f"Failed to analyze sentiment: {e}")
    
    def _calculate_virality_score(self, content: ContentCandidate) -> float:
        """Calculate virality score based on engagement metrics"""
        # TEST: Virality score calculation with multiple factors
        engagement_rate = content.engagement.total_interactions / max(content.reach, 1)
        growth_rate = content.engagement.growth_rate
        velocity = content.engagement.velocity
        
        # TEST: Weighted virality calculation
        virality_score = (
            engagement_rate * self.config.engagement_weight +
            growth_rate * self.config.growth_weight +
            velocity * self.config.velocity_weight
        )
        
        # TEST: Score normalization to 0-100 range
        return min(max(virality_score * 100, 0), 100)
    
    def _is_crypto_relevant(self, content: str) -> bool:
        """Determine if content is relevant to cryptocurrency"""
        # TEST: Crypto relevance detection using keywords and patterns
        crypto_keywords = self.config.crypto_keywords
        token_patterns = self.config.token_patterns
        
        content_lower = content.lower()
        
        # TEST: Keyword matching
        keyword_matches = sum(1 for keyword in crypto_keywords if keyword in content_lower)
        
        # TEST: Token pattern matching
        pattern_matches = sum(1 for pattern in token_patterns if re.search(pattern, content))
        
        # TEST: Relevance threshold check
        total_matches = keyword_matches + pattern_matches
        return total_matches >= self.config.min_relevance_matches
```

## Module: SentimentSource (Abstract Base)

```python
class SentimentSource(ABC):
    """Abstract base class for sentiment data sources"""
    
    def __init__(self, config: SourceConfig):
        # TEST: Source initialization with valid configuration
        self.source_id = config.source_id
        self.platform = config.platform
        self.endpoint = config.endpoint
        self.credentials = config.credentials
        self.rate_limiter = RateLimiter(config.rate_limits)
        self.is_active = config.is_active
        self.credibility_score = config.credibility_score
        
    @abstractmethod
    async def collect_data(self, query: str, timeframe: str, limit: int) -> List[RawSentimentData]:
        """Collect raw sentiment data from source"""
        pass
    
    @abstractmethod
    def validate_connection(self) -> bool:
        """Validate connection to data source"""
        pass
    
    def supports_viral_detection(self) -> bool:
        """Check if source supports viral content detection"""
        return hasattr(self, 'detect_viral_content')
```

## Module: TwitterSentimentSource

```python
class TwitterSentimentSource(SentimentSource):
    """Twitter-specific sentiment data collection"""
    
    def __init__(self, config: TwitterSourceConfig):
        super().__init__(config)
        # TEST: Twitter API client initialization
        self.twitter_client = self._create_twitter_client(config.credentials)
        
    async def collect_data(self, query: str, timeframe: str, limit: int) -> List[RawSentimentData]:
        """Collect tweets matching query criteria"""
        # TEST: Query construction with filters
        search_query = self._build_twitter_query(query, timeframe)
        
        try:
            # TEST: Twitter API search with pagination
            tweets = await self.twitter_client.search_tweets(
                query=search_query,
                max_results=limit,
                tweet_fields=['public_metrics', 'author_id', 'created_at', 'context_annotations']
            )
            
            # TEST: Tweet data conversion
            sentiment_data = []
            for tweet in tweets:
                data_point = RawSentimentData(
                    data_id=tweet.id,
                    source_id=self.source_id,
                    content=tweet.text,
                    author=tweet.author_id,
                    author_credibility=await self._get_author_credibility(tweet.author_id),
                    engagement=EngagementMetrics(
                        likes=tweet.public_metrics.like_count,
                        retweets=tweet.public_metrics.retweet_count,
                        replies=tweet.public_metrics.reply_count,
                        reach=tweet.public_metrics.impression_count
                    ),
                    created_at=tweet.created_at,
                    raw_data=tweet.data
                )
                sentiment_data.append(data_point)
            
            return sentiment_data
            
        except TwitterAPIError as e:
            # TEST: Twitter API errors are handled appropriately
            raise SentimentCollectionError(f"Twitter data collection failed: {e}")
    
    async def detect_viral_content(self, lookback_period: int) -> List[ContentCandidate]:
        """Detect viral crypto-related content on Twitter"""
        # TEST: Viral content detection with trending topics
        try:
            # TEST: Trending topics retrieval
            trending_topics = await self.twitter_client.get_trending_topics()
            
            # TEST: Crypto-relevant trending filter
            crypto_trending = [
                topic for topic in trending_topics
                if self._is_crypto_trending_topic(topic)
            ]
            
            viral_candidates = []
            for topic in crypto_trending:
                # TEST: High-engagement tweet retrieval
                viral_tweets = await self.twitter_client.search_tweets(
                    query=f"{topic.name} min_retweets:100 min_faves:500",
                    max_results=50
                )
                
                for tweet in viral_tweets:
                    # TEST: Viral candidate creation
                    candidate = ContentCandidate(
                        content_id=tweet.id,
                        platform="twitter",
                        content=tweet.text,
                        engagement=self._calculate_twitter_engagement(tweet),
                        detected_at=datetime.utcnow()
                    )
                    viral_candidates.append(candidate)
            
            return viral_candidates
            
        except Exception as e:
            # TEST: Viral detection errors are logged
            logger.error(f"Twitter viral detection failed: {e}")
            return []
    
    def validate_connection(self) -> bool:
        """Validate Twitter API connection"""
        # TEST: Connection validation with API test
        try:
            response = self.twitter_client.get_me()
            return response is not None
        except Exception:
            # TEST: Connection validation handles errors
            return False
```

## Module: SentimentAggregator

```python
class SentimentAggregator:
    """Aggregates sentiment data across multiple sources and timeframes"""
    
    def __init__(self, config: AggregationConfig):
        # TEST: Aggregator initialization with weights
        self.config = config
        self.source_weights = config.source_weights
        self.time_decay_factor = config.time_decay_factor
        
    async def aggregate_sentiment(self, analyzed_data: List[AnalyzedSentimentData], timeframe: str, token_address: str) -> SentimentAnalysis:
        """Aggregate sentiment data into comprehensive analysis"""
        # TEST: Data grouping by source
        data_by_source = self._group_by_source(analyzed_data)
        
        # TEST: Source-level sentiment calculation
        source_sentiments = {}
        for source_id, data_points in data_by_source.items():
            source_sentiment = self._calculate_source_sentiment(data_points)
            source_sentiments[source_id] = source_sentiment
        
        # TEST: Weighted sentiment aggregation
        total_weight = 0
        weighted_sentiment = 0
        
        for source_id, sentiment in source_sentiments.items():
            weight = self.source_weights.get(source_id, 1.0)
            weighted_sentiment += sentiment.score * weight
            total_weight += weight
        
        aggregated_sentiment = weighted_sentiment / total_weight if total_weight > 0 else 0
        
        # TEST: Sentiment trend calculation
        sentiment_trend = await self._calculate_sentiment_trend(analyzed_data, timeframe)
        
        # TEST: Momentum calculation
        momentum = self._calculate_sentiment_momentum(analyzed_data)
        
        # TEST: Source summary creation
        source_summaries = [
            SentimentSourceSummary(
                source_id=source_id,
                sentiment_score=sentiment.score,
                data_points=len(data_points),
                confidence=sentiment.confidence,
                weight=self.source_weights.get(source_id, 1.0)
            )
            for source_id, sentiment in source_sentiments.items()
        ]
        
        # TEST: Comprehensive sentiment analysis creation
        return SentimentAnalysis(
            analysis_id=generate_uuid(),
            token_address=token_address,
            timeframe=timeframe,
            aggregated_sentiment=aggregated_sentiment,
            sentiment_trend=sentiment_trend,
            momentum=momentum,
            sources=source_summaries,
            data_quality_score=self._calculate_data_quality(analyzed_data),
            generated_at=datetime.utcnow()
        )
    
    def _calculate_source_sentiment(self, data_points: List[AnalyzedSentimentData]) -> SourceSentiment:
        """Calculate sentiment for specific source"""
        # TEST: Time-weighted sentiment calculation
        total_weight = 0
        weighted_sentiment = 0
        
        current_time = datetime.utcnow()
        
        for data_point in data_points:
            # TEST: Time decay calculation
            time_diff = (current_time - data_point.processed_at).total_seconds() / 3600  # hours
            time_weight = math.exp(-time_diff * self.time_decay_factor)
            
            # TEST: Confidence weighting
            confidence_weight = data_point.confidence
            
            # TEST: Combined weight calculation
            combined_weight = time_weight * confidence_weight
            
            weighted_sentiment += data_point.sentiment_score * combined_weight
            total_weight += combined_weight
        
        # TEST: Source sentiment result
        return SourceSentiment(
            score=weighted_sentiment / total_weight if total_weight > 0 else 0,
            confidence=total_weight / len(data_points) if data_points else 0,
            data_points=len(data_points)
        )
```

## Configuration Schema

```python
@dataclass
class SentimentConfig:
    """Configuration for sentiment integration engine"""
    sources: List[SourceConfig]
    analyzers: List[AnalyzerConfig]
    aggregation_settings: AggregationConfig
    influencer_settings: InfluencerConfig
    spam_detection: SpamDetectionConfig
    cache_settings: CacheConfig
    
    # Analysis parameters
    min_data_points: int = 10
    min_confidence_threshold: float = 0.7
    cache_ttl: int = 300  # seconds
    max_data_per_source: int = 1000
    
    # Viral detection settings
    viral_detection_window: int = 24  # hours
    max_viral_alerts: int = 10
    
    # Relevance detection
    crypto_keywords: List[str] = field(default_factory=list)
    token_patterns: List[str] = field(default_factory=list)
    min_relevance_matches: int = 2
    
    # Virality scoring weights
    engagement_weight: float = 0.4
    growth_weight: float = 0.3
    velocity_weight: float = 0.3

@dataclass
class SourceConfig:
    """Configuration for sentiment data sources"""
    source_id: str
    platform: str
    endpoint: str
    credentials: Dict[str, str]
    rate_limits: RateLimitConfig
    credibility_score: float = 1.0
    is_active: bool = True
```

## Error Handling

```python
class SentimentError(Exception):
    """Base exception for sentiment analysis errors"""
    pass

class InsufficientSentimentDataError(SentimentError):
    """Raised when not enough sentiment data is available"""
    pass

class SentimentCollectionError(SentimentError):
    """Raised when sentiment data collection fails"""
    pass

class InvalidInfluencerIdsError(SentimentError):
    """Raised when influencer IDs are invalid"""
    pass

class LowConfidenceError(SentimentError):
    """Raised when sentiment confidence is below threshold"""
    pass
```

## Integration Points

- **Phase 1 Integration**: Uses event system for real-time sentiment alerts
- **Phase 2 Integration**: Provides sentiment insights to trading strategies
- **Predictive Models**: Feeds sentiment data to AI prediction engines
- **Risk Management**: Integrates sentiment risk factors
- **Monitoring**: Tracks sentiment analysis performance and accuracy

---

*This pseudocode specification provides the foundation for implementing the Sentiment Integration Engine with comprehensive social media monitoring and analysis capabilities.*