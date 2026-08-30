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

## Two hard gates

Everything else on this page can flex. These two cannot, because each would be
expensive or embarrassing to fix after the tag.

### 1. Run the protocol spike against the real sign

Tracked in [readerboard#19](https://github.com/mjaksn/readerboard/issues/19).

The design itself is still contingent on question 1 in `docs/protocol-notes.md`:
whether the sign rotates through several files without blanking between them. The
implementation this project replaced wrote everything to the priority file, so
multi-file rotation has never actually been observed on this sign. If it is not
seamless, the fallback is server-side rotation, which reshapes the registry, the
settings, and probably the API.

One session with `scripts/protocol_spike.py` also settles whether a run sequence
write cancels a running alert, which decides the fate of the deferral in
`MessageRegistry._apply_run_sequence`, and it measures the real inter-packet
delay. The unmeasured 0.5 s default in `inter_packet_delay` is itself part of the
surface being frozen.

### 2. Settle the `constants.py` provenance

Tracked in [readerboard#20](https://github.com/mjaksn/readerboard/issues/20).

The README openly says the vendored constants table is the one part of the
project not cleanly MIT. That is an honest caveat on a 0.x and a bad look on a
1.0 PyPI page.

The escape route is already built: `docs/protocol-notes.md` cites the primary
protocol document for every claim, and `tests/test_constant_values.py` pins every
byte against it with a citation per assertion. A clean-room regeneration of the
table from the document is mechanically verifiable by the suite that already
exists, and the licence caveat paragraph then disappears from the README.

## Decide before the freeze: cheap now, breaking later

None of these block work, but each is a one-line decision today and a major
version bump afterward.

- **Is `/v2` the path to be stuck with?** Keep it. Renaming is a breaking change
  forever after; keeping it costs nothing. Just make it a decision rather than an
  accident.
- **Does `refresh_interval_seconds` survive?**
  ([readerboard#21](https://github.com/mjaksn/readerboard/issues/21)) Spike
  question 4, whether the sign answers reads through the Ethernet adapter,
  decides if reconciliation can become read-and-compare instead of a blind
  re-push. Settings names are frozen surface, so decide whether the timer is the
  committed design and read-back lands additively later, or whether read-back
  reshapes it first.
- **The word "scheduling" in the package description.**
  ([readerboard#22](https://github.com/mjaksn/readerboard/issues/22)) Reword it.
  TTL is expiry, not scheduling, and the protocol's own per-file start and stop
  times are a feature deliberately bypassed with `FFFF`. Fix the word before it
  sits on a 1.0 PyPI page, or build the feature it promises.
- **The simple surface's contract.** Keep it exactly as it is.
  `POST /Write/Message` and its all-200 convention exist for clients that do not
  change. 1.0 is the last cheap chance to reconsider, and the right
  reconsideration is none.
- **The trove of small tag-time flips.** The `Development Status :: 4 - Beta`
  classifier becomes `5 - Production/Stable`, and the changelog's 0.x caveat
  about the interface still moving comes out.

## Safely after 1.0: additive, so let none of it gate the tag

Each of these adds paths or settings without changing existing ones, which makes
them minor releases under the project's own rules.

- **Read-back reconciliation**, turning the fifteen-minute re-push into a cheap
  question and comparison, once the spike proves the adapter passes reads.
- **Multiple or scoped API keys**, such as a read-only key a monitor can hold
  without being able to write to the sign.
- **A Home Assistant integration write-up or blueprint**, since the README
  already names it as the natural first client.
- **New display features**, checked first against the Alpha 1.0 generation
  constraint in the protocol notes, because the BetaBrite's command set is the
  small one.

## The sequence, from here to the tag

1. **Flush the current unreleased work as 0.2.0**
   ([readerboard#18](https://github.com/mjaksn/readerboard/issues/18)). The
   simulator, the combined launcher, and the Swagger authorize change are a
   meaty, coherent release. Ship them and clear the deck.
2. **Take the spike to the sign**
   ([readerboard#19](https://github.com/mjaksn/readerboard/issues/19)). One
   session answers all four open questions and the delay measurement. Update the
   protocol notes from "not yet confirmed on hardware" to confirmed, simplify
   the run sequence deferral if question 3 allows, and set the measured delay as
   the default.
3. **Regenerate `constants.py` from the protocol document**
   ([readerboard#20](https://github.com/mjaksn/readerboard/issues/20)).
   Clean-room, verified by the existing byte-value suite. Drop the licence
   caveat from the README in the same change.
4. **Land the freeze decisions**
   ([readerboard#21](https://github.com/mjaksn/readerboard/issues/21),
   [readerboard#22](https://github.com/mjaksn/readerboard/issues/22)). Any
   resulting renames go out as the last breaking 0.x release, so 1.0.0 itself
   changes nothing.
5. **Cut `v1.0.0-rc1`**
   ([readerboard#23](https://github.com/mjaksn/readerboard/issues/23)). The
   release plumbing already anticipates this: `latest=auto` exists precisely so
   a prerelease tag does not move `latest`. The rc rehearses the full
   three-registry pipeline end to end.
6. **Docs audit, then tag 1.0.0**
   ([readerboard#24](https://github.com/mjaksn/readerboard/issues/24)). By the
   project's own convention that prose is part of the product, the audit is the
   final pre-tag step: README, changelog, docstrings, config comments, OpenAPI
   descriptions, and everything the service prints.

## Closing note

Resist the temptation to attach features to 1.0. The project's whole character is
that it does a small thing carefully, and its release machinery, lock files, and
CI are already more 1.0-ready than most 1.0s. The only things genuinely standing
between here and the tag are one afternoon in front of the sign and one table of
bytes with a tidy origin story.

*Plan drafted 2026-08-30, at readerboard v0.1.4.*
