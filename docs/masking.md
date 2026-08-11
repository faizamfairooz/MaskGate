# Masking Strategies

MaskGate provides a comprehensive set of data masking strategies to protect sensitive information while maintaining data utility for development, testing, and analytics purposes.

## Available Strategies

### 1. Redaction (`redaction`)

**Description**: Replaces entire values with asterisks.

**Use Case**: When complete data concealment is required.

**Example**:
- Input: `john.smith@email.com`
- Output: `*******************`

**Parameters**: None required

**Best For**: Highly sensitive data where no pattern preservation is needed

---

### 2. Partial Mask (`partial_mask`)

**Description**: Shows first and last characters with asterisks in between.

**Use Case**: When some pattern recognition is needed but values must be obscured.

**Example**:
- Input: `Hello World`
- Output: `H********d`

**Parameters**:
- `visible_chars` (integer, default: 2) - Number of characters to show at start and end

**Best For**: Names, addresses, and identification numbers

---

### 3. Hash (`hash`)

**Description**: Replaces values with cryptographic hash.

**Use Case**: When data must be irreversibly anonymized but remain consistent.

**Example**:
- Input: `sensitive_data`
- Output: `a3f5e8b2c1d4f6e7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1`

**Parameters**:
- `algorithm` (string, default: "sha256") - Hash algorithm (md5, sha1, sha256, sha512)

**Best For**: Passwords, tokens, and irreversible identifiers

---

### 4. Email Mask (`email_mask`)

**Description**: Email-specific masking that preserves domain but obscures local part.

**Use Case**: When email format must be maintained for validation but addresses must be protected.

**Example**:
- Input: `user@example.com`
- Output: `u***@example.com`

**Parameters**: None required

**Best For**: Email addresses in customer data

---

### 5. Phone Mask (`phone_mask`)

**Description**: Phone number masking that preserves last 4 digits.

**Use Case**: When phone format validation is needed but numbers must be protected.

**Example**:
- Input: `123-456-7890`
- Output: `***-***-7890`

**Parameters**: None required

**Best For**: Phone numbers in contact information

---

### 6. SSN Mask (`ssn_mask`)

**Description**: Social Security Number masking following standard format.

**Use Case**: When SSN format must be maintained for validation but numbers must be protected.

**Example**:
- Input: `123-45-6789`
- Output: `***-**-6789`

**Parameters**: None required

**Best For**: Social Security Numbers and similar government IDs

---

### 7. Credit Card Mask (`credit_card_mask`)

**Description**: Credit card number masking that preserves last 4 digits.

**Use Case**: When payment card format validation is needed but numbers must be protected.

**Example**:
- Input: `4111111111111111`
- Output: `************1111`

**Parameters**: None required

**Best For**: Credit card numbers and payment information

---

### 8. Tokenization (`tokenization`)

**Description**: Replaces values with random tokens.

**Use Case**: When consistent replacement is needed across datasets.

**Example**:
- Input: `sensitive_value`
- Output: `aB3xY7zK9pQ2rT5`

**Parameters**:
- `token_length` (integer, default: 16) - Length of generated token

**Best For**: Cross-dataset consistency and reference integrity

---

### 9. Noise Addition (`noise_addition`)

**Description**: Adds random noise to numeric values.

**Use Case**: When statistical properties must be maintained but exact values must be obscured.

**Example**:
- Input: `50000`
- Output: `51234.56`

**Parameters**:
- `noise_level` (float, default: 0.1) - Noise level as percentage (0.0 to 1.0)

**Best For**: Salary, income, and other numeric sensitive data

---

### 10. Date Mask (`date_mask`)

**Description**: Preserves year but masks month and day.

**Use Case**: When year-level granularity is sufficient for analysis.

**Example**:
- Input: `1990-05-15`
- Output: `1990-01-01`

**Parameters**: None required

**Best For**: Birth dates, hire dates, and other temporal data

---

### 11. Generalization (`generalization`)

**Description**: Converts exact values to ranges.

**Use Case**: When range-based analysis is sufficient.

**Example**:
- Input: `52350`
- Output: `52000-53000`

**Parameters**:
- `bin_size` (integer, default: 1000) - Size of range bins

**Best For**: Income ranges, age groups, and numeric categorization

---

## Strategy Selection Guidelines

### Data Type Recommendations

