#!/usr/bin/env python3

"""Say what is out of step across the repositories.

Six repositories, four systems: git, GitHub, PyPI, and two container
registries. Nothing watches all four at once, so this does, and it does it
by asking rather than by remembering. Every number below is read at run
time; nothing here is a copy of what was true when it was written.

    python scripts/sweep.py                 the table, on stdout
    python scripts/sweep.py --readme FILE   rewrite the block in FILE too

Standard library only, and no repository is cloned: everything comes from
the APIs. A full sweep is about ten requests per repository against a
budget of five thousand an hour, so it can run as often as you like.

Exit status is 1 when something is wrong rather than merely untidy. The
difference matters: an unreleased commit on `main` is normal, and a version
that disagrees with the tag it shipped under is not.

Authentication is `GITHUB_TOKEN` if it is set, and `gh auth token`
otherwise, so it needs no setup on a machine where gh is already logged in.
The repositories are public, so a token only buys the larger rate limit.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tomllib
import urllib.error
import urllib.request
from dataclasses import dataclass, field

API = "https://api.github.com"
OWNER = "mjaksn"


@dataclass
class Repo:
    """One repository, and where its version and its artefacts live."""

    name: str
    # Every file that states the version, and how to read it out. They must
    # all agree with each other and with the tag that shipped them.
    versions: list[tuple[str, str]]
    pypi: str | None = None
    # Registry paths, without a tag. Both registries are asked, because they
    # are pushed by separate jobs and can therefore come to differ.
    images: list[str] = field(default_factory=list)


REPOS = [
    Repo("nettail",
         versions=[("pyproject.toml", "pyproject"), ("nettail/__init__.py", "python")],
         pypi="nettail",
         images=["ghcr.io/mjaksn/nettail", "docker.io/mjaksn/nettail"]),
    Repo("netflume",
         versions=[("pyproject.toml", "pyproject"), ("netflume/__init__.py", "python")],
         pypi="netflume"),
    Repo("lanname",
         versions=[("pyproject.toml", "pyproject"), ("lanname/__init__.py", "python")],
         pypi="lanname"),
    Repo("readerboard",
         versions=[("pyproject.toml", "pyproject"),
                   ("readerboard/__init__.py", "python")],
         pypi="readerboard",
         images=["ghcr.io/mjaksn/readerboard", "docker.io/mjaksn/readerboard"]),
    Repo("bravia-http-remote",
         versions=[("package.json", "package.json"), ("app.js", "js")],
         images=["ghcr.io/mjaksn/bravia-http-remote",
                 "docker.io/mjaksn/bravia-http-remote"]),
    # Neither a package nor an image: shell scripts for one board, where the
    # release page and the tarball on it are the whole of the distribution.
    # Published stays empty for it, and the columns that say whether it is in
    # step are the release and the tag.
    Repo("cec-ir-bridge",
         versions=[("bin/cec-ir-bridge", "bash")]),
]


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
        # Unauthenticated works, at sixty requests an hour, which covers one
        # repository and not six. Say so here rather than failing halfway
        # through against a rate limit nobody was expecting.
        print("warning: no GitHub token, so the rate limit will bite",
              file=sys.stderr)
        return ""


def get(url: str, headers: dict[str, str] | None = None):
    """A JSON GET that answers None on 403 and 404 rather than raising.

    A missing release, a package that was never published and a registry
    with nothing in it are all ordinary states here, not errors.
    """
    request = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        if error.code in (403, 404):
            return None
        raise


def gh(path: str, tok: str):
    """A call to the GitHub API."""
    headers = {"Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28"}
    if tok:
        headers["Authorization"] = "Bearer " + tok
    return get(API + path, headers)


def raw(repo: str, path: str, tok: str) -> str | None:
    """One file off the default branch, as text."""
    headers = {"Accept": "application/vnd.github.raw"}
    if tok:
        headers["Authorization"] = "Bearer " + tok
    url = "%s/repos/%s/%s/contents/%s" % (API, OWNER, repo, path)
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise


def pypi_version(name: str) -> str | None:
    """What PyPI currently serves as the latest version."""
    found = get("https://pypi.org/pypi/%s/json" % name)
    return found["info"]["version"] if found else None


def image_tags(image: str) -> list[str]:
    """The tags an image carries, from whichever registry holds it.

    Docker Hub answers anonymously. GHCR wants a bearer token, which it
    hands out for the asking on a public repository, so neither of these
    needs a credential of yours.
    """
    if image.startswith("docker.io/"):
        path = image[len("docker.io/"):]
        found = get("https://hub.docker.com/v2/repositories/%s/tags?page_size=50"
                    % path)
        return sorted(tag["name"] for tag in found.get("results", [])) if found else []

    path = image.split("/", 1)[1]
    granted = get("https://ghcr.io/token?scope=repository:%s:pull&service=ghcr.io"
                  % path)
    if not granted:
        return []
    found = get("https://ghcr.io/v2/%s/tags/list" % path,
                {"Authorization": "Bearer " + granted["token"]})
    return sorted(found.get("tags", [])) if found else []


# Reading a version out of a file.

def read_version(text: str, kind: str) -> str | None:
    if kind == "pyproject":
        return tomllib.loads(text).get("project", {}).get("version")
    if kind == "package.json":
        return json.loads(text).get("version")
    if kind == "python":
        found = re.search(r'^__version__\s*=\s*["\']([^"\']+)', text, re.M)
        return found.group(1) if found else None
    if kind == "js":
        found = re.search(r'APP_VERSION\s*=\s*["\']([^"\']+)', text)
        return found.group(1) if found else None
    if kind == "bash":
        found = re.search(r'^VERSION="([^"]+)"', text, re.M)
        return found.group(1) if found else None
    raise ValueError(kind)


# The sweep itself.

@dataclass
class Result:
    repo: str
    version: str = "?"
    release: str = "none"
    tags_on_main: str = "?"
    unreleased: str = "?"
    ci: str = "?"
    prs: int = 0
    branches: str = "none"
    published: str = "none"
    # Wrong, and worth an exit status.
    problems: list[str] = field(default_factory=list)
    # True, deliberate, and worth saying once rather than alarming about.
    notes: list[str] = field(default_factory=list)


def sweep_one(repo: Repo, tok: str) -> Result:
    out = Result(repo.name)
    base = "/repos/%s/%s" % (OWNER, repo.name)

    # The version, everywhere it is written down. The release workflows
    # already refuse to publish a disagreement, so finding one on main means
    # somebody bumped one file and not the other and has not tagged yet.
    versions = {}
    for path, kind in repo.versions:
        text = raw(repo.name, path, tok)
        versions[path] = read_version(text, kind) if text else None
    stated = {v for v in versions.values() if v}
    out.version = "/".join(sorted(stated)) if stated else "?"
    if len(stated) > 1:
        out.problems.append("versions disagree: %s" % versions)

    # The latest release, and whether it is the version main claims.
    release = gh(base + "/releases/latest", tok)
    if release:
        out.release = release["tag_name"]
        if stated and release["tag_name"].lstrip("v") not in stated:
            out.notes.append("latest release %s trails main at %s"
                             % (release["tag_name"], out.version))

    # Every tag, checked against main. Both `behind` and `identical` mean the
    # tag is an ancestor of main; `diverged` means it was cut somewhere main
    # never went, which is what a tag put on a branch before a squash merge
    # looks like once the merge has happened.
    tags = gh(base + "/tags?per_page=100", tok) or []
    off = []
    for tag in tags:
        compared = gh("%s/compare/main...%s" % (base, tag["name"]), tok)
        if compared and compared["status"] == "diverged":
            off.append(tag["name"])
    out.tags_on_main = ("all %d" % len(tags) if not off
                        else "%d of %d" % (len(tags) - len(off), len(tags)))
    for name in off:
        out.notes.append("%s is not on main" % name)

    # How far main has moved since the release. Ordinary in itself, and shown
    # so that a release which is overdue is visible rather than inferred.
    if release:
        compared = gh("%s/compare/main...%s" % (base, release["tag_name"]), tok)
        behind = compared["behind_by"] if compared else 0
        out.unreleased = ("none" if not behind
                          else "%d commit%s" % (behind, "" if behind == 1 else "s"))

    # CI, as of the most recent run of each workflow on main. A workflow that
    # has never run there is not a failure: it is one that only fires on tags.
    runs = gh(base + "/actions/runs?branch=main&per_page=20", tok) or {}
    latest: dict[str, dict] = {}
    for run in runs.get("workflow_runs", []):
        latest.setdefault(run["name"], run)
    states = {name: run["conclusion"] or run["status"]
              for name, run in latest.items()}
    bad = [n for n, s in states.items()
           if s not in ("success", "in_progress", "queued")]
    if not states:
        out.ci = "no runs"
    elif not bad:
        out.ci = "success"
    else:
        out.ci = ", ".join("%s %s" % (n, states[n]) for n in bad)
        for name in bad:
            out.problems.append("%s on main is %s" % (name, states[name]))

    # Open pull requests, and branches that are not in main. A branch that is
    # only behind was merged and left behind; one that is ahead or has
    # diverged still holds work.
    out.prs = len(gh(base + "/pulls?state=open&per_page=100", tok) or [])
    unmerged = []
    for branch in gh(base + "/branches?per_page=100", tok) or []:
        if branch["name"] == "main":
            continue
        compared = gh("%s/compare/main...%s" % (base, branch["name"]), tok)
        if compared and compared["status"] in ("ahead", "diverged"):
            unmerged.append("%s (+%d/-%d)" % (branch["name"],
                                              compared["ahead_by"],
                                              compared["behind_by"]))
    out.branches = ", ".join(unmerged) if unmerged else "none"

    # What actually reached the outside world. A green publish job is a
    # different claim from a package that is there, which is why this asks
    # the registries rather than the workflow that pushed to them.
    published = []
    wanted = sorted(stated)[0] if stated else None
    if repo.pypi:
        found = pypi_version(repo.pypi)
        published.append("PyPI %s" % (found or "missing"))
        if found and stated and found not in stated:
            out.notes.append("PyPI has %s, main says %s" % (found, out.version))
    for image in repo.images:
        where = "GHCR" if image.startswith("ghcr.io") else "Docker Hub"
        if wanted and wanted in image_tags(image):
            published.append("%s %s" % (where, wanted))
        else:
            published.append("%s missing %s" % (where, wanted or "?"))
            out.notes.append("%s has no %s tag" % (image, wanted))
    out.published = ", ".join(published) if published else "none"
    return out


# Saying what it found.

COLUMNS = [
    ("Repo", "repo"), ("Version", "version"), ("Release", "release"),
    ("Tags on main", "tags_on_main"), ("Unreleased", "unreleased"),
    ("CI", "ci"), ("PRs", "prs"), ("Unmerged", "branches"),
    ("Published", "published"),
]


def table(results: list[Result]) -> str:
    lines = ["| " + " | ".join(head for head, _ in COLUMNS) + " |",
             "| " + " | ".join("---" for _ in COLUMNS) + " |"]
    for result in results:
        lines.append("| " + " | ".join(str(getattr(result, key))
                                       for _, key in COLUMNS) + " |")
    return "\n".join(lines)


START = "<!-- sweep:start -->"
END = "<!-- sweep:end -->"


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
    parser = argparse.ArgumentParser(description="Sweep the repositories.")
    parser.add_argument("--readme", help="a file with sweep markers to rewrite")
    args = parser.parse_args()

    tok = token()
    results = [sweep_one(repo, tok) for repo in REPOS]

    body = table(results)
    notes = [(r.repo, note) for r in results for note in r.notes]
    if notes:
        body += "\n\nWorth knowing:\n\n" + "\n".join("- %s: %s" % pair
                                                     for pair in notes)
    print(body)

    problems = [(r.repo, problem) for r in results for problem in r.problems]
    if problems:
        print("\nOut of step:\n")
        for repo, problem in problems:
            print("- %s: %s" % (repo, problem))

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write("## Repository sweep\n\n" + body + "\n")
            if problems:
                handle.write("\n### Out of step\n\n"
                             + "\n".join("- **%s**: %s" % pair
                                         for pair in problems) + "\n")

    if args.readme:
        rewrite(args.readme, body)

    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
