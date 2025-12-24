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

* For every exercise, find the appropriate documentation on: https://fly.io/docs/
* Also, check for code samples via context7.
* Once we understand the problem and the solution, write one lesson for each exercise.
* In the lesson, link to the best documentation sources (usually on https://fly.io/docs/).
* The lessons are written to files `Lesson/<number>-<title>.md`.
* You cannot run OPS commands yourself (git commit/push; fly).  Tell me what to do and I
  report back the output.
