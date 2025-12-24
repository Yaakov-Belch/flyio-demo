# Fly.io demo: The Goal

I want to learn how to deploy FastMCP servers with Fly.io.

With "Git-OPS" and with "API-OPS":
* Git-OPS is triggered by committing a git repository -- and can also be executed
  locally.
* Semifunctional API-OPS is initially more low-level: Create artifacts programmatically,
  one-by-one.  But because functions can be composed, we can build a higher-level toolbox.

This is a sequence of exercises --- from simple/foundational to more complex, high-level
goals.  Even more important than reaching the technical goal is to document the learning
as good lessons.

## Rules
* We always use `uv` and never use `python` or `pip` directly.
* When starting a new exercise read the executive summary and the table of content
  at the top of each previous lessons present in `Lessons/` -- and, as needed, read
  more of the lessons learned.  The exercises build each on top of the lessons before.
* For every exercise, find the appropriate documentation on: https://fly.io/docs/
* Also, check for code samples via context7.
* Once we understand the problem and solution approaches, ask any open questions before
  implementation and documentation.
* Once we understand the problem and the solution, write one lesson for each exercise.
* In the lesson, link to the best documentation sources (usually on https://fly.io/docs/).
* The lessons are written to files `Lesson/<number>-<title>.md`.
* Each lesson consists of:
  - Executive summary
  - Complete table of contents
  - Step-by-step walkthrough with all lessons learned
  - Troubleshooting section documenting all issues encountered
  - Comparison table: Manual vs. GitOps deployment
  - Key concepts, refereces (URLS) and additional resources
  - DO NOT MAKE PLANS FOR THE FOLLOWING LESSONS!
* You cannot run OPS commands yourself (git commit/push; fly).
  - Tell me what to do and I report back the output.
* NOTE: Please use the URL with the path /info for checks -- the path / returns an empty
  response with curl (it's a redirect) and the path `/static/` returns a long HTML
  document. `info` is best for testing.

