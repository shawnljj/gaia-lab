# Enterprise Support Engineer Suite

## Overview

The **Enterprise Support Engineer Suite** evaluates how well LLMs perform as customer support chatbots in enterprise environments. This suite tests critical support capabilities including response quality, professional communication, escalation decision-making, and technical accuracy.

## Evaluation Goals

- **Customer Satisfaction**: Measure response helpfulness and accuracy
- **Professional Communication**: Ensure empathetic, professional tone
- **Escalation Intelligence**: Proper identification of complex issues requiring specialist attention
- **Technical Competence**: Accurate troubleshooting and solution guidance

## Suite Structure

### Dataset
**File**: `datasets/enterprise/support_engineer.jsonl`

Contains 10 realistic customer support scenarios:
- Software crashes and technical issues
- Account access problems (password resets)
- Angry customer situations
- Billing and refund requests
- Product updates and downgrades
- Compliance questions (GDPR)
- API integration support
- Data access and recovery
- System performance issues
- Accidental data deletion

Each entry includes:
- `prompt`: Customer inquiry/complaint
- `expected`: Ideal support response demonstrating best practices

### Recipes (4 Tests)

#### 1. **Support Response Quality** (`recipes/enterprise/support_response_quality.json`)
- **Purpose**: Evaluates response accuracy and helpfulness against ideal support responses
- **Metric**: Semantic similarity with 0.7 threshold
- **Methodology**: 
  - Uses vector embeddings to compare LLM response with expected response
  - Threshold of 0.7 ensures responses capture key information and approach
  - Accounts for different phrasing while maintaining semantic meaning
- **Prompt Template**: "You are a professional customer support engineer. Respond to this customer inquiry with empathy, accuracy, and clear next steps: {prompt}"
- **Pass Criteria**: Semantic similarity ≥ 0.7
- **Failure Indicators**: Missing key information, incorrect guidance, unhelpful responses

#### 2. **Support Tone Professionalism** (`recipes/enterprise/support_tone_professionalism.json`)
- **Purpose**: Measures professional and empathetic communication style
- **Metric**: Custom `tone_analysis.py` with 4-component scoring system
- **Methodology**:
  - **Empathy Detection (30% weight)**: Scans for empathy phrases ("understand", "apologize", "sorry", "frustrating", "appreciate", "help", "assist", "concern")
  - **Professional Language (20% weight)**: Flags unprofessional terms ("yeah", "nope", "gonna", "hey", "lol", etc.)
  - **Solution Orientation (30% weight)**: Identifies action-oriented language ("let me", "i can", "try", "step", "solution", "resolve", "fix")
  - **Response Length (20% weight)**: Validates appropriate length (20-150 words)
- **Scoring**: Each component contributes to final score (max 1.0)
- **Pass Criteria**: Score ≥ 0.7 with balanced performance across all components
- **Failure Indicators**: Robotic responses, unprofessional language, lack of empathy, overly brief/verbose

#### 3. **Support Escalation Handling** (`recipes/enterprise/support_escalation_handling.json`)
- **Purpose**: Tests accuracy of escalation decision-making and process
- **Metric**: Custom `escalation_analysis.py` with decision logic evaluation
- **Methodology**:
  - **Escalation Need Detection (40% weight)**: Compares escalation keywords in prediction vs expected response
    - Keywords: "escalate", "specialist", "technical team", "supervisor", "manager", "expert", "advanced support", "tier 2"
  - **Process Communication (30% weight)**: Evaluates clear escalation process explanation
    - Indicators: "connect you", "transfer", "forward", "appropriate team"
  - **Information Gathering (30% weight)**: Checks for relevant detail collection before escalation
    - Patterns: "details", "information", "tell me", "account", "system", question words
- **Scoring Logic**:
  - Correct escalation identification: +0.4
  - Proper process communication: +0.3  
  - Information gathering: +0.3
- **Pass Criteria**: Score ≥ 0.7 with correct escalation decision
- **Failure Indicators**: Missing escalations, unnecessary escalations, unclear process

#### 4. **Support Technical Accuracy** (`recipes/enterprise/support_technical_accuracy.json`)
- **Purpose**: Validates correctness of technical troubleshooting guidance
- **Metric**: Exact match (case-insensitive) against expert-validated responses
- **Methodology**:
  - Direct string comparison with case normalization
  - Punctuation preserved to maintain technical precision
  - No partial credit - response must be technically correct
- **Prompt Template**: "Provide accurate technical support for this customer issue: {prompt}"
- **Pass Criteria**: Exact match with expected technical solution
- **Failure Indicators**: Incorrect steps, missing critical information, wrong technical advice

### Custom Metrics - Detailed Methodology

#### `metrics/tone_analysis.py`
**Function**: `evaluate_professional_tone(prediction, target)`

**Scoring Algorithm** (Maximum: 1.0):

1. **Empathy Detection (0.3 points)**
   - **Method**: Keyword matching against empathy vocabulary
   - **Keywords**: "understand", "apologize", "sorry", "frustrating", "appreciate", "help", "assist", "concern"
   - **Logic**: `any(phrase in prediction.lower() for phrase in empathy_phrases)`
   - **Rationale**: Customer support requires emotional intelligence and acknowledgment of customer feelings
   - **Pass**: At least one empathy indicator present
   - **Fail**: Cold, robotic responses without emotional awareness

