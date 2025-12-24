# Lesson 01: Hello World on Fly.io

## Executive Summary

This lesson provides a comprehensive introduction to Fly.io, covering installation, deployment, and advanced features like custom domains and automation. You'll learn how to deploy applications using existing Docker images, manage machines through both interactive and automated workflows, and configure custom domains with automatic SSL certificates.

**Key achievements:**
- Install and configure flyctl on Linux
- Deploy applications with zero configuration using `fly launch`
- Understand Fly.io's auto-scaling and high-availability features
- Master automation flags for scriptable deployments
- Configure custom domains with automatic Let's Encrypt certificates
- Verify that app names can be reused after deletion

**Time to complete:** 1-2 hours (including DNS propagation time)

---

## Table of Contents

1. [Installing flyctl on Linux](#part-1-installing-flyctl-on-linux)
   - Installation Command
   - What the Installation Script Does
   - Troubleshooting (NetFree/Content Filtering)
   - After Installation

2. [Create an Ephemeral Fly Machine with Shell Access](#part-2-create-an-ephemeral-fly-machine-with-shell-access)
   - Prerequisites: Account Setup
   - First-Time Authentication
   - The Command
   - Real-World Example
   - Cleanup of Pending Apps

3. [Deploy a "Hello World" Server](#part-3-deploy-a-hello-world-server)
   - Non-Interactive Deployment with Custom Name
   - Real-World Deployment Example (Interactive)
   - Key Observations
   - The Generated fly.toml Configuration
   - Verify Deployment
   - Optional Experiments Before Cleanup
   - Cleanup

4. [Using a Custom Domain](#using-a-custom-domain)
   - Step-by-step certificate and DNS setup
   - Verification and troubleshooting

5. [Complete Walkthrough: Non-Interactive Deployment with Custom Domain](#complete-walkthrough-non-interactive-deployment-with-custom-domain)
   - Full automation workflow
   - Testing app name reusability
   - Custom domain configuration
   - Complete cleanup

6. [Key Concepts Learned](#key-concepts-learned)

7. [Additional Resources](#additional-resources)

---

## Prerequisites
- A Linux machine with curl installed
- Internet connection
- (Optional) A custom domain for the custom domain exercises

---

## Part 1: Installing flyctl on Linux

### Installation Command
The recommended way to install flyctl on Linux is using the official installation script:

```bash
curl -L https://fly.io/install.sh | sh
```

**Documentation:** https://fly.io/docs/flyctl/install/

### What Does the Installation Script Do?

I've analyzed the installation script (`install.sh`). Here's what it does:

1. **Detects your system:** Determines your OS (using `uname -s`) and architecture (using `uname -m`)

2. **Downloads the correct binary:**
   - Queries Fly.io's API to get the download URL for the appropriate flyctl release
   - Downloads the tarball to `~/.fly/tmp/`
   - Supports version selection (latest, prerel, or specific versions via arguments)

3. **Installs flyctl:**
   - Extracts to `~/.fly/bin/flyctl`
   - Creates a symlink `~/.fly/bin/fly` pointing to `flyctl`
   - Sets executable permissions
   - Uses atomic operations (extract to temp, then move) to avoid corrupting existing installations

4. **PATH configuration (interactive):**
   - Detects your shell (bash or zsh)
   - Checks if flyctl is already in your PATH
   - If not, offers to automatically add it to your shell configuration:
     - For bash: Checks `~/.bashrc.d/`, `~/.bashrc`, or `~/.bash_profile`
     - For zsh: Checks `~/.zshrc.d/` or `~/.zshrc`
   - Adds these lines if you accept:
     ```bash
     export FLYCTL_INSTALL="$HOME/.fly"
     export PATH="$FLYCTL_INSTALL/bin:$PATH"
     ```

5. **Non-interactive mode:**
   - Supports `--non-interactive` flag (skips PATH prompts)
   - Supports `--setup-path` flag (automatically configures PATH)
   - Detects piped input (non-TTY) and disables prompts

**Installation location:** `~/.fly/bin/flyctl` (and symlink `~/.fly/bin/fly`)

**Script options:**
- `--non-interactive`: Skip interactive prompts
- `--setup-path`: Automatically add to PATH
- `prerel` or `pre`: Install pre-release version
- `latest`: Install latest stable (default)
- Version number (e.g., `v0.1.23`): Install specific version

### Troubleshooting: NetFree or Content Filtering

**Issue encountered:** When using NetFree or other content filtering systems, the installation script may fail with:
```
curl: (3) URL using bad/illegal format or missing URL
```

**Root cause:** The script queries `https://api.fly.io/app/flyctl_releases/$os/$arch/$version` to get the download URL. When this API call is blocked, it returns HTML instead of the expected URL, causing the subsequent `curl` command to fail.

**Solution:** Open `api.fly.io` in NetFree settings before running the installation script. This domain is required for:
- Installation (downloading flyctl)
- API operations in subsequent exercises

After opening api.fly.io, the standard installation works:
```bash
curl -L https://fly.io/install.sh | sh
```

**Alternative workaround - Manual installation from GitHub (if you cannot open api.fly.io):**

```bash
# 1. Find the latest release for Linux x86_64
curl -s https://api.github.com/repos/superfly/flyctl/releases/latest | \
  grep "browser_download_url.*Linux_x86_64" | head -1

# 2. Install manually (using the URL from step 1)
mkdir -p ~/.fly/bin
cd ~/.fly/bin
curl -L https://github.com/superfly/flyctl/releases/download/v0.3.236/flyctl_0.3.236_Linux_x86_64.tar.gz | tar xz
ln -sf flyctl fly

# 3. Verify installation
./flyctl version

# 4. Add to PATH
echo 'export PATH="$HOME/.fly/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 5. Verify it's in PATH
flyctl version
```

**Note:** Replace the version number (v0.3.236) with the latest version from the GitHub releases page: https://github.com/superfly/flyctl/releases

### Alternative: Manual Installation Steps

If you prefer to review the script first before running it:

```bash
# 1. Download and review the script
curl -L https://fly.io/install.sh > /tmp/fly-install.sh
less /tmp/fly-install.sh

# 2. Run the reviewed script
sh /tmp/fly-install.sh

# 3. Follow the prompts to configure your PATH
# Or run with: sh /tmp/fly-install.sh --setup-path
```

### After Installation

After installation completes, you'll need to either:
- Open a new terminal (PATH will be configured automatically), OR
- Source your shell config file:
  ```bash
  source ~/.bashrc  # for bash
  # or
  source ~/.zshrc   # for zsh
  ```

Verify the installation:
```bash
flyctl version
# or
fly version
```

---

## Part 2: Create an Ephemeral Fly Machine with Shell Access

Fly.io provides a powerful feature to create temporary machines for quick testing and exploration. These machines are automatically cleaned up when you exit.

### Prerequisites: Account Setup

**IMPORTANT:** Before running any Fly.io commands, ensure you have:
1. A Fly.io account with authentication completed
2. **A payment method added** (credit card) OR an active trial period

If you try to create resources without a payment method, the command will fail partway through and leave a "pending" app that needs manual cleanup.

### First-Time Authentication

The first time you run a Fly.io command, you'll be prompted to authenticate:

```bash
fly machine run --shell
```

Expected authentication flow:
```
? You must be logged in to do this. Would you like to sign in? Yes
Opening https://fly.io/app/auth/cli/[TOKEN] ...
Waiting for session... Done
successfully logged in as your.email@example.com
automatically selected personal organization: Your Name
```

**Authentication options:**
- Login with Google
- Login with GitHub
- Login with email

**Account verification:**
After logging in, Fly.io will prompt you to verify your account by adding a credit card before you can create resources. Complete this step to avoid errors.

### The Command

```bash
fly machine run --shell
```

**Documentation:** https://fly.io/docs/machines/flyctl/fly-machine-run/

### What This Does

- Creates a **temporary Fly machine** (default: Ubuntu image)
- Creates a **temporary app** (if no app context exists)
- Provides an **interactive shell** (default: bash)
- **Auto-cleanup:** When you exit the shell, the machine AND app are automatically deleted
- The machine runs in Fly.io's infrastructure (not locally)

### Real-World Example

After authentication and account verification:

```bash
$ fly machine run --shell
Searching for image 'ubuntu' remotely...
image found: img_dozgpeo9o2d9v096
Image: docker-hub-mirror.fly.io/library/ubuntu:latest@sha256:4fdf0125919d...
Image size: 30 MB

Success! A Machine has been successfully launched in app flyctl-interactive-shells-...
 Machine ID: 89d52ec6669268
Connecting to fdaa:3a:fb19:a7b:e:d2e:53ba:2... complete
root@89d52ec6669268:/# ls
bin   dev  home  lib64  mnt  proc  run   srv  tmp  var
boot  etc  lib   media  opt  root  sbin  sys  usr
root@89d52ec6669268:/# exit
```

**Key observations:**
- Fly.io uses a Docker Hub mirror (`docker-hub-mirror.fly.io`) for faster image pulls
- The machine is assigned a unique ID
- You get a root shell by default
- The hostname matches the machine ID
- Standard Ubuntu filesystem layout

### Options

```bash
# Use default Ubuntu image
fly machine run --shell

# Use a specific Docker image
fly machine run debian --shell

# Use a different shell (if bash isn't available)
fly machine run alpine --shell --command /bin/sh

# Use a non-root user
fly machine run --shell --user nobody
```

### Cleanup of Pending Apps

**Good news:** Fly.io automatically cleans up incomplete resources! If you encounter an error during resource creation (like the authentication/payment issue above), Fly.io will detect the incomplete state and auto-cleanup the pending app after a short time.

**Manual cleanup (if needed):**
If you need to clean up immediately or have lingering apps:

```bash
# List all apps
fly apps list

# Destroy a specific app
fly apps destroy <app-name>
```

---

## Part 3: Deploy a "Hello World" Server

Now let's deploy a real web service using an existing Docker image. Fly.io provides a demo image called `flyio/hellofly:latest` that's perfect for this.

### The Command

```bash
fly launch --image flyio/hellofly:latest
```

**Documentation:** https://fly.io/docs/getting-started/launch-demo/

### What This Does

1. **Prompts for configuration:**
   - App name (auto-generated or derived from directory name)
   - Region selection (automatically suggests fastest region)
   - Optional services (Postgres, Redis, Tigris)
   - Machine configuration (CPU, RAM)

2. **Creates `fly.toml`:** A configuration file with sensible defaults

3. **Deploys the image:** Pulls `flyio/hellofly:latest` from Fly.io's Docker Hub mirror

4. **Allocates resources:** Creates machines, assigns IP addresses, configures DNS

5. **Provides a URL:** Gives you a `https://<app-name>.fly.dev` URL to access your app

### Non-Interactive Deployment with Custom Name

For automation and scripting, you can skip all prompts and specify your app name:

```bash
fly launch --image flyio/hellofly:latest --name code-insight --yes
```

**Flags:**
- `--name code-insight`: Specifies your custom app name (creates `code-insight.fly.dev`)
- `--yes` (or `-y`): Accepts all defaults without prompting
- Optional: `--now` to deploy immediately, `--detach` to return without monitoring

**About app name reuse:**
The documentation doesn't explicitly state whether app names become available after deletion. This should be tested empirically. Network names are permanently associated with their IDs and never reused within an organization, which suggests app names might follow similar rules.

**Documentation:** https://fly.io/docs/flyctl/launch/

### Real-World Deployment Example (Interactive)

```bash
$ fly launch --image flyio/hellofly:latest
Using image flyio/hellofly:latest
Creating app in /root

We're about to launch your app on Fly.io. Here's what you're getting:

Organization: Yaakov Belch               (fly launch defaults to the personal org)
Name:         root-small-wildflower-9689 (generated)
Region:       Secaucus, NJ (US)          (this is the fastest region for you)
App Machines: shared-cpu-1x, 1GB RAM     (most apps need about 1GB of RAM)
Postgres:     <none>                     (not requested)
Redis:        <none>                     (not requested)
Tigris:       <none>                     (not requested)

? Do you want to tweak these settings before proceeding? No

Created app 'root-small-wildflower-9689' in organization 'personal'

Admin URL: https://fly.io/apps/root-small-wildflower-9689
Hostname: root-small-wildflower-9689.fly.dev
Wrote config file fly.toml
Validating /root/fly.toml
✓ Configuration is valid

==> Building image
Searching for image 'flyio/hellofly:latest' remotely...
image found: img_e1zd4mjy6gn402yw

Watch your deployment at https://fly.io/apps/root-small-wildflower-9689/monitoring

Provisioning ips for root-small-wildflower-9689
  Dedicated ipv6: 2a09:8280:1::be:c80:0
  Shared ipv4: 66.241.125.101
  Add a dedicated ipv4 with: fly ips allocate-v4

This deployment will:
 * create 2 "app" machines

No machines in group app, launching a new machine
Creating a second machine for high availability and zero downtime deployments.
To disable this, set "min_machines_running = 0" in your fly.toml.
Finished launching new machines
-------
 ✔ Machine 1859397c97d548 [app] update finished: success
NOTE: The machines for [app] have services with 'auto_stop_machines = "stop"' that will be stopped when idling

-------
Checking DNS configuration for root-small-wildflower-9689.fly.dev
✓ DNS configuration verified

🎉  SUCCESS! Your app is live and ready to use!  🎉

Visit: https://root-small-wildflower-9689.fly.dev/
```

### Key Observations

**1. High Availability by Default:**
- Fly.io automatically creates **2 machines** for high availability and zero-downtime deployments
- This can be disabled by setting `min_machines_running = 0` in `fly.toml`
- Note for future exercises: Investigate how these 2 machines work (active/standby? load balanced?)

**2. Auto-Stop Machines:**
- Machines have `auto_stop_machines = "stop"` configured
- They will automatically stop when idle to save resources
- They restart automatically when traffic arrives

**3. IP Addresses:**
- **Dedicated IPv6** assigned automatically (free)
- **Shared IPv4** assigned automatically (free, shared with other apps)
- Optional: Can allocate a dedicated IPv4 with `fly ips allocate-v4` (costs extra)

**4. Region Selection:**
- Fly.io automatically detects the fastest region based on your location
- Can be customized during the launch prompts

### Expected Output

When you visit `https://<your-app-name>.fly.dev`, you should see:

```html
<!DOCTYPE html>
<html lang="en">
<head>
</head>
<body>
<h1>Hello from Fly</h1>
</body>
</html>
```

You can also test with curl:
```bash
curl https://<your-app-name>.fly.dev/
```

### The Generated fly.toml Configuration

The `fly launch` command created a `fly.toml` configuration file in your current directory. Here's what it contains:

```toml
# fly.toml app configuration file generated for root-small-wildflower-9689 on 2025-12-24T13:29:29Z
#
# See https://fly.io/docs/reference/configuration/ for information about how to use this file.
#

app = 'root-small-wildflower-9689'
primary_region = 'ewr'

[build]
  image = 'flyio/hellofly:latest'

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
  memory_mb = 1024
```

**Configuration breakdown:**

- **`app`**: Unique app name on Fly.io
- **`primary_region`**: The region where your app is deployed (`ewr` = Secaucus, NJ)
- **`[build]`**: Specifies the Docker image to use
- **`[http_service]`**: HTTP service configuration
  - `internal_port = 8080`: The app listens on port 8080 inside the container
  - `force_https = true`: Automatically redirect HTTP to HTTPS
  - `auto_stop_machines = 'stop'`: Stop machines when idle
  - `auto_start_machines = true`: Start machines automatically when traffic arrives
  - `min_machines_running = 0`: Allow all machines to stop when idle (saves costs)
  - `processes = ['app']`: Which process groups this service applies to
- **`[[vm]]`**: Virtual machine configuration
  - `memory = '1gb'`: 1GB of RAM
  - `cpu_kind = 'shared'`: Shared CPU (not dedicated)
  - `cpus = 1`: Single CPU core

**Key insight:** The `min_machines_running = 0` combined with `auto_stop_machines = 'stop'` means your app can scale to zero when not in use, saving resources and costs. When a request arrives, Fly.io automatically starts a machine.

**Documentation:** https://fly.io/docs/reference/configuration/

### Verify Deployment

After deployment, you can check the status and view logs:

```bash
fly status
```

**Output:**
```
App
  Name     = root-small-wildflower-9689
  Owner    = personal
  Hostname = root-small-wildflower-9689.fly.dev
  Image    = flyio/hellofly:latest

Machines
PROCESS    ID                VERSION    REGION    STATE      ROLE    CHECKS    LAST UPDATED
app        1859397c97d548    1          ewr       stopped                      2025-12-24T13:37:17Z
app        833e41a7773658    1          ewr       started                      2025-12-24T13:29:34Z
```

**Key observations:**
- Shows 2 machines (high availability setup)
- One is **stopped** (auto-stopped due to idle)
- One is **started** (handling requests)
- Both are in the same region (`ewr`)

```bash
fly logs
```

**Key log insights:**

1. **Container startup:**
   - Uses Firecracker VM (version 1.12.1) for isolation
   - Pulls from `docker-hub-mirror.fly.io`
   - Container already prepared (cached)

2. **Application details:**
   - Built with Go and Gin web framework
   - Listens on port 8080 internally
   - Two route handlers: `GET /` and `GET /:name`
   - SSH access available on each machine

3. **Auto-scaling behavior:**
   ```
   App root-small-wildflower-9689 has excess capacity, autostopping machine 1859397c97d548.
   1 out of 2 machines left running
   ```
   - After ~3 minutes of low traffic, Fly.io stopped one machine
   - Demonstrates the auto-stop feature in action
   - Saves resources while maintaining availability

4. **HTTP requests logged:**
   - Shows actual requests with response times (250µs - 2.8ms)
   - Client IP addresses visible
   - Both machines handled requests (load balancing)

**Other useful commands:**

```bash
# Open the app in your browser
fly open

# SSH into a running machine
fly ssh console

# List all machines
fly machines list

# View logs with real-time streaming (default behavior)
fly logs
# Press Ctrl+C to stop streaming

# View logs without streaming (one-time snapshot)
fly logs --no-tail
```

### Optional Experiments Before Cleanup

Before destroying the app, you might want to try:

1. **Test the auto-start feature:**
   - Wait for both machines to stop (check with `fly status`)
   - Visit the URL and observe auto-start in logs

2. **Test the URL pattern:**
   - Visit `https://root-small-wildflower-9689.fly.dev/YourName`
   - The app has a `GET /:name` handler

3. **SSH into a machine:**
   ```bash
   fly ssh console
   ```

   **Inside the container, you'll find:**

   - **Fly.io environment variables** (visible with `env`):
     - `FLY_APP_NAME`: Your app name
     - `FLY_REGION`: Current region (e.g., `ewr`)
     - `FLY_MACHINE_ID`: Unique machine identifier
     - `FLY_PRIVATE_IP`: IPv6 private address (fdaa:...)
     - `FLY_PUBLIC_IP`: IPv6 public address
     - `FLY_VM_MEMORY_MB`: Memory allocation
     - `FLY_IMAGE_REF`: Docker image reference
     - `PRIMARY_REGION`: The primary deployment region

   - **Fly.io infrastructure**:
     - `/fly/init`: Fly.io's init system (PID 1)
     - `/.fly/hallpass`: Authentication proxy
     - `/.fly/api`: Internal Fly.io API proxy

   - **Application files** (for hellofly example):
     - `/goapp/app`: The Go binary
     - `/goapp/resources/templates/`: HTML templates

4. **Scale the app:**
   ```bash
   fly scale count 3  # Add more machines
   fly status        # Verify 3 machines
   fly scale count 1  # Scale down
   ```

   **Key observations from scaling:**
   - Scaling up creates new machines instantly (~2 seconds)
   - Scaling down **destroys** machines (not just stops them)
   - When you scale down from 3 to 1, Fly.io intelligently chooses which machines to destroy
   - The newly created machine (when scaling up) stays running initially
   - Machines get friendly names like "frosty-grass-4829" and "still-breeze-9546"

5. **Check machine details:**
   ```bash
   fly machines list
   fly machine status <machine-id>
   ```

### Cleanup

When you're done experimenting:

```bash
# Destroy the app and all resources
fly apps destroy <your-app-name>
```

**Example:**
```bash
$ fly apps destroy root-small-wildflower-9689
Destroying an app is not reversible.
? Destroy app root-small-wildflower-9689? Yes
Destroyed app root-small-wildflower-9689
```

**Verification:**
After destroying the app, attempts to access it will fail (as expected):
```bash
$ fly status
Error: failed to get app: Could not find App "root-small-wildflower-9689"

$ fly logs
Error: 401 Unauthorized
```

This confirms the app and all its resources have been completely removed.

---

## Using a Custom Domain

You can point your own domain (e.g., `code-insight.yaakovnet.net`) to your Fly.io app instead of using the default `*.fly.dev` domain.

### Step 1: Add a Certificate

```bash
fly certs add code-insight.yaakovnet.net
```

This command:
- Registers your custom domain with the app
- Initiates the Let's Encrypt TLS certificate process
- Provides DNS validation instructions

**Documentation:** https://fly.io/docs/networking/custom-domain/

### Step 2: View Certificate Status and DNS Instructions

```bash
fly certs show code-insight.yaakovnet.net
```

**Example output:**
```
Hostname                    = code-insight.yaakovnet.net
Configured                  = false
Issued                      =
Certificate Authority       = lets_encrypt
DNS Provider                =
DNS Validation Instructions = CNAME _acme-challenge.code-insight.yaakovnet.net => code-insight.yaakovnet.net.5xzw.flydns.net.
DNS Validation Hostname     = _acme-challenge.code-insight.yaakovnet.net
DNS Validation Target       = code-insight.yaakovnet.net.5xzw.flydns.net
Source                      = fly
Created At                  = 1m ago
Status                      = Pending
```

### Step 3: Configure DNS Records

Add two DNS records at your domain registrar:

**1. CNAME for the domain (points to your app):**
```
code-insight.yaakovnet.net CNAME code-insight.fly.dev
```

**2. CNAME for ACME validation (for Let's Encrypt):**
```
_acme-challenge.code-insight.yaakovnet.net CNAME code-insight.yaakovnet.net.5xzw.flydns.net
```

**Note:** The exact validation target will be provided by `fly certs show`.

### Step 4: Verify Certificate Issuance

After DNS propagates (usually 5-30 minutes):

```bash
fly certs check code-insight.yaakovnet.net
```

Once `Configured = true` and `Status = Ready`, your custom domain is live!

### Additional Commands

```bash
# List all certificates
fly certs list

# Remove a certificate
fly certs remove code-insight.yaakovnet.net
```

### Wildcard Domains

You can also add wildcard certificates:

```bash
fly certs add "*.yaakovnet.net"
```

**Important:** Use quotes to prevent shell expansion.

---

## Complete Walkthrough: Non-Interactive Deployment with Custom Domain

This section demonstrates a complete end-to-end workflow using automation flags and custom domains.

### Scenario

Deploy an app named `test001`, verify it works, test name reusability, add a custom domain, and clean up.

### Step 1: Deploy with Automation Flags

```bash
fly launch --image flyio/hellofly:latest --name test001 --yes
```

**Result:**
- No prompts - fully automated
- App created: `test001`
- URL: `https://test001.fly.dev/`
- 2 machines created automatically
- IPv4 (shared): `66.241.124.72`
- IPv6 (dedicated): `2a09:8280:1::be:f80:0`

**Verify:**
```bash
curl https://test001.fly.dev/
# Returns: Hello from Fly
```

### Step 2: Test App Deletion

```bash
fly apps destroy test001 -y
```

**Result:**
- App and all resources destroyed
- `-y` flag skips confirmation prompt (automation-friendly)

**Verify:**
```bash
fly status
# Returns: Could not find App "test001"
```

### Step 3: Test Name Reusability ✅

**Key Question:** Can we reuse the name "test001" after deletion?

```bash
fly launch --image flyio/hellofly:latest --name test001 --yes
```

**Result:** ✅ **SUCCESS! App names CAN be reused immediately after deletion**

- App recreated with same name: `test001`
- New IP addresses allocated (different from first deployment)
- No errors or conflicts

**Important finding:** Unlike network names (which are permanently associated with IDs), app names become available immediately after `fly apps destroy`.

### Step 4: Add Custom Domain

```bash
fly certs add test001.yaakovnet.net
```

**Output provides three DNS setup options:**

1. **A and AAAA records (recommended):**
   ```
   A    test001.yaakovnet.net → 66.241.124.72
   AAAA test001.yaakovnet.net → 2a09:8280:1::be:f80:0
   ```

2. **CNAME record:**
   ```
   CNAME test001.yaakovnet.net → n2nn1z1.test001.fly.dev
   ```

3. **ACME DNS Challenge (for wildcard or pre-validation):**
   ```
   CNAME _acme-challenge.test001.yaakovnet.net → test001.yaakovnet.net.n2nn1z1.flydns.net
   ```

### Step 5: Configure DNS

Add records at your DNS provider (e.g., NearlyFreeSpeech.NET):

```
test001.yaakovnet.net           A     66.241.124.72           TTL 180
test001.yaakovnet.net           AAAA  2a09:8280:1::be:f80:0   TTL 180
_acme-challenge.test001.yaakovnet.net  CNAME  test001.yaakovnet.net.n2nn1z1.flydns.net  TTL 180
```

### Step 6: Verify DNS Propagation

```bash
dig test001.yaakovnet.net A +short
# Returns: 66.241.124.72

dig test001.yaakovnet.net AAAA +short
# Returns: 2a09:8280:1::be:f80:0

dig _acme-challenge.test001.yaakovnet.net CNAME +short
# Returns: test001.yaakovnet.net.n2nn1z1.flydns.net.
```

### Step 7: Check Certificate Status

```bash
fly certs check test001.yaakovnet.net
```

**Output:**
```
Status                    = Ready
Hostname                  = test001.yaakovnet.net
DNS Provider              = nearlyfreespeech
Certificate Authority     = Let's Encrypt
Issued                    = rsa,ecdsa
Added to App              = 7 minutes ago
Expires                   = 2 months from now
Source                    = fly

✓ Your certificate has been issued!
Your DNS is correctly configured and this certificate will auto-renew before expiration.
```

**Key observations:**
- Fly.io automatically detected DNS provider (nearlyfreespeech)
- Both RSA and ECDSA certificates issued
- Auto-renewal configured
- Certificate issuance is typically very fast (can be virtually immediate once DNS propagates)

### Step 8: Test Custom Domain

```bash
curl https://test001.yaakovnet.net/
```

**Result:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
</head>
<body>
<h1>Hello from Fly</h1>
</body>
</html>
```

✅ **Custom domain working with HTTPS!**

### Step 9: Complete Cleanup

```bash
# Remove certificate
fly certs remove test001.yaakovnet.net

# Destroy app
fly apps destroy test001 -y

# Remove local config
rm fly.toml

# Remove DNS records from your provider
# (via your DNS provider's control panel)
```

**Verification:**
```bash
fly status
# Returns: Could not find App "test001"
```

### Summary of Automation Flags

**For deployment:**
```bash
fly launch --name <app-name> --yes [--image <image>]
```

**For destruction:**
```bash
fly apps destroy <app-name> -y
```

These flags enable fully automated, scriptable workflows with no user interaction required.

---

## Key Concepts Learned

1. **flyctl installation:** Single-command installation with automatic PATH configuration
2. **Ephemeral machines:** Perfect for quick testing without leaving resources behind
3. **Docker image deployment:** Can deploy any public Docker image with `fly launch --image`
4. **Non-interactive deployment:** Use `--name` and `--yes` flags for automation (also `-y` for destruction)
5. **App name reusability:** App names become available immediately after deletion
6. **fly.toml:** Configuration file that defines your app's infrastructure
7. **Automatic HTTPS:** Every app gets a secure `https://*.fly.dev` URL
8. **Custom domains:** Point your own domain to Fly.io apps with automatic Let's Encrypt certificates
9. **Auto-scaling:** Machines auto-stop when idle and auto-start on traffic
10. **High availability:** 2 machines deployed by default for zero-downtime deployments
11. **Certificate management:** Automatic Let's Encrypt certificates with auto-renewal

---

## Additional Resources

- [Fly.io Docs](https://fly.io/docs/)
- [flyctl Reference](https://fly.io/docs/flyctl/)
- [Machines API](https://fly.io/docs/machines/)
- [Getting Started Guide](https://fly.io/docs/getting-started/)
