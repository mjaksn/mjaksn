# mjaksn

Small networking and hardware tools. Mostly Python, mostly no dependencies,
and each one built to be read as well as run.

| Project | What it is | Latest | Build |
| --- | --- | --- | --- |
| [nettail](https://github.com/mjaksn/nettail) | `tail -f` for your network: a NetFlow and IPFIX collector that prints flows with hostnames, colour and a live status bar | [![PyPI](https://img.shields.io/pypi/v/nettail)](https://pypi.org/project/nettail/) | [![CI](https://github.com/mjaksn/nettail/actions/workflows/ci.yml/badge.svg)](https://github.com/mjaksn/nettail/actions/workflows/ci.yml) |
| [netflume](https://github.com/mjaksn/netflume) | NetFlow v5, NetFlow v9 and IPFIX collection and parsing, as a library | [![PyPI](https://img.shields.io/pypi/v/netflume)](https://pypi.org/project/netflume/) | [![CI](https://github.com/mjaksn/netflume/actions/workflows/ci.yml/badge.svg)](https://github.com/mjaksn/netflume/actions/workflows/ci.yml) |
| [lanname](https://github.com/mjaksn/lanname) | Address to hostname lookup on a local network: reverse DNS, mDNS and NetBIOS, cached and non-blocking | [![PyPI](https://img.shields.io/pypi/v/lanname)](https://pypi.org/project/lanname/) | [![CI](https://github.com/mjaksn/lanname/actions/workflows/ci.yml/badge.svg)](https://github.com/mjaksn/lanname/actions/workflows/ci.yml) |
| [readerboard](https://github.com/mjaksn/readerboard) | An HTTP service for BetaBrite and Alpha protocol LED signs, with alerts, scheduling and clock sync | [![PyPI](https://img.shields.io/pypi/v/readerboard)](https://pypi.org/project/readerboard/) | [![CI](https://github.com/mjaksn/readerboard/actions/workflows/ci.yml/badge.svg)](https://github.com/mjaksn/readerboard/actions/workflows/ci.yml) |
| [bravia-http-remote](https://github.com/mjaksn/bravia-http-remote) | A single-page console for controlling a Sony Bravia display over your network | [![Release](https://img.shields.io/github/v/release/mjaksn/bravia-http-remote)](https://github.com/mjaksn/bravia-http-remote/releases/latest) | [![CI](https://github.com/mjaksn/bravia-http-remote/actions/workflows/ci.yml/badge.svg)](https://github.com/mjaksn/bravia-http-remote/actions/workflows/ci.yml) |
| [cec-ir-bridge](https://github.com/mjaksn/cec-ir-bridge) | Volume control for an IR-only soundbar from the Apple TV Remote app, over HDMI-CEC and an ESP32 IR blaster | [![Release](https://img.shields.io/github/v/release/mjaksn/cec-ir-bridge)](https://github.com/mjaksn/cec-ir-bridge/releases/latest) | [![CI](https://github.com/mjaksn/cec-ir-bridge/actions/workflows/ci.yml/badge.svg)](https://github.com/mjaksn/cec-ir-bridge/actions/workflows/ci.yml) |

## Where everything stands

The badges above say whether the last build passed and what the registries
serve. They cannot say whether those two agree with each other, or whether a
tag is on the branch it claims to be on, so the table below asks.

[`scripts/sweep.py`](scripts/sweep.py) reads it fresh from GitHub, PyPI and
both container registries every morning and writes what it found here. It is
standard library only and clones nothing. When something is genuinely wrong,
as opposed to merely untidy, the run fails rather than quietly updating a
table nobody reads.

<!-- sweep:start -->

| Repo | Version | Release | Tags on main | Unreleased | CI | PRs | Unmerged | Published |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nettail | 0.13.0 | v0.12.0 | all 16 | 3 commits | success | 1 | dependabot/docker/python-3.14.7-slim (+1/-14) | PyPI 0.12.0, GHCR missing 0.13.0, Docker Hub missing 0.13.0 |
| netflume | 0.3.0 | v0.3.0 | all 3 | none | success | 1 | template-events (+4/-1), template-kind-changes (+1/-0) | PyPI 0.3.0 |
| lanname | 0.2.1 | v0.2.1 | all 3 | 2 commits | success | 0 | none | PyPI 0.2.1 |
| readerboard | 0.3.0 | v0.3.0 | all 6 | 3 commits | success | 1 | worktree-rule (+1/-0) | PyPI 0.3.0, GHCR 0.3.0, Docker Hub 0.3.0 |
| bravia-http-remote | 1.3.0 | v1.3.0 | all 4 | 1 commit | success | 2 | dependabot/github_actions/actions/checkout-7.0.1 (+1/-3), dependabot/github_actions/actions/upload-artifact-7.0.1 (+1/-3), split-app-js (+2/-18) | GHCR 1.3.0, Docker Hub 1.3.0 |
| cec-ir-bridge | 0.1.1 | v0.1.1 | all 2 | none | success | 0 | none | none |

Worth knowing:

- nettail: latest release v0.12.0 trails main at 0.13.0
- nettail: PyPI has 0.12.0, main says 0.13.0
- nettail: ghcr.io/mjaksn/nettail has no 0.13.0 tag
- nettail: docker.io/mjaksn/nettail has no 0.13.0 tag

<sub>Generated: 2026-09-03 19:17 UTC</sub>

<!-- sweep:end -->

Read the columns this way. **Tags on main** counts tags that are ancestors of
`main`; a tag put on a release branch before it was squash merged is not one,
and the history stops describing it. **Unreleased** is how far `main` has
moved since the newest release, which is normal in itself. **Published** is
what the registries actually serve, asked of them rather than inferred from a
green publish job.
