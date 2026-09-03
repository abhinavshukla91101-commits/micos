# Security Policy

MiniOS is a pre-release, personal project. It has **not** been
professionally audited. If you find a security issue, please report it
privately rather than opening a public GitHub issue — that gives time to
fix it before it's public knowledge.

## Reporting a vulnerability

**Do not open a public issue for security problems.** Instead:

1. Use GitHub's private reporting: go to the **Security** tab on this repo
   → **Report a vulnerability**. This opens a private draft advisory that
   only you and the maintainer can see.
2. If that's unavailable, email `aradhyshuklapro@gmail.com` with:
   - What the issue is and where (file/component)
   - Steps to reproduce, if possible
   - What you think the impact is (e.g. "leaks the wifi password," "lets
     any local user get root")

You'll get an acknowledgment within a few days. This is a one-person
pre-release project, not a company with an SLA — please be patient.

## Scope — what counts as a security issue here

Given what MiniOS actually does, the areas most worth scrutiny are:

- **Sudoers rules** (`config/hooks/live/0100-minios-setup.hook.chroot`) —
  anything broader than the narrow `wg-quick`-only rule that's there now
- **OAuth handling** (Settings → Accounts) — token storage, whether
  client secrets could leak, redirect URI validation
- **VPN config handling** (`vpn_toggle.py`) — whether `.conf` files or
  their contents (private keys) are ever logged, exposed to other users
  on the system, or world-readable
- **pkexec / admin terminal access** — anything that lets a non-admin
  user escalate without a password prompt
- **Autologin** — this is intentional (live-distro standard behavior),
  not itself a bug to report, but issues in *how* it's implemented
  (e.g. a bypass that also worked on an installed, non-live system) are
  in scope

## What "leaks passwords/emails" would mean here

To be concrete about the community's specific worry:

- MiniOS itself doesn't run a server, doesn't transmit your data
  anywhere, and doesn't collect telemetry — there's no MiniOS-operated
  backend that could leak anything.
- The realistic risk categories are local: a `.conf` file left readable
  by other local users, a build/log file that accidentally captures
  something sensitive, or a sudo rule that's broader than intended letting
  one local user affect another.
- If you find any of those, that's exactly what this policy wants
  reported.

## Not in scope

- Anything requiring physical access + no disk encryption (live/demo
  systems assume this; not fixable at the OS-shell level)
- Issues in upstream Debian packages themselves (report those to Debian)
- The known pre-release gaps already listed in
  [CHANGELOG.md](CHANGELOG.md) under "Known untested / likely broken"
