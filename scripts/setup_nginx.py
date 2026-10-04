#!/usr/bin/env python3
"""
MR.GREEN — Production Nginx Reverse Proxy Setup

Configures Nginx reverse proxy so that incoming requests to ports 80 and 443
are routed directly to the MR.GREEN FastAPI backend (http://127.0.0.1:8000).
"""

import glob
import os
import re
import subprocess
import sys

def main():
    print("🌿 [MR.GREEN] Configuring Nginx reverse proxy...")

    nginx_dir = "/etc/nginx"
    if not os.path.isdir(nginx_dir):
        print("ℹ️ Nginx directory not found. Skipping Nginx configuration.")
        return

    # Proxy configuration block
    proxy_config = """
    # MR.GREEN Reverse Proxy Block
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

    conf_files = (
        glob.glob(os.path.join(nginx_dir, "sites-enabled", "*")) +
        glob.glob(os.path.join(nginx_dir, "sites-available", "*")) +
        glob.glob(os.path.join(nginx_dir, "conf.d", "*.conf"))
    )

    print(f"🔍 Found {len(conf_files)} Nginx config files: {conf_files}")

    updated_any = False
    for filepath in conf_files:
        # Resolve symlinks to target file
        real_path = os.path.realpath(filepath)
        if not os.path.isfile(real_path):
            continue

        try:
            with open(real_path, "r", encoding="utf-8") as f:
                content = f.read()

            print(f"📄 Inspecting: {filepath}")

            if "http://127.0.0.1:8000" in content:
                print(f"   Already configured for 127.0.0.1:8000: {filepath}")
                updated_any = True
                continue

            # Replace any existing location / block or try_files
            if re.search(r"location\s+/\s*\{", content):
                # Replace the entire location / { ... } block
                new_content = re.sub(
                    r"location\s+/\s*\{[^}]*\}",
                    proxy_config.strip(),
                    content
                )
                with open(real_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"✅ Updated existing location / block in: {filepath}")
                updated_any = True
            elif "server {" in content:
                # Append proxy block before the closing brace of server block
                idx = content.rfind("}")
                if idx != -1:
                    new_content = content[:idx] + proxy_config + content[idx:]
                    with open(real_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"✅ Added location / proxy block into server block in: {filepath}")
                    updated_any = True
        except Exception as e:
            print(f"⚠️ Error processing {filepath}: {e}")

    # Also create a standalone site in conf.d/mrgreen.conf as fallback
    fallback_conf = os.path.join(nginx_dir, "conf.d", "mrgreen.conf")
    fallback_content = """server {
    listen 80;
    listen [::]:80;
    server_name _;

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
}
"""
    if not os.path.exists(fallback_conf):
        try:
            with open(fallback_conf, "w", encoding="utf-8") as f:
                f.write(fallback_content)
            print(f"✅ Created fallback config at {fallback_conf}")
        except Exception as e:
            print(f"⚠️ Could not write {fallback_conf}: {e}")

    # Test and reload Nginx
    res = subprocess.run(["nginx", "-t"], capture_output=True, text=True)
    print("🩺 Nginx test:", res.stdout, res.stderr)
    if res.returncode == 0:
        subprocess.run(["systemctl", "reload", "nginx"], check=False)
        print("🔄 Nginx reloaded successfully!")
    else:
        print("⚠️ Nginx test failed, skipping reload.")

if __name__ == "__main__":
    main()