| Data Type | Recommended Strategies | Alternative Strategies |
|-----------|----------------------|----------------------|
| Email | `email_mask` | `hash`, `partial_mask` |
| Phone | `phone_mask` | `partial_mask`, `redaction` |
| SSN | `ssn_mask` | `hash`, `redaction` |
| Credit Card | `credit_card_mask` | `hash`, `tokenization` |
| Password | `hash` | `redaction` |
| Name | `partial_mask` | `redaction` |
| Address | `partial_mask` | `redaction` |
| Date of Birth | `date_mask` | `generalization` |
| Salary/Income | `noise_addition` | `generalization` |
| IP Address | `partial_mask` | `redaction` |

### Use Case Recommendations

#### Development/Testing
- **Goal**: Maintain data format and relationships
- **Recommended**: `partial_mask`, `tokenization`, `noise_addition`
- **Avoid**: `redaction` (too destructive for testing)

#### Analytics
- **Goal**: Preserve statistical properties
- **Recommended**: `noise_addition`, `generalization`, `date_mask`
- **Avoid**: `redaction`, `hash` (destroys statistical patterns)

#### Compliance/Privacy
- **Goal**: Maximum data protection
- **Recommended**: `redaction`, `hash`, `tokenization`
- **Avoid**: `partial_mask` (reveals too much information)

#### Data Sharing
- **Goal**: Balance utility and privacy
- **Recommended**: `email_mask`, `phone_mask`, `ssn_mask`
- **Avoid**: `redaction` (may impact data usefulness)

## Policy Management

### Creating Policies

Policies can be created through the API or frontend interface:

```json
{
  "name": "Customer Email Protection",
  "description": "Masks customer email addresses",
  "table_name": "customers",
  "column_name": "email",
  "strategy": "email_mask",
  "parameters": {}
}
```

### Policy Priority

When multiple policies apply to the same column:
1. Policies are applied in order of creation
2. More specific policies take precedence
3. Policies can be enabled/disabled without deletion

### Policy Validation

The system automatically validates:
- Strategy existence and configuration
- Parameter validity for chosen strategy
- Table and column existence
- Policy conflicts and duplications

## Performance Considerations

### Masking Overhead

- **Lightweight**: `redaction`, `partial_mask`, `email_mask`
- **Medium**: `hash`, `tokenization`
- **Heavy**: `noise_addition`, `generalization`

### Optimization Tips

1. **Batch Processing**: Process large datasets in batches
2. **Caching**: Cache masked results for repeated queries
3. **Indexing**: Ensure proper database indexing for filtered queries
4. **Async Processing**: Use async operations for AI-assisted detection

## Security Best Practices

1. **Never Store Unmasked Data**: Apply masking at the database level
2. **Audit All Access**: Log all data access and masking operations
3. **Regular Policy Review**: Update policies as data sensitivity changes
4. **Test Thoroughly**: Validate masking effectiveness before production
5. **Compliance Alignment**: Ensure strategies meet regulatory requirements

## Compliance Mapping

### GDPR (General Data Protection Regulation)
- **Personal Data**: Use `hash`, `tokenization`, or `redaction`
- **Special Category Data**: Use `redaction` or strong `hash`
- **Right to Erasure**: Implement with policy deletion

### CCPA (California Consumer Privacy Act)
- **Personal Information**: Use `partial_mask` or `hash`
- **Sensitive Personal Information**: Use `redaction`
- **Data Minimization**: Use `generalization` for analytics

### HIPAA (Health Insurance Portability and Accountability Act)
- **PHI (Protected Health Information)**: Use `redaction` or strong `hash`
- **18 Identifiers**: Apply appropriate masking strategies
- **De-identification**: Use `tokenization` for research datasets

## Advanced Usage

### Custom Strategies

Developers can create custom masking strategies by extending the `MaskingStrategy` base class:

```python
class CustomStrategy(MaskingStrategy):
    def mask(self, value, parameters):
        # Custom masking logic
        return masked_value
    
    def validate_parameters(self, parameters):
        # Parameter validation
        return True
```

### AI-Assisted Strategy Selection

The system can recommend masking strategies based on:
- Column name analysis
- Data type detection
- Pattern recognition
- Regulatory requirements

### Conditional Masking

Apply different strategies based on conditions:
- User roles and permissions
- Data sensitivity levels
- Compliance requirements
- Geographic regions
