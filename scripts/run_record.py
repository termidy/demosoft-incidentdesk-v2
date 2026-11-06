"""Build the run record of an epic from GitHub: docs/runs/<epic>.md.

    python scripts/run_record.py 40              # writes docs/runs/40.md and docs/runs/40.json
    python scripts/run_record.py --check 40      # fails when a sub-issue's pull request has no handoff note

The record reads only what GitHub already keeps: the epic's sub-issues, the pull request that closed each one, its
timeline (agent sessions, commits, reviews, the merge), its checks, and the plan pull request. Nothing is typed by hand.

A handoff note is what the implementer profile asks every pull request description for: a link to the plan and each
success criterion with the test that proves it. The next reader (the reviewer, the next agent, an auditor) starts there.
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone

REPO = os.environ.get("GITHUB_REPOSITORY", "termidy/demosoft-incidentdesk-v2")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN", "")
API = "https://api.github.com"
PEOPLE = ("User",)  # bots and Copilot are not people


def call(path, data=None):
    url = path if path.startswith("http") else f"{API}{path}"
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None, headers={
        "Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def pages(path):
    out, page = [], 1
    while True:
        sep = "&" if "?" in path else "?"
        batch = call(f"{path}{sep}per_page=100&page={page}")
        out += batch
        if len(batch) < 100:
            return out
        page += 1


def closing_pr(number):
    owner, name = REPO.split("/")
    q = """query($o:String!,$n:String!,$i:Int!){repository(owner:$o,name:$n){issue(number:$i){
           closedByPullRequestsReferences(first:5,includeClosedPrs:true){nodes{number merged}}}}}"""
    res = call("/graphql", {"query": q, "variables": {"o": owner, "n": name, "i": number}})
    nodes = res["data"]["repository"]["issue"]["closedByPullRequestsReferences"]["nodes"]
    merged = [n["number"] for n in nodes if n["merged"]]
    return (merged or [n["number"] for n in nodes] or [None])[0]


def body_edits(number):
    """Edits of a pull request's description: who and when (the description's own history)."""
    owner, name = REPO.split("/")
    q = """query($o:String!,$n:String!,$i:Int!){repository(owner:$o,name:$n){pullRequest(number:$i){
           userContentEdits(first:20){nodes{editedAt editor{login}}}}}}"""
    res = call("/graphql", {"query": q, "variables": {"o": owner, "n": name, "i": number}})
    return [{"at": e["editedAt"], "by": (e["editor"] or {}).get("login")}
            for e in res["data"]["repository"]["pullRequest"]["userContentEdits"]["nodes"]]


def t(stamp):
    return datetime.fromisoformat(stamp.replace("Z", "+00:00")) if stamp else None


def hm(stamp):
    return t(stamp).strftime("%d.%m %H:%M") if stamp else "-"


def first_sentence(text, limit=150):
    text = re.sub(r"\s+", " ", re.sub(r"`", "", text or "")).strip()
    m = re.match(r"(.+?[.!?])(\s|$)", text)
    s = m.group(1) if m else text
    return s if len(s) <= limit else s[: limit - 3].rstrip() + "..."


def handoff(body, issue):
    """The implementer profile's note: the plan linked, each criterion with its test."""
    body = body or ""
    plan = f"docs/plans/{issue}.md" in body
    tests = sorted(set(re.findall(r"\btest_\w+", body)))
    return {"plan_linked": plan, "tests_named": tests, "present": plan and bool(tests)}


