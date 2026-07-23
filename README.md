# sdk-actions

Small, composable GitHub Actions for building and publishing Twilio's public
SDKs: **Artifactory OIDC login**, **lockfile hygiene**, and **publishing**.
Drop them into your own `ci.yml` / `publish.yml` as steps — there is no
black-box pipeline to adopt. `artifactory-oidc` and lockfile hygiene cover both
npm and Python (uv); `npm-publish` is npm-specific.

## The actions

| Action | What it does |
|--------|--------------|
| [`artifactory-oidc`](artifactory-oidc/action.yml) | Exchanges the GitHub OIDC token for a short-lived Artifactory token and points your package manager at the curated registry — npm via `~/.npmrc`, or Python (`ecosystem: python`) via `UV_INDEX_URL` / `PIP_INDEX_URL`. No stored secret. |
| [`npm-lockfile-hygiene`](npm-lockfile-hygiene/action.yml) | Fails closed if a lockfile/config names a non-public registry host, and (optionally) does a clean-room public install to prove external installability. Secret-less — safe on forks. |
| [`uv-lockfile-hygiene`](uv-lockfile-hygiene/action.yml) | Same gate for Python (uv): scans `uv.lock` / `requirements*.txt` and clean-room installs with `uv sync --frozen` from public PyPI. Secret-less — safe on forks. |
| [`npm-publish`](npm-publish/action.yml) | Validates the release tag vs `package.json`, then publishes to public npm via OIDC trusted publishing (prereleases → `next`). |

Each is a **drop-in step** — you own the runner, matrix, lint, build, and test.

## Compose them: CI

```yaml
# .github/workflows/ci.yml — you write and own this
name: CI
on: { push: { branches: [main] }, pull_request: {}, workflow_dispatch: {} }

jobs:
  # Secret-less gate — its own job so the clean-room install is truly isolated.
  npm-lockfile-hygiene:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<sha>          # v4
      - uses: twilio/sdk-actions/npm-lockfile-hygiene@<sha>  # v1.2.3
        with:
          package-manager: yarn               # npm | yarn | pnpm

  test:
    # Fork PRs -> GitHub-hosted; internal PRs -> your self-hosted runner. Your call.
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
      - uses: actions/setup-node@<sha>        # v6
        with: { node-version: '${{ matrix.node }}', cache: yarn }
      - run: yarn install --frozen-lockfile
      - run: yarn lint
      - run: yarn build
      - run: yarn test
```

## Compose them: CI (Python)

Pass `ecosystem: python` to `artifactory-oidc` (it exports `UV_INDEX_URL` /
`PIP_INDEX_URL` so `uv sync` / `pip install` resolve through Artifactory), and
use `uv-lockfile-hygiene` for the supply-chain gate. `npm-publish` is
npm-specific and doesn't apply.

```yaml
# .github/workflows/ci.yml — you write and own this
jobs:
  # Secret-less gate — its own job so the clean-room install is truly isolated.
  uv-lockfile-hygiene:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<sha>          # v4
      - uses: twilio/sdk-actions/uv-lockfile-hygiene@<sha>  # v1.2.3

  test:
    runs-on: ${{ github.event.pull_request.head.repo.fork && 'ubuntu-latest' || 'ubuntu-x64' }}
    permissions:
      contents: read
      id-token: write                         # needed for the OIDC login below
    steps:
      - uses: actions/checkout@<sha>          # v4
      # Forks have no Artifactory secret; skip login and resolve from public PyPI.
      - if: ${{ !github.event.pull_request.head.repo.fork }}
        uses: twilio/sdk-actions/artifactory-oidc@<sha>  # v1.2.3
        with:
          ecosystem: python
      - uses: astral-sh/setup-uv@<sha>        # v5
      - uses: actions/setup-python@<sha>      # v5
        with: { python-version: '3.12' }
      - run: uv sync --frozen --all-extras --all-groups
      - run: uv run pytest
```

## Compose them: Publish (single package)

```yaml
# .github/workflows/publish.yml — you write and own this
name: Publish
on: { release: { types: [published] } }

jobs:
  publish:
    runs-on: ubuntu-x64
    if: github.repository_owner == 'twilio'    # your GitHub org
    environment: production                    # gates the publish; see note below
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@<sha>           # v4
      - uses: twilio/sdk-actions/artifactory-oidc@<sha>  # v1.2.3
      - uses: actions/setup-node@<sha>         # v6 — Node >= 24 for trusted publishing
        with: { node-version: 24, registry-url: 'https://registry.npmjs.org' }
      - run: npm ci --ignore-scripts
      - run: npm run build
      - uses: twilio/sdk-actions/npm-publish@<sha> # v1.2.3
        with:
          # tag-prefix: ''      # un-prefixed tags like 2.18.3
          # provenance: false   # REQUIRED for private/internal source repos
```

## Lerna monorepos

Compose `artifactory-oidc` + `npm-lockfile-hygiene` as above; for the publish step,
run Lerna yourself (the `npm-publish` action is single-package). Toggle provenance
via the env var Lerna passes through to npm:

```yaml
      - uses: twilio/sdk-actions/artifactory-oidc@<sha>  # v1.2.3
      - run: npx lerna publish from-package --yes
        env:
          npm_config_provenance: 'true'        # false on private repos
          npm_config_access: public
          npm_config_registry: https://registry.npmjs.org/
```

## Notes that bite

- **`id-token: write`** must be on any job using `artifactory-oidc` or `npm-publish`.
- **`artifactory-url`** defaults to `https://twilio.jfrog.io` — no need to set it;
  pass the input only to override the host.
- **Publish env is `production`** — the GitHub Environment, the `environment:` in
  your workflow, and the npm trusted-publisher registration must all say
  `production`, or OIDC publish fails.
- **Node ≥ 24** for the publish job (npm ≥ 11.5.1 for OIDC trusted publishing).
- **Private repos**: `provenance: false` — npm rejects provenance from private
  sources even for public packages.
- **yarn Berry** reads `.yarnrc.yml`, not `~/.npmrc`; `artifactory-oidc` writes
  `~/.npmrc` (works for npm / yarn-classic / pnpm). Berry needs extra config.
- **Python** (`ecosystem: python`): `artifactory-oidc` exports `UV_INDEX_URL` /
  `PIP_INDEX_URL` into `$GITHUB_ENV` (token as the basic-auth password, empty
  username — JFrog rejects `token` as the username). It does not touch
  `~/.npmrc`. Use `uv-lockfile-hygiene` for the gate; `npm-publish` doesn't apply.

## Versioning & pinning

> **Pin a full commit SHA**, with the version in a trailing comment — not a
> moving tag. This is the recommended supply-chain practice for third-party
> actions:
> `uses: twilio/sdk-actions/npm-publish@<40-char-sha>  # v1.2.3`

Released as `vMAJOR.MINOR.PATCH` via GitHub Releases; a matching `vMAJOR` tag
moves to the latest compatible release. Breaking input/behavior changes bump the
major.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and our [Code of Conduct](CODE_OF_CONDUCT.md).
