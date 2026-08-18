import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from typing import List

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.ai.llm import LLMClient
from app.ai.llm_schemas import (
    ColumnRecommendation,
    SchemaAnalysisLLMResult,
    SensitivityLevel,
    ConfidenceLevel,
    MaskingStrategyRecommendation,
    RuntimeDetectionResult,
    SensitiveValueDetection,
)
from app.ai.schema_analyzer import SchemaAnalyzer
from app.ai.sensitive_data_detector import SensitiveDataDetector
from app.schemas.database import ColumnSchema


@pytest.fixture
def llm_client():
    """Create LLM client for testing."""
    return LLMClient()


@pytest.fixture
def schema_analyzer():
    """Create schema analyzer for testing."""
    return SchemaAnalyzer()


@pytest.fixture
def sample_columns():
    """Sample column data for testing."""
    return [
        ColumnSchema(column_name="id", data_type="integer", is_nullable=False),
        ColumnSchema(column_name="email", data_type="character varying", is_nullable=False),
        ColumnSchema(column_name="phone", data_type="character varying", is_nullable=True),
        ColumnSchema(column_name="address", data_type="text", is_nullable=True),
        ColumnSchema(column_name="name", data_type="character varying", is_nullable=False),
    ]


@pytest.fixture
def sample_query_data():
    """Sample query result data for testing."""
    return [
        [1, "john@example.com", "555-1234", "123 Main St", "John Doe"],
        [2, "jane@test.org", "555-5678", "456 Oak Ave", "Jane Smith"],
        [3, "bob@company.net", "555-9012", "789 Pine Rd", "Bob Johnson"],
    ]


@pytest.fixture
def sensitive_data_detector():
    """Create sensitive data detector for testing."""
    return SensitiveDataDetector()


