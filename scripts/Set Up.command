#!/bin/sh
cd "$(dirname "$0")" || exit 1
/usr/bin/python3 scripts/setup_macos.py
result=$?
printf '\nPress Return to close this window.'
read -r _
exit "$result"
