# Take-Home Assessment

## Context
Powerfleet builds AI software that helps users:
- answer technical and troubleshooting questions
- understand fleet and asset data
- do so reliably, with clear limits and measurable quality

This exercise simulates a small but realistic slice of that work.

## Time Expectation
Please spend no more than 4 to 6 hours on this exercise.

## Scenario
You are asked to design and implement a minimal production-minded AI assistant for a fleet and asset management environment.

The assistant must support two classes of requests:

1. Technical support and troubleshooting questions
Examples:
- Why is device model PX-200 not reporting trips?
- What does error code E104 mean?
- How should I troubleshoot repeated ignition anomalies?

2. Data understanding questions
Examples:
- Which 5 assets had the highest idle time yesterday?
- Why did asset A104 trigger a battery alert three times this week?
- Summarize unusual refrigerated temperature behavior in the North region.

## Input Material
You have been given:
- a small documentation corpus in `input/docs/`
- a small structured dataset in `input/data/`
- a schema and caveats file in `input/schema.md`
- a seed question list in `input/questions_seed.csv`

## Your Task
Build a minimal system that can handle both classes of requests and demonstrate sound engineering and evaluation judgment.

Your solution should:
- answer documentation and troubleshooting questions using grounded retrieval or another defensible approach
- answer data questions using structured reasoning over the provided data
- ask a clarifying question when the request is underspecified
- avoid fabricating answers when evidence is weak, conflicting, or insufficient
- provide concise evidence, citations, or intermediate reasoning artifacts that justify the answer
- include a lightweight but meaningful evaluation approach
- surface key operational considerations for a production version

You may choose the architecture and tools.

Examples of acceptable approaches:
- retrieval plus structured query execution
- RAG plus SQL or pandas
- agentic workflow with tool routing
- non-agentic orchestration, if you believe it is the better choice

We care more about the quality of your decisions than about framework sophistication.

## Constraints
- Keep the solution focused and small.
- Favor the simplest design that works.
- You do not need a polished UI.
- A CLI, notebook, or small API is sufficient.
- Optimize for correctness, judgment, and clarity rather than breadth.

## AI Tool Usage Policy
You may use AI tools during this exercise, but you must disclose how you used them.

Please include a completed `AI_USAGE.md` based on the provided template.

Your submission will be evaluated on your judgment, your transparency, and the quality of the final result. We are not testing whether you can avoid AI. We are testing whether you can use it responsibly while still demonstrating independent technical thinking.

## Required Deliverables
Please submit:

1. Runnable code
A small repository containing your implementation.

2. README
Include:
- setup and run instructions
- architecture overview
- why you chose this design
- major trade-offs
- known limitations
- what you would do next with another 1 to 2 days

3. Evaluation note
A short document describing:
- how you evaluated the system
- what success means for this task
- failure modes you observed
- how you would prevent regressions

4. Test set
Include:
- results on the provided seed questions
- at least 5 additional adversarial, ambiguous, or edge-case questions you designed yourself
- a short explanation of why each added case matters

5. Short walkthrough
Provide either:
- a 5 to 8 minute video walkthrough, or
- a written equivalent covering the same points

Please explain:
- how the system works
- one important design trade-off
- one failure case
- one change you would make first in production

6. AI usage disclosure
Complete the provided template.

## What We Will Evaluate
We will score on the following dimensions:
- problem framing and technical judgment
- engineering quality
- reliability and groundedness
- evaluation maturity
- product sense
- communication

## Important
We do not expect a perfect system. We expect a senior-quality approach:
- clear scoping
- good trade-offs
- sound engineering
- honest discussion of limitations

A small, well-reasoned solution is stronger than a broad but shallow one.