def sub_issue(n):
    issue = call(f"/repos/{REPO}/issues/{n}")
    itl = pages(f"/repos/{REPO}/issues/{n}/timeline")
    assigned = [e for e in itl if e["event"] == "assigned" and (e.get("assignee") or {}).get("login") == "Copilot"]
    pr_number = closing_pr(n)
    rec = {"number": n, "title": issue["title"], "state": issue["state"], "closed_at": issue.get("closed_at"),
           "assigned_by": assigned[0]["actor"]["login"] if assigned else None,
           "assigned_at": assigned[0]["created_at"] if assigned else None, "pr": None}
    if not pr_number:
        return rec
    pr = call(f"/repos/{REPO}/pulls/{pr_number}")
    tl = pages(f"/repos/{REPO}/issues/{pr_number}/timeline")
    starts = [e["created_at"] for e in tl if e["event"] == "copilot_work_started"]
    ends = [e["created_at"] for e in tl if e["event"] == "copilot_work_finished"]
    reviews = [{"by": e["user"]["login"], "state": e["state"], "at": e["submitted_at"],
                "text": first_sentence(e.get("body")), "url": e["html_url"]}
               for e in tl if e["event"] == "reviewed" and e["user"]["type"] in PEOPLE]
    line_comments = [{"by": c["user"]["login"], "at": c["created_at"], "text": first_sentence(c["body"]),
                      "where": f"{c['path']} line {c.get('line') or c.get('original_line')}", "url": c["html_url"]}
                     for c in pages(f"/repos/{REPO}/pulls/{pr_number}/comments") if c["user"]["type"] in PEOPLE]
    asks = [{"by": e["actor"]["login"], "at": e["created_at"], "text": first_sentence(e["body"]), "url": e["html_url"]}
            for e in tl if e["event"] == "commented" and e["actor"]["type"] in PEOPLE]
    commits = pages(f"/repos/{REPO}/pulls/{pr_number}/commits")
    merges_in = [{"sha": c["sha"][:7], "by": (c.get("author") or {}).get("login") or c["commit"]["author"]["name"],
                  "at": c["commit"]["committer"]["date"]} for c in commits if len(c["parents"]) > 1]
    checks = call(f"/repos/{REPO}/commits/{pr['head']['sha']}/check-runs?per_page=100")["check_runs"]
    rec["pr"] = {
        "number": pr_number, "title": pr["title"], "author": pr["user"]["login"], "branch": pr["head"]["ref"],
        "opened_at": pr["created_at"], "merged_at": pr["merged_at"],
        "merged_by": (pr.get("merged_by") or {}).get("login"),
        "merge_commit": (pr.get("merge_commit_sha") or "")[:7] if pr["merged_at"] else None,
        "sessions": [{"start": s, "end": ends[i] if i < len(ends) else None} for i, s in enumerate(starts)],
        "commits": len(commits), "merge_commits": merges_in,
        "reviews": reviews, "line_comments": line_comments, "asks": asks,
        "checks": sorted({(c["name"], c["conclusion"] or c["status"]) for c in checks}),
        "handoff": handoff(pr["body"], n), "url": pr["html_url"],
        "edited_after_merge": [e for e in body_edits(pr_number) if pr["merged_at"] and e["at"] > pr["merged_at"]]}
    return rec


def plan_pr(numbers):
    """The pull request that added the sub-issues' plan files."""
    for n in numbers:
        commits = call(f"/repos/{REPO}/commits?path=docs/plans/{n}.md&per_page=100")
        if commits:
            prs = call(f"/repos/{REPO}/commits/{commits[-1]['sha']}/pulls")
            if prs:
                p = prs[0]
                tl = pages(f"/repos/{REPO}/issues/{p['number']}/timeline")
                return {"number": p["number"], "title": p["title"], "merged_at": p["merged_at"],
                        "merge_commit": (p.get("merge_commit_sha") or "")[:7], "url": p["html_url"],
                        "reviews": [{"by": e["user"]["login"], "state": e["state"], "at": e["submitted_at"],
                                     "text": first_sentence(e.get("body")), "url": e["html_url"]}
                                    for e in tl if e["event"] == "reviewed" and e["user"]["type"] in PEOPLE],
                        "asks": [{"by": e["actor"]["login"], "at": e["created_at"], "text": first_sentence(e["body"]),
                                  "url": e["html_url"]}
                                 for e in tl if e["event"] == "commented" and e["actor"]["type"] in PEOPLE]}
    return None


