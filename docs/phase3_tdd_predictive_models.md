# Phase 3: Predictive Models TDD Specifications

## Overview

This document provides comprehensive Test-Driven Development (TDD) anchor specifications for the Predictive Models System, following London School TDD principles with outside-in development and extensive use of test doubles.

## Test Categories

### 1. Unit Tests for Core Functions

#### PredictiveModelsManager Unit Tests

```python
class TestPredictiveModelsManager:
    """Unit tests for PredictiveModelsManager core functionality"""
    
    def setup_method(self):
        """Setup test doubles and dependencies"""
        self.mock_config = Mock(spec=PredictiveConfig)
        self.mock_event_bus = Mock(spec=EventBus)
        self.mock_cache = Mock(spec=PredictionCache)
        self.mock_performance_tracker = Mock(spec=PerformanceTracker)
        self.mock_model_selector = Mock(spec=ModelSelector)
        
        # Configure mock config
        self.mock_config.engines = [Mock(spec=EngineConfig)]
        self.mock_config.cache_settings = Mock()
        self.mock_config.prediction_timeout = 30
        self.mock_config.min_predictions = 2
        
    def test_manager_initialization_with_valid_config(self):
        """GIVEN valid configuration
        WHEN PredictiveModelsManager is initialized
        THEN manager should initialize with correct dependencies"""
        
        manager = PredictiveModelsManager(self.mock_config, self.mock_event_bus)
        
        assert manager.config == self.mock_config
        assert manager.event_bus == self.mock_event_bus
        assert isinstance(manager.engines, dict)
        assert manager.cache is not None
        
    def test_manager_initialization_with_invalid_config(self):
        """GIVEN invalid configuration
        WHEN PredictiveModelsManager is initialized
        THEN should raise ConfigurationError"""
        
        invalid_config = None
        
        with pytest.raises(ConfigurationError):
            PredictiveModelsManager(invalid_config, self.mock_event_bus)
    
    def test_initialize_engines_success(self):
        """GIVEN valid engine configurations
        WHEN initialize_engines is called
        THEN all engines should be registered successfully"""
        
        mock_engine = Mock(spec=PredictionEngine)
        mock_engine.engine_id = "test_engine"
        mock_engine.validate_connection.return_value = True
        
        with patch.object(PredictiveModelsManager, '_create_engine', return_value=mock_engine):
            manager = PredictiveModelsManager(self.mock_config, self.mock_event_bus)
            result = manager.initialize_engines()
            
            assert result is True
            assert "test_engine" in manager.engines
            self.mock_event_bus.emit.assert_called_once()
    
    def test_initialize_engines_connection_failure(self):
        """GIVEN engine with failed connection
        WHEN initialize_engines is called
        THEN engine should not be registered"""
        
        mock_engine = Mock(spec=PredictionEngine)
        mock_engine.validate_connection.return_value = False
        
        with patch.object(PredictiveModelsManager, '_create_engine', return_value=mock_engine):
            manager = PredictiveModelsManager(self.mock_config, self.mock_event_bus)
            result = manager.initialize_engines()
            
            assert len(manager.engines) == 0
    
    @pytest.mark.asyncio
    async def test_predict_token_success_with_cache_hit(self):
        """GIVEN cached prediction exists
        WHEN predict_token_success is called
        THEN should return cached result without engine calls"""
        
        request = Mock(spec=PredictionRequest)
        cached_result = Mock(spec=PredictionResult)
        cached_result.is_expired.return_value = False
        
        manager = PredictiveModelsManager(self.mock_config, self.mock_event_bus)
        manager.cache = self.mock_cache
        manager.performance_tracker = self.mock_performance_tracker
        
        self.mock_cache.get.return_value = cached_result
        
        with patch.object(manager, '_validate_request', return_value=request):
            with patch.object(manager, '_generate_cache_key', return_value="test_key"):
                result = await manager.predict_token_success(request)
                
                assert result == cached_result
                self.mock_performance_tracker.record_cache_hit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_predict_token_success_with_cache_miss(self):
        """GIVEN no cached prediction
        WHEN predict_token_success is called
        THEN should generate new prediction using engines"""
        
        request = Mock(spec=PredictionRequest)
        request.request_type = "SUCCESS_PROBABILITY"
        request.priority = "HIGH"
        
        mock_engine = Mock(spec=PredictionEngine)
        mock_prediction = Mock(spec=PredictionResult)
        mock_engine.predict.return_value = mock_prediction
        
        manager = PredictiveModelsManager(self.mock_config, self.mock_event_bus)
        manager.cache = self.mock_cache
        manager.model_selector = self.mock_model_selector
        manager.performance_tracker = self.mock_performance_tracker
        
        self.mock_cache.get.return_value = None
        self.mock_model_selector.select_engines.return_value = [mock_engine]
        
        with patch.object(manager, '_validate_request', return_value=request):
            with patch.object(manager, '_generate_cache_key', return_value="test_key"):
                with patch.object(manager, '_aggregate_predictions', return_value=mock_prediction):
                    result = await manager.predict_token_success(request)
                    
                    assert result == mock_prediction
                    mock_engine.predict.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    async def test_predict_token_success_insufficient_predictions(self):
        """GIVEN insufficient valid predictions
        WHEN predict_token_success is called
        THEN should raise InsufficientPredictionsError"""
        
        request = Mock(spec=PredictionRequest)
        self.mock_config.min_predictions = 2
        
        manager = PredictiveModelsManager(self.mock_config, self.mock_event_bus)
        manager.cache = self.mock_cache
        manager.model_selector = self.mock_model_selector
        
        self.mock_cache.get.return_value = None
        self.mock_model_selector.select_engines.return_value = []
        
        with patch.object(manager, '_validate_request', return_value=request):
            with patch.object(manager, '_generate_cache_key', return_value="test_key"):
                with pytest.raises(InsufficientPredictionsError):
                    await manager.predict_token_success(request)
    
    def test_validate_request_with_invalid_token_address(self):
        """GIVEN request with invalid token address
        WHEN _validate_request is called
        THEN should raise InvalidTokenAddressError"""
        
        request = Mock(spec=PredictionRequest)
        request.token_address = "invalid_address"
        
        manager = PredictiveModelsManager(self.mock_config, self.mock_event_bus)
        
        with patch('is_valid_address', return_value=False):
            with pytest.raises(InvalidTokenAddressError):
                manager._validate_request(request)
    
    def test_validate_request_with_unsupported_request_type(self):
        """GIVEN request with unsupported type
        WHEN _validate_request is called
        THEN should raise UnsupportedRequestTypeError"""
        
        request = Mock(spec=PredictionRequest)
        request.token_address = "0x123"
        request.request_type = "UNSUPPORTED_TYPE"
        
        manager = PredictiveModelsManager(self.mock_config, self.mock_event_bus)
        
        with patch('is_valid_address', return_value=True):
            with pytest.raises(UnsupportedRequestTypeError):
                manager._validate_request(request)
    
    def test_aggregate_predictions_with_empty_list(self):
        """GIVEN empty predictions list
        WHEN _aggregate_predictions is called
        THEN should raise NoPredictionsError"""
        
        manager = PredictiveModelsManager(self.mock_config, self.mock_event_bus)
        request = Mock(spec=PredictionRequest)
        
        with pytest.raises(NoPredictionsError):
            manager._aggregate_predictions([], request)
    
    def test_aggregate_predictions_weighted_ensemble(self):
        """GIVEN multiple predictions with different weights
        WHEN _aggregate_predictions is called
        THEN should return weighted ensemble result"""
        
        prediction1 = Mock(spec=PredictionResult)
        prediction1.engine_id = "engine1"
        prediction1.prediction.success_probability = 0.8
        prediction1.confidence = 0.9
        
        prediction2 = Mock(spec=PredictionResult)
        prediction2.engine_id = "engine2"
        prediction2.prediction.success_probability = 0.6
        prediction2.confidence = 0.7
        
        manager = PredictiveModelsManager(self.mock_config, self.mock_event_bus)
        manager.performance_tracker = self.mock_performance_tracker
        
        # Mock performance tracker to return equal weights
        self.mock_performance_tracker.get_engine_performance.return_value = Mock()
        
        request = Mock(spec=PredictionRequest)
        request.request_id = "test_request"
        
        with patch.object(manager, '_calculate_weight', return_value=1.0):
            with patch.object(manager, '_calculate_confidence_interval', return_value=(0.6, 0.9)):
                with patch.object(manager, '_aggregate_signals', return_value=[]):
                    with patch.object(manager, '_generate_ensemble_explanation', return_value="test"):
                        result = manager._aggregate_predictions([prediction1, prediction2], request)
                        
                        # Should be weighted average: (0.8 + 0.6) / 2 = 0.7
                        assert result.prediction.success_probability == 0.7
                        assert result.confidence == 0.8  # (0.9 + 0.7) / 2
```

