#!/bin/bash
# MiniOS Admin Terminal
# Opens a terminal running as root via pkexec (graphical sudo prompt —
# asks for the user's own password, no passwordless root).
exec pkexec x-terminal-emulator
