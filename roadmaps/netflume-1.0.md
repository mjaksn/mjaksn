# Netflume 1.0

**1.0.0 is not a feature milestone. It is a freeze.** The
[changelog](https://github.com/mjaksn/netflume/blob/main/CHANGELOG.md) already
defines what is versioned: everything reachable from `netflume.__all__`, the
module-level names listed under *Everything else exported*, the normalised
record keys, and the documented defaults. Tagging 1.0.0 is the moment changing
any of those becomes a breaking change.

Netflume differs from most projects arriving at a freeze in one way that shapes
the whole plan: its README already carries a twelve-item roadmap, and all twelve
are in scope before the tag. So this is not a question of what to cut. It is a
question of **what order**, and the order is decided by one rule: every change
that can break a consumer happens while 0.x still makes that cheap, and
everything after it is built on shapes that will not move again.

This plan is tracked in the
[v1.0.0 milestone](https://github.com/mjaksn/netflume/milestone/1), with
[netflume#44](https://github.com/mjaksn/netflume/issues/44) as its pinned table
of contents. The issue list is live state; this page is the reasoning.

## The measurement that decided the ordering

Taken at 0.2.1 on Python 3.12.10, against synthetic datagrams from
`tests/packets.py`. A 16-field all-fixed-length template of the shape a router
actually exports, 24 records per datagram.

| path | flows/s | datagrams/s | how it decodes a record |
| --- | --- | --- | --- |
| IPFIX | 169,023 | 7,043 | field by field, slice and convert |
| NetFlow v9 | 166,598 | 6,942 | field by field, slice and convert |
| **NetFlow v5** | **792,453** | **26,415** | **one `struct.Struct` for the whole record** |
| `Flow.from_record` | 270,165 | n/a | the typed layer, on top of the dict decode |

v5 is **4.7x faster than v9** on equivalent records, and the reason is visible
in the source rather than mysterious. `parse_v5` already unpacks a whole record
in a single call, which is exactly what the roadmap's template-compilation item
proposes doing for v9 and IPFIX. The fastest path in the package is already the
design the slowest paths are waiting for.

A prototype of that change, run against the existing `parse_data_record` on the
same template and asserting the output dicts are equal:

```
current   0.242s   164,960 records/s
compiled  0.062s   649,830 records/s
speedup   3.94x          outputs identical
```

That turns the largest roadmap item from a hypothesis into a port, and it costs
no public API at all. It also sets the shape of everything around it:
the benchmark harness has to come before it, and every feature that touches the
parse path has to come after it.

## Four constraints decide the sequence

**Measure before optimising.** A 3.94x claim nobody can reproduce is a complaint
rather than a number, and a regression after the rewrite needs a before to be a
regression at all. So `tools/bench.py` is the first thing built.

**Break once, early.** The floor raise and every signature change land in two
adjacent releases, so a consumer meets breakage twice rather than five times,
and nothing later is built on a shape that is about to move.

**The parse core is finished before anything extends it.** Selective decoding
and the enterprise element registry are both nearly free on a compiled template
and awkward on a per-field walk. Landing them first would mean implementing them
twice.

**New surface last, prose last of all.** The asyncio interface, the capture
source and `python -m netflume` are independent additive modules with no
interaction, which makes them the safest work to be doing while the API settles
into its final shape. 1.0.0 itself contains no library code.

## The sequence, from here to the tag

### 0.3.0, ground and instruments

Nothing can be optimised before it can be measured, and the floor raise touches
the typing style of every module, so anything merged before it gets rewritten by
it. That puts both first.

The floor moves to **3.11**
([netflume#12](https://github.com/mjaksn/netflume/issues/12)). 3.9 reached end of
life in October 2025, and the matrix does not yet cover 3.14. It becomes 3.11
through 3.14 on both operating systems with no exclusions, which incidentally
deletes the awkward Windows 3.9 cell and the long comment justifying it. The
pyupgrade lint rules, disabled on purpose because they ask for the exact syntax
3.9 cannot take, can then be enabled
([netflume#13](https://github.com/mjaksn/netflume/issues/13)).

`tools/bench.py` ([netflume#14](https://github.com/mjaksn/netflume/issues/14))
is standard library only and shaped like `tools/fuzz.py`, which is the file it
should read like. Its workflow runs on demand and after a merge, deliberately
**not** in the gate
([netflume#15](https://github.com/mjaksn/netflume/issues/15)), for the reason
`AGENTS.md` already gives for keeping fuzzing out of it: a required check that
fails for a novel reason is one people learn to click past, and shared runners
make throughput noisy enough that a hard threshold becomes that check within
a month.

### 0.4.0, transport and the shape of the surface

The break-it-once release. Every signature change in the plan is in it.

IPv6 collection belongs here rather than later because it changes the `bind`
default, and changing a default separately from the feature that needs it is two
breakages instead of one.

**One thing has to happen first, and it is easy to miss.** On a dual-stack
socket an IPv4 exporter arrives as `::ffff:192.0.2.1` rather than
`192.0.2.1`. Templates, sequence streams and sampling rates are keyed by that
string, so the same router would key differently depending on the collector's
socket family. That silently splits three tables and makes a restart look like a
new device. So address normalisation
([netflume#16](https://github.com/mjaksn/netflume/issues/16)) is a prerequisite
for the IPv6 work
([netflume#17](https://github.com/mjaksn/netflume/issues/17)), not a detail
inside it.

Three smaller corrections ride along, because this is the last cheap moment for
the first of them:

- `flow_duration` loses the argument its own docstring calls "accepted and
  ignored" ([netflume#18](https://github.com/mjaksn/netflume/issues/18)).
- `Message.typed_flows()` reads the clock once per message rather than once per
  flow ([netflume#19](https://github.com/mjaksn/netflume/issues/19)). A 24-flow
  message currently makes 24 clock calls, and its flows can straddle a tick,
  which means flows that arrived together get judged against different readings.
- A v5 datagram carrying fewer records than its header declares, and an IPFIX
  `msg_len` that overruns the datagram, are both partial successes reported as
  nothing at all today. A counter makes them visible
  ([netflume#20](https://github.com/mjaksn/netflume/issues/20)).

### 0.5.0, the fast path

The riskiest rewrite in the plan, and it touches nothing a consumer can see.

Template compilation
([netflume#21](https://github.com/mjaksn/netflume/issues/21)) builds a
`struct.Struct` and a post-processing plan the moment a template is learned,
when every field is fixed length. Unsigned integers of width 1, 2, 4 and 8 need
no post-processing at all. A template with any variable-length field is simply
not compiled and keeps the current walk, so IPFIX variable-length encoding is
untouched and the two paths coexist by design rather than by accident.

The safety net matters more than the change. A silent decode difference is
exactly the failure class `tests/test_hardening.py` exists for: it does not
raise, so the fuzzer cannot see it, and it returns something untrue. So the
interpreted path stays reachable behind an internal flag, for no reason other
than that a differential test can exist
([netflume#22](https://github.com/mjaksn/netflume/issues/22)), running both
paths over every message in `tests/packets.py`, every prefix of every one of
them, and a fuzz corpus.

Two smaller items sit behind it. `memoryview`
([netflume#23](https://github.com/mjaksn/netflume/issues/23)) turns out narrower
than the roadmap line suggests: `socket.inet_ntoa` and `int.from_bytes` accept a
view, but `ipaddress.IPv6Address` raises on one and a memoryview has no
`decode`, so v6, MAC and string fields still materialise bytes. Compiled
templates make it largely moot for the common case, which leaves the
variable-length walk as the only place it clearly pays. It should be dropped
without ceremony if the number does not move. And `decode_value`'s bare
`except Exception` gets a counter rather than a narrower catch
([netflume#24](https://github.com/mjaksn/netflume/issues/24)): the broad catch
is what upholds the never-raises promise and should stay, but it is also where a
genuine conversion bug would hide in complete silence.

### 0.6.0, extending the decode

All three items build on the compiled path, and two are nearly free on it.

The enterprise element registry
([netflume#25](https://github.com/mjaksn/netflume/issues/25)) turns a vendor's
flow direction or application ID from `e9.12345` and raw bytes into a
first-class field. It carries one decision that has to be written down rather
than left implicit: names resolve at template-learn time, so an element
registered after a template has been learned does not apply to it.

Selective decoding
([netflume#26](https://github.com/mjaksn/netflume/issues/26)) is a filter on the
post-processing plan, applied once per template, and therefore free per record.
Three constraints keep it honest: offsets are still walked so records stay
aligned; the allow-list applies to flow records only, because `SamplingWatch`
reads option records and would otherwise go blind; and the keys `Flow` needs are
unioned in when a caller asks for typed flows, rather than letting an allow-list
quietly produce a `Flow` with no octets.

Widening `Flow`
([netflume#27](https://github.com/mjaksn/netflume/issues/27)) is the last
breaking change in the plan. It widens `MODELLED_FIELDS` and therefore
`as_dict(include_raw=False)`, which is somebody's database column set. The
docstring already promises the set may gain fields, so it is permitted, but it
still changes an `INSERT`.

### 0.7.0, durability

The item that matters most to a long-running daemon, kept in its own release
because it is the only place in the package where a **file** becomes untrusted
input.

v9 and IPFIX data records are undecodable until their template arrives, and
exporters resend on their own schedule of one to ten minutes. A process restart
therefore drops every flow in that window today. Saving and restoring the
template store ([netflume#28](https://github.com/mjaksn/netflume/issues/28))
closes it, in JSON and **never pickle**: the file is untrusted the moment it is
on disk, and pickle would turn a template cache into arbitrary code execution.

The restore path then gets the discipline the parse path already has
([netflume#29](https://github.com/mjaksn/netflume/issues/29)): the ceiling
enforced during the load rather than after it, every field triple type-checked,
an unknown schema version refused, and a malformed file raising once rather than
half-loading. And templates go stale
([netflume#30](https://github.com/mjaksn/netflume/issues/30)): a store restored
from a week-old file may decode records against a layout the exporter has since
changed, which produces confident nonsense rather than a gap. Absent costs a
resend window; wrong costs correctness, and this package's preference between
those two is already settled and visible in the way a truncated template is
refused rather than salvaged.

### 0.8.0, new front doors

Four independent modules with no interaction between them and no effect on the
decode path, which makes this the safest work to be doing while everything else
settles. This release publishes every remaining roadmap item, so 1.0.0 can carry
no library code at all.

- **An asyncio collector**
  ([netflume#31](https://github.com/mjaksn/netflume/issues/31)), built on
  `create_datagram_endpoint` rather than `add_reader`, because `add_reader` on a
  socket is unsupported on the Windows Proactor loop and the matrix includes
  Windows. Its queue is bounded: UDP has no backpressure, and an unbounded queue
  is the same memory leak every ceiling in this package exists to prevent.
- **A pcap capture source**
  ([netflume#32](https://github.com/mjaksn/netflume/issues/32)), hand-parsed
  because there is no reader in the standard library and a dependency is out of
  the question, and bounds-checked because a capture file is untrusted input
  exactly as a datagram is.
- **`python -m netflume`**
  ([netflume#33](https://github.com/mjaksn/netflume/issues/33)), a JSONL smoke
  test. This one needs a carve-out written into `AGENTS.md` in the same change,
  or the "Nothing prints" rule reads as violated the day it lands: the ban
  governs the importable package, and `__main__.py` is imported by no library
  path.
- **Worked consumers**
  ([netflume#34](https://github.com/mjaksn/netflume/issues/34)). The sqlite one
  is standard library, so CI can run it, which makes it the example that cannot
  rot. The MQTT one needs a third-party package and so is lint-checked only; the
  zero-dependency rule covers tests too.

### 1.0.0, the freeze

Prose, policy and a version number. 0.8.0 published every line of code 1.0.0
freezes, which is the shape 0.2.1 already took, and it means the thing being
frozen has been installed by real people before it is frozen.

The documentation audit
([netflume#35](https://github.com/mjaksn/netflume/issues/35)) runs on the
standing definition: if a person reads it, it is in scope, wherever it lives.
Known to be stale when it runs are the throughput figures, the test count,
the Ceilings table, the Counters table, and the Limitations list, of which IPv6
transport and single-threaded receive are both wrong. The Roadmap section
is reduced to the non-goals
([netflume#36](https://github.com/mjaksn/netflume/issues/36)), because a 1.0 that
still advertises a roadmap has not frozen anything.

Then the policy itself
([netflume#37](https://github.com/mjaksn/netflume/issues/37)), which is the
actual content of a freeze and the thing most easily left unwritten. What a 1.x
minor may do: add names, add `Flow` fields, add counter keys, add constructor
arguments with defaults, add information elements. What requires a 2.0: removing
or renaming any public name, changing a signature, renaming a normalised record
key, changing a documented default. Deprecation runs one full minor with a
`DeprecationWarning` first, which goes through `warnings` rather than stdout and
so does not touch the printing rule. And one genuinely ambiguous question that a
freeze should not leave open: whether raising the Python floor is a minor or a
major.

Finally the metadata and the tag
([netflume#38](https://github.com/mjaksn/netflume/issues/38)). The classifier
moves from beta to production, the version goes to `1.0.0` in both places the
release workflow checks, and the tag goes on the **merge commit on `main`**
after the pull request lands, never the branch it came from. That last rule is
the one `v0.2.0` exists to justify.

## Decide before the freeze

Five calls, each cheap now and permanent afterward. Each is an issue with a
recommendation on it.

- **A source address filter**
  ([netflume#39](https://github.com/mjaksn/netflume/issues/39)). Not a roadmap
  item, raised because the README already names a spoofing flood as how the
  ceilings get reached in the first place. Every table has a ceiling, so a flood
  degrades the collector rather than killing it; an `accept` predicate means
  the flood never reaches the tables at all. **Take it**, in 0.4.0 with the rest
  of the surface work.
- **A per-exporter sub-cap on the template store**
  ([netflume#40](https://github.com/mjaksn/netflume/issues/40)). Eviction is
  least-recently-used across the whole store, not per exporter, so one exporter
  churning template IDs can evict another exporter's live templates. The ceiling
  holds, which is what it promises; the fairness does not. **Take it**, in
  0.7.0, where the store is already open.
- **The sequence tuning constants**
  ([netflume#41](https://github.com/mjaksn/netflume/issues/41)). `max_streams`
  is a constructor argument; `MAX_REORDER`, `RESYNC_AFTER` and
  `MAX_PLAUSIBLE_GAP` are not. **Declare them internal**, which is what removing
  them from `__all__` in 0.2.0 already decided, and add a sentence to the README
  so the silence is a statement rather than an omission.
- **pcapng** ([netflume#42](https://github.com/mjaksn/netflume/issues/42)).
  Meaningfully more work than classic pcap, and the format most tools now write
  by default. **Decline it in writing** for 1.0, noting that `editcap` converts
  in one command. It is additive, so a 1.x minor can add it if anyone asks.
- **Threaded receive**
  ([netflume#43](https://github.com/mjaksn/netflume/issues/43)). **A worked
  example, not a `ThreadedCollector` class.** An example costs nothing at the
  freeze and can be rewritten in any release; a class is public surface and is
  permanent. The right queue depth and the right behaviour on overflow depend on
  the sink, making the pattern application-shaped rather than library-shaped.

## Safely after 1.0

Nothing is being deferred, which is the unusual part: the whole roadmap ships
before the tag. What remains afterward is only what the project has always
declined, and those stay declined.

sFlow, which is a different protocol, not a variant. Aggregation, alerting
and storage, which belong to the consumer and are what the worked examples exist
to demonstrate. Any form of presentation, including the byte-size and rate
formatters deliberately absent from `netflume.values`. And hostname resolution,
which lives on its own as [lanname](https://github.com/mjaksn/lanname) and which
nothing here depends on.

## Closing note

The hard part of this freeze is not the work; it is the ordering, and the
ordering is unusually well determined here. One measurement fixes most of it: v5
is already 4.7x faster than v9 because it already does the thing the roadmap's
biggest item asks for, so that item is a port rather than an invention, and
everything that touches the parse path wants to be on the near side of it.
Everything else follows from breaking early and freezing late.

The one genuine risk is the compiled decode path returning something subtly
different rather than something wrong, which no amount of fuzzing would catch.
That is what the differential test is for, and it is worth keeping the old path
alive purely to have something to compare against.

*Plan drafted 2026-08-31, at netflume v0.2.1.*