#### PredictionEngine Unit Tests

```python
class TestPredictionEngine:
    """Unit tests for abstract PredictionEngine base class"""
    
    def test_engine_initialization(self):
        """GIVEN valid engine configuration
        WHEN PredictionEngine is initialized
        THEN should set correct attributes"""
        
        config = Mock(spec=EngineConfig)
        config.engine_id = "test_engine"
        config.name = "Test Engine"
        config.engine_type = "API"
        
        # Create concrete implementation for testing
        class TestEngine(PredictionEngine):
            async def predict(self, request):
                pass
            def validate_connection(self):
                return True
        
        engine = TestEngine(config)
        
        assert engine.engine_id == "test_engine"
        assert engine.name == "Test Engine"
        assert engine.engine_type == "API"
        assert engine.is_active is False
    
    def test_update_performance_metrics(self):
        """GIVEN prediction outcome data
        WHEN update_performance is called
        THEN should update performance metrics"""
        
        config = Mock(spec=EngineConfig)
        
        class TestEngine(PredictionEngine):
            async def predict(self, request):
                pass
            def validate_connection(self):
                return True
#### Performance Benchmarking Tests

```python
class TestPerformanceBenchmarking:
    """Tests for model performance benchmarking and latency validation"""
    
    @pytest.mark.asyncio
    async def test_prediction_latency_benchmark(self):
        """GIVEN prediction engine with latency requirements
        WHEN prediction is requested
        THEN should complete within acceptable time limits"""
        
        config = LocalEngineConfig(
            engine_id="benchmark_engine",
            model_path="/path/to/model",
            max_latency_ms=100
        )
        
        engine = LocalModelEngine(config)
        
        # Mock fast model
        mock_model = Mock()
        mock_model.predict.return_value = np.array([0.75])
        mock_model.predict_proba.return_value = np.array([[0.25, 0.75]])
        engine.model = mock_model
        
        request = PredictionRequest(
            request_id="benchmark_test",
            token_address="0x123",
            request_type="SUCCESS_PROBABILITY"
        )
        
        start_time = time.time()
        result = await engine.predict(request)
        end_time = time.time()
        
        latency_ms = (end_time - start_time) * 1000
        
        assert latency_ms < config.max_latency_ms
        assert result.prediction.success_probability == 0.75
    
    def test_throughput_benchmark(self):
        """GIVEN prediction system under load
        WHEN multiple concurrent requests are processed
        THEN should maintain minimum throughput requirements"""
        
        manager = PredictiveModelsManager(Mock(), Mock())
        
        # Mock high-throughput engine
        mock_engine = Mock(spec=PredictionEngine)
        mock_result = Mock(spec=PredictionResult)
        mock_engine.predict.return_value = mock_result
        
        manager.engines = {"throughput_engine": mock_engine}
        
        # Simulate 100 requests per second requirement
        num_requests = 100
        max_time_seconds = 1.0
        
        requests = [
            PredictionRequest(
                request_id=f"req_{i}",
                token_address="0x123",
                request_type="SUCCESS_PROBABILITY"
            )
            for i in range(num_requests)
        ]
        
        start_time = time.time()
        
        with patch.object(manager.model_selector, 'select_engines', return_value=[mock_engine]):
            for request in requests:
                asyncio.create_task(manager.predict_token_success(request))
        
        end_time = time.time()
        total_time = end_time - start_time
        
        throughput = num_requests / total_time
        
        assert throughput >= 100  # 100 requests per second minimum
    
    def test_model_drift_detection(self):
        """GIVEN model performance over time
        WHEN accuracy degrades beyond threshold
        THEN should trigger model drift alert"""
        
        drift_detector = ModelDriftDetector(
            accuracy_threshold=0.8,
            window_size=100
        )
        
        # Simulate good performance initially
        for i in range(50):
            drift_detector.add_prediction(0.9, 1.0)  # High accuracy
        
        # Simulate performance degradation
        for i in range(50):
            drift_detector.add_prediction(0.6, 1.0)  # Low accuracy
        
        drift_status = drift_detector.check_drift()
        
        assert drift_status.drift_detected is True
        assert drift_status.current_accuracy < 0.8
        assert drift_status.recommendation == "RETRAIN_MODEL"
