# Support Engineer Dataset - Batch Management

## Overview
This directory contains the Support Engineer evaluation dataset, organized in batches of 100 prompts each to scale from 10 to 1,000 total scenarios.

## Batch Structure

### Completed Batches
- **batch_00_core.jsonl** (10 prompts) - Foundation scenarios covering key support areas

### Planned Batches (100 prompts each)
- **batch_01_technical.jsonl** - Software crashes, performance, installation, configuration
- **batch_02_billing.jsonl** - Account access, subscriptions, refunds, permissions  
- **batch_03_escalation.jsonl** - Data recovery, security incidents, complex technical issues
- **batch_04_angry_customers.jsonl** - Difficult customer situations, complaints, frustrations
- **batch_05_integrations.jsonl** - API issues, third-party integrations, developer support
- **batch_06_security.jsonl** - Security questions, compliance (GDPR, SOC2), data protection
- **batch_07_onboarding.jsonl** - New user help, getting started, feature explanations
- **batch_08_product_issues.jsonl** - Bug reports, feature requests, product feedback
- **batch_09_edge_cases.jsonl** - Unusual scenarios, complex multi-issue cases

### Target Distribution (1,000 total prompts)
```
Core Foundation:     10 prompts  (1%)
Technical Issues:   100 prompts (10%)
Billing/Account:    100 prompts (10%)
Escalation Cases:   100 prompts (10%)
Difficult Customers: 100 prompts (10%)
Integrations:       100 prompts (10%)
Security/Compliance: 100 prompts (10%)
Onboarding:         100 prompts (10%)
Product Issues:     100 prompts (10%)
Edge Cases:         100 prompts (10%)
Additional Batches: 290 prompts (29%)
```

## Usage

### Individual Batch Testing
Update recipe dataset path to specific batch:
```json
"dataset": {
  "type": "jsonl", 
  "path": "datasets/enterprise/support_engineer/batch_01_technical.jsonl"
}
```

### Combined Dataset Testing
Use merged dataset for full evaluation:
```json
"dataset": {
  "type": "jsonl",
  "path": "datasets/enterprise/support_engineer/combined_full.jsonl"
}
```

## Batch Creation Guidelines

### Quality Standards
- **Realistic scenarios** based on actual customer support interactions
- **Diverse difficulty levels** (easy, medium, hard) within each batch
- **Expert-validated responses** for expected answers
- **Balanced coverage** of escalation vs non-escalation cases
- **Varied customer personas** (technical, non-technical, frustrated, polite)

### Prompt Categories per Batch
Each 100-prompt batch should include:
- **25 prompts**: Simple/straightforward issues
- **50 prompts**: Medium complexity requiring multi-step solutions
- **25 prompts**: Complex scenarios testing edge cases

### Expected Response Guidelines
- **Empathetic opening** acknowledging customer concern
- **Clear action steps** or information gathering
- **Appropriate escalation** when needed
- **Professional closing** with next steps or follow-up