2. **Professional Language Assessment (0.2 points)**
   - **Method**: Negative keyword detection for unprofessional terms
   - **Flagged Terms**: "yeah", "nope", "gonna", "wanna", "kinda", "sorta", "hey", "yo", "sup", "lol", "omg", "wtf"
   - **Logic**: `not any(term in prediction.lower() for term in unprofessional_terms)`
   - **Rationale**: Enterprise support requires formal, professional communication standards
   - **Pass**: No unprofessional language detected
   - **Fail**: Casual or inappropriate language present

3. **Solution Orientation (0.3 points)**
   - **Method**: Action-oriented language detection
   - **Keywords**: "let me", "i can", "we can", "try", "step", "solution", "resolve", "fix", "help you", "assist you"
   - **Logic**: `any(indicator in prediction.lower() for indicator in solution_indicators)`
   - **Rationale**: Support responses must be actionable and helpful, not just acknowledgments
   - **Pass**: Contains solution-focused language
   - **Fail**: Passive or non-actionable responses

4. **Response Length Appropriateness (0.2 points)**
   - **Method**: Word count validation
   - **Range**: 20-150 words
   - **Logic**: `20 <= len(prediction.split()) <= 150`
   - **Rationale**: Too brief = insufficient help; too verbose = overwhelming customers
   - **Pass**: Within optimal word range
   - **Fail**: Too brief (<20 words) or too verbose (>150 words)

**Output Structure**:
```python
{
    "score": float,  # 0.0-1.0
    "feedback": str,  # Human-readable summary
    "details": {
        "empathy_found": bool,
        "professional_language": bool,
        "solution_oriented": bool,
        "word_count": int
    }
}
```

#### `metrics/escalation_analysis.py`
**Function**: `evaluate_escalation_decision(prediction, target)`

**Scoring Algorithm** (Maximum: 1.0):

1. **Escalation Need Recognition (0.4 points)**
   - **Method**: Keyword-based escalation detection in both prediction and target
   - **Keywords**: "escalate", "specialist", "technical team", "supervisor", "manager", "expert", "advanced support", "tier 2"
   - **Logic**: 
     ```python
     target_suggests_escalation = any(keyword in target.lower() for keyword in escalation_keywords)
     prediction_suggests_escalation = any(keyword in prediction.lower() for keyword in escalation_keywords)
     ```
   - **Scoring Matrix**:
     - Correct escalation (both true): +0.4
     - Correct no-escalation (both false): +0.4
     - Missed escalation (target=true, prediction=false): +0.0
     - Unnecessary escalation (target=false, prediction=true): +0.0
   - **Rationale**: Critical to identify complex issues requiring specialist expertise vs. issues resolvable at first level

2. **Escalation Process Communication (0.3 points)**
   - **Method**: Process clarity assessment when escalation is suggested
   - **Indicators**: "connect you", "transfer", "forward", "specialist", "technical team", "next level", "appropriate team"
   - **Logic**: `any(indicator in prediction.lower() for indicator in process_indicators)`
   - **Rationale**: Customers need clear understanding of what happens next in escalation
   - **Pass**: Clear escalation process explained
   - **Fail**: Vague or missing escalation process

3. **Information Gathering (0.3 points)**
   - **Method**: Question and detail-seeking language detection
   - **Patterns**: "details", "information", "tell me", "could you", "what", "when", "how", "which", "account", "system"
   - **Logic**: `any(phrase in prediction.lower() for phrase in info_gathering)`
   - **Rationale**: Effective support requires gathering context before providing solutions or escalating
   - **Pass**: Asks relevant clarifying questions
   - **Fail**: Provides generic responses without context gathering

**Output Structure**:
```python
{
    "score": float,  # 0.0-1.0
    "feedback": str,  # Human-readable assessment
    "details": {
        "escalation_needed": bool,      # From target analysis
        "escalation_identified": bool,  # From prediction analysis
        "gathers_information": bool     # Information-seeking behavior
    }
}
```

### Evaluation Thresholds & Interpretation

**Overall Suite Performance**:
- **Excellent (≥0.85)**: Ready for production deployment
- **Good (0.7-0.84)**: Minor improvements needed
- **Needs Work (0.5-0.69)**: Significant training required
- **Poor (<0.5)**: Not suitable for customer-facing role

**Per-Recipe Thresholds**:
- **Response Quality**: ≥0.7 semantic similarity
- **Tone Professionalism**: ≥0.7 composite score
- **Escalation Handling**: ≥0.7 decision accuracy
- **Technical Accuracy**: 1.0 exact match (binary pass/fail)

### Cookbook
**File**: `cookbooks/enterprise_support_engineer.json`
- Groups all 4 Support Engineer recipes
- Provides comprehensive support capability evaluation
- Description explains the evaluation focus areas

## Running the Suite

### Prerequisites
1. Virtual environment activated: `source .venv/bin/activate`
2. API keys configured in `.env` file
3. Dependencies installed: `pip install -r requirements.txt`

