#!/usr/bin/env python3
"""Print the distinct hosts a composer.lock would fetch packages from.

Invoked by action.yml via $GITHUB_ACTION_PATH. One host per line, sorted, so the
caller can match each against its allow-list.

Only `dist.url` and `source.url` are considered — those are the keys that decide
where a dependency actually comes from. `funding`, `homepage`, and `support`
legitimately point anywhere and are all over a real composer.lock.

Exits non-zero if the lockfile cannot be read or parsed. Printing nothing and
succeeding would tell the caller "no non-public hosts here", which is a pass this
script has not earned — the gate it feeds must fail closed.
"""

import json
import sys
from urllib.parse import urlparse


def dist_hosts(data):
    hosts = set()
    for key in ("packages", "packages-dev"):
        for pkg in data.get(key) or []:
            if not isinstance(pkg, dict):
                continue
            for section in ("dist", "source"):
                url = (pkg.get(section) or {}).get("url")
                if isinstance(url, str) and url.startswith(("http://", "https://")):
                    netloc = urlparse(url).netloc
                    if netloc:
                        hosts.add(netloc)
    return sorted(hosts)


def main(argv):
    if len(argv) != 2:
        print(f"usage: {argv[0]} <composer.lock>", file=sys.stderr)
        return 2
    try:
        with open(argv[1], encoding="utf-8") as fh:
            data = json.load(fh)
    except OSError as exc:
        print(f"cannot read {argv[1]}: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"{argv[1]} is not valid JSON: {exc}", file=sys.stderr)
        return 1
    if not isinstance(data, dict):
        print(f"{argv[1]} is not a JSON object", file=sys.stderr)
        return 1
    for host in dist_hosts(data):
        print(host)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