```

### 3. Data Pipeline Integrity Tests

#### Feature Engineering Validation Tests

```python
class TestFeatureEngineering:
    """Tests for feature extraction and preprocessing pipeline"""
    
    def setup_method(self):
        """Setup test data and feature extractor"""
        self.feature_extractor = FeatureExtractor(Mock())
        self.sample_market_data = {
            "prices": [100, 105, 102, 108, 110],
            "volumes": [1000, 1200, 800, 1500, 1100],
            "timestamps": [1640995200, 1640995260, 1640995320, 1640995380, 1640995440]
        }
    
    @pytest.mark.asyncio
    async def test_technical_indicators_extraction(self):
        """GIVEN market data
        WHEN technical indicators are extracted
        THEN should return valid indicator values"""
        
        request = PredictionRequest(
            request_id="test",
            token_address="0x123",
            request_type="SUCCESS_PROBABILITY"
        )
        
        with patch.object(self.feature_extractor, '_get_market_data', 
                         return_value=self.sample_market_data):
            features = await self.feature_extractor.extract_features(request)
            
            # Verify technical indicators are present
            assert "rsi" in features
            assert "macd" in features
            assert "bollinger_bands" in features
            assert "volume_sma" in features
            
            # Verify values are within expected ranges
            assert 0 <= features["rsi"] <= 100
            assert isinstance(features["macd"], float)
            assert len(features["bollinger_bands"]) == 3  # upper, middle, lower
    
    def test_feature_normalization(self):
        """GIVEN raw feature values
        WHEN features are normalized
        THEN should scale values to expected range"""
        
        raw_features = {
            "price": 1000.0,
            "volume": 50000.0,
            "market_cap": 1000000000.0
        }
        
        normalizer = FeatureNormalizer()
        normalized_features = normalizer.normalize(raw_features)
        
        # All normalized features should be in [0, 1] range
        for key, value in normalized_features.items():
            assert 0 <= value <= 1, f"Feature {key} not normalized: {value}"
    
    def test_missing_data_handling(self):
        """GIVEN incomplete market data
        WHEN features are extracted
        THEN should handle missing values appropriately"""
        
        incomplete_data = {
            "prices": [100, None, 102, None, 110],
            "volumes": [1000, 1200, None, 1500, 1100],
            "timestamps": [1640995200, 1640995260, 1640995320, 1640995380, 1640995440]
        }
        
        request = PredictionRequest(
            request_id="test",
            token_address="0x123",
            request_type="SUCCESS_PROBABILITY"
        )
        
        with patch.object(self.feature_extractor, '_get_market_data', 
                         return_value=incomplete_data):
            features = await self.feature_extractor.extract_features(request)
            
            # Should not contain NaN values
            for key, value in features.items():
                if isinstance(value, (int, float)):
                    assert not math.isnan(value), f"Feature {key} contains NaN"
    
    def test_feature_validation(self):
        """GIVEN extracted features
        WHEN features are validated
        THEN should reject invalid feature sets"""
        
        validator = FeatureValidator()
        
        # Valid features
        valid_features = {
            "rsi": 65.0,
            "macd": 0.5,
            "volume_ratio": 1.2,
            "price_change": 0.05
        }
        
        assert validator.validate(valid_features) is True
        
        # Invalid features (RSI out of range)
        invalid_features = {
            "rsi": 150.0,  # RSI should be 0-100
            "macd": 0.5,
            "volume_ratio": 1.2,
            "price_change": 0.05
        }
        
        with pytest.raises(FeatureValidationError):
            validator.validate(invalid_features)
