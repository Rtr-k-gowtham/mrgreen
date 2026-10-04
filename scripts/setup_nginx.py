#!/usr/bin/env python3
"""
MR.GREEN — Production Nginx Reverse Proxy Setup

Configures Nginx to route all traffic on port 80 and 443 to MR.GREEN (http://127.0.0.1:8000).
"""

import glob
import os
import re
import subprocess
import sys

PROXY_PASS_DIRECTIVE = """
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
"""

def process_file(filepath):
    real_path = os.path.realpath(filepath)
    if not os.path.isfile(real_path):
        return

    print(f"🔧 Processing Nginx config: {filepath} -> {real_path}")
    try:
        with open(real_path, "r", encoding="utf-8") as f:
            content = f.read()

        # If already configured with proxy_pass to 127.0.0.1:8000 in location /, skip
        if "proxy_pass http://127.0.0.1:8000" in content:
            print(f"   Already contains proxy_pass to MR.GREEN: {real_path}")
            return

        lines = content.splitlines()
        new_lines = []
        in_location_slash = False
        location_brace_depth = 0

        for line in lines:
            stripped = line.strip()

            # Detect start of location / or location / {
            if re.match(r"^location\s+/\s*\{?", stripped):
                in_location_slash = True
                location_brace_depth = line.count("{") - line.count("}")
                new_lines.append("    location / {")
                new_lines.append(PROXY_PASS_DIRECTIVE.strip())
                if location_brace_depth <= 0 and "}" in line:
                    new_lines.append("    }")
                    in_location_slash = False
                continue

            if in_location_slash:
                location_brace_depth += line.count("{") - line.count("}")
                if location_brace_depth <= 0 or "}" in line:
                    new_lines.append("    }")
                    in_location_slash = False
                continue

            # If inside server block and no location / was found, we will inject it after server_name
            if re.match(r"^\s*server_name\s+", stripped):
                new_lines.append(line)
                new_lines.append("    # MR.GREEN Proxy Block")
                new_lines.append("    location / {")
                new_lines.append(PROXY_PASS_DIRECTIVE.strip())
                new_lines.append("    }")
                continue

            # Comment out static root directives so they don't override proxy_pass
            if re.match(r"^\s*root\s+/var/www", stripped) or re.match(r"^\s*try_files\s+", stripped):
                new_lines.append(f"    # commented for MR.GREEN: {line}")
                continue

            new_lines.append(line)

        new_content = "\n".join(new_lines) + "\n"
        with open(real_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"✅ Successfully updated {real_path}")

    except Exception as e:
        print(f"⚠️ Error updating {filepath}: {e}")

def main():
    print("🌿 [MR.GREEN] Configuring Nginx reverse proxy...")
    nginx_dir = "/etc/nginx"
    if not os.path.isdir(nginx_dir):
        print("ℹ️ Nginx directory not found. Skipping.")
        return

    # Check all active config files
    conf_files = sorted(list(set(
        glob.glob(os.path.join(nginx_dir, "sites-enabled", "*")) +
        glob.glob(os.path.join(nginx_dir, "conf.d", "*.conf")) +
        glob.glob(os.path.join(nginx_dir, "sites-available", "*"))
    )))

    for f in conf_files:
        process_file(f)

    # Test and reload
    res = subprocess.run(["nginx", "-t"], capture_output=True, text=True)
    print("🩺 Nginx test stdout:", res.stdout)
    print("🩺 Nginx test stderr:", res.stderr)

    if res.returncode == 0:
        subprocess.run(["systemctl", "reload", "nginx"], check=False)
        subprocess.run(["service", "nginx", "reload"], check=False)
        print("🔄 Nginx reloaded successfully!")
    else:
        print("⚠️ Nginx test had errors, trying systemctl reload anyway")
        subprocess.run(["systemctl", "reload", "nginx"], check=False)

if __name__ == "__main__":
    main()