def build(epic):
    e = call(f"/repos/{REPO}/issues/{epic}")
    subs = [sub_issue(s["number"]) for s in call(f"/repos/{REPO}/issues/{epic}/sub_issues")]
    return {"repo": REPO, "epic": {"number": epic, "title": e["title"], "state": e["state"], "url": e["html_url"]},
            "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "run_url": (f"{os.environ['GITHUB_SERVER_URL']}/{REPO}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
                        if os.environ.get("GITHUB_RUN_ID") else None),
            "plan": plan_pr([s["number"] for s in subs]), "sub_issues": subs}


def minutes(a, b):
    return round((t(b) - t(a)).total_seconds() / 60) if a and b else None


def markdown(r):
    ep, subs = r["epic"], r["sub_issues"]
    out = [f"# Run record: #{ep['number']} {ep['title']}", "",
           f"Built by `scripts/run_record.py` from GitHub at {r['built_at']}"
           + (f" ([workflow run]({r['run_url']}))" if r["run_url"] else "") + ". Times are UTC. Nothing here is typed by hand: "
           "every line comes from an issue, a pull request, a review or a check.", "",
           "## Outcomes", "",
           "| Sub-issue | Pull request | Agent sessions | Handoff note | Approved by | Merged | Issue |",
           "|---|---|---|---|---|---|---|"]
    for s in subs:
        p = s["pr"]
        if not p:
            out.append(f"| #{s['number']} {s['title']} | none | - | - | - | - | {s['state']} |")
            continue
        h = p["handoff"]
        late = p.get("edited_after_merge")
        note = ("yes" if not late else f"added after the merge by {late[-1]['by']}") if h["present"] else "**missing**"
        approved = ", ".join(sorted({v["by"] for v in p["reviews"] if v["state"] == "approved"})) or "-"
        merged = f"{hm(p['merged_at'])} by {p['merged_by']} ({p['merge_commit']})" if p["merged_at"] else "open"
        out.append(f"| #{s['number']} {s['title']} | [#{p['number']}]({p['url']}) | {len(p['sessions'])} | {note} | "
                   f"{approved} | {merged} | {s['state']} |")
    pl = r["plan"]
    out += ["", "## Plan", ""]
    if pl:
        approved = ", ".join(sorted({v["by"] for v in pl["reviews"] if v["state"] == "approved"})) or "nobody"
        out += [f"- [#{pl['number']}]({pl['url']}) {pl['title']}: approved by {approved}, merged {hm(pl['merged_at'])} "
                f"({pl['merge_commit']}).",
                "- Plans: " + ", ".join(f"`docs/plans/{s['number']}.md`" for s in subs) + "."]
    out += ["", "## Handoffs", "",
            "What each agent left for the next reader in its pull request description: the plan linked, and each "
            "success criterion with the test that proves it (the implementer profile).", ""]
    for s in subs:
        p = s["pr"]
        if not p:
            continue
        h = p["handoff"]
        tests = ", ".join(f"`{x}`" for x in h["tests_named"]) or "none"
        late = p.get("edited_after_merge")
        mark = "Handoff note present" if h["present"] else "**Handoff note missing**"
        if h["present"] and late:
            mark += f", added after the merge by {late[-1]['by']} at {hm(late[-1]['at'])}"
        out.append(f"- #{s['number']} → #{p['number']}: {mark}. Plan linked: {'yes' if h['plan_linked'] else 'no'}. "
                   f"Tests named: {tests}.")
    out += ["", "## Decisions", "", "Every decision a person wrote down on the epic's pull requests, in order.", ""]
    decisions = []
    if pl:
        decisions += [(d["at"], f"#{pl['number']}", d) for d in pl["asks"] + [v for v in pl["reviews"] if v["text"]]]
    for s in subs:
        p = s["pr"]
        if p:
            decisions += [(d["at"], f"#{p['number']}" + (f" {d['where']}" if "where" in d else ""), d)
                          for d in p["asks"] + p["line_comments"] + [v for v in p["reviews"] if v["text"]]]
    for at, where, d in sorted(decisions, key=lambda x: x[0]):
        state = f" ({d['state'].replace('_', ' ')})" if "state" in d else ""
        out.append(f"- {hm(at)} {d['by']}{state} on [{where}]({d['url']}): {d['text']}")
    out += ["", "## Timeline", ""]
    events = []
    if pl:
        events.append((pl["merged_at"], f"plan #{pl['number']} merged"))
    for s in subs:
        p = s["pr"]
        if s["assigned_at"]:
            events.append((s["assigned_at"], f"#{s['number']} assigned to Copilot by {s['assigned_by']}"))
        if not p:
            continue
        for i, x in enumerate(p["sessions"]):
            label = "session" if i == 0 else "session again"
            events.append((x["start"], f"#{p['number']} {label} started"))
            if x["end"]:
                events.append((x["end"], f"#{p['number']} {label} finished ({minutes(x['start'], x['end'])} min)"))
        for v in p["reviews"]:
            state = "review comment" if v["state"] == "commented" else v["state"].replace("_", " ")
            events.append((v["at"], f"#{p['number']} {state} by {v['by']}"))
        for e in p.get("edited_after_merge", []):
            events.append((e["at"], f"#{p['number']} description edited after the merge by {e['by']}"))
        for m in p["merge_commits"]:
            events.append((m["at"], f"#{p['number']} conflict with main resolved by {m['by']} ({m['sha']})"))
        if p["merged_at"]:
            events.append((p["merged_at"], f"#{p['number']} merged ({p['merge_commit']})"))
    out += [f"- {hm(at)} {what}" for at, what in sorted(e for e in events if e[0])]
    out += ["", "## Signals", "",
            "| Sub-issue | Sessions | Changes requested | Merge conflicts resolved | Checks not passing | "
            "Assigned → merged |", "|---|---|---|---|---|---|"]
    for s in subs:
        p = s["pr"]
        if not p:
            continue
        cr = sum(v["state"] == "changes_requested" for v in p["reviews"])
        bad = [f"{n}: {c}" for n, c in p["checks"] if c not in ("success", "skipped", "neutral")]
        out.append(f"| #{s['number']} | {len(p['sessions'])} | {cr} | "
                   f"{', '.join(m['sha'] for m in p['merge_commits']) or 'none'} | {', '.join(bad) or 'none'} | "
                   f"{minutes(s['assigned_at'], p['merged_at'])} min |")
    return "\n".join(out) + "\n"


def main(argv):
    check = "--check" in argv
    epic = int([a for a in argv if not a.startswith("--")][0])
    path = f"docs/runs/{epic}"
    if check:
        r = json.load(open(f"{path}.json"))
        missing = [s for s in r["sub_issues"] if s["pr"] and not s["pr"]["handoff"]["present"]]
        for s in missing:
            h = s["pr"]["handoff"]
            lacks = " and ".join(x for x, ok in (("no plan link", h["plan_linked"]),
                                                 ("no test named", h["tests_named"])) if not ok)
            print(f"::error title=Handoff note missing::Pull request #{s['pr']['number']} (sub-issue "
                  f"#{s['number']}) has no handoff note: {lacks}.")
        print(f"{len(missing)} of {sum(1 for s in r['sub_issues'] if s['pr'])} pull requests without a handoff note.")
        return 1 if missing else 0
    r = build(epic)
    os.makedirs("docs/runs", exist_ok=True)
    json.dump(r, open(f"{path}.json", "w"), indent=2)
    open(f"{path}.md", "w").write(markdown(r))
    print(f"wrote {path}.md")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
