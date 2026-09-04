# Issue tracker: GitHub

Issues and specifications for this repository live in GitHub Issues at `realjunjiejj/singhack`. Use the `gh` CLI for all operations and infer the repository from the configured `origin` remote.

## Conventions

- Create one parent specification issue and one issue per approved vertical ticket.
- Apply `ready-for-agent` only when the issue is executable without another product decision.
- Create tickets in dependency order so their `Blocked by` sections can reference real issue numbers.
- Use native GitHub blocking relationships when available; otherwise keep the `Blocked by` section authoritative.
- Claim work by assigning the issue before editing.
- Record verification evidence and remaining uncertainty in an issue comment before closing.
- Pull requests are not treated as incoming triage requests.

## Publishing

When a skill publishes a specification or ticket, create a GitHub issue with `gh issue create`. Read issues with comments and labels before acting. Never replace multiple implementation tickets with one combined issue.
