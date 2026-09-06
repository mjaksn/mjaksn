#!/usr/bin/env python3

"""Which Dependabot pull requests have waited long enough to merge.

The house rule is that no third-party version is used within seven days of
its release. Dependabot has a cooldown setting that is meant to enforce the
same thing, and the repositories set it, but it only holds where the
registry hands Dependabot a publication date. Docker Hub does not, and the
pull requests say so in their first line. This asks the registries itself,
for every open Dependabot pull request in every repository the README
lists, and prints links to the ones that are old enough.

    python scripts/are_you_cool_enough.py            the lists, on stdout
    python scripts/are_you_cool_enough.py --write    rewrite the README block too

The repositories come from the project table in the README, not from a
list in here, so adding a row there is the whole of adding a repository.
The same table names the PyPI packages that are mine, and a bump to one of
those is exempt from the wait: the rule is about other people's releases.
With `--write` the README also receives the answer: the block between its
markers is replaced with the links that are old enough and the ones still
waiting, each with the moment it clears, and nothing else in the file is
touched. A pull request that could not be dated is only in the run's own
output, since a line with no date on it would leave the reader nothing to
do.

Standard library only, and nothing is cloned. The exit status is always 0.
An empty list is an ordinary morning, and a registry that will not answer
raises and fails the run on its own.

The Docker case is answered conservatively. Docker Hub only records when a
tag was last pushed, and a tag is pushed again whenever the image behind it
is rebuilt, so the clock restarts on a rebuild. That can only make an image
look newer than it is, never older.

Authentication is `GITHUB_TOKEN` if it is set, and `gh auth token`
otherwise, so it needs no setup on a machine where gh is already logged in.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

API = "https://api.github.com"
OWNER = "mjaksn"
BOT = "dependabot[bot]"


# Talking to the outside.

def token() -> str:
    """The GitHub token, from the environment or from gh."""
    if os.environ.get("GITHUB_TOKEN"):
        return os.environ["GITHUB_TOKEN"]
    try:
        found = subprocess.run(["gh", "auth", "token"], capture_output=True,
                               text=True, check=True)
        return found.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        print("warning: no GitHub token, so the rate limit will bite",
              file=sys.stderr)
        return ""


def get(url: str, headers: dict[str, str] | None = None):
    """A JSON GET that answers None on 404 rather than raising.

    A version the registry has never heard of is an answer here, not an
    error: it means the date is unknown, and unknown is not old enough.
    """
    request = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise


def gh(path: str, tok: str):
    """A call to the GitHub API."""
    headers = {"Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28"}
    if tok:
        headers["Authorization"] = "Bearer " + tok
    return get(API + path, headers)


def when(stamp: str) -> datetime:
    """An ISO 8601 timestamp from any of the registries, as UTC."""
    parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


# Reading the README.

SWEEP = "<!-- sweep:start -->"
START = "<!-- cool:start -->"
END = "<!-- cool:end -->"


def repos_in(readme: str) -> list[str]:
    """The repositories the project table links to, in table order.

    Only a link that ends at the repository counts. The badge links carry
    on into `/actions/...` and `/releases/...` and so are left out, and
    the sweep block below the table is not read at all.
    """
    head = readme.split(SWEEP, 1)[0]
    found = re.findall(r"\]\(https://github\.com/%s/([A-Za-z0-9_.-]+)\)" % OWNER,
                       head)
    return list(dict.fromkeys(found))


def packages_in(readme: str) -> set[str]:
    """The PyPI packages the project table links to: the ones that are mine."""
    head = readme.split(SWEEP, 1)[0]
    return set(re.findall(r"https://pypi\.org/project/([A-Za-z0-9_.-]+)/?", head))


# Reading a pull request.

@dataclass
class Bump:
    """One dependency moving from one version to another."""

    name: str
    old: str
    new: str


@dataclass
class Pull:
    repo: str
    number: int
    title: str
    url: str
    ecosystem: str
    bumps: list[Bump] = field(default_factory=list)


BUMP = re.compile(r"[Bb]umps? (\S+) from (\S+) to (\S+)")
GROUPED = re.compile(r"^Updates `([^`]+)` from (\S+) to (\S+)", re.M)


def read_pull(repo: str, pull: dict) -> Pull:
    """What a Dependabot pull request is bumping, and in which ecosystem.

    The ecosystem is the second segment of the branch name, which is the
    only place Dependabot states it in a form a machine can trust. The
    versions are in the title for a single bump and, for a grouped update,
    one per line in the body. A version string that ends in a full stop is
    the title's own punctuation, not part of the version.
    """
    branch = pull["head"]["ref"].split("/")
    ecosystem = branch[1] if len(branch) > 1 else "?"
    out = Pull(repo, pull["number"], pull["title"], pull["html_url"], ecosystem)
    found = BUMP.search(pull["title"])
    if found:
        out.bumps.append(Bump(*(part.rstrip(".") for part in found.groups())))
    else:
        for name, old, new in GROUPED.findall(pull.get("body") or ""):
            out.bumps.append(Bump(name, old, new.rstrip(".")))
    return out


# Asking the registries when a version came out.

def released_pypi(name: str, version: str) -> datetime | None:
    found = get("https://pypi.org/pypi/%s/%s/json"
                % (urllib.parse.quote(name), urllib.parse.quote(version)))
    stamps = [f["upload_time_iso_8601"] for f in (found or {}).get("urls", [])
              if f.get("upload_time_iso_8601")]
    return min(when(s) for s in stamps) if stamps else None


def released_npm(name: str, version: str) -> datetime | None:
    found = get("https://registry.npmjs.org/" + name)
    stamp = (found or {}).get("time", {}).get(version)
    return when(stamp) if stamp else None


def released_action(name: str, version: str, tok: str) -> datetime | None:
    """When a GitHub Action's version was released.

    The release is asked first, under both spellings of the tag, because
    a release can be published some days after its tag was cut and the
    later of the two is the one a user could have chosen. A tag with no
    release falls back to the date of the commit it points at.

    An action can live in a subdirectory of its repository, the way
    `github/codeql-action/init` does, and Dependabot names it that way.
    The release is the repository's, so only the first two segments are
    asked about.
    """
    name = "/".join(name.split("/")[:2])
    for tag in ("v" + version, version):
        release = gh("/repos/%s/releases/tags/%s" % (name, tag), tok)
        if release and release.get("published_at"):
            return when(release["published_at"])
    for tag in ("v" + version, version):
        ref = gh("/repos/%s/git/ref/tags/%s" % (name, tag), tok)
        if not ref:
            continue
        target = ref["object"]
        if target["type"] == "tag":
            target = (gh("/repos/%s/git/tags/%s" % (name, target["sha"]), tok)
                      or {}).get("object", target)
        commit = gh("/repos/%s/commits/%s" % (name, target["sha"]), tok)
        if commit:
            return when(commit["commit"]["committer"]["date"])
    return None


def released_docker(name: str, version: str) -> datetime | None:
    """When a Docker Hub tag was last pushed, which is the best it offers."""
    if name.startswith("docker.io/"):
        name = name[len("docker.io/"):]
    if "/" not in name:
        name = "library/" + name
    elif name.count("/") > 1 or "." in name.split("/", 1)[0]:
        # Some other registry entirely, GHCR included, and none of them
        # publish a date for a tag.
        return None
    found = get("https://hub.docker.com/v2/repositories/%s/tags/%s"
                % (name, urllib.parse.quote(version)))
    stamp = (found or {}).get("tag_last_pushed")
    return when(stamp) if stamp else None


def released(ecosystem: str, bump: Bump, tok: str) -> datetime | None:
    if ecosystem == "pip":
        return released_pypi(bump.name, bump.new)
    if ecosystem == "npm_and_yarn":
        return released_npm(bump.name, bump.new)
    if ecosystem == "github_actions":
        return released_action(bump.name, bump.new, tok)
    if ecosystem == "docker":
        return released_docker(bump.name, bump.new)
    return None


def mine(ecosystem: str, bump: Bump, packages: set[str]) -> bool:
    """Whether the thing being bumped is one of mine, and so exempt."""
    if ecosystem == "pip":
        return bump.name.lower().replace("_", "-") in {
            p.lower().replace("_", "-") for p in packages}
    return bump.name.lower().startswith(OWNER + "/")


# The check itself.

@dataclass
class Verdict:
    pull: Pull
    # Every bump cleared the wait, or is mine.
    eligible: bool = False
    # The moment the last bump clears, when it is known.
    ready: datetime | None = None
    # Why a bump could not be dated, when one could not.
    reasons: list[str] = field(default_factory=list)


def judge(pull: Pull, packages: set[str], days: int, now: datetime,
          tok: str) -> Verdict:
    out = Verdict(pull)
    if not pull.bumps:
        out.reasons.append("could not read what it bumps from the title or body")
        return out
    ready = now
    for bump in pull.bumps:
        if mine(pull.ecosystem, bump, packages):
            continue
        stamp = released(pull.ecosystem, bump, tok)
        if stamp is None:
            out.reasons.append("no release date for %s %s in %s"
                               % (bump.name, bump.new, pull.ecosystem))
            continue
        ready = max(ready, stamp + timedelta(days=days))
    if out.reasons:
        return out
    out.ready = ready
    out.eligible = ready <= now
    return out


def footer(now: datetime) -> str:
    """When this was checked, in the smallest type GitHub will render."""
    return "<sub>Checked: %s UTC</sub>" % now.strftime("%Y-%m-%d %H:%M")


def approved(verdicts: list[Verdict]) -> str:
    """The links that are old enough."""
    eligible = [v for v in verdicts if v.eligible]
    if not eligible:
        return "Nothing yet."
    return "\n".join("- %s: [%s](%s)" % (v.pull.repo, v.pull.title, v.pull.url)
                     for v in eligible)


def waiting(verdicts: list[Verdict]) -> str:
    """The links that are not old enough yet, each with the moment it will be."""
    return "\n".join("- %s: [%s](%s), ready %s" % (
        v.pull.repo, v.pull.title, v.pull.url,
        v.ready.strftime("%Y-%m-%d %H:%M UTC"))
        for v in verdicts if not v.eligible and not v.reasons)


def block(verdicts: list[Verdict], now: datetime) -> str:
    """What the README is told: the two dated lists, and when they were made.

    The section around the markers already has a heading, so the second
    list gets a lead-in line rather than a heading of its own.
    """
    body = approved(verdicts)
    later = waiting(verdicts)
    if later:
        body += "\n\nStill waiting:\n\n" + later
    return body + "\n\n" + footer(now)


def report(verdicts: list[Verdict], now: datetime) -> str:
    """The three lists, as markdown that reads the same on a terminal."""
    unknown = [v for v in verdicts if v.reasons]

    lines = ["## Cool enough", "", approved(verdicts)]
    later = waiting(verdicts)
    if later:
        lines += ["", "## Still waiting", "", later]
    if unknown:
        lines += ["", "## Could not tell", ""]
        lines += ["- %s: [%s](%s), %s" % (
            v.pull.repo, v.pull.title, v.pull.url, "; ".join(v.reasons))
            for v in unknown]
    lines += ["", footer(now)]
    return "\n".join(lines)


def rewrite(path: str, body: str) -> None:
    """Replace the block between the markers, and nothing else.

    The rest of the file is written by hand and stays that way, so this
    refuses a file with no markers rather than guessing where the generated
    part was meant to go.
    """
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    if START not in text or END not in text:
        raise SystemExit("%s has no %s and %s markers" % (path, START, END))
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(head + START + "\n\n" + body + "\n\n" + END + tail)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List the Dependabot pull requests that are old enough.")
    parser.add_argument("--readme", default="README.md",
                        help="the README whose project table names the repos")
    parser.add_argument("--days", type=int, default=7,
                        help="how long a release has to have been out")
    parser.add_argument("--write", action="store_true",
                        help="rewrite the block between the README's markers")
    args = parser.parse_args()

    with open(args.readme, encoding="utf-8") as handle:
        readme = handle.read()
    repos = repos_in(readme)
    if not repos:
        raise SystemExit("%s links to no repositories under %s"
                         % (args.readme, OWNER))
    packages = packages_in(readme)

    tok = token()
    now = datetime.now(timezone.utc)
    verdicts = []
    for repo in repos:
        pulls = gh("/repos/%s/%s/pulls?state=open&per_page=100" % (OWNER, repo),
                   tok) or []
        for pull in pulls:
            if pull["user"]["login"] != BOT:
                continue
            verdicts.append(judge(read_pull(repo, pull), packages, args.days,
                                  now, tok))

    body = report(verdicts, now)
    print(body)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(body + "\n")
    if args.write:
        rewrite(args.readme, block(verdicts, now))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
