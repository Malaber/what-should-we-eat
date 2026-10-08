#!/usr/bin/env python3
"""Resolve an installed iPhone simulator; avoid hard-coding runner device names."""
import json
import subprocess

devices = json.loads(subprocess.check_output(["xcrun", "simctl", "list", "devices", "available", "--json"]))["devices"]
for runtime, entries in sorted(devices.items(), reverse=True):
    if ".iOS-" in runtime:
        for device in entries:
            if device["name"].startswith("iPhone"):
                print(device["udid"])
                raise SystemExit(0)
raise SystemExit("Install an iOS simulator runtime in Xcode Settings > Components.")
