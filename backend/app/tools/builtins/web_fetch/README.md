# Web Fetch Tool

Fetches public web pages with built-in SSRF protection and HTML text extraction.

- **Permission**: `network.read`
- **Risk Level**: Medium
- **Safety**:
  - Rejects localhost, 127.0.0.1, 0.0.0.0, private subnets (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16).
  - Rejects cloud metadata services (169.254.169.254).
  - 15-second timeout, 500KB response cap, max 3 redirects.
