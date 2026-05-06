"""
RAG Evaluation Module using Ragas

Provides quantitative metrics for RAG pipeline performance:
- Faithfulness: Is the answer faithful to the retrieved context?
- Relevance: Is the retrieved context relevant to the question?
- Precision: How many retrieved chunks are actually relevant?
- F1 Score: Harmonic mean of precision and recall

Golden dataset format:
{
    "questions": ["Q1", "Q2", ...],
    "contexts": [["context1", "context2"], ...],
    "ground_truths": ["Expected answer 1", "Expected answer 2", ...]
}
"""

import json
import logging
from typing import Optional
from pathlib import Path

import numpy as np
from ragas import evaluate
from ragas.metrics import (
    answer_faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from datasets import Dataset

logger = logging.getLogger(__name__)


class RagasEvaluator:
    """Evaluate RAG pipeline performance using Ragas metrics."""

    def __init__(self, llm_provider: str = "groq"):
        """
        Initialize Ragas evaluator.
        
        Args:
            llm_provider: "groq" or "gemini" - used for metric evaluation
        """
        self.llm_provider = llm_provider
        logger.info(f"Initialized RagasEvaluator with provider: {llm_provider}")

    def load_golden_dataset(self, path: str) -> dict:
        """
        Load golden dataset from JSON file.
        
        Expected format:
        {
            "questions": ["Q1", "Q2"],
            "contexts": [["c1", "c2"], ["c3"]],
            "ground_truths": ["A1", "A2"]
        }
        """
        try:
            with open(path, "r") as f:
                dataset = json.load(f)
            logger.info(f"Loaded golden dataset from {path}")
            return dataset
        except FileNotFoundError:
            logger.error(f"Golden dataset not found at {path}")
            return None

    def create_eval_dataset(
        self,
        questions: list,
        contexts: list,
        answers: list,
        ground_truths: list,
    ) -> Dataset:
        """
        Create Ragas-compatible dataset for evaluation.
        
        Args:
            questions: List of questions
            contexts: List of context lists (each question may have multiple contexts)
            answers: List of model answers
            ground_truths: List of expected answers
        
        Returns:
            HuggingFace Dataset compatible with Ragas
        """
        data = {
            "question": questions,
            "contexts": contexts,
            "answer": answers,
            "ground_truth": ground_truths,
        }
        return Dataset.from_dict(data)

    def evaluate(
        self,
        questions: list,
        contexts: list,
        answers: list,
        ground_truths: list,
    ) -> dict:
        """
        Evaluate RAG pipeline on questions and answers.
        
        Returns dict with metrics:
        - faithfulness (0-1): Confidence in factual correctness
        - answer_relevancy (0-1): Answer relevance to question
        - context_precision (0-1): Fraction of relevant retrieved contexts
        - context_recall (0-1): Coverage of required information
        """
        try:
            # Create evaluation dataset
            eval_dataset = self.create_eval_dataset(
                questions=questions,
                contexts=contexts,
                answers=answers,
                ground_truths=ground_truths,
            )

            # Run Ragas evaluation
            logger.info("Running Ragas evaluation...")
            results = evaluate(
                eval_dataset,
                metrics=[
                    answer_faithfulness,
                    answer_relevancy,
                    context_precision,
                    context_recall,
                ],
            )

            # Convert to dict and calculate aggregate metrics
            metrics_dict = {
                "faithfulness": float(results["answer_faithfulness"]),
                "answer_relevancy": float(results["answer_relevancy"]),
                "context_precision": float(results["context_precision"]),
                "context_recall": float(results["context_recall"]),
            }

            # Calculate harmonic mean (F1-like score)
            metrics_dict["aggregate_score"] = float(
                np.mean([v for v in metrics_dict.values()])
            )

            logger.info(f"Evaluation complete: {metrics_dict}")
            return metrics_dict

        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            raise

    def generate_report(
        self,
        metrics: dict,
        output_path: str = "evaluation_report.json",
    ) -> None:
        """
        Generate and save evaluation report.
        
        Args:
            metrics: Dictionary of metrics from evaluate()
            output_path: Where to save the report JSON
        """
        report = {
            "timestamp": str(Path(output_path).stat().st_mtime),
            "metrics": metrics,
            "interpretation": {
                "faithfulness": "Higher is better (0-1). How much the answer is grounded in context.",
                "answer_relevancy": "Higher is better (0-1). How relevant the answer is to the question.",
                "context_precision": "Higher is better (0-1). What fraction of retrieved context is relevant.",
                "context_recall": "Higher is better (0-1). What fraction of required info was retrieved.",
                "aggregate_score": "Mean of all metrics (0-1). Overall pipeline quality.",
            },
            "thresholds": {
                "good": 0.7,
                "acceptable": 0.5,
                "needs_improvement": "<0.5",
            },
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Evaluation report saved to {output_path}")
        return report


def create_sample_golden_dataset() -> dict:
    """Create a sample golden dataset for testing."""
    return {
        "questions": [
            "What is the primary use case of this chatbot?",
            "How is the vector database structured?",
            "What LLM providers are supported?",
        ],
        "contexts": [
            ["This chatbot is a RAG system designed for AI SaaS applications."],
            ["ChromaDB is used as the local persistent vector database."],
            ["Groq and Google Gemini are the supported LLM providers."],
        ],
        "ground_truths": [
            "This chatbot is a Retrieval-Augmented Generation (RAG) system for AI SaaS applications",
            "The vector database is ChromaDB, which provides local persistent storage",
            "The system supports both Groq (ultra-fast) and Google Gemini as LLM providers",
        ],
    }


# Example usage for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    evaluator = RagasEvaluator(llm_provider="groq")

    # Create sample dataset
    dataset = create_sample_golden_dataset()

    # Sample answers from the RAG system
    sample_answers = [
        "This is a RAG-based chatbot for enterprise applications.",
        "The system uses ChromaDB for vector storage.",
        "Both Groq and Gemini are available.",
    ]

    try:
        # Run evaluation
        metrics = evaluator.evaluate(
            questions=dataset["questions"],
            contexts=dataset["contexts"],
            answers=sample_answers,
            ground_truths=dataset["ground_truths"],
        )

        print("\n📊 Evaluation Results:")
        for key, value in metrics.items():
            print(f"  {key}: {value:.3f}")

        # Generate report
        evaluator.generate_report(metrics, "evaluation_report.json")

    except Exception as e:
        print(f"Error during evaluation: {e}")