```

### 4. Security Tests for AI-Specific Vulnerabilities

#### Input Validation and Sanitization Tests

```python
class TestPredictionSecurity:
    """Security tests for prediction system vulnerabilities"""
    
    def test_malicious_token_address_injection(self):
        """GIVEN malicious token address input
        WHEN prediction request is validated
        THEN should reject malicious input"""
        
        manager = PredictiveModelsManager(Mock(), Mock())
        
        malicious_addresses = [
            "'; DROP TABLE predictions; --",
            "<script>alert('xss')</script>",
            "0x" + "A" * 1000,  # Extremely long address
            "../../../etc/passwd",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>"
        ]
        
        for malicious_address in malicious_addresses:
            request = PredictionRequest(
                request_id="test",
                token_address=malicious_address,
                request_type="SUCCESS_PROBABILITY"
            )
            
            with pytest.raises((InvalidTokenAddressError, ValidationError)):
                manager._validate_request(request)
    
    def test_request_parameter_sanitization(self):
        """GIVEN request with potentially malicious parameters
        WHEN request is processed
        THEN should sanitize all inputs"""
        
        manager = PredictiveModelsManager(Mock(), Mock())
        
        request = PredictionRequest(
            request_id="<script>alert('xss')</script>",
            token_address="0x123456789abcdef",
            request_type="SUCCESS_PROBABILITY",
            timeframe="1h'; DROP TABLE timeframes; --",
            parameters={
                "malicious_key": "<script>alert('xss')</script>",
                "sql_injection": "'; DROP TABLE users; --"
            }
        )
        
        # Should either sanitize or reject
        with patch('is_valid_address', return_value=True):
            try:
                validated_request = manager._validate_request(request)
                # If validation passes, ensure no malicious content remains
                assert "<script>" not in str(validated_request.request_id)
                assert "DROP TABLE" not in str(validated_request.timeframe)
                assert "<script>" not in str(validated_request.parameters)
            except ValidationError:
                # Rejection is also acceptable
                pass
    
    def test_model_poisoning_detection(self):
        """GIVEN potentially poisoned training data
        WHEN model training is performed
        THEN should detect and reject poisoned samples"""
        
        poison_detector = ModelPoisoningDetector()
        
        # Normal training samples
        normal_samples = [
            {"features": [1, 2, 3], "label": 0},
            {"features": [2, 3, 4], "label": 1},
            {"features": [3, 4, 5], "label": 0}
        ]
        
        # Poisoned samples (unusual feature patterns)
        poisoned_samples = [
            {"features": [1000, -1000, 999], "label": 1},  # Extreme values
            {"features": [0, 0, 0], "label": 1},  # All zeros
            {"features": [1, 2, 3], "label": 999}  # Invalid label
        ]
        
        all_samples = normal_samples + poisoned_samples
        
        clean_samples = poison_detector.filter_samples(all_samples)
        
        assert len(clean_samples) == len(normal_samples)
        assert all(sample in normal_samples for sample in clean_samples)
