# mjaksn

Small networking and hardware tools, a Windows memory forensics monitor, and
a shed for the scripts that belong to none of them. Mostly Python, mostly no
dependencies, and each one built to be read as well as run.

| Project | What it is | Latest | Build |
| --- | --- | --- | --- |
| [nettail](https://github.com/mjaksn/nettail) | `tail -f` for your network: a NetFlow and IPFIX collector that prints flows with hostnames, colour and a live status bar | [![PyPI](https://img.shields.io/pypi/v/nettail)](https://pypi.org/project/nettail/) | [![CI](https://github.com/mjaksn/nettail/actions/workflows/ci.yml/badge.svg)](https://github.com/mjaksn/nettail/actions/workflows/ci.yml) |
| [netflume](https://github.com/mjaksn/netflume) | NetFlow v5, NetFlow v9 and IPFIX collection and parsing, as a library | [![PyPI](https://img.shields.io/pypi/v/netflume)](https://pypi.org/project/netflume/) | [![CI](https://github.com/mjaksn/netflume/actions/workflows/ci.yml/badge.svg)](https://github.com/mjaksn/netflume/actions/workflows/ci.yml) |
| [lanname](https://github.com/mjaksn/lanname) | Address to hostname lookup on a local network: reverse DNS, mDNS and NetBIOS, cached and non-blocking | [![PyPI](https://img.shields.io/pypi/v/lanname)](https://pypi.org/project/lanname/) | [![CI](https://github.com/mjaksn/lanname/actions/workflows/ci.yml/badge.svg)](https://github.com/mjaksn/lanname/actions/workflows/ci.yml) |
| [readerboard](https://github.com/mjaksn/readerboard) | An HTTP service for BetaBrite and Alpha protocol LED signs, with alerts, scheduling and clock sync | [![PyPI](https://img.shields.io/pypi/v/readerboard)](https://pypi.org/project/readerboard/) | [![CI](https://github.com/mjaksn/readerboard/actions/workflows/ci.yml/badge.svg)](https://github.com/mjaksn/readerboard/actions/workflows/ci.yml) |
| [bravia-http-remote](https://github.com/mjaksn/bravia-http-remote) | A single-page console for controlling a Sony Bravia display over your network | [![Release](https://img.shields.io/github/v/release/mjaksn/bravia-http-remote)](https://github.com/mjaksn/bravia-http-remote/releases/latest) | [![CI](https://github.com/mjaksn/bravia-http-remote/actions/workflows/ci.yml/badge.svg)](https://github.com/mjaksn/bravia-http-remote/actions/workflows/ci.yml) |
| [cec-ir-bridge](https://github.com/mjaksn/cec-ir-bridge) | Volume control for an IR-only soundbar from the Apple TV Remote app, over HDMI-CEC and an ESP32 IR blaster | [![Release](https://img.shields.io/github/v/release/mjaksn/cec-ir-bridge)](https://github.com/mjaksn/cec-ir-bridge/releases/latest) | [![CI](https://github.com/mjaksn/cec-ir-bridge/actions/workflows/ci.yml/badge.svg)](https://github.com/mjaksn/cec-ir-bridge/actions/workflows/ci.yml) |
| [toolshed](https://github.com/mjaksn/toolshed) | Small scripts and helper apps that belong to no particular project, one directory per tool, and mixed languages on purpose | no releases | [![CI](https://github.com/mjaksn/toolshed/actions/workflows/ci.yml/badge.svg)](https://github.com/mjaksn/toolshed/actions/workflows/ci.yml) |

## Where everything stands

The badges above say whether the last build passed and what the registries
serve. They cannot say whether those two agree with each other, or whether a
tag is on the branch it claims to be on, so the table below asks, of every
repository in the table above.

[`scripts/sweep.py`](scripts/sweep.py) reads it fresh from GitHub, PyPI and
both container registries every morning and writes what it found here. It is
standard library only and clones nothing. When something is genuinely wrong,
as opposed to merely untidy, the run fails rather than quietly updating a
table nobody reads.

<!-- sweep:start -->

| Repo | Version | Release | Tags on main | Unreleased | CI | PRs | Unmerged | Published |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nettail | 0.20.1 | v0.20.1 | all 26 | none | success | 2 | dependabot/github_actions/docker/build-push-action-7.4.0 (+1/-0), dependabot/github_actions/docker/setup-buildx-action-4.4.1 (+1/-0), mac-docs (+2/-28) | PyPI 0.20.1, GHCR 0.20.1, Docker Hub 0.20.1 |
| netflume | 0.6.0 | v0.6.0 | all 8 | none | success | 3 | compile-templates (+4/-0), dependabot/pip/dot-github/requirements/build-1.6.1 (+1/-0), dependabot/pip/dot-github/requirements/idna-3.20 (+1/-0), dependabot/pip/dot-github/requirements/readme-renderer-46.0 (+1/-0) | PyPI 0.6.0 |
| lanname | 0.5.0 | v0.5.0 | all 6 | none | success | 0 | none | PyPI 0.5.0 |
| readerboard | 0.6.0 | v0.6.0 | all 9 | 10 commits | success | 5 | dependabot/github_actions/docker/build-push-action-7.4.0 (+1/-0), dependabot/github_actions/docker/setup-buildx-action-4.4.1 (+1/-0), dependabot/pip/anyio-gte-4.14.2-and-lt-4.16 (+1/-17), picture-spike-notes (+1/-0), pool-from-sign (+3/-10), starlette-1-7 (+1/-0) | PyPI 0.6.0, GHCR 0.6.0, Docker Hub 0.6.0 |
| bravia-http-remote | 1.3.0 | v1.3.0 | all 4 | 3 commits | success | 2 | dependabot/github_actions/docker/build-push-action-7.4.0 (+1/-0), dependabot/github_actions/docker/setup-buildx-action-4.4.1 (+1/-0), split-app-js (+2/-20) | GHCR 1.3.0, Docker Hub 1.3.0 |
| cec-ir-bridge | 0.1.1 | v0.1.1 | all 2 | none | success | 0 | none | none |
| toolshed | none | none | none | n/a | success | 1 | dependabot/pip/dot-github/ruff-0.16.8 (+1/-3) | none |

<sub>Generated: 2026-10-02 13:21 UTC</sub>

<!-- sweep:end -->

Read the columns this way. **Tags on main** counts tags that are ancestors of
`main`; a tag put on a release branch before it was squash merged is not one,
and the history stops describing it. **Unreleased** is how far `main` has
moved since the newest release, which is normal in itself. **Published** is
what the registries actually serve, asked of them rather than inferred from a
green publish job. **CI** is the latest run of each workflow on `main`,
leaving out any the sweep is told is a fixture rather than a check: toolshed's
Dungeon Crawl exists to be dispatched at and fails on purpose when fed bad
input, so its runs are not read. A repository that releases nothing, which is
what the shed is and what Memlapse is for now, shows `none` and `n/a` where
those questions do not apply, and the columns that say anything about it are
CI, PRs and Unmerged.

## Are you cool enough

Nothing third-party is used within seven days of its release. Dependabot has
a cooldown setting for that, and the repositories above that use Dependabot
set it, but it only holds where the registry tells Dependabot when a version
came out, and Docker Hub does not.
[`scripts/are_you_cool_enough.py`](scripts/are_you_cool_enough.py) asks the
registries itself, every morning after the sweep, for each open Dependabot
pull request in the repositories above, and writes the ones that have waited
long enough here, then the ones still waiting with the moment each clears.
One it could not date at all is only in the run's summary, with the reason.
It reads the project table above for the repositories to check, so a row
added there is a row checked here.

<!-- cool:start -->

- nettail: [ci: bump docker/build-push-action from 7.3.0 to 7.4.0](https://github.com/mjaksn/nettail/pull/82)
- nettail: [ci: bump docker/setup-buildx-action from 4.3.0 to 4.4.1](https://github.com/mjaksn/nettail/pull/81)
- netflume: [ci: bump idna from 3.19 to 3.20 in /.github/requirements](https://github.com/mjaksn/netflume/pull/63)
- netflume: [ci: bump build from 1.6.0 to 1.6.1 in /.github/requirements](https://github.com/mjaksn/netflume/pull/62)
- netflume: [ci: bump readme-renderer from 45.0 to 46.0 in /.github/requirements](https://github.com/mjaksn/netflume/pull/61)
- readerboard: [ci: bump docker/setup-buildx-action from 4.3.0 to 4.4.1](https://github.com/mjaksn/readerboard/pull/87)
- readerboard: [ci: bump docker/build-push-action from 7.3.0 to 7.4.0](https://github.com/mjaksn/readerboard/pull/86)
- bravia-http-remote: [ci: bump docker/setup-buildx-action from 4.3.0 to 4.4.1](https://github.com/mjaksn/bravia-http-remote/pull/26)
- bravia-http-remote: [ci: bump docker/build-push-action from 7.3.0 to 7.4.0](https://github.com/mjaksn/bravia-http-remote/pull/25)
- toolshed: [ci: bump ruff from 0.16.6 to 0.16.8 in /.github](https://github.com/mjaksn/toolshed/pull/29)

<sub>Checked: 2026-10-02 14:00 UTC</sub>

<!-- cool:end -->

## Tooling

Claude Code is my preferred coding assistant, and this is the one place it
is named. Individual projects, commits and files do not credit the agent or
model behind them; a credit on every item reads as an advertisement. The
same thinking puts agent instructions in AGENTS.md rather than one vendor's
file, and keeps JetBrains and VS Code configurations in parallel. I am not
in the business of promoting one commercial tool over another, and none of
them should be a condition of using or adopting anything here.
