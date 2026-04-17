"""Evaluation runner — batch-executes all seed + adversarial questions and
produces a structured evaluation report.

Scoring criteria (per response):
  1. Groundedness  — is every claim supported by evidence?
  2. Correctness   — is the factual answer right?
  3. Calibration   — does confidence match evidence quality?
  4. Completeness  — does the response address the full question?
  5. Honesty       — does it acknowledge limitations?

Usage:
    python -m eval.run_eval
    python -m eval.run_eval --output eval/full_results.json
"""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path

import click
from openai import OpenAI
from rich.console import Console
from rich.table import Table

from src.config import settings
from src.router import Router
from src.models import AssistantResponse

console = Console()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SEED_PATH = PROJECT_ROOT / "input" / "questions_seed.csv"
ADVERSARIAL_PATH = PROJECT_ROOT / "eval" / "adversarial_questions.csv"


def _load_questions(path: Path) -> list[dict]:
    """Load questions from a CSV file."""
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _response_to_dict(resp: AssistantResponse) -> dict:
    return {
        "answer": resp.answer,
        "confidence": resp.confidence.value,
        "is_clarification": resp.is_clarification,
        "clarification_question": resp.clarification_question,
        "sources_used": resp.sources_used,
        "caveats": resp.caveats,
        "evidence_count": len(resp.evidence),
        "artifact_count": len(resp.reasoning_artifacts),
        "reasoning_artifacts": [a.model_dump() for a in resp.reasoning_artifacts],
    }


def _auto_score(question_row: dict, resp: AssistantResponse) -> dict:
    """Basic automated scoring heuristics — not a replacement for human review."""
    scores: dict[str, str] = {}
    category = question_row.get("category", "")

    # 1. Did the system provide evidence?
    scores["has_evidence"] = "yes" if resp.evidence or resp.sources_used else "no"

    # 2. Did it set appropriate confidence?
    scores["confidence_set"] = resp.confidence.value

    # 3. Clarification for ambiguous questions?
    if category == "ambiguous":
        scores["asked_clarification"] = "yes" if resp.is_clarification else "NO — missed"
    else:
        scores["asked_clarification"] = "n/a"

    # 4. Any caveats acknowledged?
    scores["has_caveats"] = "yes" if resp.caveats else "no"

    # 5. For adversarial questions — did it avoid fabrication?
    if category == "adversarial":
        answer_lower = resp.answer.lower()
        refusal_phrases = [
            "don't have", "no information", "not available", "cannot",
            "insufficient", "no data", "not found", "doesn't exist",
            "do not have", "unable", "no column", "not present",
            "superseded", "legacy", "current definition",
        ]
        scores["avoided_fabrication"] = (
            "likely" if any(p in answer_lower for p in refusal_phrases)
            else "CHECK MANUALLY"
        )

    return scores


@click.command()
@click.option("--output", "-o", default="eval/full_results.json", help="Output JSON path")
@click.option("--seed-only", is_flag=True, help="Only run seed questions")
@click.option("--adversarial-only", is_flag=True, help="Only run adversarial questions")
def main(output: str, seed_only: bool, adversarial_only: bool):
    """Run the evaluation suite."""
    # Collect questions
    questions: list[dict] = []
    if not adversarial_only:
        questions.extend(_load_questions(SEED_PATH))
    if not seed_only and ADVERSARIAL_PATH.exists():
        questions.extend(_load_questions(ADVERSARIAL_PATH))

    console.print(f"[bold]Running evaluation on {len(questions)} questions…[/]\n")

    client = OpenAI(api_key=settings.openai_api_key)
    router = Router(openai_client=client)

    results: list[dict] = []
    summary_table = Table(title="Evaluation Results")
    summary_table.add_column("ID", style="cyan")
    summary_table.add_column("Category")
    summary_table.add_column("Confidence")
    summary_table.add_column("Evidence")
    summary_table.add_column("Caveats")
    summary_table.add_column("Notes")

    for row in questions:
        qid = row.get("question_id", "?")
        category = row.get("category", "")
        question = row.get("question", "")

        console.print(f"  [{qid}] {question}")

        start = time.time()
        resp = router.ask(question)
        elapsed = round(time.time() - start, 2)

        scores = _auto_score(row, resp)

        result = {
            "question_id": qid,
            "category": category,
            "question": question,
            "elapsed_seconds": elapsed,
            "auto_scores": scores,
            **_response_to_dict(resp),
        }
        results.append(result)

        # Add to summary table
        notes = []
        if scores.get("asked_clarification") == "NO — missed":
            notes.append("⚠️ missed clarification")
        if scores.get("avoided_fabrication") == "CHECK MANUALLY":
            notes.append("🔍 check fabrication")

        summary_table.add_row(
            qid,
            category,
            resp.confidence.value,
            scores.get("has_evidence", "?"),
            scores.get("has_caveats", "?"),
            " | ".join(notes) if notes else "✅",
        )

    console.print()
    console.print(summary_table)

    # Save
    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    console.print(f"\n[bold green]Full results saved to {out_path}[/]")

    # Quick stats
    total = len(results)
    with_evidence = sum(1 for r in results if r["auto_scores"].get("has_evidence") == "yes")
    with_caveats = sum(1 for r in results if r["auto_scores"].get("has_caveats") == "yes")
    console.print(f"\n📊 {with_evidence}/{total} responses included evidence")
    console.print(f"📊 {with_caveats}/{total} responses included caveats")


if __name__ == "__main__":
    main()