class TestLLMClient:
    """Test LLM client functionality."""

    def test_llm_client_creation(self, llm_client):
        """Test LLM client can be created."""
        assert llm_client is not None
        assert llm_client.model is not None

    def test_llm_client_not_available_without_api_key(self):
        """Test LLM client is not available when no API key is configured."""
        with patch('app.ai.llm.settings.OPENAI_API_KEY', None), patch('app.ai.llm.settings.GOOGLE_API_KEY', None):
            client = LLMClient()
            assert client.is_available() is False

    @patch('app.ai.llm.settings.OPENAI_API_KEY', 'test-key')
    @patch('langchain_openai.ChatOpenAI')
    def test_llm_client_available_with_api_key(self, mock_chat_openai):
        """Test LLM client is available when API key is configured."""
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        
        client = LLMClient()
        assert client.is_available() is True
        mock_chat_openai.assert_called_once()

    @patch('app.ai.llm.settings.OPENAI_API_KEY', 'test-key')
    @patch('langchain_openai.ChatOpenAI')
    def test_llm_client_timeout_configured(self, mock_chat_openai):
        """Test LLM client explicitly passes configured timeout to constructor."""
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm

        with patch('app.ai.llm.settings.LLM_DETECTION_TIMEOUT_SECONDS', 5):
            client = LLMClient()
            assert client.timeout == 5
            mock_chat_openai.assert_called_once_with(
                model=client.model,
                temperature=client.temperature,
                api_key='test-key',
                timeout=5,
            )

    @patch('app.ai.llm.settings.OPENAI_API_KEY', 'test-key')
    @patch('langchain_openai.ChatOpenAI')
    def test_analyze_schema_metadata_valid_response(self, mock_chat_openai):
        """Test schema analysis with valid LLM response."""
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        
        # Mock structured output
        mock_structured = Mock()
        mock_result = SchemaAnalysisLLMResult(
            table_name="users",
            recommendations=[
                ColumnRecommendation(
                    table="users",
                    column="email",
                    sensitivity=SensitivityLevel.HIGH,
                    data_type="character varying",
                    recommended_strategy=MaskingStrategyRecommendation.EMAIL,
                    rationale="Email addresses are personally identifiable information",
                    source="llm"
                ),
                ColumnRecommendation(
                    table="users",
                    column="phone",
                    sensitivity=SensitivityLevel.HIGH,
                    data_type="character varying",
                    recommended_strategy=MaskingStrategyRecommendation.PHONE_LAST4,
                    rationale="Phone numbers are contact information",
                    source="llm"
                )
            ]
        )
        mock_structured.invoke.return_value = mock_result
        mock_llm.with_structured_output.return_value = mock_structured
        
        client = LLMClient()
        columns = [("email", "character varying"), ("phone", "character varying")]
        result = client.analyze_schema_metadata("users", columns)
        
        assert result is not None
        assert result.table_name == "users"
        assert len(result.recommendations) == 2
        assert result.recommendations[0].column == "email"
        assert result.recommendations[0].sensitivity == SensitivityLevel.HIGH
        assert result.recommendations[0].recommended_strategy == MaskingStrategyRecommendation.EMAIL
        assert result.recommendations[1].recommended_strategy == MaskingStrategyRecommendation.PHONE_LAST4

    def test_format_schema_metadata_contains_only_metadata_no_rows(self, llm_client):
        """Verify formatted schema metadata contains only column names and types with zero row values."""
        columns = [("email", "character varying"), ("phone", "text"), ("balance", "numeric")]
        formatted = llm_client.format_schema_metadata("patients", columns)
        
        assert "- email (character varying)" in formatted
        assert "- phone (text)" in formatted
        assert "- balance (numeric)" in formatted
        # Ensure no SQL keywords or row data structures
        assert "SELECT" not in formatted
        assert "WHERE" not in formatted
        assert "INSERT" not in formatted

    @patch('app.ai.llm.settings.OPENAI_API_KEY', 'test-key')
    @patch('langchain_openai.ChatOpenAI')
    def test_analyze_schema_metadata_invalid_response(self, mock_chat_openai):
        """Test schema analysis with invalid LLM response returns None."""
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        
        # Mock structured output to raise exception
        mock_structured = Mock()
        mock_structured.invoke.side_effect = Exception("LLM error")
        mock_llm.with_structured_output.return_value = mock_structured
        
        # Mock fallback to also fail
        mock_llm.invoke.side_effect = Exception("Fallback error")
        
        client = LLMClient()
        columns = [("email", "character varying")]
        result = client.analyze_schema_metadata("users", columns)
        
        assert result is None

    @patch('app.ai.llm.settings.OPENAI_API_KEY', 'test-key')
    @patch('langchain_openai.ChatOpenAI')
    def test_analyze_schema_metadata_fallback_parsing(self, mock_chat_openai):
        """Test fallback parsing when structured output fails."""
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        
        # Mock structured output to raise exception
        mock_structured = Mock()
        mock_structured.invoke.side_effect = Exception("Structured output failed")
        mock_llm.with_structured_output.return_value = mock_structured
        
        # Mock fallback to return valid JSON
        mock_response = Mock()
        mock_response.content = '{"table_name": "users", "recommendations": [{"table": "users", "column": "email", "sensitivity": "HIGH", "data_type": "character varying", "recommended_strategy": "EMAIL", "rationale": "PII"}]}'
        mock_llm.invoke.return_value = mock_response
        
        client = LLMClient()
        columns = [("email", "character varying")]
        result = client.analyze_schema_metadata("users", columns)
        
        assert result is not None
        assert result.table_name == "users"
        assert len(result.recommendations) == 1
        assert result.recommendations[0].recommended_strategy == MaskingStrategyRecommendation.EMAIL

    def test_analyze_schema_metadata_no_llm(self):
        """Test schema analysis returns None when LLM is not available."""
        client = LLMClient()
        client._llm = None
        columns = [("email", "character varying")]
        result = client.analyze_schema_metadata("users", columns)
        assert result is None

    @patch('app.ai.llm.settings.OPENAI_API_KEY', 'test-key')
    @patch('langchain_openai.ChatOpenAI')
    def test_summarize_runtime_detection(self, mock_chat_openai):
        """Test runtime detection summary."""
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        
        mock_response = Mock()
        mock_response.content = "Summary: Potential privacy risks detected in email columns."
        mock_llm.invoke.return_value = mock_response
        
        client = LLMClient()
        column_stats = [{"column": "email", "risk_score": 0.9}]
        result = client.summarize_runtime_detection(column_stats)
        
        assert result is not None
        assert "privacy risks" in result.lower()

    def test_summarize_runtime_detection_no_llm(self):
        """Test runtime detection summary returns None when LLM unavailable."""
        client = LLMClient()
        client._llm = None
        column_stats = [{"column": "email", "risk_score": 0.9}]
        result = client.summarize_runtime_detection(column_stats)
        assert result is None

    @patch('app.ai.llm.settings.OPENAI_API_KEY', 'test-key')
    @patch('langchain_openai.ChatOpenAI')
    def test_detect_runtime_sensitive_data_valid(self, mock_chat_openai, sample_query_data):
        """Test runtime sensitive data detection with valid LLM response."""
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm

        # Mock structured output
        mock_structured = Mock()
        mock_result = RuntimeDetectionResult(
            has_sensitive_data=True,
            detections=[
                SensitiveValueDetection(
                    row_index=0,
                    column_name="email",
                    sensitivity=SensitivityLevel.HIGH,
                    data_type="email",
                    recommended_strategy="email_mask",
                    rationale="Email address detected"
                ),
                SensitiveValueDetection(
                    row_index=1,
                    column_name="phone",
                    sensitivity=SensitivityLevel.HIGH,
                    data_type="phone",
                    recommended_strategy="phone_mask",
                    rationale="Phone number detected"
                )
            ],
            summary="Detected email and phone data",
            confidence="high"
        )
        mock_structured.invoke.return_value = mock_result
        mock_llm.with_structured_output.return_value = mock_structured

        client = LLMClient()
        columns = ["id", "email", "phone", "address", "name"]
        result = client.detect_runtime_sensitive_data(sample_query_data, columns, [])

        assert result is not None
        assert result.has_sensitive_data is True
        assert len(result.detections) == 2
        assert result.detections[0].column_name == "email"
        assert result.detections[0].recommended_strategy == "email_mask"
        assert result.confidence == ConfidenceLevel.HIGH

    @patch('app.ai.llm.settings.OPENAI_API_KEY', 'test-key')
    @patch('langchain_openai.ChatOpenAI')
    def test_detect_runtime_sensitive_data_no_sensitive_data(self, mock_chat_openai, sample_query_data):
        """Test runtime detection when no sensitive data is found."""
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm

        # Mock structured output with no detections
        mock_structured = Mock()
        mock_result = RuntimeDetectionResult(
            has_sensitive_data=False,
            detections=[],
            summary="No sensitive data detected",
            confidence="high"
        )
        mock_structured.invoke.return_value = mock_result
        mock_llm.with_structured_output.return_value = mock_structured

        client = LLMClient()
        columns = ["id", "email", "phone", "address", "name"]
        result = client.detect_runtime_sensitive_data(sample_query_data, columns, [])

        assert result is not None
        assert result.has_sensitive_data is False
        assert len(result.detections) == 0

    @patch('app.ai.llm.settings.OPENAI_API_KEY', 'test-key')
    @patch('langchain_openai.ChatOpenAI')
    def test_detect_runtime_sensitive_data_with_already_masked(self, mock_chat_openai, sample_query_data):
        """Test runtime detection respects already masked columns."""
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm

        # Mock structured output - should only detect in non-masked columns
        mock_structured = Mock()
        mock_result = RuntimeDetectionResult(
            has_sensitive_data=True,
            detections=[
                SensitiveValueDetection(
                    row_index=0,
                    column_name="address",  # Not in already_masked
                    sensitivity=SensitivityLevel.MEDIUM,
                    data_type="address",
                    recommended_strategy="partial_mask",
                    rationale="Address detected"
                )
            ],
            summary="Detected address data",
            confidence="medium"
        )
        mock_structured.invoke.return_value = mock_result
        mock_llm.with_structured_output.return_value = mock_structured

        client = LLMClient()
        columns = ["id", "email", "phone", "address", "name"]
        already_masked = ["email", "phone"]  # These should be ignored
        result = client.detect_runtime_sensitive_data(sample_query_data, columns, already_masked)

        assert result is not None
        assert result.has_sensitive_data is True
        # Should only detect address, not email or phone
        assert all(d.column_name not in already_masked for d in result.detections)

    @patch('app.ai.llm.settings.OPENAI_API_KEY', 'test-key')
    @patch('langchain_openai.ChatOpenAI')
    def test_detect_runtime_sensitive_data_fallback_parsing(self, mock_chat_openai, sample_query_data):
        """Test fallback parsing when structured output fails."""
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm

        # Mock structured output to raise exception
        mock_structured = Mock()
        mock_structured.invoke.side_effect = Exception("Structured output failed")
        mock_llm.with_structured_output.return_value = mock_structured

        # Mock fallback to return valid JSON
        mock_response = Mock()
        mock_response.content = '{"has_sensitive_data": true, "detections": [{"row_index": 0, "column_name": "email", "sensitivity": "high", "data_type": "email", "recommended_strategy": "email_mask", "rationale": "Email detected"}], "summary": "Email found", "confidence": "high"}'
        mock_llm.invoke.return_value = mock_response

        client = LLMClient()
        columns = ["id", "email", "phone", "address", "name"]
        result = client.detect_runtime_sensitive_data(sample_query_data, columns, [])

        assert result is not None
        assert result.has_sensitive_data is True
        assert len(result.detections) == 1

    def test_detect_runtime_sensitive_data_no_llm(self, sample_query_data):
        """Test runtime detection returns None when LLM unavailable."""
        client = LLMClient()
        client._llm = None
        columns = ["id", "email", "phone", "address", "name"]
        result = client.detect_runtime_sensitive_data(sample_query_data, columns, [])
        assert result is None

    @patch('app.ai.llm.settings.OPENAI_API_KEY', 'test-key')
    @patch('langchain_openai.ChatOpenAI')
    def test_detect_runtime_sensitive_data_empty_data(self, mock_chat_openai):
        """Test runtime detection with empty data."""
        client = LLMClient()
        columns = ["id", "email"]
        result = client.detect_runtime_sensitive_data([], columns, [])
        assert result is None


