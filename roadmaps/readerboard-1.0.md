# Readerboard 1.0

**1.0.0 is not a feature milestone. It is a freeze.** The
[changelog](https://github.com/mjaksn/readerboard/blob/main/CHANGELOG.md) already
defines what is versioned: the HTTP paths, the request and response bodies, the
status codes, and the settings names. Tagging 1.0.0 is the moment changing any of
those becomes a breaking change.

That framing sorts every piece of remaining work into three buckets: things that
gate the release, decisions to make before the freeze, and things that are safely
additive afterward.

This plan is tracked in the
[v1.0.0 milestone](https://github.com/mjaksn/readerboard/milestone/1), with
[readerboard#25](https://github.com/mjaksn/readerboard/issues/25) as its pinned
table of contents. The issue list is live state; this page is the reasoning.

## Two hard gates, both cleared

### 1. Run the protocol spike against the real sign: done

Tracked in [readerboard#19](https://github.com/mjaksn/readerboard/issues/19).

The design was contingent on whether the sign rotates through several files
without blanking between them. Three sessions with the sign in September 2026
answered that and ten other questions, recorded with the measurement behind each
in `docs/protocol-notes.md`. Rotation is seamless near enough, so the
sign-driven design stands. A run sequence write does not cancel an alert. The sign
answers reads through the Ethernet adapter. The inter-packet delay was measured
and its default halved to 0.25s.

### 2. Settle the `constants.py` provenance: done

Tracked in [readerboard#20](https://github.com/mjaksn/readerboard/issues/20).

The table was regenerated from the primary protocol document, verified by the
byte-value suite in `tests/test_constant_values.py`, and the licence caveat came
out of the README.

## Decided before the freeze, and merged

All of these are in
[readerboard#116](https://github.com/mjaksn/readerboard/pull/116), which is
merged and goes out as the last breaking 0.x release.

- **Does `refresh_interval_seconds` survive?**
  ([readerboard#21](https://github.com/mjaksn/readerboard/issues/21)) The timer
  stays and the name does not. Read-back landed under the timer rather than
  replacing it: with icons in use, each tick reads one picture file back and
  re-pushes only when that read cannot vouch for the sign. The setting is now
  `check_interval_seconds`, so the name says what a tick does first.
- **Should `GET /health` say `ok` while `sign_in_sync` is false?** No. `status`
  is `degraded` whenever the service knows something it wrote has not reached the
  sign, as well as when the link is down, so a monitor watching one field sees
  both. It still cannot see a sign power cycled behind a connected adapter until
  the next check finds it; nothing can.
- **Can an alert wait its turn?** Yes. Day-to-day use showed that an alert worth
  showing eventually, but not worth dismissing the one already up for, is common,
  and a caller had to keep polling or resending until the sign was free.
  `fail_if_active` is now `if_active`, with `replace`, `queue` and `fail`, and the
  service holds queued alerts and shows each when the one before it ends. This is
  a feature, which the closing note below argues against attaching to 1.0, and it
  is here anyway for one reason: the field swap is a breaking change, so after the
  tag it would have waited for 2.0. The queue landed with the swap so that
  `if_active` never existed with one of its three values missing.
- **Deadlines have a ceiling.** Reviewing the queue found that a large enough
  `ttl_seconds` put a deadline past the last date the service can hold, and was a
  500. Every `ttl_seconds`, and the queue's `max_wait_seconds`, is now at most a
  year, a bound that could not be added after the tag.

Still to do at tag time: the `Development Status :: 4 - Beta` classifier becomes
`5 - Production/Stable`, and the changelog's 0.x caveat about the interface still
moving comes out.

## Decided, and since reversed

The first draft of this page kept the `/v2` prefix and the simple surface
(`POST /Write/Message` and its all-200 convention) exactly as they were. On
2026-09-01 backward compatibility was dropped for the rest of 0.x, and 0.3.0
removed both. Dropping compatibility bought a deletion rather than a redesign: the
old surface had been kept well apart and never distorted the newer one. The point
of recording it is that 1.0 is the line after which a reversal like that stops
being cheap.

## Safely after 1.0: additive, so let none of it gate the tag

- **Read-back for a service with no icons**, which still re-pushes on the timer
  because it has no picture file to ask about.
- **Multiple or scoped API keys**, such as a key that can write messages but not
  reboot the sign. Reads and `GET /health` already need no key, so a monitor
  needs none.
- **A Home Assistant integration write-up or blueprint**, since the README
  already names it as the natural first client.
- **New display features**, checked first against the Alpha 1.0 generation
  constraint in the protocol notes, because the BetaBrite's command set is the
  small one.

## The sequence, from here to the tag

1. ~~Flush the unreleased work as 0.2.0~~ (#18), done 2026-08-30.
2. ~~Take the spike to the sign~~ (#19), done across September 2026.
3. ~~Regenerate `constants.py`~~ (#20), done 2026-08-31.
4. ~~Settle the freeze decisions~~ (#21 and the rest, in #116), merged
   2026-11-12.
5. **Fix the two persistence bugs the review found**
   ([readerboard#117](https://github.com/mjaksn/readerboard/issues/117),
   [readerboard#118](https://github.com/mjaksn/readerboard/issues/118)). Neither
   changes the surface, so neither gates the freeze, but an interrupted reboot or
   a startup with the adapter down should not leave the state file disagreeing
   with the sign in a release meant to be the stable one.
6. **Release the last breaking 0.x version**, carrying #116, so that 1.0.0
   itself changes nothing.
7. **Cut `v1.0.0-rc1`**
   ([readerboard#23](https://github.com/mjaksn/readerboard/issues/23)).
   `latest=auto` exists so a prerelease tag does not move `latest`. The rc
   rehearses the full pipeline: PyPI, both container registries, the release page
   and the Docker Hub overview. CI's `rehearsal` job already exercises the GHCR
   half on every pull request, so the rc mostly proves the parts it cannot.
8. **Docs audit, then tag 1.0.0**
   ([readerboard#24](https://github.com/mjaksn/readerboard/issues/24)). By the
   project's own convention that prose is part of the product, the audit is the
   final pre-tag step: README, changelog, docstrings, config comments, OpenAPI
   descriptions, and everything the service prints.

## Closing note

Resist the temptation to attach features to 1.0. The project's whole character is
that it does a small thing carefully. Variables, icons, hiding and the reboot
route all landed during 0.x, which was the right place for them. The alert queue
is the one feature attached to the freeze, and only because its request field
could not change afterwards. What stands between here and the tag now is two
fixes, one release, one rehearsal and one audit.

*Plan drafted 2026-08-30, at readerboard v0.1.4. Revised 2026-11-12, with the
freeze decisions merged and v0.8.3 the latest release.*
