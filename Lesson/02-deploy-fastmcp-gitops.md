# Lesson 02: Deploy FastMCP Server with GitOps on Fly.io

## Executive Summary

This lesson demonstrates how to deploy a custom FastMCP (Model Context Protocol) server to Fly.io using both manual deployment and automated GitOps workflows. You'll learn how to containerize a Python application with `uv`, deploy it to Fly.io's global infrastructure, configure custom domains with automatic SSL certificates, and set up continuous deployment via GitHub Actions.

**Key achievements:**
- Create a FastMCP server with custom HTTP routes for static file serving
- Build production Docker images using `uv` for fast dependency management
- Deploy applications to Fly.io with automatic HTTPS and high availability
- Configure custom domains with Let's Encrypt SSL certificates
- Implement GitOps workflows with GitHub Actions for automatic deployment
- Understand the difference between manual (`fly deploy`) and automated (Git push) deployment strategies

**Time to complete:** 2-3 hours

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Part 1: Understanding the FastMCP Application](#part-1-understanding-the-fastmcp-application)
   - Application Structure
   - FastMCP Routes and Features
   - Static File Serving
3. [Part 2: Creating the Project Structure](#part-2-creating-the-project-structure)
   - Package Organization
   - Dependency Management with pyproject.toml
4. [Part 3: Containerizing with Docker](#part-3-containerizing-with-docker)
   - Dockerfile Design
   - Using `uv` for Fast Builds
   - Docker Build Context and .dockerignore
5. [Part 4: Manual Deployment to Fly.io](#part-4-manual-deployment-to-flyio)
   - Fly.io Configuration (fly.toml)
   - Initial Deployment
   - Troubleshooting Build Issues
6. [Part 5: Custom Domain Configuration](#part-5-custom-domain-configuration)
   - Adding SSL Certificates
   - DNS Configuration
   - Certificate Verification
7. [Part 6: Setting Up GitOps with GitHub Actions](#part-6-setting-up-gitops-with-github-actions)
   - Creating the Workflow File
   - Configuring Secrets
   - Testing Auto-Deployment
8. [Key Concepts Learned](#key-concepts-learned)
9. [Additional Resources](#additional-resources)

---

## Prerequisites

- Completed [Lesson 01: Hello World on Fly.io](01-hello-world.md)
- `flyctl` installed and authenticated
- Python 3.14+ installed locally
- `uv` package manager installed
- A GitHub repository for your project
- (Optional) A custom domain for the custom domain exercises

---

## Part 1: Understanding the FastMCP Application

### What is FastMCP?

FastMCP is a Python framework for building Model Context Protocol (MCP) servers. MCP servers provide tools, prompts, and resources that AI assistants can use to enhance their capabilities. FastMCP makes it easy to create HTTP servers that can serve both MCP endpoints and traditional web content.

### Application Structure

Our application is organized as follows:

```
flyio-demo/
├── src/
│   └── flyio_demo/
│       ├── __init__.py
│       └── code_insight/
│           ├── __init__.py
│           ├── mcp_server.py          # Main FastMCP server
│           ├── add_numbers.py         # Example tool
│           └── static/
│               └── index.html         # Static web page
├── pyproject.toml                     # Python project configuration
├── Dockerfile                         # Container build instructions
├── fly.toml                           # Fly.io deployment configuration
└── .github/
    └── workflows/
        └── fly-deploy.yml             # GitHub Actions workflow
```

### FastMCP Routes and Features

Our `mcp_server.py` implements several features:

**1. MCP Tools:**
```python
@mcp.tool
def mirror_tool(text: str) -> str:
    """Mirror a text"""
    return text[::-1]

mcp.tool(add)  # Registered from add_numbers.py
```

**2. MCP Prompts:**
```python
@mcp.prompt
def hello() -> str:
    """A simple greeting prompt"""
    return "Hello world!"
```

**3. Custom HTTP Routes:**
```python
@mcp.custom_route("/info", methods=["GET"])
async def show_info(request: Request) -> PlainTextResponse:
    return PlainTextResponse("Health Ok! - Auto-deployed via GitHub Actions")

@mcp.custom_route("/", methods=["GET"])
async def root_redirect(request: Request) -> RedirectResponse:
    """Redirect root path to static pages"""
    return RedirectResponse(url="/static/", status_code=302)

@mcp.custom_route("/static/{filepath:path}", methods=["GET"])
async def serve_static(request: Request) -> FileResponse | HTMLResponse:
    """Serve static files from the static directory"""
    # Implementation includes security checks and path validation
```

**4. ASGI Application:**
```python
# Create ASGI application for production deployment
app = mcp.http_app()
```

This `app` object is what Uvicorn uses to run the server in production.

---

## Part 2: Creating the Project Structure

### Package Organization

The project follows Python packaging best practices with a `src/` layout:

- **`src/flyio_demo/`**: Top-level package matching the project name in `pyproject.toml`
- **`src/flyio_demo/code_insight/`**: The actual FastMCP server package
- **`src/flyio_demo/code_insight/static/`**: Static assets (HTML, CSS, images)

This structure allows `uv` to properly build and install the package during Docker builds.

### Dependency Management with pyproject.toml

```toml
[project]
name = "flyio-demo"
version = "0.1.0"
description = "Learn how to deploy FastMCP to flyio: Git-OPS and API-OPS"
readme = "README.md"
authors = [
    { name = "Yaakov Belch", email = "git-commit@yaakovnet.net" }
]
requires-python = ">=3.14"
dependencies = [
    "fastmcp>=2.13.3",
]

[build-system]
requires = ["uv_build>=0.9.11,<0.10.0"]
build-backend = "uv_build"
```

**Key points:**
- `name` must match the directory structure (`flyio-demo` → `src/flyio_demo/`)
- `readme = "README.md"` requires README.md to be present during builds
- `fastmcp>=2.13.3` includes all necessary dependencies (FastAPI, Starlette, Uvicorn)
- Using `uv_build` as the build backend for fast, modern builds

---

## Part 3: Containerizing with Docker

### Dockerfile Design

Our Dockerfile uses a multi-stage approach with `uv` for fast dependency installation:

```dockerfile
# Use Python 3.14 slim base image
FROM python:3.14-slim

# Install uv for fast package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files and source code
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install dependencies using uv (without lockfile, create virtual env)
RUN uv sync --no-dev

# Expose port (Fly.io uses PORT env variable, defaults to 8080)
ENV PORT=8080
EXPOSE 8080

# Run the FastMCP server with uvicorn
# The PORT environment variable will be set by Fly.io
CMD ["uv", "run", "uvicorn", "flyio_demo.code_insight.mcp_server:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Important lessons learned:**

1. **Copy source before `uv sync`**: The package needs to exist for `uv` to build it
2. **Include README.md**: Referenced in `pyproject.toml`, must be present
3. **Use `uv run` in CMD**: Ensures the virtual environment is activated
4. **Full module path**: `flyio_demo.code_insight.mcp_server:app` follows the package structure

### Build Optimization with .dockerignore

```
# Python
__pycache__/
*.py[cod]
.pytest_cache/

# Documentation
Lesson/
LICENSE

# Git
.git/
.gitignore

# Fly.io (generated during deployment)
fly.toml
.github/
```

**Note:** We exclude `README.md` from this list because it's referenced in `pyproject.toml` and needed for the build.

---

## Part 4: Manual Deployment to Fly.io

### Fly.io Configuration (fly.toml)

```toml
app = 'code-insight'
primary_region = 'ewr'

[build]

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = 'stop'
  auto_start_machines = true
  min_machines_running = 0
  processes = ['app']

[[vm]]
  memory = '1gb'
  cpu_kind = 'shared'
  cpus = 1
```

**Configuration breakdown:**
- **`internal_port = 8080`**: Must match the port Uvicorn listens on
- **`auto_stop_machines = 'stop'`**: Machines stop when idle to save costs
- **`auto_start_machines = true`**: Automatically wake up on incoming requests
- **`min_machines_running = 0`**: Scale to zero when not in use
- **`force_https = true`**: Automatic HTTP → HTTPS redirect

### Initial Deployment

```bash
fly launch --name code-insight --yes
```

**What happens:**
1. Fly.io detects the Dockerfile
2. Builds the Docker image using Depot (their remote builder)
3. Pushes the image to Fly.io's registry
4. Creates 2 machines for high availability
5. Allocates IPv4 (shared) and IPv6 (dedicated) addresses
6. Configures DNS for `code-insight.fly.dev`
7. Issues Let's Encrypt SSL certificate

**Deployment output:**
```
Created app 'code-insight' in organization 'personal'

Admin URL: https://fly.io/apps/code-insight
Hostname: code-insight.fly.dev

Provisioning ips for code-insight
  Dedicated ipv6: 2a09:8280:1::be:131b:0
  Shared ipv4: 66.241.125.162

This deployment will:
 * create 2 "app" machines

🎉  SUCCESS! Your app is live and ready to use!  🎉

Visit: https://code-insight.fly.dev/
```

### Troubleshooting Build Issues

**Issue 1: Missing `uv.lock`**
```
error: Unable to find lockfile at `uv.lock`
```

**Solution:** Remove `--frozen` flag from `uv sync` command:
```dockerfile
RUN uv sync --no-dev  # Instead of: uv sync --frozen --no-dev
```

**Issue 2: Package not found**
```
Expected a Python module at: src/flyio_demo/__init__.py
```

**Solution:** Copy source code before running `uv sync`:
```dockerfile
COPY src/ ./src/    # Must come BEFORE uv sync
RUN uv sync --no-dev
```

**Issue 3: README.md not found**
```
failed to open file `/app/README.md`: No such file or directory
```

**Solution:** Remove README.md from `.dockerignore` and include it in the COPY:
```dockerfile
COPY pyproject.toml README.md ./
```

### Verifying Deployment

```bash
# Check app status
fly status

# View logs
fly logs

# Test endpoints
curl https://code-insight.fly.dev/
curl https://code-insight.fly.dev/info
curl https://code-insight.fly.dev/static/
```

**Log output shows successful startup:**
```
INFO:     Started server process [658]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     172.16.9.122:51018 - "GET /static/ HTTP/1.1" 200 OK
```

---

## Part 5: Custom Domain Configuration

### Adding SSL Certificates

```bash
fly certs add code-insight.yaakovnet.net
```

**Output provides DNS configuration options:**

**Option 1: A and AAAA records (recommended)**
```
A    code-insight.yaakovnet.net → 66.241.125.162
AAAA code-insight.yaakovnet.net → 2a09:8280:1::be:131b:0
```

**Option 2: CNAME record**
```
CNAME code-insight.yaakovnet.net → o2lln0r.code-insight.fly.dev
```

**Option 3: ACME DNS Challenge (for pre-validation)**
```
CNAME _acme-challenge.code-insight.yaakovnet.net → code-insight.yaakovnet.net.o2lln0r.flydns.net
```

### DNS Configuration

Add the following records at your DNS provider:

```
code-insight.yaakovnet.net           A     66.241.125.162           TTL 180
code-insight.yaakovnet.net           AAAA  2a09:8280:1::be:131b:0   TTL 180
_acme-challenge.code-insight.yaakovnet.net  CNAME  code-insight.yaakovnet.net.o2lln0r.flydns.net  TTL 180
```

### Certificate Verification

```bash
fly certs check code-insight.yaakovnet.net
```

**Successful output:**
```
Status                    = Ready
Hostname                  = code-insight.yaakovnet.net
DNS Provider              = nearlyfreespeech
Certificate Authority     = Let's Encrypt
Issued                    = rsa,ecdsa
Added to App              = 2 minutes ago
Expires                   = 2 months from now
Source                    = fly

✓ Your certificate has been issued!
Your DNS is correctly configured and this certificate will auto-renew before expiration.
```

**Key observations:**
- Fly.io automatically detected the DNS provider (nearlyfreespeech)
- Both RSA and ECDSA certificates were issued for compatibility
- Certificate auto-renewal is configured
- No manual intervention required once DNS is configured

### Testing the Custom Domain

```bash
curl https://code-insight.yaakovnet.net/
# Returns 302 redirect to /static/

curl https://code-insight.yaakovnet.net/info
# Returns: "Health Ok!"
```

---

## Part 6: Setting Up GitOps with GitHub Actions

### Creating the Workflow File

Create `.github/workflows/fly-deploy.yml`:

```yaml
# GitHub Actions workflow for automatic deployment to Fly.io
#
# Setup instructions:
# 1. Generate a Fly.io deploy token: fly tokens create deploy -x 999999h
# 2. Add the token as a GitHub secret: Settings > Secrets and variables > Actions > New repository secret
#    - Name: FLY_API_TOKEN
#    - Value: [paste the token from step 1, including "FlyV1 " prefix]
# 3. Uncomment the workflow below to activate automatic deployments
# 4. Push to the main branch to trigger deployment

# WORKFLOW IS CURRENTLY DISABLED - Uncomment the lines below to activate

# name: Fly Deploy
#
# on:
#   push:
#     branches:
#       - main
#
# jobs:
#   deploy:
#     name: Deploy app
#     runs-on: ubuntu-latest
#     concurrency: deploy-group    # Ensures only one deployment runs at a time
#     steps:
#       - uses: actions/checkout@v4
#       - uses: superfly/flyctl-actions/setup-flyctl@master
#       - run: flyctl deploy --remote-only
#         env:
#           FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

**Design decisions:**
- **Commented by default**: Prevents accidental deployments during development
- **Clear setup instructions**: Embedded in the file for easy reference
- **`concurrency: deploy-group`**: Prevents multiple simultaneous deployments
- **`--remote-only`**: Builds on Fly.io's infrastructure, not in GitHub Actions

### Configuring Secrets

**Step 1: Generate deploy token**
```bash
fly tokens create deploy -x 999999h
```

**Output:**
```
FlyV1 fm2_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Important:** Copy the entire output including the `FlyV1 ` prefix and space.

**Step 2: Add to GitHub secrets**
1. Navigate to: https://github.com/[your-username]/flyio-demo/settings/secrets/actions
2. Click "New repository secret"
3. Name: `FLY_API_TOKEN`
4. Value: Paste the entire token (including `FlyV1 `)
5. Click "Add secret"

### Testing Auto-Deployment

**Step 1: Verify baseline**
```bash
curl https://code-insight.fly.dev/info
# Returns: "Health Ok!"
```

**Step 2: Activate the workflow**

Uncomment the workflow in `.github/workflows/fly-deploy.yml`:
```yaml
# WORKFLOW IS CURRENTLY ACTIVE - Testing auto-deployment

name: Fly Deploy

on:
  push:
    branches:
      - main

jobs:
  deploy:
    name: Deploy app
    runs-on: ubuntu-latest
    concurrency: deploy-group
    steps:
      - uses: actions/checkout@v4
      - uses: superfly/flyctl-actions/setup-flyctl@master
      - run: flyctl deploy --remote-only
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

**Step 3: Make a measurable change**

Edit `src/flyio_demo/code_insight/mcp_server.py`:
```python
@mcp.custom_route("/info", methods=["GET"])
async def show_info(request: Request) -> PlainTextResponse:
    return PlainTextResponse("Health Ok! - Auto-deployed via GitHub Actions")
```

**Step 4: Commit and push**
```bash
git add .
git commit -m "Enable GitHub Actions auto-deployment and update healthcheck message

- Activated GitHub Actions workflow for automatic deployment
- Changed /info endpoint message to verify auto-deployment works
- Testing GitOps workflow"
git push origin main
```

**Step 5: Monitor deployment**
1. Visit: https://github.com/[your-username]/flyio-demo/actions
2. Watch the "Fly Deploy" workflow run
3. Deployment typically takes 2-3 minutes

**Step 6: Verify deployment**
```bash
curl https://code-insight.fly.dev/info
# Returns: "Health Ok! - Auto-deployed via GitHub Actions"
```

✅ **Success!** The healthcheck message changed, confirming GitOps works.

**Step 7: Deactivate workflow**

To prevent deployments on every push during the learning exercises, comment out the workflow again:

```yaml
# WORKFLOW IS CURRENTLY DISABLED - Uncomment the lines below to activate

# name: Fly Deploy
#
# on:
#   push:
#     branches:
#       - main
# ...
```

Commit and push this change to deactivate auto-deployment.

---

## Key Concepts Learned

### 1. FastMCP Server Architecture
- **MCP tools and prompts**: Provide AI capabilities through structured interfaces
- **Custom HTTP routes**: Mix MCP endpoints with traditional web serving
- **ASGI applications**: Production-ready with Uvicorn
- **Static file serving**: With security checks and path validation

### 2. Docker Build Optimization
- **Multi-stage builds**: Copy from the `uv` image for the latest version
- **Build order matters**: Source code must exist before `uv sync`
- **Minimal base images**: `python:3.14-slim` reduces image size
- **`.dockerignore`**: Exclude unnecessary files from build context

### 3. Python Package Management with `uv`
- **Fast dependency resolution**: Significantly faster than pip
- **Virtual environment management**: `uv run` activates automatically
- **`pyproject.toml` structure**: Modern Python packaging standards
- **Build backends**: `uv_build` for modern, fast builds

### 4. Fly.io Deployment Strategies
- **Manual deployment**: `fly launch` and `fly deploy` for hands-on control
- **GitOps deployment**: Automatic deployment on git push via GitHub Actions
- **High availability**: 2 machines deployed by default
- **Auto-scaling**: Scale to zero when idle, wake on traffic
- **Global anycast**: Requests route to the nearest machine

### 5. Custom Domains and SSL
- **Automatic Let's Encrypt**: Free SSL certificates with auto-renewal
- **Multiple certificate types**: Both RSA and ECDSA for compatibility
- **DNS flexibility**: A/AAAA records or CNAME, your choice
- **ACME challenges**: Automatic validation via DNS

### 6. CI/CD Best Practices
- **Deployment tokens**: Separate from user authentication
- **Concurrency control**: Prevent simultaneous deployments
- **Remote builds**: Offload Docker builds to Fly.io infrastructure
- **Workflow comments**: Document setup and activation process inline

### 7. Troubleshooting Techniques
- **Read the logs**: `fly logs` shows startup and runtime issues
- **Check the build**: Build failures provide specific error messages
- **SSH access**: `fly ssh console` for live debugging
- **Incremental fixes**: Fix one issue at a time, redeploy, verify

---

## Additional Resources

### Fly.io Documentation
- [Continuous Deployment with GitHub Actions](https://fly.io/docs/launch/continuous-deployment-with-github-actions/)
- [fly.toml Configuration Reference](https://fly.io/docs/reference/configuration/)
- [Custom Domains and SSL](https://fly.io/docs/networking/custom-domain/)
- [Fly.io Docker Deployment](https://fly.io/docs/languages-and-frameworks/dockerfile/)

### FastMCP Documentation
- [FastMCP HTTP Deployment](https://gofastmcp.com/deployment/http)
- [FastMCP Custom Routes](https://gofastmcp.com/concepts/custom-routes)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)

### Python & Docker
- [uv Package Manager](https://github.com/astral-sh/uv)
- [Python Packaging Guide](https://packaging.python.org/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/dev-best-practices/)

### GitHub Actions
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Encrypted Secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions)
- [superfly/flyctl-actions](https://github.com/superfly/flyctl-actions)

---

## Comparison: Manual vs. GitOps Deployment

| Aspect | Manual Deployment | GitOps Deployment |
|--------|------------------|-------------------|
| **Command** | `fly deploy` | `git push` |
| **When to use** | Testing, quick iterations, learning | Production, team collaboration |
| **Build location** | Local or Fly.io (with `--remote-only`) | Always Fly.io |
| **Audit trail** | Git commits (manual tracking) | Automatic via GitHub Actions |
| **Rollback** | Manual redeployment of previous version | Git revert + automatic redeployment |
| **Team workflow** | Requires fly.io access for all deployers | Only needs GitHub access |
| **Deployment speed** | Immediate | ~2-3 minutes (includes GitHub Actions overhead) |
| **Best for** | Development and learning | Production and collaboration |

---

**Congratulations!** You've successfully deployed a FastMCP server to Fly.io using both manual deployment and automated GitOps workflows. You now understand the complete lifecycle from development to production deployment with continuous delivery.
