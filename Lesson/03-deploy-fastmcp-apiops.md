# Lesson 03: Deploy FastMCP Server with API-OPS on Fly.io

## Executive Summary

This lesson demonstrates how to deploy a FastMCP server to Fly.io using API-OPS (programmatic operations) instead of GitOps. You'll learn how to build Docker images locally, push them to Fly.io's private container registry, and deploy applications from registry images using the Fly.io CLI. This approach provides more control over the deployment pipeline and enables integration with custom CI/CD workflows.

**Key achievements:**
- Build Docker images locally with git commit SHA tags
- Authenticate with Fly.io's private Docker registry
- Push custom images to `registry.fly.io`
- Deploy applications from registry images using `fly deploy --image`
- Create a new Fly.io app (`test001`) without affecting existing deployments
- Understand the differences between GitOps and API-OPS deployment strategies

**Time to complete:** 30-60 minutes

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Milestone 1: Build Docker Image Locally](#milestone-1-build-docker-image-locally)
   - Understanding Image Tagging Strategy
   - Getting the Current Git Commit SHA
   - Building the Image
   - Verifying the Build
3. [Milestone 2: Push Image to Fly.io Registry](#milestone-2-push-image-to-flyio-registry)
   - Understanding Fly.io's Registry Structure
   - Authenticating Docker with Fly.io
   - Tagging for Fly.io Registry
   - Pushing the Image
   - Verifying the Push
4. [Milestone 3: Deploy from Registry](#milestone-3-deploy-from-registry)
   - Creating the New App (`test001`)
   - Configuring fly.toml
   - Deploying from Registry Image
   - Verifying Deployment
5. [Key Concepts Learned](#key-concepts-learned)
6. [References and Additional Resources](#references-and-additional-resources)

---

## Prerequisites

Before starting this lesson, ensure you have:

1. **Docker installed and running locally**
   - Verify with: `docker --version`

2. **Fly.io CLI (`flyctl`) installed and authenticated**
   - Verify with: `fly auth whoami`

3. **Completed Lesson 02** (Deploy FastMCP with GitOps)
   - Existing `code-insight` app deployed
   - Understanding of the application structure

4. **Git repository initialized**
   - Working in a git repository with commits
   - Verify with: `git status`

---

## Milestone 1: Build Docker Image Locally

### Understanding Image Tagging Strategy

For this lesson, we'll use git commit SHAs as image tags. This provides:
- **Traceability**: Each image maps to a specific code version
- **Reproducibility**: You can rebuild from any commit
- **Uniqueness**: Each commit gets a unique tag

The image will be tagged for the `code-insight` registry (Fly.io uses app names as registry namespaces).

### Step 1.1: Get the Current Git Commit SHA

First, get the short SHA of the current commit:

```bash
git rev-parse --short HEAD
```

**Example output:**
```
e1d78c3
```

Save this value - you'll use it as the image tag.

### Step 1.2: Build the Docker Image

Build the image with the git commit SHA as the tag:

```bash
docker build -t registry.fly.io/code-insight:e1d78c3 .
```

**What happens:**
- Docker reads the `Dockerfile` in the current directory
- Builds the image layer by layer
- Tags it as `registry.fly.io/code-insight:e1d78c3`

**Expected output (abbreviated):**
```
[+] Building 45.2s (10/10) FINISHED
 => [internal] load build definition from Dockerfile
 => => transferring dockerfile: 571B
 => [internal] load metadata for docker.io/library/python:3.14-slim
 => [1/5] FROM python:3.14-slim
 => [2/5] COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
 => [3/5] WORKDIR /app
 => [4/5] COPY pyproject.toml README.md ./
 => [5/5] COPY src/ ./src/
 => [6/5] RUN uv sync --no-dev
 => exporting to image
 => => naming to registry.fly.io/code-insight:e1d78c3
```

### Step 1.3: Verify the Build

Verify that the image was created successfully:

```bash
docker images | grep code-insight
```

**Expected output:**
```
registry.fly.io/code-insight   e1d78c3   abc123def456   2 minutes ago   234MB
```

You can also test the image locally:

```bash
docker run --rm -p 8080:8080 registry.fly.io/code-insight:e1d78c3
```

Then visit `http://localhost:8080/` in your browser. Press Ctrl+C to stop the container.

---

## Milestone 2: Push Image to Fly.io Registry

### Understanding Fly.io's Registry Structure

Fly.io provides a private Docker registry at `registry.fly.io`. Each app gets its own namespace:

- Registry URL: `registry.fly.io`
- Image path format: `registry.fly.io/<app-name>:<tag>`
- Example: `registry.fly.io/code-insight:e1d78c3`

**Important notes:**
- Access is scoped per organization
- You can use images across apps in the same organization
- Authentication tokens expire after 5 minutes
- There's no API to list all tags (only deployed releases are visible)

### Step 2.1: Authenticate Docker with Fly.io

Authenticate your local Docker client with Fly.io's registry:

```bash
fly auth docker
```

**Expected output:**
```
Authentication successful. You can now tag and push images to registry.fly.io/{your-app}
```

**What happens:**
- Updates `~/.docker/config.json` with authentication credentials
- Token is valid for 5 minutes
- If you get authentication errors later, re-run this command

### Step 2.2: Push the Image

Since we already tagged the image correctly in Milestone 1, we can push directly:

```bash
docker push registry.fly.io/code-insight:e1d78c3
```

**Expected output:**
```
The push refers to repository [registry.fly.io/code-insight]
5f70bf18a086: Pushed
e1d78c3: digest: sha256:abc123... size: 2345
```

**If authentication fails:**
- Token may have expired (run `fly auth docker` again)
- Verify you're authenticated: `fly auth whoami`

### Step 2.3: Verify the Push

You can verify the image was pushed by inspecting its manifest:

```bash
docker manifest inspect registry.fly.io/code-insight:e1d78c3
```

**Expected output:**
```json
{
   "schemaVersion": 2,
   "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
   "config": {
      "mediaType": "application/vnd.docker.container.image.v1+json",
      "size": 7234,
      "digest": "sha256:abc123..."
   },
   ...
}
```

---

## Milestone 3: Deploy from Registry

### Step 3.1: Create the New App (`test001`)

Create a new Fly.io app for testing (this won't affect the existing `code-insight` deployment):

```bash
fly apps create test001
```

**Expected output:**
```
New app created: test001
```

**If the name is taken:**
- Choose a different name
- Or use `--generate-name` to auto-generate: `fly apps create --generate-name`

### Step 3.2: Configure fly.toml

We'll create a new `fly.toml` configuration file for the `test001` app. The key difference from GitOps is that we specify the image directly instead of building from source.

Create a new file `fly-test001.toml` (keeping the original `fly.toml` for the production `code-insight` app):

```toml
# fly-test001.toml - API-OPS deployment configuration
app = 'test001'
primary_region = 'ewr'

[build]
  image = "registry.fly.io/code-insight:e1d78c3"

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

**Key differences from GitOps fly.toml:**
1. `app = 'test001'` - Different app name
2. `[build] image = "..."` - Uses pre-built registry image instead of building from Dockerfile
3. No `[build] dockerfile` section needed

### Step 3.3: Deploy from Registry Image

Deploy using the registry image:

```bash
fly deploy --config fly-test001.toml
```

**What happens:**
- Fly.io pulls the image from `registry.fly.io/code-insight:e1d78c3`
- Skips the build process (image is already built)
- Creates/updates Fly Machines with the new image
- Performs health checks

**Expected output:**
```
==> Verifying app config
--> Verified app config
==> Building image
Searching for image 'registry.fly.io/code-insight:e1d78c3' remotely...
image found: img_abc123...

--> Creating release
Release v1 created

--> Monitoring deployment
1 desired, 1 placed, 1 healthy, 0 unhealthy [health checks: 1 total, 1 passing]
--> v1 deployed successfully
```

### Step 3.4: Verify Deployment

Check the app status:

```bash
fly status --app test001
```

**Expected output:**
```
App
  Name     = test001
  Owner    = your-org
  Hostname = test001.fly.dev
  Image    = registry.fly.io/code-insight:e1d78c3
  Platform = machines

Machines
ID              STATE   REGION  HEALTH CHECKS   IMAGE                                          CREATED
abc123def456    started ewr     1 total, 1 passing   registry.fly.io/code-insight:e1d78c3   2m ago
```

Test the deployment:

```bash
curl https://test001.fly.dev/
```

**Expected output:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Code Insight MCP</title>
...
```

Alternatively, visit `https://test001.fly.dev/` in your browser.

### Step 3.5: View Deployment History

See all releases and their images:

```bash
fly releases --app test001 --image
```

**Expected output:**
```
VERSION STABLE  TYPE    STATUS          DESCRIPTION                                     IMAGE                                     CREATED
v1      true    deploy  successful      Deploy image registry.fly.io/code-insight:e1d78c3   registry.fly.io/code-insight:e1d78c3   5m ago
```

---

## Key Concepts Learned

### 1. Local Docker Build
- **Git SHA tagging**: Using `git rev-parse --short HEAD` for reproducible builds
- **Registry naming**: Images must be tagged with `registry.fly.io/<app-name>:<tag>`
- **Local testing**: Can test images with `docker run` before pushing

### 2. Fly.io Private Registry
- **Authentication**: `fly auth docker` updates Docker credentials (5-minute expiry)
- **Registry structure**: `registry.fly.io/<app-name>:<tag>`
- **Organization scope**: Images can be shared across apps in the same org
- **No tag listing**: Can only view deployed releases, not all available tags

### 3. API-OPS Deployment
- **Image-based deployment**: Uses `[build] image = "..."` in fly.toml
- **Skip build process**: Deployment is faster (no build step)
- **Multiple apps from one image**: Can deploy the same image to different apps
- **Version control**: Git SHAs provide clear version tracking

### 4. GitOps vs. API-OPS

| Aspect | GitOps (Lesson 02) | API-OPS (Lesson 03) |
|--------|-------------------|---------------------|
| **Trigger** | Git push to repository | Manual `fly deploy` or script |
| **Build location** | Fly.io builders | Local machine |
| **Build time** | During deployment | Before deployment |
| **Image storage** | Temporary | Persistent in registry |
| **Configuration** | `[build]` section empty or with dockerfile | `[build] image = "..."` |
| **Flexibility** | Automatic, hands-off | Manual control, scriptable |
| **Speed** | Slower (builds on every deploy) | Faster (pre-built images) |
| **Use case** | Continuous deployment | Custom pipelines, testing |

---

## References and Additional Resources

### Official Fly.io Documentation
- **Using the Fly Docker Registry**: https://fly.io/docs/blueprints/using-the-fly-docker-registry/
  - Complete guide to authentication, tagging, and pushing images

- **Builders and Build Configuration**: https://fly.io/docs/reference/builders/
  - Overview of Dockerfile, buildpacks, and pre-built image options

- **Deploy Applications**: https://fly.io/docs/launch/deploy/
  - Deployment strategies, health checks, and smoke tests

- **fly.toml Configuration Reference**: https://fly.io/docs/reference/configuration/
  - Complete reference for all `fly.toml` options

- **fly auth docker**: https://fly.io/docs/flyctl/auth-docker/
  - CLI command reference for Docker authentication

### Docker Documentation
- **docker build**: https://docs.docker.com/engine/reference/commandline/build/
  - Building images from Dockerfiles

- **docker push**: https://docs.docker.com/engine/reference/commandline/push/
  - Pushing images to registries

- **docker manifest inspect**: https://docs.docker.com/engine/reference/commandline/manifest_inspect/
  - Inspecting image manifests

### Git
- **git rev-parse**: https://git-scm.com/docs/git-rev-parse
  - Getting commit SHAs for image tagging

---

## Next Steps

With the three milestones complete, you now have a working API-OPS deployment pipeline. Future enhancements could include:

- Automating the build-tag-push-deploy workflow with scripts
- Integrating with custom CI/CD systems
- Using multiple environments (dev, staging, production)
- Implementing blue-green deployments
- Adding health checks and monitoring

**Note:** We'll add more detailed steps in future iterations of this lesson as we explore additional API-OPS capabilities.
