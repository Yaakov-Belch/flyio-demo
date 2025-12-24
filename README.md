+++
created_at = 2025-12-24T12:26:01+02:00
tags = "today project flyio-demo"
+++

# flyio-demo
Learn how to deploy FastMCP to flyio: Git-OPS and API-OPS

1. Always use the name "code_insight" or "code-insight" as appropriate.
2. Check `cat .git/config`: url = git@github.com:Yaakov-Belch/flyio-demo.git -- This
   repository is already on Github.  It will be pushed as we make progress.  In fact, I
   push after every successful learning step.  This may cause many github actions to
   run.
   ==> Let's activate the github action when `fly launch` has already been tested.
       - That means: At the right time you just create the workflow file.
   ==> Let's then test that the auto-deployment works with one measurable change.
   ==> Let's then de-activate the github action to not cause extra work/conflicts.
       (This is a learning exercise, not a mission-critical project).
3. Yes: First `fly launch`, then GitHub Actions.  Then only `fly launch`.
4. We always use `uv` and never use `perl` or `pip` directly.
   * In fact, I would prefer using `buildah` as an experiment in addition to
     `docker build`.  We will dig deeper into that in a later exercise.
5. Follow the Fly.io example with PORT=8080 and test that FastMCP or our scripts pick
   up that number.
6. The Lesson starts with an executive summary, followed by a table of contents, followed
   by the entire process with lessons learned, followed by concepts learned and
   references.
7. 302

8. Correct on all your recommendations.
9. Keep things as they are.  This is another, orthogonal learning experience.
10. Correct.
11. Comment out.
12. --yes
Any more questions?
----
fly.io APIs
gitops apiops

* Run a simple server -- static html
* Add domain, ssl
* Run a fastmcp server
  - add static pages: / and /static
  - test it with z mcp_ls
  - test it with claude code
* Learn about scaling and test it.
* Try authentication? -- later

