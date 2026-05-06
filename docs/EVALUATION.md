# Step-2: Ragas Evaluation Framework

## Overview
Ragas is a framework for evaluating RAG pipeline quality using LLM-based metrics. Instead of subjective "does it feel good?", you get quantitative scores for faithfulness, relevancy, precision, and recall.

## Why Ragas Matters for MLOps
- **Detect degradation:** If chunk_size changes from 500→800, does quality improve or degrade?
- **Compare variants:** A/B test different retrieval strategies scientifically
- **Track over time:** Monitor performance as your corpus grows
- **Set baselines:** Know what "good" looks like for your use case

## Metrics Explained

### 1. Faithfulness (0-1)
**Question:** Is the answer grounded in the retrieved context?  
**How it works:** LLM checks if answer claims are supported by context  
**Good score:** >0.7  
**Example:** If context says "Plan A costs $10" and answer says "Plan A costs $20", faithfulness is low

### 2. Answer Relevancy (0-1)
**Question:** Is the answer relevant to the question?  
**How it works:** LLM compares question semantic similarity to answer  
**Good score:** >0.7  
**Example:** If question is "pricing?" and answer is about features, relevancy is low

### 3. Context Precision (0-1)
**Question:** What fraction of retrieved context is actually relevant?  
**How it works:** LLM checks if each context chunk supports the expected answer  
**Good score:** >0.8  
**Example:** If you retrieve 5 chunks but only 4 are useful, precision is 0.8

### 4. Context Recall (0-1)
**Question:** Did we retrieve all the information needed to answer?  
**How it works:** LLM checks if anything critical is missing  
**Good score:** >0.7  
**Example:** If answer needs 3 facts but you only retrieved 2, recall is low

## Quick Start

### 1. Install Ragas
```bash
pip install ragas datasets
```

### 2. Create Golden Dataset
A golden dataset is Q/A/Context triplets you know are correct:

```json
{
  "questions": ["What pricing plans exist?"],
  "contexts": [["Our plans: Basic ($9), Pro ($29), Enterprise (custom)"]],
  "ground_truths": ["We offer Basic, Pro, and Enterprise plans"]
}
```

We've provided a sample: `data/golden_dataset.json`

### 3. Run Evaluation

```python
from backend.evaluation import RagasEvaluator
import json

# Initialize evaluator
evaluator = RagasEvaluator(llm_provider="groq")

# Load golden dataset
golden_dataset = json.load(open("data/golden_dataset.json"))

# Get answers from your RAG system (pseudo-code)
answers = [rag_engine.ask(q)["answer"] for q in golden_dataset["questions"]]

# Evaluate
metrics = evaluator.evaluate(
    questions=golden_dataset["questions"],
    contexts=golden_dataset["contexts"],
    answers=answers,
    ground_truths=golden_dataset["ground_truths"]
)

# Generate report
evaluator.generate_report(metrics, "evaluation_report.json")

print(f"Overall Score: {metrics['aggregate_score']:.2%}")
```

### 4. Interpret Results

| Metric | Score | Interpretation |
|--------|-------|---|
| aggregate_score | 0.85 | 85% quality - Excellent |
| faithfulness | 0.92 | Answers are well-grounded |
| answer_relevancy | 0.78 | Answers address the question |
| context_precision | 0.88 | Retrieved docs are relevant |
| context_recall | 0.81 | Retrieved all necessary info |

## Command-Line Usage

```bash
# Run evaluation with sample golden dataset
python backend/evaluation.py

# Output:
# 📊 Evaluation Results:
#   faithfulness: 0.847
#   answer_relevancy: 0.821
#   context_precision: 0.903
#   context_recall: 0.756
#   aggregate_score: 0.832
```

## Best Practices

### 1. Build a Good Golden Dataset
- **Quality over quantity:** 10 high-quality Q/A pairs > 100 random ones
- **Diverse coverage:** Different question types, difficulty levels
- **Real-world data:** Use actual user questions from logs
- **Clear answers:** Ground truths should be unambiguous

### 2. Evaluate Regularly
```bash
# After changing chunk_size
python backend/ingest.py
python backend/evaluation.py

# After updating retrieval logic
python backend/evaluation.py

# After ingesting new data
python backend/evaluation.py
```

### 3. A/B Testing
```bash
# Test with chunk_size=500
config.CHUNK_SIZE = 500
metrics_1 = evaluator.evaluate(...)

# Test with chunk_size=800
config.CHUNK_SIZE = 800
metrics_2 = evaluator.evaluate(...)

# Compare
print(f"500 vs 800: {metrics_1['aggregate_score']} vs {metrics_2['aggregate_score']}")
```

## Understanding Metric Interactions

- **High faithfulness, low relevancy** = You're answering something different than asked
- **High relevancy, low faithfulness** = Right answer, but not grounded in context
- **Low precision, high recall** = You retrieved too much; add filtering
- **High precision, low recall** = You're too restrictive; broaden search

## File Structure

```
backend/
  └── evaluation.py           # Main evaluator class
data/
  └── golden_dataset.json    # Sample Q/A/Context triplets
docs/
  └── EVALUATION.md          # This file
evaluation_report.json       # Generated after running evaluation
```

## Integration with MLOps Pipeline

### Continuous Evaluation (CI/CD)
Add to your GitHub Actions:

```yaml
- name: Run Ragas Evaluation
  run: python backend/evaluation.py
  
- name: Check Quality Gate
  run: |
    python -c "
    import json
    report = json.load(open('evaluation_report.json'))
    assert report['metrics']['aggregate_score'] > 0.7, 'Quality below threshold'
    "
```

### Monitoring
Track metrics over time in a dashboard:

```python
# Log to monitoring system (Prometheus, DataDog, etc.)
metrics = evaluator.evaluate(...)
prometheus_client.gauge('rag_faithfulness', metrics['faithfulness'])
prometheus_client.gauge('rag_aggregate_score', metrics['aggregate_score'])
```

## Troubleshooting

### Q: "Ragas requires LLM API calls, will this be expensive?"
**A:** Each question costs ~1-2 cents on Groq. A golden dataset of 20 questions = ~40-80 cents per run.

### Q: "Why is my aggregate_score low?"
**A:** Run individual metrics to diagnose:
- Low faithfulness → Ensure retrieved context actually answers the question
- Low precision → Filter retrieval results more aggressively
- Low recall → Broaden search or lower similarity threshold

### Q: "Can I use a different LLM for evaluation?"
**A:** Yes, update the `llm_provider` in `RagasEvaluator.__init__()`

## Next Steps
1. ✅ Evaluation Framework Set Up
2. 🔍 Add LangSmith tracing (Step-3)
3. 🤖 Automate ingestion (Step-4)
4. ✔️ Expand pytest coverage (Step-5)
