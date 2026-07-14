# sdk-actions

Small, composable GitHub Actions for the concerns the SDK platform team owns:
**Artifactory OIDC login**, **lockfile hygiene**, and **publishing**. Teams keep
their own `ci.yml` / `publish.yml` and drop these in as steps — no black-box
pipeline to adopt.

Implements the **build-public, gate-internal, publish-public** pattern from
**ADR 1634** (Rule 3b delivery). Tracked in **PEA-1331**.

> This repo is `internal`-visibility with Actions access open to the `twilio`
> org, so public `twilio/*` repos can `uses:` these actions.

## The three actions

| Action | What it does |
|--------|--------------|
| [`artifactory-oidc`](artifactory-oidc/action.yml) | Exchanges the GitHub OIDC token for a short-lived Artifactory token and points npm at the curated registry (`~/.npmrc`). No stored secret. |
| [`lockfile-hygiene`](lockfile-hygiene/action.yml) | Fails closed if a lockfile/config names a non-public registry host, and (optionally) does a clean-room public install to prove external installability. Secret-less — safe on forks. |
| [`publish`](publish/action.yml) | Validates the release tag vs `package.json`, then publishes to public npm via OIDC trusted publishing (prereleases → `next`). |

Each is a **drop-in step** — you own the runner, matrix, lint, build, and test.

## Compose them: CI

```yaml
# .github/workflows/ci.yml — you write and own this
name: CI
on: { push: { branches: [main] }, pull_request: {}, workflow_dispatch: {} }

jobs:
  # Secret-less gate — its own job so the clean-room install is truly isolated.
  lockfile-hygiene:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<sha>          # v4
      - uses: twilio/sdk-actions/lockfile-hygiene@<sha>  # v1.2.3
        with:
          package-manager: yarn               # npm | yarn | pnpm

  test:
    # Fork PRs -> GitHub-hosted; org PRs -> internal Artifactory runner. Your call.
    runs-on: ${{ github.event.pull_request.head.repo.fork && 'ubuntu-latest' || 'ubuntu-x64' }}
    permissions:
      contents: read
      id-token: write                         # needed for the OIDC login below
    strategy:
      matrix: { node: [22, 24] }
    steps:
      - uses: actions/checkout@<sha>          # v4
      # Forks have no Artifactory secret; skip login and resolve from public npm.
      - if: ${{ !github.event.pull_request.head.repo.fork }}
        uses: twilio/sdk-actions/artifactory-oidc@<sha>  # v1.2.3
        with:
          artifactory-url: ${{ vars.ARTIFACTORY_URL }}
      - uses: actions/setup-node@<sha>        # v6
        with: { node-version: '${{ matrix.node }}', cache: yarn }
      - run: yarn install --frozen-lockfile
      - run: yarn lint
      - run: yarn build
      - run: yarn test
```

## Compose them: Publish (single package)

```yaml
# .github/workflows/publish.yml — you write and own this
name: Publish
on: { release: { types: [published] } }

jobs:
  publish:
    runs-on: ubuntu-x64
    if: github.repository_owner == 'twilio'    # or 'twilio-internal'
    environment: production                    # gates the publish; see note below
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@<sha>           # v4
      - uses: twilio/sdk-actions/artifactory-oidc@<sha>  # v1.2.3
        with: { artifactory-url: '${{ vars.ARTIFACTORY_URL }}' }
      - uses: actions/setup-node@<sha>         # v6 — Node >= 24 for trusted publishing
        with: { node-version: 24, registry-url: 'https://registry.npmjs.org' }
      - run: npm ci --ignore-scripts
      - run: npm run build
      - uses: twilio/sdk-actions/publish@<sha> # v1.2.3
        with:
          # tag-prefix: ''      # un-prefixed tags like 2.18.3
          # provenance: false   # REQUIRED for private (twilio-internal/*) sources
```

## Lerna monorepos

Compose `artifactory-oidc` + `lockfile-hygiene` as above; for the publish step,
run Lerna yourself (the `publish` action is single-package). Toggle provenance
via the env var Lerna passes through to npm:

```yaml
      - uses: twilio/sdk-actions/artifactory-oidc@<sha>  # v1.2.3
        with: { artifactory-url: '${{ vars.ARTIFACTORY_URL }}' }
      - run: npx lerna publish from-package --yes
        env:
          npm_config_provenance: 'true'        # false on private repos
          npm_config_access: public
          npm_config_registry: https://registry.npmjs.org/
```

## Notes that bite

- **`id-token: write`** must be on any job using `artifactory-oidc` or `publish`.
- **Publish env is `production`** — the GitHub Environment, the `environment:` in
  your workflow, and the npm trusted-publisher registration must all say
  `production`, or OIDC publish fails. (The IPD "npm" reference is stale.)
- **Node ≥ 24** for the publish job (npm ≥ 11.5.1 for OIDC trusted publishing).
- **Private repos**: `provenance: false` — npm rejects provenance from private
  sources even for public packages.
- **yarn Berry** reads `.yarnrc.yml`, not `~/.npmrc`; `artifactory-oidc` writes
  `~/.npmrc` (works for npm / yarn-classic / pnpm). Berry needs extra config.

## Versioning & pinning

> **Org policy: SHA-pin.** `@v1`-style tags on `uses:` are rejected org-wide.
> Pin a full commit SHA with the version in a trailing comment:
> `uses: twilio/sdk-actions/publish@<40-char-sha>  # v1.2.3`

Released as `vMAJOR.MINOR.PATCH` via GitHub Releases (following the
`twilio-internal/github-actions-library` precedent). Dependabot bumps the SHA in
consumer repos.

## Enforcement (PEA-1331)

Composable actions are opt-in, so a repo *could* omit `lockfile-hygiene`. To make
the gate un-weakenable, it's wired as an **org-level required check** (ruleset) —
tracked as a follow-up below.

## Adoption status

- [x] Composable actions: `artifactory-oidc`, `lockfile-hygiene`, `publish` (npm/yarn/pnpm, single + Lerna).
- [ ] Rewrite the IPD onboarding doc to reference these actions instead of copied bash.
- [ ] Adopt across the SDK repos (typescript / python / aws / microsoft).
- [ ] Org-level required check (ruleset) for `lockfile-hygiene`.
- [ ] Python/PyPI equivalents (PEA-1325).
- [ ] Roll out across orgs: `twilio`, `twilio-internal`, `segmentio`, `sendgrid`.
