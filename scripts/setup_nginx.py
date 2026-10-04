#!/usr/bin/env python3
"""
MR.GREEN — Production Nginx Reverse Proxy Setup
"""

import glob
import os
import re
import subprocess
import sys

PROXY_PASS_DIRECTIVE = """
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
"""

def update_config_file(filepath):
    real_path = os.path.realpath(filepath)
    if not os.path.isfile(real_path):
        return

    print(f"🔧 Inspecting: {filepath} ({real_path})")
    try:
        with open(real_path, "r", encoding="utf-8") as f:
            content = f.read()

        if "proxy_pass http://127.0.0.1:8000" in content:
            print(f"   Already has proxy_pass to MR.GREEN: {real_path}")
            return

        # Replace existing location / or append before last closing brace
        if re.search(r"location\s+/\s*\{", content):
            new_content = re.sub(
                r"location\s+/\s*\{[^\}]*\}",
                PROXY_PASS_DIRECTIVE.strip(),
                content
            )
        else:
            # Insert proxy block before the closing brace of each server block
            new_content = re.sub(
                r"(\n\s*\}\s*)$",
                "\n" + PROXY_PASS_DIRECTIVE + r"\1",
                content
            )

        # Comment out conflicting root/try_files in the server block
        new_content = re.sub(r"(\s*)(root\s+[^;]+;)", r"\1# \2", new_content)
        new_content = re.sub(r"(\s*)(try_files\s+[^;]+;)", r"\1# \2", new_content)

        with open(real_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"✅ Successfully configured MR.GREEN proxy in {real_path}")

    except Exception as e:
        print(f"⚠️ Error updating {filepath}: {e}")

def main():
    print("🌿 [MR.GREEN] Locating Nginx configs for server.caseyuggoc.co.in...")

    # Find configs mentioning the domain or nginx sites
    candidates = set()

    # Search known paths
    search_dirs = [
        "/etc/nginx",
        "/www/server/nginx/conf",
        "/www/server/panel/vhost",
        "/etc/nginx/sites-enabled",
        "/etc/nginx/conf.d",
    ]
    for d in search_dirs:
        if os.path.isdir(d):
            for root, _, files in os.walk(d):
                for f in files:
                    if f.endswith(".conf") or f in ("default", "mrgreen"):
                        candidates.add(os.path.join(root, f))

    # Also search via grep for domain name
    try:
        res = subprocess.run(
            ["grep", "-rl", "server.caseyuggoc.co.in", "/etc", "/www"],
            capture_output=True,
            text=True
        )
        for line in res.stdout.splitlines():
            line = line.strip()
            if os.path.isfile(line) and not line.endswith(".log"):
                candidates.add(line)
    except Exception as e:
        print("grep error:", e)

    print(f"🔍 Found candidate config files: {candidates}")

    for c in sorted(candidates):
        update_config_file(c)

    # Test and reload
    res = subprocess.run(["nginx", "-t"], capture_output=True, text=True)
    print("🩺 Nginx test stdout:", res.stdout)
    print("🩺 Nginx test stderr:", res.stderr)

    subprocess.run(["systemctl", "reload", "nginx"], check=False)
    subprocess.run(["service", "nginx", "reload"], check=False)
    subprocess.run(["nginx", "-s", "reload"], check=False)
    print("🔄 Nginx reload commands dispatched!")

if __name__ == "__main__":
    main()