```

## Test Execution Framework

### Pytest Configuration

```python
# conftest.py
import pytest
import asyncio
from unittest.mock import Mock
from src.predictive_models.manager import PredictiveModelsManager
from src.predictive_models.config import PredictiveConfig

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_config():
    """Provide mock configuration for tests"""
    config = Mock(spec=PredictiveConfig)
    config.engines = []
    config.cache_settings = Mock()
    config.prediction_timeout = 30
    config.min_predictions = 1
    return config

@pytest.fixture
def mock_event_bus():
    """Provide mock event bus for tests"""
    return Mock()

@pytest.fixture
def prediction_manager(mock_config, mock_event_bus):
    """Provide configured prediction manager for tests"""
    return PredictiveModelsManager(mock_config, mock_event_bus)
```

### Test Execution Commands

```bash
# Run all predictive models tests
pytest tests/test_predictive_models/ -v

# Run specific test categories
pytest tests/test_predictive_models/test_unit.py -v
pytest tests/test_predictive_models/test_integration.py -v
pytest tests/test_predictive_models/test_performance.py -v
pytest tests/test_predictive_models/test_security.py -v

# Run with coverage
pytest tests/test_predictive_models/ --cov=src.predictive_models --cov-report=html

# Run performance benchmarks
pytest tests/test_predictive_models/test_performance.py -m benchmark

