+++
created_at = 2025-12-24T12:26:01+02:00
tags = "today project flyio-demo"
+++

# flyio-demo
Learn how to deploy FastMCP to flyio: Git-OPS and API-OPS

test001

* Reuse the same ssl certificate configuration
* Build the artifacts semi-functionally.  Use hashs to skip work that can be skipped.
* Use buildah instead of Docker.
* Git commit SHA in image name ==> image-sha.

* Run a simple server -- static html
* Add domain, ssl
* Run a fastmcp server
  - add static pages: / and /static
  - test it with z mcp_ls
  - test it with claude code
* Learn about scaling and test it.
* Try authentication? -- later


1. The git commit SHA looks good -- but may not be correct: If you change the
   code without committing, you still get the old git commit SHA.  If we can
   get an SHA of the current git tree that will be equal to the git commit SHA,
   then this would be perfect.
2. In both of your two options, the function returns only after the image has
   been built (either previously or just now).  Once we have the image name in
   a variable, there is a guarantee hat this name is usable for the next step.
3. We want to research all three directions and make an informed decision based on:
   * Simplicity/complexity
   * Whether the solution officially aims the kind of guarantees that we need
     so we can trust the semi-functional results.
4. Research all these three questions.
5. All three (the last one should be researched but may be optional).

I tend to buildah because of the same suspicion.  I want you to research it for
an informed decision.
