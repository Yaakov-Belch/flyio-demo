# Lesson 04: Semi-Functional Deployment with Python

## Executive Summary

This lesson introduces the **semi-functional programming paradigm** for container deployment workflows. Semi-functional programming combines functional programming principles (determinism, composability) with controlled side effects (caching) to create reliable, fast, and consistent deployment pipelines.

**Key achievements:**
- Understand the semi-functional approach to deployment automation
- Choose between Docker and Buildah for Python-based workflows
- Implement content-addressed image naming using git tree hashes
- Build deterministic, cacheable deployment functions
- Create deployment pipelines that guarantee consistency

**Time to complete:** Research and decision-making phase

---

## Table of Contents

1. [Understanding Semi-Functional Programming](#understanding-semi-functional-programming)
   - What is Semi-Functional?
   - Benefits for Deployment Reliability
   - Benefits for Consistency
   - Benefits for Speed
2. [Research Findings](#research-findings)
   - Git Tree SHA for Content-Based Naming
   - Docker Python SDK Analysis
   - Buildah Scripting Analysis
   - Registry Push De-duplication
   - Build Reproducibility
3. [Decision: Docker vs Buildah](#decision-docker-vs-buildah)
   - Comparison Matrix
   - Recommendation
   - Rationale
4. [References and Additional Resources](#references-and-additional-resources)

---

## Understanding Semi-Functional Programming

### What is Semi-Functional?

**Semi-functional programming** is an approach to managing computations and operations that provides:

1. **Deterministic functions** - Same inputs always produce same outputs
2. **Controlled side effects** - Side effects (like caching) are allowed but must be unobservable in normal operations
3. **Composability** - Functions can be combined to build higher-level operations
4. **Strong guarantees** - You can only obtain a value after its preconditions are satisfied

### Core Principles for Deployment

In our deployment context, semi-functional means:

**Image Building:**
```python
def build_image(source_tree_hash: str) -> ImageName:
    """
    Returns an image name that is guaranteed to exist locally.
    The image name is derived from the source content hash.

    Key guarantees:
    - If source changes, image name changes
    - If source is identical, image name is identical
    - When you have an image name, the image EXISTS locally
    - The only way to get the name is to build (or verify) the image
    """
```

**Registry Publishing:**
```python
def publish_image(image_name: ImageName) -> RegistryReference:
    """
    Returns a registry reference that is guaranteed to be pullable.

    Key guarantees:
    - Upload optimizes using layer de-duplication
    - When you have a registry reference, the image EXISTS in registry
    - The only way to get the reference is to publish the image
    """
```

**Application Deployment:**
```python
def deploy_application(registry_ref: RegistryReference) -> ApplicationURL:
    """
    Returns an application URL that is guaranteed to be accessible.

    Key guarantees:
    - When you have a URL, the application is DEPLOYED and ACCESSIBLE
    - The only way to get the URL is to deploy (or verify) the application
    - May use caching to skip re-deployment of identical images
    """
```

### Benefits for Deployment Reliability

**Type-level guarantees:**
- Cannot use an image name before it's built
- Cannot publish before building
- Cannot deploy before publishing
- Compiler/runtime enforces correct ordering

**No partial states:**
- Functions return only after completing their work
- No "image might exist" - it either exists (you have the name) or doesn't (you don't have the name)
- Failures are explicit exceptions, not silent partial states

**Idempotency:**
- Running the same function with the same inputs produces the same result
- Safe to retry operations
- Safe to run in parallel (with proper locking for caches)

### Benefits for Consistency

**Content-addressable naming:**
- Image names derived from content hashes
- Identical code → identical hash → identical image name
- Changed code → different hash → different image name
- No version number confusion

**Deterministic builds:**
- Same source tree hash always produces same image
- Reproducible across machines and time
- Git tree SHA captures ALL source code state (committed or uncommitted)

**Cache coherence:**
- Caches keyed by content hashes
- Invalid cache entries are impossible (hash mismatch = rebuild)
- Old cache entries are safe to use (hash match = identical content)

### Benefits for Speed

**Intelligent caching:**
- Build cache: Skip rebuild if image for tree hash exists
- Registry cache: Skip push if registry already has the image
- Deployment cache: Skip redeploy if same image is running

**Layer-level optimization:**
- Docker/Buildah automatically reuse unchanged layers
- Registry push skips layers that exist remotely
- Minimal data transfer for incremental changes

**Parallel-safe:**
- Multiple processes can safely check caches
- Content-addressed storage prevents conflicts
- Lock-free reads from cache

**Example workflow:**
```python
# First run: Build everything
tree_hash = get_tree_hash()  # e.g., "a3f2e19"
image_name = build_image(tree_hash)  # Builds, caches, returns "registry.fly.io/code-insight:a3f2e19"
reg_ref = publish_image(image_name)  # Pushes to registry
app_url = deploy_application(reg_ref)  # Deploys, returns "https://test001.fly.dev"

# Second run (no code changes): Everything cached
tree_hash = get_tree_hash()  # Still "a3f2e19"
image_name = build_image(tree_hash)  # Cache hit! Returns immediately
reg_ref = publish_image(image_name)  # Registry already has it, skips
app_url = deploy_application(reg_ref)  # Same image running, skips

# Third run (code changed): Only rebuild what changed
tree_hash = get_tree_hash()  # Now "b7d4c92"
image_name = build_image(tree_hash)  # New hash → must rebuild
reg_ref = publish_image(image_name)  # Pushes only changed layers
app_url = deploy_application(reg_ref)  # Deploys new version
```

---

## Research Findings

### 1. Git Tree SHA for Content-Based Naming

**Goal:** Generate a hash that represents the entire source tree state, including uncommitted changes.

**Solution:** Use `git write-tree` with a temporary index.

**How it works:**
- Git's tree SHA represents the exact state of all tracked files
- Committed code: `git rev-parse HEAD^{tree}` gives the tree SHA for the current commit
- Uncommitted code: Stage all changes to a temporary index, then `git write-tree`

**Implementation approach:**
```python
import subprocess
import tempfile
import os

def get_source_tree_hash() -> str:
    """
    Returns a SHA hash representing the current source tree state.
    Includes both committed and uncommitted changes.
    """
    # Create temporary index file
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_index = tmp.name

    try:
        # Copy current index
        subprocess.run(['cp', '.git/index', tmp_index], check=True)

        # Set temporary index
        env = os.environ.copy()
        env['GIT_INDEX_FILE'] = tmp_index

        # Stage all changes
        subprocess.run(['git', 'add', '--all'], env=env, check=True)

        # Get tree hash
        result = subprocess.run(
            ['git', 'write-tree'],
            env=env,
            capture_output=True,
            text=True,
            check=True
        )

        return result.stdout.strip()
    finally:
        os.unlink(tmp_index)
```

**Benefits:**
- Hash changes when ANY file changes
- Hash stays same when nothing changes
- Includes uncommitted changes (critical for iterative development)
- When committed, tree SHA equals commit's tree SHA

**Alignment with semi-functional goals:** ✅ Excellent
- Deterministic: Same source → same hash
- Content-addressed: Hash represents actual content
- Composable: Can be used as input to build functions

---

### 2. Docker Python SDK Analysis

**Library:** `docker-py` (Docker SDK for Python)
- **Repository:** https://github.com/docker/docker-py
- **Documentation:** https://docker-py.readthedocs.io/
- **Code Snippets Available:** 357 (high-quality examples)
- **Benchmark Score:** 92.3 (excellent)

**Capabilities:**

**Building Images:**
```python
import docker

client = docker.from_env()

# Build with explicit tag
image, build_logs = client.images.build(
    path='/path/to/project',
    tag='myapp:latest',
    rm=True,
    nocache=False
)

# Access image hash/ID
print(image.id)  # sha256:abc123...
print(image.short_id)  # abc123

# Tag with custom name
image.tag('registry.fly.io/code-insight', tag='a3f2e19')
```

**Accessing Image Metadata:**
```python
# Get image by ID or tag
image = client.images.get('myapp:latest')

# Inspect image
attrs = image.attrs
digest = attrs['RepoDigests'][0]  # Full SHA256 digest
```

**Pushing to Registry:**
```python
# Push to registry
for line in client.images.push('registry.fly.io/code-insight', tag='a3f2e19', stream=True, decode=True):
    print(line)
```

**Strengths:**
- ✅ Native Python API (no subprocess calls)
- ✅ Rich object model (Image, Container objects)
- ✅ Excellent documentation and examples
- ✅ Mature, stable, well-maintained
- ✅ Can access image digests and metadata programmatically
- ✅ Stream build logs for progress feedback

**Weaknesses:**
- ❌ Requires Docker daemon running
- ❌ No built-in reproducible build flags
- ❌ Must rely on Docker's default behavior for layer caching
- ❌ No explicit `--timestamp` option in Python API

**Deterministic Builds:**
- Docker images are content-addressed (layers have SHA256 hashes)
- Image ID is deterministic IF build is reproducible
- Layer caching works automatically
- **However:** No Python API for setting timestamps for reproducibility

**Registry De-duplication:**
- ✅ Docker automatically skips layers that exist in registry
- ✅ Uses HEAD requests to check layer existence
- ✅ Cross-repository mounts supported (since Registry v2.3.0)
- ✅ Efficient: Only pushes what's needed

**Alignment with semi-functional goals:** ⚠️ Good, with caveats
- Determinism: ⚠️ Possible but requires Dockerfile-level controls
- Python Integration: ✅ Excellent
- Image Hashes: ✅ Accessible via API
- Reproducibility: ❌ No built-in timestamp control in Python API

---

### 3. Buildah Scripting Analysis

**Tool:** Buildah (CLI tool for building OCI images)
- **Repository:** https://github.com/containers/buildah
- **Documentation:** https://buildah.io/
- **Code Snippets Available:** 971 (extensive examples)
- **Benchmark Score:** 89.5 (excellent)

**Capabilities:**

**Building Images (Dockerfile):**
```bash
buildah build \
  --timestamp 0 \
  --tag localhost/myapp:a3f2e19 \
  .
```

**Building Images (Script-based):**
```bash
#!/bin/bash
ctr=$(buildah from scratch)
mnt=$(buildah mount $ctr)
# ... install packages, copy files ...
buildah config --entrypoint "/bin/app" $ctr
buildah commit --timestamp=0 $ctr myapp:latest
buildah unmount $ctr
```

**Python Integration:**
```python
import subprocess

def build_with_buildah(tree_hash: str) -> str:
    """Build image using buildah subprocess."""
    tag = f"registry.fly.io/code-insight:{tree_hash}"

    result = subprocess.run([
        'buildah', 'build',
        '--timestamp', '0',  # Reproducible builds
        '--tag', tag,
        '.'
    ], capture_output=True, text=True, check=True)

    return tag
```

**Accessing Image Metadata:**
```bash
buildah inspect myapp:latest
buildah images --format "{{.ID}} {{.Digest}}"
```

**Pushing to Registry:**
```bash
buildah push localhost/myapp:a3f2e19 docker://registry.fly.io/code-insight:a3f2e19
```

**Strengths:**
- ✅ **Explicit `--timestamp` flag** for reproducible builds
- ✅ No daemon required (daemonless architecture)
- ✅ Designed for scripting and automation
- ✅ Supports both Dockerfile and script-based builds
- ✅ Can run rootless
- ✅ OCI-compliant

**Weaknesses:**
- ❌ No native Python bindings (must use subprocess)
- ❌ Less "pythonic" than docker-py
- ❌ Need to parse CLI output for metadata
- ❌ Newer tool (less widespread than Docker)

**Deterministic Builds:**
- ✅ **`--timestamp 0`** flag ensures identical timestamps
- ✅ **`--source-date-epoch`** for setting creation time
- ✅ Explicitly designed for reproducible builds
- ✅ Same inputs → same image hash (when timestamp set)

**Registry De-duplication:**
- ✅ Standard OCI/Docker registry protocol
- ✅ Skips layers that exist in registry
- ✅ Efficient layer reuse

**Alignment with semi-functional goals:** ✅ Excellent
- Determinism: ✅ Built-in `--timestamp` flag
- Python Integration: ⚠️ Requires subprocess, but clean
- Image Hashes: ✅ Accessible via inspect
- Reproducibility: ✅ Explicitly supported

---

### 4. Registry Push De-duplication

**Docker:**
- Each layer upload starts with HEAD request to check existence
- If layer exists: Registry returns 200 OK, client skips upload
- Cross-repository mounts: Layers shared across different images
- Efficient: Only uploads what's missing

**Buildah:**
- Uses standard OCI/Docker registry protocol
- Same de-duplication behavior as Docker
- Skips existing layers automatically

**Conclusion:** Both tools have equivalent registry push efficiency.

---

### 5. Build Reproducibility

**Requirements for reproducible builds:**
1. Deterministic timestamps in image metadata
2. Consistent layer ordering
3. Stable base images (use digests, not tags)
4. Fixed file permissions and ownership

**Docker Approach:**
- Timestamps set during build (no Python API control)
- Can use `SOURCE_DATE_EPOCH` environment variable
- Requires Dockerfile modifications for full reproducibility

**Buildah Approach:**
- `--timestamp 0` flag (CLI level)
- `--source-date-epoch` flag (CLI level)
- Explicitly designed for reproducible builds

**Conclusion:** Buildah has better explicit support for reproducibility.

---

## Decision: Docker vs Buildah

### Comparison Matrix

| Criterion | Docker (`docker-py`) | Buildah (subprocess) | Winner |
|-----------|---------------------|---------------------|---------|
| **Python Integration** | Native SDK, pythonic API | Subprocess calls, CLI parsing | Docker |
| **Reproducible Builds** | Possible but requires ENV vars | Built-in `--timestamp` flag | **Buildah** |
| **Deterministic Hashes** | Yes (with proper setup) | Yes (out of the box) | **Buildah** |
| **Image Hash Access** | Programmatic (`.id`, `.attrs`) | CLI parsing (`inspect`) | Docker |
| **Registry De-duplication** | Automatic | Automatic | Tie |
| **Daemon Requirement** | Requires Docker daemon | Daemonless | **Buildah** |
| **Documentation Quality** | Excellent (92.3 score) | Excellent (89.5 score) | Tie |
| **Code Examples** | 357 snippets | 971 snippets | **Buildah** |
| **Maturity** | Very mature, widespread | Newer, growing | Docker |
| **Simplicity** | More complex (daemon, API) | Simpler (just CLI) | **Buildah** |
| **Semi-Functional Alignment** | Good (with workarounds) | Excellent (native support) | **Buildah** |

### Recommendation

**Use Buildah with Python subprocess calls.**

### Rationale

**1. Reproducibility is First-Class**

Buildah's `--timestamp 0` flag directly supports our semi-functional goal of deterministic builds:

```python
def build_image(tree_hash: str) -> str:
    """Guaranteed deterministic build."""
    subprocess.run([
        'buildah', 'build',
        '--timestamp', '0',  # Same source → same image hash
        '--tag', f'localhost/code-insight:{tree_hash}',
        '.'
    ], check=True)

    return f'localhost/code-insight:{tree_hash}'
```

With Docker, we'd need to:
- Set `SOURCE_DATE_EPOCH` environment variable
- Ensure it's respected throughout the build
- No Python API support for this

**2. Simpler Mental Model**

Buildah is "just a CLI tool":
- No daemon to manage
- No background processes
- Subprocess calls are straightforward
- Errors are explicit

Docker daemon adds complexity:
- Must be running before Python script starts
- API connection can fail
- Daemon state can be inconsistent

**3. Better Alignment with Semi-Functional Principles**

Semi-functional programming values **explicit guarantees**. Buildah provides:

```python
# Build: Returns only after image exists locally
image_name = build_with_buildah(tree_hash)

# Push: Returns only after image exists in registry
registry_ref = push_with_buildah(image_name)
```

The subprocess approach makes side effects (building, pushing) explicit and synchronous.

**4. Content-Addressable by Design**

Buildah with `--timestamp 0` ensures:
- Same source tree → same image digest
- Different source → different digest
- Perfect for content-addressed caching

**5. Trade-off: Subprocess vs Native API**

Yes, subprocess calls are less "pythonic" than `docker-py`. However:

- **Simpler to reason about:** Subprocess exit codes are clear
- **Easier to debug:** Can run exact same command in terminal
- **More reliable:** No API version mismatches
- **Future-proof:** CLI is stable interface

**6. Practical Considerations**

- Buildah is available on Linux (our deployment target)
- No licensing concerns (Apache 2.0)
- Active development and community support
- Can run rootless (better security)

---

## References and Additional Resources

### Git Tree Hashing
- **git-write-tree**: https://git-scm.com/docs/git-write-tree
  - Creating tree objects from index
- **Using git write-tree to cache builds**: https://blog.djy.io/using-git-write-tree-to-cache-builds/
  - Practical examples of content-based caching

### Docker Python SDK
- **docker-py Repository**: https://github.com/docker/docker-py
  - Official Docker SDK for Python
- **docker-py Documentation**: https://docker-py.readthedocs.io/
  - Complete API reference
- **Docker SDK Images API**: https://docker-py.readthedocs.io/en/stable/images.html
  - Building and managing images

### Buildah
- **Buildah Official Site**: https://buildah.io/
  - Introduction and getting started
- **Buildah Repository**: https://github.com/containers/buildah
  - Source code and issue tracking
- **buildah-build Manual**: https://github.com/containers/buildah/blob/main/docs/buildah-build.1.md
  - Complete CLI reference including `--timestamp`
- **buildah-commit Manual**: https://github.com/containers/buildah/blob/main/docs/buildah-commit.1.md
  - Committing containers to images

### Reproducible Builds
- **Reproducible Container Images**: https://tensor5.dev/reproducible-container-images/
  - In-depth guide to deterministic builds
- **Buildah Issue #1452**: https://github.com/containers/buildah/issues/1452
  - Discussion on deterministic creation times

### Registry De-duplication
- **Docker Layer De-duplication**: https://docs.docker.com/reference/cli/docker/image/push/
  - How Docker push handles existing layers
- **OCI Distribution Spec**: https://github.com/opencontainers/distribution-spec
  - Standard registry protocol

### Semi-Functional Programming
- **Pure Functions in Python**: https://docs.python.org/3/howto/functional.html
  - Functional programming principles
- **Content-Addressable Storage**: https://en.wikipedia.org/wiki/Content-addressable_storage
  - Theoretical foundation for our approach

---

## Next Steps

With the decision made to use Buildah, Lesson 05 will implement the semi-functional deployment pipeline:

1. **Git tree hash function** - Compute content-based hashes
2. **Build function** - Build images with deterministic tags
3. **Push function** - Publish to registry with verification
4. **Deploy function** - Deploy from registry and return URL
5. **Caching layer** - Implement smart caching for speed
6. **Integration** - Tie it all together in a deployment script

**Note:** We'll add implementation details in future iterations as we build the actual Python deployment system.