class TestSensitiveDataDetector:
    """Test sensitive data detector functionality."""

    def test_detector_creation(self, sensitive_data_detector):
        """Test detector can be created."""
        assert sensitive_data_detector is not None

    def test_detect_sensitive_data_pattern_matching(self, sensitive_data_detector, sample_query_data):
        """Test pattern-based sensitive data detection."""
        columns = ["id", "email", "phone", "address", "name"]
        result = sensitive_data_detector.detect_sensitive_data(sample_query_data, columns)

        assert result is not None
        assert result['total_rows'] == 3
        assert 'column_risks' in result
        assert 'high_risk_rows' in result

    def test_detect_local_cells_all_patterns(self, sensitive_data_detector):
        """Test local cell-level detection for all supported patterns."""
        columns = ["id", "email", "phone", "ssn", "cc", "ip", "url", "safe_text"]
        data = [
            [1, "user@domain.com", "555-123-4567", "123-45-6789", "4111222233334444", "192.168.1.1", "https://example.com/api", "Clean description"],
            [2, "not-an-email", "invalid-phone", "not-ssn", "short", "999.999", "ftp", "Normal text"],
        ]
        detected = sensitive_data_detector.detect_local_cells(data, columns)
        
        # Should detect all 6 sensitive cells in row 0
        coords = [(r, c, dt, strat) for r, c, dt, strat in detected]
        assert (0, 1, "email", "EMAIL") in coords
        assert (0, 2, "phone", "PHONE_LAST4") in coords
        assert (0, 3, "ssn", "REDACT") in coords
        assert (0, 4, "credit_card", "REDACT") in coords
        assert (0, 5, "ip_address", "REDACT") in coords
        assert (0, 6, "url", "REDACT") in coords

        # Row 1 has no valid PII patterns
        row1_detections = [d for d in detected if d[0] == 1]
        assert len(row1_detections) == 0

    def test_detect_local_cells_respects_unmasked_col_indices(self, sensitive_data_detector):
        """Test that detect_local_cells only analyzes specified unmasked column indices."""
        columns = ["id", "email", "phone", "notes"]
        data = [
            [1, "alice@example.com", "555-0199", "Call me at alice@work.org"],
        ]
        # Only check column 3 (notes)
        detected = sensitive_data_detector.detect_local_cells(data, columns, unmasked_col_indices=[3])
        assert len(detected) == 1
        assert detected[0] == (0, 3, "email", "EMAIL")

    def test_detect_runtime_sensitive_data_with_llm(self, sensitive_data_detector, sample_query_data):
        """Test runtime detection with LLM (mocked)."""
        columns = ["id", "email", "phone", "address", "name"]
        already_masked = ["email"]

        with patch('app.ai.sensitive_data_detector.llm_client') as mock_llm:
            # Mock LLM response
            mock_result = RuntimeDetectionResult(
                has_sensitive_data=True,
                detections=[
                    SensitiveValueDetection(
                        row_index=0,
                        column_name="phone",
                        sensitivity=SensitivityLevel.HIGH,
                        data_type="phone",
                        recommended_strategy="phone_mask",
                        rationale="Phone number detected"
                    )
                ],
                summary="Phone detected",
                confidence="high"
            )
            mock_llm.detect_runtime_sensitive_data.return_value = mock_result

            llm_result, operations = sensitive_data_detector.detect_runtime_sensitive_data(
                sample_query_data, columns, already_masked
            )

            assert llm_result is not None
            assert llm_result.has_sensitive_data is True
            assert len(operations) == 1
            assert operations[0] == (0, 2, "phone_mask")  # row 0, col 2 (phone), phone_mask

    def test_detect_runtime_sensitive_data_no_llm(self, sensitive_data_detector, sample_query_data):
        """Test runtime detection when LLM is unavailable."""
        columns = ["id", "email", "phone", "address", "name"]
        already_masked = []

        with patch('app.ai.sensitive_data_detector.llm_client') as mock_llm:
            mock_llm.detect_runtime_sensitive_data.return_value = None

            llm_result, operations = sensitive_data_detector.detect_runtime_sensitive_data(
                sample_query_data, columns, already_masked
            )

            assert llm_result is not None
            assert llm_result.has_sensitive_data is False
            assert len(operations) == 0
            assert "LLM detection unavailable" in llm_result.summary

    def test_get_masking_recommendations(self, sensitive_data_detector):
        """Test masking recommendations based on detected types."""
        recommendations = sensitive_data_detector.get_masking_recommendations(
            "email", ["email"]
        )
        assert "email_mask" in recommendations

        recommendations = sensitive_data_detector.get_masking_recommendations(
            "phone", ["phone"]
        )
        assert "phone_mask" in recommendations

        recommendations = sensitive_data_detector.get_masking_recommendations(
            "unknown", ["unknown"]
        )
        assert "redaction" in recommendations


