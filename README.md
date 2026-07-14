# sdk-actions

Centralized, versioned GitHub Actions for the Twilio SDK fleet — reusable
workflows defined **once** here and consumed **by reference** so CI/publish
guards can't be weakened per-repo.

Implements the **build-public, gate-internal, publish-public** pattern from
**ADR 1634** (Rule 3b delivery). Tracked in **PEA-1331**.

> This repo is `internal`-visibility. Its Actions access allows use by other
> repositories in the `twilio` org, so public `twilio/*` SDK repos can call
> these reusable workflows.

## Naming convention

Reusable workflows must live flat in `.github/workflows/` (GitHub forbids
subdirectories), so they are namespaced by **ecosystem** via a filename prefix.

| Prefix | Ecosystem | Status |
|--------|-----------|--------|
| `node-*` | JS/TS — npm, yarn, pnpm | ✅ available |
| `lerna-*` | JS/TS monorepos (Lerna) | ✅ available |
| `python-*` / `pypi-*` | Python | ⏳ planned (PEA-1325) |
| `maven-*`, `nuget-*` | JVM / .NET | 🔜 future |

## What's here

| Workflow | For | Purpose |
|----------|-----|---------|
| [`node-ci.yml`](.github/workflows/node-ci.yml) | any JS/TS repo | **Lockfile-hygiene gate** (scan + clean-room public install) + fork-aware test matrix with Artifactory OIDC (skipped on forks). |
| [`node-publish.yml`](.github/workflows/node-publish.yml) | **single-package** repo | Release publish to public npm via **OIDC trusted publishing**, owner-guarded + environment-gated, with tag↔version validation. |
| [`lerna-publish.yml`](.github/workflows/lerna-publish.yml) | **monorepo** (Lerna) | Publishes unpublished package versions via `lerna publish`. No single tag↔version check (independent versioning). |

All three support **npm / yarn / pnpm** via the `package-manager` input (drives
`corepack enable` + the default install command). Build/test tooling can be any
package manager; **publishing is always via `npm`/`lerna→npm`** because only npm
supports OIDC trusted publishing + provenance. The OIDC step inlines the
Artifactory token exchange, so consumers drop any per-repo
`.github/actions/artifactory-oidc` composite action.

## The lockfile-hygiene gate (ADR 1634 Rule 3b)

Two secret-less jobs that run identically on fork and same-repo PRs:

1. **`lockfile-scan`** — fail closed if any tracked lockfile / resolver config
   (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `.npmrc`, `.yarnrc.yml`,
   including nested monorepo ones) names a non-public registry host. A lockfile
   pinned to internal Artifactory silently breaks external installs.
2. **`clean-room-install`** — install against **public registries only** (no
   Artifactory, no OIDC, no secrets), proving an external consumer can install.

## Consuming: CI

```yaml
# .github/workflows/ci.yml in twilio/<sdk-repo>
name: CI
on:
  push:
    branches: [main]      # or master — match your default branch
  pull_request:
  workflow_dispatch:

jobs:
  ci:
    uses: twilio/sdk-actions/.github/workflows/node-ci.yml@<sha>  # v1.2.3
    permissions:
      contents: read
      id-token: write     # required for Artifactory OIDC on org (non-fork) runs
    with:
      package-manager: yarn            # npm | yarn | pnpm
      node-versions: '[22, 24]'
      typecheck-command: ''            # empty string skips a step
      test-command: 'npm run test:unit' # heavy suite can stay on the repo's other CI
```

## Consuming: Publish (single package)

```yaml
# .github/workflows/publish.yml in twilio/<sdk-repo>
name: Publish
on:
  release:
    types: [published]

jobs:
  publish:
    uses: twilio/sdk-actions/.github/workflows/node-publish.yml@<sha>  # v1.2.3
    permissions:
      contents: read
      id-token: write
    with:
      package-manager: npm
      # tag-prefix: ''        # un-prefixed tags like 2.18.3 (e.g. twilio-voice.js)
      # provenance: false     # REQUIRED for private (twilio-internal/*) sources
      # org-owner: twilio-internal
```

## Consuming: Publish (Lerna monorepo)

```yaml
jobs:
  publish:
    uses: twilio/sdk-actions/.github/workflows/lerna-publish.yml@<sha>  # v1.2.3
    permissions:
      contents: read
      id-token: write
    with:
      package-manager: yarn
      # publish-command: 'npx lerna publish from-git --yes'  # if you tag versions
```

> **Names are load-bearing.** The npm trusted-publisher binding matches the
> **caller's** workflow filename and the `environment` (`production`). Keep the
> filename, the GitHub Environment, and the npm trusted-publisher registration
> identical or every OIDC publish fails. For Lerna, register **one publisher per
> published package name**, all pointing at `lerna-publish.yml` + `production`.

## Versioning & pinning

> **Org policy: SHA-pin.** `@v1`-style tags on `uses:` are rejected org-wide —
> including reusable-workflow references. Consumers **must pin a full commit
> SHA** with the version in a trailing comment:
>
> ```yaml
> uses: twilio/sdk-actions/.github/workflows/node-ci.yml@<40-char-sha>  # v1.2.3
> ```

Releases are cut as `vMAJOR.MINOR.PATCH` via GitHub Releases (following the
`twilio-internal/github-actions-library` precedent). Breaking input/behavior
changes bump the major. Dependabot bumps the SHA in consumer repos.

## Ownership & contribution

See [`.github/CODEOWNERS`](.github/CODEOWNERS). Changes require owner review
because they affect every consuming SDK repo. Test against a pilot repo before
cutting a release.

## Adoption status (PEA-1331)

- [x] Central repo + reusable Node CI/publish guards (npm/yarn/pnpm, single + Lerna monorepo).
- [ ] Adopt across the SDK repos (typescript / python / aws / microsoft).
- [ ] Wire as an org-level required check (ruleset) so PRs can't weaken the gate.
- [ ] `python-*` / `pypi-*` workflows (PEA-1325).
- [ ] Roll out across orgs: `twilio`, `twilio-internal`, `segmentio`, `sendgrid`.