# Run security tests
pytest tests/test_predictive_models/test_security.py -m security
```

---

*This TDD specification provides comprehensive test coverage for the Predictive Models System, ensuring robust validation of ML model accuracy, performance benchmarking, data pipeline integrity, security vulnerabilities, and edge case handling for production-ready AI trading systems.*
        
        engine = TestEngine(config)
        mock_metrics = Mock(spec=PerformanceMetrics)
        engine.performance_metrics = mock_metrics
        
        engine.update_performance(0.8, 0.75)
        
        mock_metrics.add_prediction.assert_called_once_with(0.8, 0.75)
```

### 2. ML Model Validation Tests

#### Model Accuracy and Performance Tests

```python
class TestMLModelValidation:
    """Tests for ML model accuracy, precision, and recall validation"""
    
    def setup_method(self):
        """Setup test data and model mocks"""
        self.mock_model = Mock()
        self.test_features = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        self.test_labels = np.array([0, 1, 0])
        self.predictions = np.array([0, 1, 1])  # One false positive
        
    def test_model_accuracy_calculation(self):
        """GIVEN model predictions and true labels
        WHEN accuracy is calculated
        THEN should return correct accuracy score"""
        
        validator = ModelValidator()
        accuracy = validator.calculate_accuracy(self.predictions, self.test_labels)
        
        # 2 correct out of 3 predictions = 0.667
        assert abs(accuracy - 0.667) < 0.001
    
    def test_model_precision_calculation(self):
        """GIVEN model predictions with false positives
        WHEN precision is calculated
        THEN should return correct precision score"""
        
        validator = ModelValidator()
        precision = validator.calculate_precision(self.predictions, self.test_labels)
        
        # 1 true positive, 1 false positive = 0.5
        assert abs(precision - 0.5) < 0.001
    
    def test_model_recall_calculation(self):
        """GIVEN model predictions with false negatives
        WHEN recall is calculated
        THEN should return correct recall score"""
        
        validator = ModelValidator()
        recall = validator.calculate_recall(self.predictions, self.test_labels)
        
        # 1 true positive, 0 false negatives = 1.0
        assert abs(recall - 1.0) < 0.001
    
    def test_model_f1_score_calculation(self):
        """GIVEN precision and recall scores
        WHEN F1 score is calculated
        THEN should return harmonic mean"""
        
        validator = ModelValidator()
        f1_score = validator.calculate_f1_score(self.predictions, self.test_labels)
        
        # F1 = 2 * (precision * recall) / (precision + recall)
        # F1 = 2 * (0.5 * 1.0) / (0.5 + 1.0) = 0.667
        assert abs(f1_score - 0.667) < 0.001
    
    def test_model_validation_with_minimum_accuracy_threshold(self):
        """GIVEN model with accuracy below threshold
        WHEN model is validated
        THEN should fail validation"""
        
        validator = ModelValidator(min_accuracy=0.8)
        
        with pytest.raises(ModelValidationError, match="Accuracy below threshold"):
            validator.validate_model_performance(self.predictions, self.test_labels)
    
    def test_model_validation_with_acceptable_performance(self):
        """GIVEN model with acceptable performance
        WHEN model is validated
        THEN should pass validation"""
        
        # Create better predictions
        good_predictions = np.array([0, 1, 0])  # All correct
        
        validator = ModelValidator(min_accuracy=0.8)
        result = validator.validate_model_performance(good_predictions, self.test_labels)
        
        assert result.is_valid is True
        assert result.accuracy == 1.0
        assert result.precision == 1.0
        assert result.recall == 1.0