class TestRuntimeDetectionSchemas:
    """Test Pydantic schemas for runtime detection."""

    def test_sensitive_value_detection_valid(self):
        """Test valid sensitive value detection."""
        detection = SensitiveValueDetection(
            row_index=0,
            column_name="email",
            sensitivity=SensitivityLevel.HIGH,
            confidence=ConfidenceLevel.HIGH,
            data_type="email",
            recommended_strategy="email_mask",
            rationale="Email is PII"
        )
        assert detection.row_index == 0
        assert detection.column_name == "email"
        assert detection.sensitivity == SensitivityLevel.HIGH
        assert detection.confidence == ConfidenceLevel.HIGH
        assert detection.data_type == "email"
        assert detection.recommended_strategy in ("email_mask", "EMAIL")

    def test_runtime_detection_result_valid(self):
        """Test valid runtime detection result."""
        result = RuntimeDetectionResult(
            has_sensitive_data=True,
            detections=[
                SensitiveValueDetection(
                    row_index=0,
                    column_name="email",
                    sensitivity=SensitivityLevel.HIGH,
                    confidence=ConfidenceLevel.HIGH,
                    data_type="email",
                    recommended_strategy="email_mask",
                    rationale="Email is PII"
                )
            ],
            summary="Email detected",
            confidence="high"
        )
        assert result.has_sensitive_data is True
        assert len(result.detections) == 1
        assert result.summary == "Email detected"
        assert result.confidence == ConfidenceLevel.HIGH

    def test_runtime_detection_result_no_sensitive_data(self):
        """Test runtime detection result with no sensitive data."""
        result = RuntimeDetectionResult(
            has_sensitive_data=False,
            detections=[],
            summary="No sensitive data",
            confidence="high"
        )
        assert result.has_sensitive_data is False
        assert len(result.detections) == 0
        assert result.confidence == ConfidenceLevel.HIGH


