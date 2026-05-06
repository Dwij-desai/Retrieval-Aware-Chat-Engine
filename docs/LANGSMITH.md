# Step-3: LangSmith Tracing & Observability

## Overview
LangSmith is a unified developer platform for building, testing, and monitoring LLM applications. It automatically traces every step of your RAG pipeline:
- What documents were retrieved?
- What prompt was sent to the LLM?
- How long did each step take?
- What was the output?

## Why LangSmith for MLOps

### The Problem Without Observability
User reports: "Your chatbot gave me the wrong answer."  
Without tracing, you can only guess:
- Was the retrieval wrong?
- Was the prompt unclear?
- Did the LLM hallucinate?
- Was there a latency timeout?

### The Solution With LangSmith
You see the **exact trace** of every call:
1. Retrieval: "Retrieved 3 chunks, similarity scores [0.87, 0.76, 0.62]"
2. LLM Call: "Sent 450 tokens, got 180 token response in 320ms"
3. Output: "Generated answer: ..."

## Setup (5 minutes)

### Step 1: Create Account
Go to https://smith.langchain.com and sign up (free tier available)

### Step 2: Get API Key
1. Click "Settings" (gear icon)
2. Copy your API key
3. Treat it like a password - never commit to git!

### Step 3: Set Environment Variable
```bash
export LANGCHAIN_API_KEY=your_api_key_here
```

Or add to `.env`:
```env
LANGCHAIN_API_KEY=your_api_key_here
```

### Step 4: That's It!
The code auto-enables tracing. All RAG operations are now traced.

```python
from backend.rag_engine import ask

# This is automatically traced and visible in LangSmith dashboard
answer = ask("What is this system?")
```

## Dashboard Overview

### Project View
- **Runs**: Every RAG query shows up here
- **Performance**: See latency, token usage, costs
- **Errors**: Failed runs highlighted

### Trace Details
For each run, inspect:
- **Input**: The question and context
- **Chain Steps**: Each component (retrieval, LLM, parsing)
- **Output**: Generated answer
- **Metrics**: Latency, token count, cost

### Example Trace
```
RAG Query (main chain)
├── Retrieval
│   ├── Vector Search: 45ms, retrieved 3 docs
│   └── Similarity Scores: [0.92, 0.78, 0.65]
├── LLM Call
│   ├── Model: groq
│   ├── Tokens In: 450
│   ├── Tokens Out: 180
│   └── Latency: 320ms
└── Output: "The system is a RAG chatbot..."
```

## Use Cases

### 1. Debugging Failed Queries
User: "I asked about pricing but got product info"

In LangSmith:
- See retrieved chunks - was retrieval wrong?
- See prompt - was it ambiguous?
- See LLM response - was there hallucination?

### 2. Performance Monitoring
```
Week 1: avg latency 450ms, cost $0.023/query
Week 2: avg latency 680ms, cost $0.018/query
```

Investigate: Why slower despite lower cost? (Different model?)

### 3. A/B Testing
Compare two retrieval strategies:
- Strategy A: avg latency 400ms, 85% user satisfaction
- Strategy B: avg latency 300ms, 87% user satisfaction

→ Strategy B wins!

### 4. Cost Optimization
See which queries use most tokens:
```
Query: "Give me all features"
- Tokens: 2,400
- Cost: $0.048
```

Consider: Should we chunk differently? Use different model?

## Advanced Features

### Custom Metadata
Tag runs with additional context:

```python
from backend.rag_engine import ask
from langsmith import Client

client = Client()
client.create_run(
    name="RAG Query",
    run_type="chain",
    metadata={
        "user_id": "user_123",
        "session_id": "session_abc",
        "user_tier": "premium",
        "query_category": "pricing",
    }
)
```

### Datasets for Testing
Create a dataset of test queries in LangSmith, then evaluate:

```python
from langsmith import Client

client = Client()
dataset = client.read_dataset(name="test_queries")

for example in dataset.examples:
    result = ask(example.inputs["question"])
    # LangSmith auto-compares to ground truth
```

### Feedback Loop
Log user feedback:

```python
client.create_feedback(
    run_id="run_123",
    key="user_satisfaction",
    score=5.0  # 1-5 stars
)
```

Then analyze: "Queries with low satisfaction tend to have [X property]"

## Integration with CI/CD

### GitHub Actions Example
```yaml
name: Test RAG Quality
on: [pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run RAG Evaluation
        env:
          LANGCHAIN_API_KEY: ${{ secrets.LANGCHAIN_API_KEY }}
        run: |
          python backend/evaluation.py
          # Traces automatically logged to LangSmith
          
      - name: Check Performance Gate
        run: |
          # Get latest runs from LangSmith
          python -c "
          from langsmith import Client
          client = Client()
          runs = client.list_runs(project_name='ai-saas-chatbot', limit=10)
          avg_latency = sum(r.latency_ms for r in runs) / len(runs)
          assert avg_latency < 500, f'Latency too high: {avg_latency}ms'
          "
```

## Comparison: With vs Without LangSmith

| Question | Without LangSmith | With LangSmith |
|----------|---|---|
| What was retrieved? | Check logs manually | See in trace |
| How long did it take? | Add print statements | Automatic timing |
| Did it fail? Why? | Read error message | See exact step that failed |
| Which model was used? | Check config | See in run metadata |
| How many tokens? | Can't see | Automatic tracking |
| User impact? | No feedback loop | Collect ratings |

## Troubleshooting

### Q: "API key not working"
```bash
export LANGCHAIN_API_KEY=correct_key
python -c "from langsmith import Client; Client()" # Should work
```

### Q: "Runs not appearing in dashboard"
Check:
- API key is correct: `echo $LANGCHAIN_API_KEY`
- Project name matches: `LANGCHAIN_PROJECT=ai-saas-chatbot`
- Internet connection available

### Q: "Privacy concern - is my data safe?"
- LangSmith is owned by LangChain (trusted by many enterprises)
- You control data retention
- Can use self-hosted option for on-prem deployment

## Cost Considerations
- **Free tier**: 100 runs/month, 7-day retention
- **Starter**: $39/month, unlimited runs
- **Tracing is fast**: <1ms overhead per run

## Next Steps

### Immediate
1. ✅ Enable tracing with `export LANGCHAIN_API_KEY=...`
2. ✅ Run your RAG system normally
3. ✅ Visit dashboard to see traces

### Integration
1. Add LangSmith API calls to CI/CD
2. Set up alerts for performance regressions
3. Create datasets for continuous testing

### Monitoring
1. Set up recurring evaluation schedule
2. Track metrics over time
3. Correlate with deployment events

## File Structure
```
backend/
  └── observability.py      # LangSmith integration
  └── rag_engine.py         # Auto-traces all RAG calls
docs/
  └── LANGSMITH.md          # This guide
```

## References
- [LangSmith Docs](https://docs.smith.langchain.com)
- [LangChain Integration Guide](https://python.langchain.com/docs/integrations/callbacks/langsmith)
- [Best Practices](https://docs.smith.langchain.com/tracing-best-practices)

## Progress
- ✅ Step-2: Ragas Evaluation
- ✅ Step-3: LangSmith Tracing
- ⏳ Step-4: Automate Ingestion
- ⏳ Step-5: Expand Tests
