# Lesson 05: Semi-Functional Deployment - Requirements Specification

## Executive Summary

This document specifies the requirements for a semi-functional deployment system built on Buildah. The system provides deterministic, cacheable, and composable functions for building, publishing, and deploying container images. The design leverages Buildah's reproducibility guarantees and wraps them in a Pythonic async API using frozen dataclass objects.

**Key Design Principles:**
- **Determinism**: Same inputs → same outputs, always
- **Type Safety**: Cannot use values before they're created
- **Caching**: Transparent, content-based, never invalidated
- **Composability**: Functions compose to build higher-level operations
- **Immutability**: All objects are frozen dataclasses

---

## Table of Contents

1. [Understanding Semi-Functional Programming](#understanding-semi-functional-programming)
2. [Why Buildah Aligns with Our Goals](#why-buildah-aligns-with-our-goals)
3. [High-Level Architecture](#high-level-architecture)
4. [API Specifications](#api-specifications)
5. [Caching Specifications](#caching-specifications)
6. [Pythonic Buildah Wrapper Requirements](#pythonic-buildah-wrapper-requirements)
7. [Implementation Contracts](#implementation-contracts)

---

## Understanding Semi-Functional Programming

### What is Semi-Functional?

Semi-functional programming is a pragmatic approach that combines:

1. **Pure functional principles:**
   - Functions are deterministic (same inputs → same outputs)
   - No observable side effects from the caller's perspective
   - Values are immutable
   - Functions compose cleanly

2. **Controlled side effects:**
   - Caching is allowed (but invisible to callers)
   - I/O operations are explicit in type signatures
   - Side effects are encapsulated and deterministic

### Why Semi-Functional for Deployments?

**Problem with traditional deployment scripts:**
```python
# Traditional approach - fragile and non-deterministic
def deploy():
    build_image()           # Side effect: creates image
    tag = get_latest_tag()  # Which image? When was it built?
    push(tag)               # Is image still there?
    deploy_to_fly(tag)      # Is it pushed? Which version?
```

Problems:
- Order matters, but not enforced by types
- Steps can fail leaving partial state
- Cannot tell if image exists by looking at the code
- Caching is manual and error-prone

**Semi-functional approach - reliable and deterministic:**
```python
# Semi-functional - type-safe and deterministic
async def deploy() -> ApplicationURL:
    tree_hash = await get_source_tree_hash()           # SourceTreeHash
    image_name = await build_image(tree_hash)          # LocalImageRef
    registry_ref = await publish_image(image_name)     # RegistryImageRef
    app_url = await deploy_application(registry_ref)   # ApplicationURL
    return app_url
```

Benefits:
- Type system enforces correct order
- Each function returns only after guaranteeing its postcondition
- Values are proof that work was done
- Caching is transparent and safe

### Core Guarantees

**Guarantee 1: Type-Level Ordering**
```python
# You CANNOT do this (type error):
registry_ref = await publish_image(tree_hash)  # Type error!
# publish_image expects LocalImageRef, not SourceTreeHash
```

**Guarantee 2: Existence**
```python
# If you have a LocalImageRef, the image EXISTS locally
image_name: LocalImageRef = await build_image(tree_hash)
# Now you can use image_name - it's guaranteed to exist

# If you have a RegistryImageRef, it EXISTS in registry
registry_ref: RegistryImageRef = await publish_image(image_name)
# Now you can pull it from anywhere
```

**Guarantee 3: Determinism**
```python
# Same source tree → same everything
tree_hash_1 = await get_source_tree_hash()
tree_hash_2 = await get_source_tree_hash()
assert tree_hash_1 == tree_hash_2  # If source unchanged

image_1 = await build_image(tree_hash_1)
image_2 = await build_image(tree_hash_1)  # Cache hit
assert image_1 == image_2
```

**Guarantee 4: Transparent Caching**
```python
# First call: Actually builds
image_1 = await build_image(tree_hash)  # Takes 30 seconds

# Second call: Cache hit
image_2 = await build_image(tree_hash)  # Takes 0.1 seconds

# Caller cannot tell the difference
assert image_1 == image_2
```

### Why This Improves Reliability

1. **No partial states**: Functions return only after completing their work
2. **Idempotent**: Safe to retry any operation
3. **Composable**: Build larger workflows from smaller functions
4. **Testable**: Deterministic functions are easy to test
5. **Debuggable**: Can inspect intermediate values

### Why This Improves Consistency

1. **Content-addressed**: Names derived from content hashes
2. **Reproducible**: Same source → same build → same image
3. **Traceable**: Every deployment links to exact source code
4. **Version-proof**: Cannot accidentally use wrong version

### Why This Improves Speed

1. **Smart caching**: Cache keyed by content hashes
2. **Safe to cache forever**: Content hash mismatch = rebuild automatically
3. **Parallel-safe**: Multiple processes can read caches safely
4. **Layer reuse**: Docker/Buildah layer caching works automatically

---

## Why Buildah Aligns with Our Goals

### High-Level Alignment

**Buildah's Design Philosophy:**
> "Buildah is a tool that facilitates building OCI container images. Buildah specializes in building OCI images. Buildah's commands replicate all of the commands that are found in a Dockerfile."

**Our Design Philosophy:**
> "Build deterministic, reproducible container images with strong guarantees through semi-functional programming."

**Perfect Alignment:**
- Buildah is designed for **automation and scripting**
- Buildah has **explicit reproducibility flags** (`--timestamp`)
- Buildah is **daemonless** (simpler, more reliable)
- Buildah is **OCI-compliant** (standard, portable)

### Detailed Alignment

| Our Requirement | Buildah Feature | Why It Matters |
|----------------|-----------------|----------------|
| **Deterministic builds** | `--timestamp 0` flag | Sets creation time to epoch, ensuring same source → same image digest |
| **Content-addressable** | Image digests (sha256) | Image hash uniquely identifies content |
| **Reproducible** | `--source-date-epoch` | Can set all timestamps deterministically |
| **Scriptable** | CLI designed for automation | Clean subprocess interface |
| **No hidden state** | Daemonless | No daemon state to get out of sync |
| **Layer caching** | Automatic layer reuse | Unchanged layers aren't rebuilt |
| **Registry efficiency** | Standard OCI protocol | Skips uploading existing layers |

### Buildah Team's Goals = Our Goals

The Buildah team explicitly cares about:
1. **Reproducible builds** → We need determinism
2. **Scriptability** → We need Python automation
3. **OCI compliance** → We need portability
4. **No daemon** → We need reliability

By contrast, Docker's goals include:
- Developer UX for interactive use
- Desktop application features
- Enterprise features (licensing, support)
- Backward compatibility with legacy behavior

Docker is excellent, but Buildah is **purpose-built for our use case**.

### Small Details Matter

**Example 1: Timestamp Control**

Buildah:
```bash
buildah build --timestamp 0 -t myapp:v1 .
```
Result: Creation timestamp = 0 → reproducible image hash

Docker:
```bash
docker build -t myapp:v1 .
# Timestamp = now → different hash every build
```
Workaround: Set `SOURCE_DATE_EPOCH` environment variable (less explicit)

**Example 2: Image Digest Access**

Buildah:
```bash
buildah inspect --format '{{.FromImageDigest}}' myimage
```
Clean, explicit output parsing

Docker (docker-py):
```python
image = client.images.get('myimage')
digest = image.attrs['RepoDigests'][0]
```
Requires daemon, API objects

**Example 3: Rootless Operation**

Buildah:
- Designed to run rootless
- No daemon = no privilege escalation

Docker:
- Requires daemon (usually root)
- Security implications

---

## High-Level Architecture

### Overview

```
┌─────────────────┐
│  User Code      │
│  (async/await)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Semi-Functional API Layer              │
│  - get_source_tree_hash()              │
│  - build_image()                       │
│  - publish_image()                     │
│  - deploy_application()                │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Pythonic Buildah Wrapper               │
│  - BuildahImage (frozen dataclass)      │
│  - BuildahBuilder (frozen dataclass)    │
│  - async methods with caching           │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Subprocess Layer                       │
│  - async subprocess calls to buildah    │
│  - Output parsing                       │
│  - Error handling                       │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Buildah CLI                            │
│  buildah build, push, inspect, etc.     │
└─────────────────────────────────────────┘
```

### Data Flow

```
Source Code
    ↓
[get_source_tree_hash]
    ↓
SourceTreeHash("a3f2e19...")
    ↓
[build_image]
    ↓
LocalImageRef("localhost/code-insight:a3f2e19")
    ↓
[publish_image]
    ↓
RegistryImageRef("registry.fly.io/code-insight@sha256:abc123...")
    ↓
[deploy_application]
    ↓
ApplicationURL("https://test001.fly.dev")
```

### Type Hierarchy

```python
@dataclass(frozen=True)
class SourceTreeHash:
    """Git tree hash representing source code state."""
    value: str  # e.g., "a3f2e19c8b2d1f4e6a7b9c0d2e3f5a6b7c8d9e0f"

@dataclass(frozen=True)
class LocalImageRef:
    """Reference to image in local storage."""
    name: str      # e.g., "localhost/code-insight:a3f2e19"
    digest: str    # e.g., "sha256:abc123..."

@dataclass(frozen=True)
class RegistryImageRef:
    """Reference to image in remote registry."""
    repository: str  # e.g., "registry.fly.io/code-insight"
    digest: str      # e.g., "sha256:abc123..."

    @cached_property
    def pullable_ref(self) -> str:
        """Full reference for docker pull."""
        return f"{self.repository}@{self.digest}"

@dataclass(frozen=True)
class ApplicationURL:
    """URL of deployed application."""
    url: str          # e.g., "https://test001.fly.dev"
    app_name: str     # e.g., "test001"
    image_ref: RegistryImageRef
```

---

## API Specifications

### 1. Source Tree Hashing

```python
async def get_source_tree_hash(
    repo_path: Path = Path("."),
    *,
    include_uncommitted: bool = True
) -> SourceTreeHash:
    """
    Get the git tree hash representing the current source state.

    Args:
        repo_path: Path to git repository
        include_uncommitted: Whether to include uncommitted changes

    Returns:
        SourceTreeHash: Content-based hash of source tree

    Guarantees:
        - Same source code → same hash
        - Different source code → different hash
        - Hash equals commit tree SHA if no uncommitted changes
        - Deterministic: always returns same hash for same source

    Caching:
        - Not cached (fast operation, ~10ms)
        - Source can change between calls

    Example:
        tree_hash = await get_source_tree_hash()
        print(tree_hash.value)  # "a3f2e19c8b2d1f4e..."
    """
```

### 2. Image Building

```python
async def build_image(
    source_hash: SourceTreeHash,
    *,
    dockerfile: Path = Path("Dockerfile"),
    build_args: dict[str, str] | None = None,
    target: str | None = None
) -> LocalImageRef:
    """
    Build a Docker image from source with deterministic naming.

    Args:
        source_hash: Source tree hash (from get_source_tree_hash)
        dockerfile: Path to Dockerfile
        build_args: Build arguments to pass to docker build
        target: Target stage in multi-stage build

    Returns:
        LocalImageRef: Reference to built image in local storage

    Guarantees:
        - Image name derived from source_hash
        - Image exists locally after return
        - Deterministic: same source_hash → same image digest
        - Reproducible: timestamp set to epoch (0)

    Caching:
        - Cached by source_hash
        - If image exists for this hash, returns immediately
        - Cache never invalidated (deterministic builds)

    Implementation:
        Uses: buildah build --timestamp 0 -t localhost/code-insight:{hash}

    Example:
        tree_hash = await get_source_tree_hash()
        image = await build_image(tree_hash)
        print(image.name)    # "localhost/code-insight:a3f2e19"
        print(image.digest)  # "sha256:abc123..."
    """
```

### 3. Image Publishing

```python
async def publish_image(
    local_ref: LocalImageRef,
    *,
    registry: str = "registry.fly.io",
    repository: str = "code-insight"
) -> RegistryImageRef:
    """
    Push image to registry and verify it's pullable.

    Args:
        local_ref: Local image reference (from build_image)
        registry: Registry hostname
        repository: Repository name

    Returns:
        RegistryImageRef: Reference to image in registry

    Guarantees:
        - Image exists in registry after return
        - Can be pulled by anyone with access
        - Digest matches local image digest
        - Layer de-duplication automatic (skips existing layers)

    Caching:
        - Cached by (local_ref.digest, registry, repository)
        - If image exists in registry with same digest, returns immediately
        - Verification: HEAD request to registry

    Implementation:
        Uses: buildah push localhost/image registry.fly.io/repo@digest

    Example:
        registry_ref = await publish_image(image)
        print(registry_ref.pullable_ref)
        # "registry.fly.io/code-insight@sha256:abc123..."
    """
```

### 4. Application Deployment

```python
async def deploy_application(
    image_ref: RegistryImageRef,
    *,
    app_name: str,
    region: str = "ewr",
    config: DeployConfig | None = None
) -> ApplicationURL:
    """
    Deploy application from registry image to Fly.io.

    Args:
        image_ref: Registry image reference (from publish_image)
        app_name: Fly.io app name
        region: Primary region
        config: Deployment configuration (resources, health checks, etc.)

    Returns:
        ApplicationURL: URL of deployed application

    Guarantees:
        - Application is deployed and accessible
        - Health checks passing
        - URL returns 200 OK on /info endpoint

    Caching:
        - Optional: Can cache by (image_ref.digest, app_name)
        - If same image already deployed, skip redeploy
        - Configurable: may want to always deploy for config changes

    Implementation:
        Uses: fly deploy --app {app_name} --image {image_ref.pullable_ref}

    Example:
        app_url = await deploy_application(registry_ref, app_name="test001")
        print(app_url.url)  # "https://test001.fly.dev"
    """
```

### 5. Complete Workflow

```python
async def deploy_from_source(
    app_name: str,
    *,
    repo_path: Path = Path("."),
    registry: str = "registry.fly.io",
    repository: str = "code-insight"
) -> ApplicationURL:
    """
    Complete deployment workflow: source → image → registry → deployment.

    This is the high-level function most users will call.

    Example:
        app_url = await deploy_from_source("test001")
        print(f"Deployed to: {app_url.url}")
    """
    # Each step type-enforced to use previous step's output
    tree_hash = await get_source_tree_hash(repo_path)
    local_image = await build_image(tree_hash)
    registry_ref = await publish_image(local_image, registry=registry, repository=repository)
    app_url = await deploy_application(registry_ref, app_name=app_name)
    return app_url
```

---

## Caching Specifications

### Caching Principles

1. **Content-based keys**: Cache keys are content hashes
2. **Never invalidate**: Deterministic functions → cache is always valid
3. **Safe to delete**: If cache entry deleted, recompute on next call
4. **Parallel-safe**: Multiple processes can read cache concurrently
5. **Write-safe**: Use atomic writes (write to temp, then rename)

### Cache Storage

**Location:**
```
~/.cache/flyio-deploy/
├── source-hashes/
│   └── {repo_path_hash}.json       # Last known tree hash (optimization)
├── images/
│   └── {source_hash}.json          # LocalImageRef for source hash
├── registry/
│   └── {digest}_{registry}.json    # RegistryImageRef for digest
└── deployments/
    └── {app_name}_{digest}.json    # ApplicationURL for deployment
```

**Format:**
```python
# Example: images/a3f2e19c8b2d1f4e.json
{
    "source_hash": "a3f2e19c8b2d1f4e6a7b9c0d2e3f5a6b7c8d9e0f",
    "name": "localhost/code-insight:a3f2e19",
    "digest": "sha256:abc123...",
    "built_at": "2025-12-24T17:30:00Z",  # Metadata only
    "buildah_version": "1.42.0"           # Metadata only
}
```

### Cache Lookup Algorithm

```python
async def build_image(source_hash: SourceTreeHash) -> LocalImageRef:
    # 1. Check cache
    cache_path = CACHE_DIR / "images" / f"{source_hash.value}.json"
    if cache_path.exists():
        cached = LocalImageRef.from_json(cache_path.read_text())

        # 2. Verify image still exists locally
        if await verify_local_image(cached):
            return cached  # Cache hit!

    # 3. Cache miss → build image
    image_ref = await _build_image_impl(source_hash)

    # 4. Save to cache (atomic write)
    await _save_to_cache(cache_path, image_ref)

    return image_ref
```

### Cache Verification

Each cache type has verification:

**Image cache:**
```python
async def verify_local_image(ref: LocalImageRef) -> bool:
    """Check if image exists locally with correct digest."""
    result = await run_buildah("inspect", "--format", "{{.FromImageDigest}}", ref.name)
    return result.stdout.strip() == ref.digest
```

**Registry cache:**
```python
async def verify_registry_image(ref: RegistryImageRef) -> bool:
    """Check if image exists in registry with correct digest."""
    result = await run_buildah("manifest", "inspect", ref.pullable_ref)
    return result.returncode == 0  # Image exists and is pullable
```

**Deployment cache:**
```python
async def verify_deployment(url: ApplicationURL) -> bool:
    """Check if application is deployed and healthy."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{url.url}/info", timeout=10)
            return response.status_code == 200
    except Exception:
        return False
```

---

## Pythonic Buildah Wrapper Requirements

### Design Goals

1. **Frozen dataclasses**: All objects immutable
2. **Async-first**: All I/O operations async
3. **Cached properties**: Computed values cached on objects
4. **Type-safe**: Strong typing throughout
5. **Clean API**: Hide subprocess details

### Core Objects

```python
@dataclass(frozen=True)
class BuildahImage:
    """
    Immutable reference to a buildah image.

    All properties are computed deterministically from the frozen fields.
    Use @cached_property for expensive computations.
    """
    name: str          # Image name/tag
    _digest: str | None = None  # Optional: digest if known

    @cached_property
    async def digest(self) -> str:
        """
        Get image digest (cached).

        Uses buildah inspect to get digest on first access,
        then caches the result on the object.
        """
        if self._digest is not None:
            return self._digest

        result = await run_buildah(
            "inspect",
            "--format", "{{.FromImageDigest}}",
            self.name
        )
        return result.stdout.strip()

    @cached_property
    async def created_at(self) -> datetime:
        """Get image creation timestamp (cached)."""
        result = await run_buildah(
            "inspect",
            "--format", "{{.Created}}",
            self.name
        )
        return datetime.fromisoformat(result.stdout.strip())

    @cached_property
    async def size_bytes(self) -> int:
        """Get image size in bytes (cached)."""
        result = await run_buildah(
            "inspect",
            "--format", "{{.Size}}",
            self.name
        )
        return int(result.stdout.strip())

    async def tag(self, new_name: str) -> "BuildahImage":
        """
        Tag image with new name, returning new BuildahImage.

        Returns new object (immutable), doesn't modify self.
        """
        await run_buildah("tag", self.name, new_name)
        digest = await self.digest  # Reuse cached digest
        return BuildahImage(name=new_name, _digest=digest)

    async def push(self, destination: str) -> None:
        """Push image to registry."""
        await run_buildah("push", self.name, destination)
```

```python
@dataclass(frozen=True)
class BuildahBuilder:
    """
    Builder for constructing images.

    Frozen dataclass: All configuration immutable.
    Build operations return BuildahImage objects.
    """
    dockerfile: Path
    context_path: Path
    build_args: dict[str, str] = field(default_factory=dict)
    target: str | None = None
    timestamp: int = 0  # Epoch for reproducibility

    async def build(self, tag: str) -> BuildahImage:
        """
        Build image with this configuration.

        Returns BuildahImage representing the built image.
        """
        args = ["build"]

        # Reproducibility
        args.extend(["--timestamp", str(self.timestamp)])

        # Tag
        args.extend(["--tag", tag])

        # Dockerfile
        if self.dockerfile.name != "Dockerfile":
            args.extend(["--file", str(self.dockerfile)])

        # Build args
        for key, value in self.build_args.items():
            args.extend(["--build-arg", f"{key}={value}"])

        # Target stage
        if self.target:
            args.extend(["--target", self.target])

        # Context
        args.append(str(self.context_path))

        # Execute build
        await run_buildah(*args)

        # Return image object
        return BuildahImage(name=tag)
```

### Subprocess Utilities

```python
@dataclass(frozen=True)
class CommandResult:
    """Result of subprocess command execution."""
    stdout: str
    stderr: str
    returncode: int

    def check(self) -> "CommandResult":
        """Raise exception if command failed."""
        if self.returncode != 0:
            raise BuildahError(
                f"Command failed with code {self.returncode}",
                stderr=self.stderr
            )
        return self


async def run_buildah(*args: str, check: bool = True) -> CommandResult:
    """
    Run buildah command asynchronously.

    Args:
        *args: Command arguments (e.g., "build", "--tag", "myimage")
        check: Raise exception on non-zero exit code

    Returns:
        CommandResult with stdout, stderr, returncode

    Example:
        result = await run_buildah("inspect", "--format", "{{.ID}}", "myimage")
        print(result.stdout)  # Image ID
    """
    cmd = ["buildah", *args]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    result = CommandResult(
        stdout=stdout.decode(),
        stderr=stderr.decode(),
        returncode=process.returncode
    )

    if check:
        result.check()

    return result
```

### Error Handling

```python
class BuildahError(Exception):
    """Base exception for buildah operations."""
    def __init__(self, message: str, *, stderr: str = ""):
        super().__init__(message)
        self.stderr = stderr


class ImageNotFoundError(BuildahError):
    """Image doesn't exist in local storage."""
    pass


class BuildFailedError(BuildahError):
    """Image build failed."""
    pass


class PushFailedError(BuildahError):
    """Image push to registry failed."""
    pass
```

---

## Implementation Contracts

### Contract 1: Source Tree Hashing

**Input:** Repository path
**Output:** SourceTreeHash

**Contracts:**
- MUST include all tracked files
- MUST include staged changes if `include_uncommitted=True`
- MUST include unstaged changes if `include_uncommitted=True`
- MUST return same hash for identical source state
- MUST return different hash for different source state
- Hash MUST equal commit tree SHA if no uncommitted changes

**Implementation Requirements:**
- Use `git write-tree` with temporary index
- Stage all changes to temporary index
- Compute tree hash
- Clean up temporary index

---

### Contract 2: Image Building

**Input:** SourceTreeHash, build configuration
**Output:** LocalImageRef

**Contracts:**
- Image name MUST be deterministic (derived from source hash)
- Image MUST exist locally after return
- Image digest MUST be reproducible (same source → same digest)
- Creation timestamp MUST be set to epoch (0)
- Function MUST be idempotent (calling twice has same effect)

**Implementation Requirements:**
- Use `buildah build --timestamp 0`
- Tag image with source hash: `localhost/code-insight:{hash}`
- Verify image exists before returning
- Cache result by source hash

---

### Contract 3: Image Publishing

**Input:** LocalImageRef, registry, repository
**Output:** RegistryImageRef

**Contracts:**
- Image MUST exist in registry after return
- Image MUST be pullable using returned reference
- Digest MUST match local image digest
- Function MUST be idempotent (pushing same image twice is safe)

**Implementation Requirements:**
- Use `buildah push`
- Verify registry has image (manifest inspect)
- Return reference with digest (not tag)
- Cache result by (digest, registry, repository)

---

### Contract 4: Application Deployment

**Input:** RegistryImageRef, app configuration
**Output:** ApplicationURL

**Contracts:**
- Application MUST be deployed after return
- URL MUST be accessible (HTTP 200 on health endpoint)
- Application MUST be running specified image
- Function MUST be idempotent (deploying same image twice is safe)

**Implementation Requirements:**
- Use `fly deploy --image {digest_ref}`
- Wait for health checks to pass
- Verify URL is accessible
- Return URL with image reference (traceability)

---

## Summary

This specification defines:

1. **Semi-functional approach**: Deterministic, cacheable, composable functions
2. **Buildah alignment**: Perfect match for reproducibility goals
3. **Type-safe API**: Frozen dataclasses with strong guarantees
4. **Caching strategy**: Content-based, never invalidated, safe to delete
5. **Pythonic wrapper**: Clean async API over buildah subprocess calls

**Next Steps (Lesson 06):**
- Implement `get_source_tree_hash()`
- Implement Pythonic buildah wrapper
- Implement build/push/deploy functions
- Add caching layer
- Write integration tests
- Create CLI tool

The implementation will follow these requirements strictly to ensure correctness, consistency, and reliability.