class TestLLMSchemas:
    """Test Pydantic schemas for LLM output."""

    def test_column_recommendation_valid(self):
        """Test valid column recommendation."""
        rec = ColumnRecommendation(
            table="patients",
            column="email",
            sensitivity=SensitivityLevel.HIGH,
            data_type="character varying",
            recommended_strategy=MaskingStrategyRecommendation.EMAIL,
            rationale="Email is PII",
            source="llm"
        )
        assert rec.table == "patients"
        assert rec.column == "email"
        assert rec.sensitivity == SensitivityLevel.HIGH
        assert rec.data_type == "character varying"
        assert rec.recommended_strategy == MaskingStrategyRecommendation.EMAIL
        assert rec.rationale == "Email is PII"
        assert rec.source == "llm"

    def test_column_recommendation_normalization(self):
        """Test lowercase sensitivity and strategy alias normalization."""
        rec = ColumnRecommendation(
            table="patients",
            column="email",
            sensitivity="high",
            data_type="text",
            recommended_strategy="email_mask"
        )
        assert rec.sensitivity == SensitivityLevel.HIGH
        assert rec.recommended_strategy == MaskingStrategyRecommendation.EMAIL

    def test_column_recommendation_invalid_sensitivity(self):
        """Test column recommendation with invalid sensitivity level."""
        with pytest.raises(ValueError):
            ColumnRecommendation(
                table="patients",
                column="email",
                sensitivity="critical_secret",  # Invalid
                recommended_strategy=MaskingStrategyRecommendation.EMAIL,
                rationale="Email is PII"
            )

    def test_column_recommendation_invalid_strategy(self):
        """Test column recommendation with invalid strategy."""
        with pytest.raises(ValueError):
            ColumnRecommendation(
                table="patients",
                column="email",
                sensitivity=SensitivityLevel.HIGH,
                recommended_strategy="custom_unsupported_strategy",
                rationale="Email is PII"
            )

    def test_schema_analysis_result_valid(self):
        """Test valid schema analysis result."""
        result = SchemaAnalysisLLMResult(
            table_name="users",
            recommendations=[
                ColumnRecommendation(
                    table="users",
                    column="email",
                    sensitivity=SensitivityLevel.HIGH,
                    data_type="character varying",
                    recommended_strategy=MaskingStrategyRecommendation.EMAIL,
                    rationale="Email is PII"
                )
            ]
        )
        assert result.table_name == "users"
        assert len(result.recommendations) == 1

    def test_schema_analysis_result_empty_recommendations(self):
        """Test schema analysis result with no recommendations."""
        result = SchemaAnalysisLLMResult(
            table_name="users",
            recommendations=[]
        )
        assert result.table_name == "users"
        assert len(result.recommendations) == 0


