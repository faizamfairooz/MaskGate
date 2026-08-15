# Runtime Sensitive Data Detection

## Overview

The Runtime Sensitive Data Detection is a **secondary safety layer** in MaskGate that provides additional protection beyond deterministic masking policies. It operates on query results after approved masking policies have been applied, using both pattern matching and LLM analysis to identify sensitive data that may not have been covered by existing policies.

## Architecture

### Detection Flow

```
Developer Query
       ↓
   PostgreSQL
       ↓
Approved Deterministic Masking
       ↓
Pattern-Based Detection (Phase 1)
       ↓
LLM-Based Detection (Phase 2)
       ↓
Additional Masking if Required
       ↓
Final Response
```

### Components

1. **SensitiveDataDetector** (`app/ai/sensitive_data_detector.py`)
   - Pattern-based detection using regex patterns
   - LLM-based detection for advanced analysis
   - Converts detections to actionable masking operations

2. **LLM Client** (`app/ai/llm.py`)
   - Structured LLM output for runtime detection
   - Fallback parsing when structured output fails
   - Supports both OpenAI and Google AI Studio

3. **Masking Engine** (`app/masking/engine.py`)
   - Applies two-phase runtime detection
   - Respects already-masked columns
   - Applies deterministic masking based on detection results

## Detection Phases

### Phase 1: Pattern-Based Detection

Uses regex patterns to identify common sensitive data types:

- Email addresses
- Phone numbers
- Social Security Numbers (SSN)
- Credit card numbers
- IP addresses
- URLs

This phase is fast and deterministic, catching obvious sensitive data patterns.

### Phase 2: LLM-Based Detection

Uses LLM analysis to identify sensitive data that pattern matching may miss:

- Personal names and addresses
- Custom identifiers
- Context-sensitive sensitive data
- Data that doesn't match standard patterns

**Important**: This is a secondary safety layer and is not guaranteed to detect every sensitive value. It should be used in conjunction with deterministic policies.

## API Integration

### Query Service Integration

The runtime detection is integrated into the query processing flow:

```python
# In QueryService.execute_query()
if apply_masking:
    masking_result = self.masking_service.apply_masking(
        MaskingRequest(
            table_name=self._extract_table_name(query),
            columns=columns,
            data=rows,
            auto_detect=mask_suspicious,  # Enables runtime detection
        )
    )
```

### Response Enhancement

Query responses include detection information:

```python
QueryResponse(
    columns=columns,
    rows=masked_data,
    row_count=len(rows),
    execution_time=execution_time,
    masked_columns=masked_columns,
    llm_detection_enabled=llm_detection_enabled,
    llm_detection_summary=llm_detection_summary,
)
```

## Configuration

### Environment Variables

```bash
# Enable OpenAI (optional)
OPENAI_API_KEY=your_openai_api_key_here

# Enable Google AI Studio (optional)
GOOGLE_API_KEY=your_google_ai_studio_api_key_here

# LLM Configuration
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.3
```

### Enabling Runtime Detection

Runtime detection is enabled by setting `auto_detect=True` in the masking request:

```python
masking_service.apply_masking(
    MaskingRequest(
        table_name="users",
        columns=["id", "email", "name"],
        data=query_results,
        auto_detect=True,  # Enable runtime detection
    )
)
```

## Structured LLM Output

### RuntimeDetectionResult Schema

```python
class RuntimeDetectionResult(BaseModel):
    has_sensitive_data: bool  # Whether sensitive data was detected
    detections: List[SensitiveValueDetection]  # List of detected values
    summary: str  # Brief summary of findings
    confidence: str  # Confidence level: high, medium, or low
```

### SensitiveValueDetection Schema

```python
class SensitiveValueDetection(BaseModel):
    row_index: int  # Index of the row containing the sensitive value
    column_name: str  # Name of the column containing the sensitive value
    sensitivity: SensitivityLevel  # low, medium, or high
    data_type: str  # Type of sensitive data (email, phone, custom, etc.)
    recommended_strategy: str  # Recommended masking strategy
    rationale: str  # Brief explanation of why this is sensitive
```

## Security Considerations

### Data Privacy

- **LLM Input**: Only sends truncated sample data (max 10 rows, values truncated to 50 chars)
- **Already Masked**: Columns already protected by policies are excluded from LLM analysis
- **No SQL Execution**: LLM is never allowed to execute SQL or modify data
- **Validation**: All LLM outputs are validated before application

### Deterministic Masking

- Detection results are converted to deterministic masking operations
- No reliance on LLM for the actual masking application
- Approved masking strategies are applied consistently

### Limitations

- **Not Guaranteed**: LLM detection is a secondary layer and may miss some sensitive data
- **False Positives**: May flag non-sensitive data as sensitive
- **Performance**: Adds latency to query processing when enabled
- **Cost**: Requires LLM API calls when enabled

## Testing

### Test Coverage

Comprehensive tests for runtime detection include:

- LLM client detection methods
- Schema validation for structured output
- Pattern-based detection
- LLM-based detection with mocking
- Integration with masking engine
- Edge cases (empty data, no LLM, etc.)

### Running Tests

```bash
# Run runtime detection tests
pytest backend/tests/test_ai.py::TestLLMClient::test_detect_runtime_sensitive_data_valid -v

# Run all AI tests
pytest backend/tests/test_ai.py -v
```

## Best Practices

1. **Primary Defense**: Always use deterministic masking policies as the primary defense
2. **Secondary Layer**: Use runtime detection as an additional safety net
3. **Review Results**: Regularly review detection summaries for accuracy
4. **Update Policies**: Create policies for frequently detected sensitive columns
5. **Monitor Performance**: Monitor the performance impact of runtime detection
6. **Cost Management**: Be aware of LLM API costs when enabling detection

## Future Enhancements

Potential improvements to runtime detection:

- Caching of detection results for similar queries
- Custom pattern configuration
- Confidence thresholds for automatic policy creation
- Detection result audit logging
- Performance optimization for large datasets
- Support for additional LLM providers

## Troubleshooting

### LLM Detection Not Working

1. Check API key configuration in `.env`
2. Verify LLM client availability with `llm_client.is_available()`
3. Check logs for LLM API errors
4. Ensure `auto_detect=True` is set in masking request

### Too Many False Positives

1. Review LLM temperature setting (lower for more conservative detection)
2. Add deterministic policies for known non-sensitive columns
3. Adjust pattern matching regex patterns
4. Review detection summaries to understand detection patterns

### Performance Issues

1. Reduce sample size for LLM analysis
2. Disable LLM detection and use only pattern matching
3. Add caching for frequently executed queries
4. Consider batch processing for large result sets