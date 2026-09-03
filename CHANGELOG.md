# Changelog

## v1.0.1 (pre-release)

**Status: build-tested via GitHub Actions, not yet boot-tested on real
hardware. Treat as a development snapshot.**

### Fixed
- ISO was booting straight into the Debian installer wizard instead of a
  live desktop. Removed the `--debian-installer live` flag from `lb config`
  and added the actual live-boot packages (`live-boot`, `live-config`,
  `live-config-systemd`, `live-tools`) that make a squashfs-based live
  system work at all.
- Missing GUI stack (`xorg`, `lightdm`, `openbox`) and no `sudo` on the
  installed system — this was a downstream effect of the installer bug
  above; the installer's minimal base never received our package list or
  chroot hooks.
- Boot dropping to a text console instead of the graphical desktop
  ("0wa1"). `lightdm.service` being enabled wasn't enough on its own —
  added `systemctl set-default graphical.target` to the build hook, which
  is the actual switch that tells systemd to boot graphically.
- `debootstrap` failing with a 404 on `archive.ubuntu.com/.../bookworm`
  when building on an Ubuntu-based host (Codespaces, GitHub Actions
  runners). Pinned explicit Debian mirrors (`deb.debian.org`,
  `security.debian.org`) in `lb config` instead of relying on the build
  host's own apt sources.
- Missing Debian keyring causing "Cannot check Release signature" during
  bootstrap on non-Debian hosts. `build.sh` now installs
  `debian-archive-keyring` before configuring the build.
- Build failing with "mounted with noexec or nodev" inside GitHub
  Codespaces — that mount restriction on `/workspaces` blocks
  `debootstrap` from creating device nodes. Documented building outside
  that mount (e.g. `~/minios-build`) or, better, using the GitHub Actions
  workflow, which doesn't hit this at all.
- `live-build/chroot/` (the entire built OS filesystem, hundreds of `.deb`
  files) was accidentally committed to git. Added `.gitignore` for
  `live-build/chroot/`, `cache/`, `binary/`, `.build/`, and build output
  files so this can't happen again.
- `.github/workflows/build-iso.yml` wasn't being picked up by GitHub
  Actions because the whole project was nested one level too deep in the
  repo (inside a `miniOS/` subfolder instead of at the repo root).

### Added
- Boot splash (Plymouth): dark theme, teal-to-blue "M" logo, 24-frame
  rotating spinner.
- Login screen (LightDM): matching dark gradient background, default
  avatar, auto-login into the MiniOS desktop.
- Settings tabs: Accounts (OAuth sign-in for Google/Microsoft), Power,
  Updates, Security — on top of the original Network/Display/Sound.
- Game Library app: scans installed Steam/Lutris games locally, shows
  icons, launches them. No login automation — reads the same local files
  those apps already keep on disk.
- Admin Terminal: root shell via `pkexec` (password-prompting, not
  passwordless).
- Top taskbar: running windows + clock, alongside the original bottom
  launcher bar.
- Calamares as an in-session "Install MiniOS" option, so installing to
  disk doesn't require going through the classic installer.
- GitHub Actions workflow (`build-iso.yml`) to build the ISO entirely on
  GitHub's servers — no local disk or `noexec` issues.

## v1.0.0

Initial version: Debian `live-build` ISO with a 3-button desktop shell
(Settings, Browser + WireGuard VPN toggle, Task Manager) on bare Openbox.