### Execution Options

#### Option 1: Complete Suite (when created)
```bash
python scripts/run_suite.py suites/enterprise_support_engineer.yaml
```

#### Option 2: Individual Recipe Testing
```bash
python -m moonshot cli interactive
# Then run specific recipes for debugging
```

#### Option 3: Web UI
```bash
bash scripts/start_moonshot.sh
# Navigate to http://localhost:3000
```

## Expected Outputs & Interpretation

### Report Location
`reports/enterprise_support_engineer/`

### Detailed Metrics Analysis

#### **1. Response Quality Metrics**
- **Score Range**: 0.0-1.0 (semantic similarity)
- **Interpretation**:
  - **0.9-1.0**: Response captures all key elements with excellent semantic alignment
  - **0.7-0.89**: Good response with minor semantic differences
  - **0.5-0.69**: Partial alignment, missing some key information
  - **<0.5**: Poor response, significant semantic mismatch
- **Common Failure Patterns**: Generic responses, missing specific troubleshooting steps, incorrect solutions

#### **2. Tone Professionalism Metrics**
- **Score Breakdown**: 4 weighted components totaling 1.0
  - Empathy: 0.3 max | Professional Language: 0.2 max | Solution Focus: 0.3 max | Length: 0.2 max
- **Interpretation**:
  - **0.8-1.0**: Excellent professional communication, ready for customer interaction
  - **0.6-0.79**: Good tone with minor improvements needed
  - **0.4-0.59**: Inconsistent professionalism, requires training
  - **<0.4**: Unprofessional, not suitable for customer-facing role
- **Detailed Feedback**: Each component provides specific pass/fail indicators
- **Common Issues**: Lack of empathy phrases, casual language, non-actionable responses

#### **3. Escalation Handling Metrics**
- **Score Breakdown**: 3 weighted components totaling 1.0
  - Escalation Recognition: 0.4 max | Process Communication: 0.3 max | Info Gathering: 0.3 max
- **Decision Matrix Analysis**:
  ```
  Target Escalation | Prediction Escalation | Score | Interpretation
  Yes              | Yes                   | 0.4   | Correct escalation
  No               | No                    | 0.4   | Correct resolution
  Yes              | No                    | 0.0   | Missed escalation (critical failure)
  No               | Yes                   | 0.0   | Unnecessary escalation (efficiency loss)
  ```
- **Critical Scenarios**: Data recovery, account access, technical integration issues
- **Process Quality**: Measures clarity of escalation explanation and next steps

#### **4. Technical Accuracy Metrics**
- **Score**: Binary (1.0 = exact match, 0.0 = any deviation)
- **Strictness Rationale**: Technical instructions must be precise to avoid customer confusion or system damage
- **Evaluation Method**: Case-insensitive exact string matching
- **Common Failures**: Incorrect troubleshooting steps, missing critical warnings, wrong technical procedures

### Aggregate Reporting

#### **Suite-Level Metrics**
- **Weighted Overall Score**: Average of all 4 recipe scores
- **Pass Rate**: Percentage of test cases meeting threshold (≥0.7)
- **Critical Failure Count**: Number of missed escalations or incorrect technical advice
- **Readiness Assessment**: Production deployment recommendation

#### **Comparative Analysis**
- **Model Comparison**: Side-by-side performance across different LLMs
- **Scenario Difficulty**: Which customer scenarios are most challenging
- **Improvement Areas**: Specific recommendations based on failure patterns

### Report Formats

#### **CSV Output** (`results.csv`)
```csv
test_case,recipe,prompt,prediction,target,score,feedback,details
1,support_response_quality,"My software keeps crashing...",<llm_response>,<expected>,0.85,"Good semantic alignment","..."
1,support_tone_professionalism,"My software keeps crashing...",<llm_response>,<expected>,0.9,"✓ Shows empathy; ✓ Professional language","..."
```

#### **Markdown Summary** (`summary.md`)
- Executive summary with key findings
- Per-recipe performance breakdown
- Failure analysis with specific examples
- Recommendations for model improvement
- Readiness assessment for production deployment

## Scaling to Other Enterprise Personas

This structure serves as a template for additional enterprise personas:

```
datasets/enterprise/
├── support_engineer.jsonl        ✓ Created
├── sales_representative.jsonl    → Next persona
├── technical_writer.jsonl        → Future persona
└── data_analyst.jsonl           → Future persona

recipes/enterprise/
├── support_*.json                ✓ Created (4 recipes)
├── sales_*.json                  → Next persona recipes
└── ...

cookbooks/
├── enterprise_support_engineer.json  ✓ Created
├── enterprise_sales_representative.json → Next
└── ...

suites/
├── enterprise_support_engineer.yaml → To be created
├── enterprise_sales_representative.yaml → Next
└── ...
```

## Next Steps

1. **Complete Suite**: Create `suites/enterprise_support_engineer.yaml`
2. **Test Run**: Execute the suite to validate all components work
3. **Iterate**: Refine based on initial results
4. **Scale**: Apply same pattern to other enterprise personas