class TestSchemaAnalyzer:
    """Test schema analyzer functionality."""

    def test_schema_analyzer_creation(self, schema_analyzer):
        """Test schema analyzer can be created."""
        assert schema_analyzer is not None
        assert schema_analyzer.SENSITIVE_PATTERNS is not None
        assert len(schema_analyzer.SENSITIVE_PATTERNS) > 0

    def test_detect_sensitive_columns(self, schema_analyzer, sample_columns):
        """Test detection of sensitive columns."""
        sensitive = schema_analyzer.detect_sensitive_columns(sample_columns)
        
        # Should detect email, phone, address, name as sensitive
        assert "email" in sensitive
        assert "phone" in sensitive
        assert "address" in sensitive
        assert "name" in sensitive
        # id should not be detected as sensitive
        assert "id" not in sensitive

    def test_detect_sensitive_columns_case_insensitive(self, schema_analyzer):
        """Test that column detection is case-insensitive."""
        columns = [
            ColumnSchema(column_name="EMAIL", data_type="character varying", is_nullable=False),
            ColumnSchema(column_name="Phone", data_type="character varying", is_nullable=False),
            ColumnSchema(column_name="FirstName", data_type="character varying", is_nullable=False),
        ]
        
        sensitive = schema_analyzer.detect_sensitive_columns(columns)
        assert "EMAIL" in sensitive
        assert "Phone" in sensitive
        assert "FirstName" in sensitive

    def test_analyze_column_patterns(self, schema_analyzer, sample_columns):
        """Test column pattern analysis."""
        analysis = schema_analyzer.analyze_column_patterns(sample_columns)
        
        assert analysis["total_columns"] == 5
        assert analysis["sensitive_count"] > 0
        assert len(analysis["recommendations"]) > 0
        assert "character varying" in analysis["data_types"]

    def test_suggest_masking_strategy_email(self, schema_analyzer):
        """Test masking strategy suggestion for email."""
        strategy = schema_analyzer.suggest_masking_strategy("user_email", "character varying")
        assert strategy == MaskingStrategyRecommendation.EMAIL

    def test_suggest_masking_strategy_phone(self, schema_analyzer):
        """Test masking strategy suggestion for phone."""
        strategy = schema_analyzer.suggest_masking_strategy("phone_number", "character varying")
        assert strategy == MaskingStrategyRecommendation.PHONE_LAST4

    def test_suggest_masking_strategy_ssn(self, schema_analyzer):
        """Test masking strategy suggestion for SSN."""
        strategy = schema_analyzer.suggest_masking_strategy("ssn", "character varying")
        assert strategy == MaskingStrategyRecommendation.REDACT

    def test_suggest_masking_strategy_password(self, schema_analyzer):
        """Test masking strategy suggestion for password."""
        strategy = schema_analyzer.suggest_masking_strategy("password", "character varying")
        assert strategy == MaskingStrategyRecommendation.REDACT

    def test_suggest_masking_strategy_default_text(self, schema_analyzer):
        """Test default masking strategy for text columns."""
        strategy = schema_analyzer.suggest_masking_strategy("description", "text")
        assert strategy == MaskingStrategyRecommendation.REDACT

    def test_suggest_masking_strategy_default_numeric(self, schema_analyzer):
        """Test default masking strategy for numeric columns."""
        strategy = schema_analyzer.suggest_masking_strategy("count", "integer")
        assert strategy == MaskingStrategyRecommendation.NONE

    def test_sensitivity_mapping(self, schema_analyzer):
        """Test that sensitivity levels are correctly mapped."""
        assert schema_analyzer.SENSITIVITY_MAP["email"] == SensitivityLevel.HIGH
        assert schema_analyzer.SENSITIVITY_MAP["phone"] == SensitivityLevel.HIGH
        assert schema_analyzer.SENSITIVITY_MAP["ssn"] == SensitivityLevel.HIGH
        assert schema_analyzer.SENSITIVITY_MAP["name"] == SensitivityLevel.MEDIUM
        assert schema_analyzer.SENSITIVITY_MAP["income"] == SensitivityLevel.MEDIUM

    @patch('app.ai.schema_analyzer.llm_client')
    def test_analyze_table_schema_with_llm(self, mock_llm_client, schema_analyzer, sample_columns):
        """Test table schema analysis with LLM recommendations."""
        mock_llm_client.is_available.return_value = True
        mock_result = SchemaAnalysisLLMResult(
            table_name="users",
            recommendations=[
                ColumnRecommendation(
                    table="users",
                    column="email",
                    sensitivity=SensitivityLevel.HIGH,
                    data_type="character varying",
                    recommended_strategy=MaskingStrategyRecommendation.EMAIL,
                    rationale="Email is PII",
                    source="llm"
                )
            ]
        )
        mock_llm_client.analyze_schema_metadata.return_value = mock_result
        
        recommendations = schema_analyzer.analyze_table_schema("users", sample_columns)
        
        assert len(recommendations) == 1
        assert recommendations[0].column == "email"
        assert recommendations[0].sensitivity == SensitivityLevel.HIGH
        assert recommendations[0].recommended_strategy == MaskingStrategyRecommendation.EMAIL
        assert recommendations[0].source == "llm"
        mock_llm_client.analyze_schema_metadata.assert_called_once()

    @patch('app.ai.schema_analyzer.llm_client')
    def test_schema_cross_validation_rejects_hallucinated_column(self, mock_llm_client, schema_analyzer, sample_columns):
        """Test that LLM recommendations for nonexistent columns are rejected by schema cross-validation."""
        mock_llm_client.is_available.return_value = True
        mock_result = SchemaAnalysisLLMResult(
            table_name="users",
            recommendations=[
                ColumnRecommendation(
                    table="users",
                    column="email",  # Valid column
                    sensitivity=SensitivityLevel.HIGH,
                    data_type="character varying",
                    recommended_strategy=MaskingStrategyRecommendation.EMAIL,
                    rationale="Valid email column"
                ),
                ColumnRecommendation(
                    table="users",
                    column="secret_credit_card_nonexistent",  # Hallucinated column NOT in sample_columns
                    sensitivity=SensitivityLevel.HIGH,
                    data_type="character varying",
                    recommended_strategy=MaskingStrategyRecommendation.REDACT,
                    rationale="Hallucinated"
                )
            ]
        )
        mock_llm_client.analyze_schema_metadata.return_value = mock_result
        
        recommendations = schema_analyzer.analyze_table_schema("users", sample_columns)
        
        # Only the existing column should be retained
        assert len(recommendations) == 1
        assert recommendations[0].column == "email"
        assert all(r.column != "secret_credit_card_nonexistent" for r in recommendations)

    @patch('app.ai.schema_analyzer.llm_client')
    def test_analyze_table_schema_fallback_when_llm_unavailable(self, mock_llm_client, schema_analyzer, sample_columns):
        """Test that schema analysis gracefully falls back to heuristics when LLM is unavailable."""
        mock_llm_client.is_available.return_value = False
        
        recommendations = schema_analyzer.analyze_table_schema("users", sample_columns)
        
        # Should return heuristic fallback recommendations
        assert len(recommendations) > 0
        assert all(r.source == "heuristic_fallback" for r in recommendations)
        assert any(r.column == "email" and r.recommended_strategy == MaskingStrategyRecommendation.EMAIL for r in recommendations)
        assert any(r.column == "phone" and r.recommended_strategy == MaskingStrategyRecommendation.PHONE_LAST4 for r in recommendations)

    def test_sensitive_patterns_completeness(self, schema_analyzer):
        """Test that sensitive patterns cover common PII types."""
        patterns = schema_analyzer.SENSITIVE_PATTERNS
        assert "email" in patterns
        assert "phone" in patterns
        assert "ssn" in patterns
        assert "credit_card" in patterns
        assert "password" in patterns
        assert "address" in patterns
        assert "name" in patterns
        assert "dob" in patterns
