# Contributing to `sdk-actions`

We'd love for you to contribute and help make these actions even better than
they are today! Here are the guidelines we'd like you to follow:

- [Code of Conduct](#code-of-conduct)
- [Got a Question or Problem?](#got-a-question-or-problem)
- [Found an Issue?](#found-an-issue)
- [Want a Feature?](#want-a-feature)
- [Submission Guidelines](#submission-guidelines)
- [Coding Rules](#coding-rules)

## Code of Conduct

Help us keep this project open and inclusive. Please be kind and considerate of
other developers, and treat all community members with respect. See our
[Code of Conduct](CODE_OF_CONDUCT.md).

## Got a Question or Problem?

Check the [README](README.md) first — it documents each action's inputs and
shows how to compose them. If you still need help, reach out to
[Twilio Support](https://www.twilio.com/help/contact). GitHub issues are
reserved for bug reports and feature requests, not general support questions.

## Found an Issue?

If you find a bug in the source or a mistake in the documentation, help us by
submitting an issue to our [GitHub Repository][github]. Even better, submit a
Pull Request with a fix.

## Want a Feature?

You can request a new feature by submitting an issue to our
[GitHub Repository][github].

- **Major changes** should be discussed first in an issue so we can coordinate
  efforts, prevent duplication of work, and help you craft the change so it is
  successfully accepted into the project.
- **Small changes** can be crafted and submitted as a Pull Request directly.

## Submission Guidelines

### Submitting an Issue

Before you submit, search the archive — maybe your question was already
answered. If your issue looks like a bug and hasn't been reported, open a new
one. Please include:

- **Overview** — what happened, including any error output from the workflow run
- **Which action** — `artifactory-oidc`, `npm-lockfile-hygiene`, or `npm-publish`
- **Inputs** — the `with:` values you passed (redact secrets)
- **Environment** — package manager (npm/yarn/pnpm), Node version, runner
- **Reproduce** — a link to a failing run or a minimal workflow snippet

### Submitting a Pull Request

1. Search [GitHub][pulls] for an open or closed PR that relates to your
   submission so you don't duplicate effort.
2. Fork the repo and create a branch from `main`:

   ```shell
   git checkout -b my-fix-branch main
   ```

3. Make your changes, updating the relevant `action.yml` and the README.
4. Follow our [Coding Rules](#coding-rules) and validate the change (see below).
5. Commit with a descriptive message, push your branch, and open a Pull Request
   against `main`.

After your pull request is merged, you can safely delete your branch.

## Coding Rules

- **Valid YAML** — every `action.yml` must parse. A quick check:

  ```shell
  python3 -c "import yaml; yaml.safe_load(open('artifactory-oidc/action.yml'))"
  ```

- **Portable shell** — `run:` steps use `shell: bash`; avoid Bash 4+ only
  builtins (e.g. `mapfile`) so steps work across runner images.
- **Pin by SHA** — any third-party action referenced from these actions must be
  pinned to a full commit SHA with a `# vX.Y.Z` trailing comment.
- **Untrusted input** — never interpolate `${{ github.* }}` or `${{ inputs.* }}`
  directly inside a `run:` script. Pass values through an intermediate `env:` var
  and reference them as `"$VAR"`.
- **Test against a consumer** — validate a change by pointing a real (or test)
  consumer workflow at your branch SHA and confirming the run behaves as expected.

[github]: https://github.com/twilio/sdk-actions
[pulls]: https://github.com/twilio/sdk-actions/pulls
