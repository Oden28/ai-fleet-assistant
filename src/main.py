"""CLI entrypoint for the Powerfleet AI Fleet Assistant.

Supports:
  - Interactive mode: ask questions one at a time
  - Batch mode: run all seed questions and save results
  - Single question mode: answer one question and exit
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import click
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from src.config import settings
from src.router import Router
from src.models import AssistantResponse

console = Console()


def _get_openai_client() -> OpenAI:
    """Initialise the OpenAI client."""
    if not settings.openai_api_key:
        console.print(
            "[bold red]Error:[/] OPENAI_API_KEY not set. "
            "Copy .env.example to .env and add your key.",
            style="red",
        )
        sys.exit(1)
    return OpenAI(api_key=settings.openai_api_key)


def _display_response(resp: AssistantResponse, show_artifacts: bool = False) -> None:
    """Pretty-print an assistant response."""
    if resp.is_clarification:
        console.print(Panel(
            resp.answer,
            title="🔍 Clarification Needed",
            border_style="yellow",
        ))
        return

    # Main answer
    console.print(Panel(
        Markdown(resp.answer),
        title=f"💡 Answer  [confidence: {resp.confidence.value}]",
        border_style="green" if resp.confidence.value == "high" else
                     "yellow" if resp.confidence.value == "medium" else "red",
    ))

    # Sources
    if resp.sources_used:
        console.print(f"  📚 Sources: {', '.join(resp.sources_used)}")

    # Caveats
    if resp.caveats:
        for caveat in resp.caveats:
            console.print(f"  ⚠️  {caveat}", style="dim")

    # Reasoning artifacts (optional verbose output)
    if show_artifacts and resp.reasoning_artifacts:
        for art in resp.reasoning_artifacts:
            console.print(Panel(
                art.content[:500] + ("…" if len(art.content) > 500 else ""),
                title=f"🔧 {art.artifact_type}",
                border_style="dim",
            ))

    console.print()


def _response_to_dict(resp: AssistantResponse) -> dict:
    """Convert response to serialisable dict."""
    return {
        "answer": resp.answer,
        "confidence": resp.confidence.value,
        "is_clarification": resp.is_clarification,
        "clarification_question": resp.clarification_question,
        "sources_used": resp.sources_used,
        "caveats": resp.caveats,
        "evidence": [e.model_dump() for e in resp.evidence],
        "reasoning_artifacts": [a.model_dump() for a in resp.reasoning_artifacts],
    }


@click.group()
def cli():
    """Powerfleet AI Fleet Assistant — technical support & data analysis."""
    pass


@cli.command()
@click.option("--verbose", "-v", is_flag=True, help="Show reasoning artefacts")
def interactive(verbose: bool):
    """Start an interactive Q&A session."""
    console.print(Panel(
        "Welcome to the Powerfleet Fleet Assistant.\n"
        "Ask technical or data questions about your fleet.\n"
        "Type 'quit' or 'exit' to stop.",
        title="🚛 Fleet Assistant",
        border_style="blue",
    ))

    client = _get_openai_client()
    router = Router(openai_client=client)

    while True:
        try:
            question = console.input("\n[bold cyan]Question:[/] ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if question.lower() in ("quit", "exit", "q"):
            break
        if not question:
            continue

        with console.status("Thinking…"):
            resp = router.ask(question)

        _display_response(resp, show_artifacts=verbose)


@cli.command()
@click.argument("question")
@click.option("--verbose", "-v", is_flag=True, help="Show reasoning artefacts")
@click.option("--json-output", "-j", is_flag=True, help="Output raw JSON")
def ask(question: str, verbose: bool, json_output: bool):
    """Answer a single question."""
    client = _get_openai_client()
    router = Router(openai_client=client)

    resp = router.ask(question)

    if json_output:
        click.echo(json.dumps(_response_to_dict(resp), indent=2))
    else:
        _display_response(resp, show_artifacts=verbose)


@cli.command()
@click.option(
    "--output", "-o",
    type=click.Path(),
    default="eval/seed_results.json",
    help="Output path for results JSON",
)
@click.option("--questions", "-q", type=click.Path(exists=True), default=None)
def batch(output: str, questions: str | None):
    """Run all seed questions (or a custom CSV) and save results."""
    questions_path = Path(questions) if questions else settings.seed_questions_path

    # Read questions
    with open(questions_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    console.print(f"[bold]Running {len(rows)} questions from {questions_path.name}…[/]\n")

    client = _get_openai_client()
    router = Router(openai_client=client)

    results: list[dict] = []
    for row in rows:
        qid = row.get("question_id", "")
        category = row.get("category", "")
        question = row.get("question", "")

        console.print(f"[bold]{qid}[/] [{category}] {question}")

        with console.status("Thinking…"):
            resp = router.ask(question)

        _display_response(resp)

        results.append({
            "question_id": qid,
            "category": category,
            "question": question,
            **_response_to_dict(resp),
        })

    # Save results
    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    console.print(f"\n[bold green]Results saved to {out_path}[/]")


if __name__ == "__main__":
    cli()
