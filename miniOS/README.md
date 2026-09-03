# MiniOS

A minimal, real, bootable Linux distro with exactly three things on the desktop:
**Settings**, **Browser (with WireGuard VPN toggle)**, and **Task Manager**.

## Why this shape

- **Base**: Debian (via `live-build`) — most reliable, well-documented way to
  produce a real installable/bootable ISO.
- **Desktop**: bare Openbox window manager + one custom Python/GTK "shell" —
  no taskbar, no start menu, no app grid. Just a launcher bar with 3 buttons.
- **Apps**: all three are plain GTK3 + Python. No web tech, no Electron —
  keeps the ISO small and boots fast.

## What's in this folder

```
apps/
  settings/settings_app.py        Network / Display / Sound / Accounts /
                                   Power / Updates / Security — all tabs
  taskmanager/taskmanager_app.py  Live process list + End Task
  browser/launch_browser.sh       Opens Firefox + the VPN toggle
  browser/vpn_toggle.py           WireGuard on/off switch (BYO .conf)
  gamelibrary/gamelibrary_app.py  Scans installed Steam/Lutris games, shows
                                   icons, launches them (Playnite-style)
  terminal/admin_terminal.sh      Terminal with elevated privileges (pkexec)
desktop/
  shell.py                        Launcher bar (5 buttons) + top taskbar
                                   (running windows + clock)
  openbox/autostart               Openbox startup script
  openbox/rc.xml.snippet          Window rules
  plymouth/                       Boot splash theme (needs your own logo)
  lightdm/                        Login screen theming (needs your own bg)
live-build/
  build.sh                        Builds the actual ISO
  config/package-lists/...        Packages installed into the ISO
  config/hooks/live/...           Activates boot splash + login manager
README.md                         This file
```

## About the VPN

There's no bundled VPN network — I can't ship one (that needs servers,
bandwidth, and a business behind it). What's here is a real **WireGuard
client integration**: drop a `.conf` file from any provider you trust
(Mullvad, ProtonVPN, AirVPN, or a server you run yourself) into
`~/.config/miniOS/vpn/`, pick it in the toggle, flip the switch. It runs
`wg-quick up/down` under a narrowly-scoped sudoers rule (that command only —
nothing else is passwordless).

## If your ISO boots into the Debian installer instead of the desktop

Earlier versions of `build.sh` passed `--debian-installer live` to
`lb config`, which builds a hybrid ISO centered on the classic Debian
installer wizard — not a live-boot desktop. That caused exactly this
symptom set: boots to the installer, guided partitioning fails on small
disks, and after a manual install you land on a bare `tty1` with no
`startx`/`sudo`, because the installer's minimal base system never got our
custom package list or chroot hooks (those only apply to the live
filesystem, not to whatever the installer puts on disk).

Fixed by: removing `--debian-installer` entirely, adding the actual
live-boot packages (`live-boot`, `live-config`, `live-config-systemd`,
`live-tools`) that were missing, enabling `lightdm`/`NetworkManager` at
build time, and configuring LightDM to auto-login straight into the
MiniOS desktop (standard behavior for live distros — Ubuntu Live, Mint
Live, etc. all do this). Calamares is included as an "Install MiniOS"
button in the launcher bar if you want to install it to disk from
*inside* the working desktop, which is the normal way live distros offer
installation, instead of forcing the installer as the only path.

If you built an ISO before this fix, rebuild from this version — the old
ISO doesn't self-repair.

## How to build the ISO — no local disk needed (recommended)

If you're short on disk space, `.github/workflows/build-iso.yml` builds the
entire ISO on GitHub's free build servers — your machine only downloads the
finished file at the end.

1. Create a new **public** repo on GitHub (public repos get the most free
   Actions minutes/storage — private works too, just watch your quota).
2. Push this whole `miniOS` folder to it:
   ```bash
   cd miniOS
   git init
   git add .
   git commit -m "MiniOS"
   git branch -M main
   git remote add origin https://github.com/<you>/<repo>.git
   git push -u origin main
   ```
3. On GitHub: open the **Actions** tab → "Build MiniOS ISO" → **Run workflow**.
   (It also runs automatically on every push to `main`.)
4. Wait for the green checkmark (a full desktop build typically takes
   30–60 minutes on GitHub's runners).
5. Click into the finished run → under **Artifacts**, download `MiniOS-iso`.
   That's a zip containing `live-image-amd64.hybrid.iso`.
6. Boot that ISO in VirtualBox/VMware, or flash it to USB with Rufus, same
   as any other ISO.

Artifacts are kept for 14 days (configurable in the workflow file) — the
storage counts against your GitHub Actions quota, not your PC's disk.

## How to build it yourself instead

You need a real Debian or Ubuntu machine or VM — not this chat sandbox —
with root access, ~20GB free disk, and a real internet connection, since
`live-build` downloads the full package set from Debian's mirrors.

```bash
sudo apt install live-build
cd live-build
sudo ./build.sh
```

This produces `live-image-amd64.hybrid.iso` in that directory. Flash it to a
USB with `dd` or Rufus/BalenaEtcher, boot from it, and it'll boot straight
into the 3-button MiniOS shell.

## Testing the apps without building the ISO

You can run each app directly on any Linux machine with GTK3 + the deps
listed at the top of each file:

```bash
sudo apt install python3-gi gir1.2-gtk-3.0 python3-psutil wireguard-tools network-manager
python3 apps/settings/settings_app.py
python3 apps/taskmanager/taskmanager_app.py
python3 apps/browser/vpn_toggle.py
```

## About Accounts and the Game Library

- **Accounts tab** (Settings): real OAuth "Sign in with Google/Microsoft" —
  opens the provider's actual consent page in the browser, gets back a
  token. You need to register your own OAuth app (Google Cloud Console /
  Microsoft Entra ID) and drop the client ID into
  `~/.config/miniOS/oauth.json` — the buttons are wired up but need that
  ID to actually redirect anywhere.
- **Game Library**: does *not* automate logins or check credentials against
  anything. It reads Steam's local `appmanifest_*.acf` files and Lutris's
  game list — the same local data those apps already keep on disk — and
  turns them into clickable icons. You still sign into Steam/Lutris/Epic
  the normal way, in their own windows, once.

I didn't build an "enter Google/Microsoft credentials, loop until it
succeeds or errors" flow — that specific shape (repeatedly testing whether
a login attempt succeeds) is the same mechanism behind account-checker /
credential-stuffing tools, so I stuck to the OAuth + local-scan approach
above instead, which gets you the same "sign in once, games appear" result.

## Branding assets

`desktop/plymouth/logo.png`, `desktop/plymouth/spinner/frame0..23.png`,
`desktop/lightdm/login-bg.png`, and `desktop/lightdm/user-default.png` are
included — a teal-to-blue "M" mark, a matching rotating spinner, a dark
gradient login background, and a default avatar. `build.sh` copies all of
them into the ISO automatically. Swap any of them out for your own art at
the same paths/sizes if you want different branding.

## Natural next steps

- Wire up the OAuth client IDs once you've registered apps with Google/MS
- Add Epic/Xbox App scanning to the Game Library (same local-scan pattern)
- Sign the packages / set up your own APT repo if you want auto-updates
- Swap Firefox for Chromium if you want stricter site-permission control
