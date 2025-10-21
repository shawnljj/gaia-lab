# Running Enterprise Support Engineer Evaluation

## Quick Troubleshooting

### Cookbook Not Appearing in UI?

**Try these steps:**

1. **Hard refresh your browser**
   - Chrome/Edge: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
   - Firefox: `Ctrl+F5` (Windows) or `Cmd+Shift+R` (Mac)
   - Safari: `Cmd+Option+R`

2. **Clear browser cache**
   - Go to browser settings → Privacy → Clear browsing data
   - Select "Cached images and files"
   - Clear and refresh

3. **Restart Moonshot server**
   ```bash
   pkill -f "moonshot"
   source .venv/bin/activate
   python -m moonshot web
   ```
   Then open http://localhost:3000

4. **Verify cookbook is registered**
   ```bash
   curl http://127.0.0.1:5000/api/v1/cookbooks | grep -i "enterprise"
   ```

---

## Running the Evaluation via UI

### Method 1: Through Benchmarking Section

1. **Navigate to Benchmarking**
   - Open http://localhost:3000
   - Look for "Benchmarking" or "Run" in the left sidebar

2. **Create New Benchmark**
   - Click "New Benchmark" or "Create Benchmark"
   
3. **Select Configuration**
   - **Cookbook**: Choose "Enterprise Support Engineer"
   - **Connector**: Select "openai-gpt" (GPT-4o)
   - **Dataset**: Should auto-select "enterprise-support-engineer" (1,010 prompts)

4. **Start Run**
   - Click "Run" or "Start Benchmark"
   - Monitor progress in the UI

### Method 2: Through Runners

If there's a "Runners" section:

1. **Navigate to Runners**
   - Look for "Runners" in the sidebar

2. **Create New Runner**
   - Select "Benchmarking" runner type
   
3. **Configure**
   - **Cookbook**: Enterprise Support Engineer
   - **Endpoints**: openai-gpt
   - **Number of prompts**: All (1,010)
   - **Output name**: Give it a descriptive name

4. **Execute**
   - Click "Run" to start evaluation

---

## Configuration Details

### Available Components

**Cookbook**: `enterprise_support_engineer`
- ID: `enterprise_support_engineer`
- Name: Enterprise Support Engineer
- 4 recipes included

**Recipes**:
1. `support_response_quality` - Response quality & helpfulness
2. `support_tone_professionalism` - Professional communication style
3. `support_escalation_handling` - Escalation decision evaluation
4. `support_technical_accuracy` - Technical correctness

**Dataset**: `enterprise-support-engineer`
- Total prompts: 1,010
- 11 batches covering: Core, Technical, Billing, Escalation, Difficult Customers, Integration, Security, Onboarding, Product, Performance, Mixed scenarios

**Connector**: `openai-gpt`
- Model: GPT-4o
- Temperature: 0.2
- Max tokens: 1,024

---

## Expected Results

### Runtime
- **Duration**: 15-30 minutes for full 1,010 prompts
- **Cost**: ~$10-20 in OpenAI API costs

### Output Location
```
reports/enterprise_support_engineer/
├── run_metadata.json
├── results.json
├── summary.csv
└── summary.md
```

### Metrics
Each recipe will provide:
- Overall score (A-E grade)
- Pass/fail rate
- Individual prompt results
- Aggregate statistics

---

## Troubleshooting

### "Dataset not found" error
```bash
# Verify dataset exists
ls -la moonshot-data/datasets/enterprise-support-engineer.json
ls -la moonshot-data/datasets/support_engineer/
```

### "Recipe not found" error
```bash
# Verify recipes exist
ls -la moonshot-data/recipes/enterprise/
```

### "Connector not found" error
```bash
# Check connector configuration
cat connectors/openai.yaml
# Verify API key is set
grep OPENAI_API_KEY .env
```

### API Key Issues
1. Check `.env` file has valid `OPENAI_API_KEY`
2. Ensure no spaces around the `=` sign
3. Restart Moonshot server after changing `.env`

---

## Alternative: Run via Python API

If UI issues persist, you can run directly via Python:

```python
# In Python shell with venv activated
from moonshot.integrations.cli.benchmark.runner import Runner

# Configure runner
runner = Runner(
    cookbooks=["enterprise_support_engineer"],
    endpoints=["openai-gpt"],
    num_of_prompts=1010,
    random_seed=42,
    system_prompt="You are a professional customer support engineer.",
    runner_processing_module="benchmarking",
    result_processing_module="benchmarking-result"
)

# Run evaluation
runner.run()
```

---

## Viewing Results

After evaluation completes:

1. **In UI**: Navigate to "Results" or "Reports" section
2. **Via Files**: Check `reports/enterprise_support_engineer/`
3. **Via API**: 
   ```bash
   curl http://127.0.0.1:5000/api/v1/results
   ```

---

## Support

If issues persist:
1. Check moonshot logs: `moonshot.log` and `moonshot-web.log`
2. Verify all components with: `ls -la moonshot-data/{cookbooks,recipes,datasets}/enterprise*`
3. Restart with clean cache: `rm -rf ~/.moonshot/cache`

---

**Last Updated**: 2025-10-22  
**Moonshot Version**: 0.7.3  
**Python Version**: 3.11.12
