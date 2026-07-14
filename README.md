# sdk-actions

Centralized, versioned GitHub Actions for the Twilio SDK fleet — reusable
workflows defined **once** here and consumed **by reference** so CI/publish
guards can't be weakened per-repo.

Implements the **build-public, gate-internal, publish-public** pattern from
**ADR 1634** (Rule 3b delivery). Tracked in **PEA-1331**.

> This repo is `internal`-visibility. Its Actions access is set to allow use by
> other repositories in the `twilio` org, so public `twilio/*` SDK repos can call
> these reusable workflows.

## What's here

| Workflow | Purpose |
|----------|---------|
| [`.github/workflows/sdk-ci.yml`](.github/workflows/sdk-ci.yml) | PR/push CI: **lockfile-hygiene gate** + fork-aware test matrix with Artifactory OIDC (skipped on forks). |
| [`.github/workflows/sdk-publish.yml`](.github/workflows/sdk-publish.yml) | Release publish to public npm via **OIDC trusted publishing**, owner-guarded and gated by a GitHub Environment. |

Both inline the Artifactory OIDC token exchange, so consumers no longer need a
per-repo `.github/actions/artifactory-oidc` composite action.

## Consuming: CI

Replace the SDK repo's inline `ci.yml` body with a thin caller:

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
    uses: twilio/sdk-actions/.github/workflows/sdk-ci.yml@v1
    permissions:
      contents: read
      id-token: write     # required for Artifactory OIDC on org (non-fork) runs
    with:
      node-versions: '[22, 24]'
      # Trim to scripts that exist and run on a plain ubuntu runner.
      # Empty string skips a step:
      typecheck-command: ''            # repo has no standalone typecheck
      test-command: 'npm run test:unit' # heavy suite stays on the repo's other CI
```

## Consuming: Publish

```yaml
# .github/workflows/publish.yml in twilio/<sdk-repo>
name: Publish
on:
  release:
    types: [published]

jobs:
  publish:
    uses: twilio/sdk-actions/.github/workflows/sdk-publish.yml@v1
    permissions:
      contents: read
      id-token: write
    with:
      # tag-prefix: ''        # for un-prefixed tags like 2.18.3 (e.g. twilio-voice.js)
      # provenance: false     # REQUIRED for private (twilio-internal/*) source repos
      # org-owner: twilio-internal
```

> **Names are load-bearing.** The npm trusted-publisher binding matches the
> **caller's** workflow filename (e.g. `publish.yml`) and the `environment`
> (`production`). Keep the workflow filename, the GitHub Environment, and the npm
> trusted-publisher registration identical or every OIDC publish fails.

## Inputs

See the `workflow_call.inputs` block in each workflow for the full, documented
list. Highlights:

- **`sdk-ci.yml`** — `node-versions`, `org-runner`, `{install,lint,typecheck,build,test}-command` (empty = skip), `check-lockfile-hygiene`, `timeout-minutes`.
- **`sdk-publish.yml`** — `org-owner`, `environment`, `tag-prefix`, `provenance`, `publish-node-version`, plus the same command inputs.

## Versioning

Consumers **pin by version**, never a moving branch:

- **`@v1`** — a moving major tag; picks up backward-compatible fixes.
- **`@v1.2.3`** — an immutable release tag; fully reproducible.
- **`@<full-sha>`** — maximum supply-chain strictness (recommended for the
  most sensitive repos).

Releases are cut as `vMAJOR.MINOR.PATCH` tags; the `vMAJOR` tag is force-moved
to the latest compatible release. Breaking input/behavior changes bump the major.

## Ownership & contribution

See [`.github/CODEOWNERS`](.github/CODEOWNERS). Changes require owner review
because they affect every consuming SDK repo. Test changes against a pilot repo
before moving the `vMAJOR` tag.

## Adoption status (PEA-1331)

- [x] Central repo + reusable CI/publish guards (this repo).
- [ ] Adopt across the four SDK repos: `twilio-*-typescript` / `python` / `aws` / `microsoft`.
- [ ] Wire as an org-level required check (ruleset) so PRs can't weaken the gate.
- [ ] Roll out across orgs: `twilio`, `twilio-internal`, `segmentio`, `sendgrid`.
