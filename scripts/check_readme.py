#!/usr/bin/env python3
"""
Leddro Documentation Integrity & Anchor Linter
Validates that:
1. Every Table-of-Contents anchor in README.md matches a real GitHub-rendered heading slug.
2. Every local relative file link in README.md points to an existing file.
3. Every local image or screenshot reference exists on disk.
"""

import sys
import re
from pathlib import Path

# Ensure utf-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def to_github_slug(heading: str) -> str:
    """Converts a markdown heading title to GitHub's anchor slug format."""
    # Remove markdown link formatting inside heading if any: [text](url) -> text
    clean = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', heading)
    # Remove HTML tags: <tag> -> ''
    clean = re.sub(r'<[^>]+>', '', clean)
    # Lowercase
    clean = clean.strip().lower()
    # Remove punctuation except hyphens and whitespace
    clean = re.sub(r'[^\w\s-]', '', clean)
    # Convert whitespace to single hyphen
    clean = re.sub(r'[\s]+', '-', clean)
    # Strip leading/trailing hyphens (matches GitHub's slugification for emojis and punctuation)
    return clean.strip('-')

def lint_readme(readme_path: Path = Path("README.md")) -> bool:
    if not readme_path.exists():
        print(f"ERROR: {readme_path} not found.")
        return False

    content = readme_path.read_text(encoding="utf-8")
    errors = []

    # 1. Extract all headings
    heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    headings = heading_pattern.findall(content)
    slugs = {to_github_slug(h[1]) for h in headings}

    # 2. Extract TOC anchor links
    # Look for table of contents links: [Title](#anchor)
    toc_pattern = re.compile(r'\[([^\]]+)\]\(#([a-zA-Z0-9_-]+)\)')
    toc_matches = toc_pattern.findall(content)

    print(f"[lint] Found {len(headings)} headings and {len(toc_matches)} anchor links in {readme_path}...")

    missing_anchors = []
    for title, anchor in toc_matches:
        if anchor not in slugs:
            missing_anchors.append((title, anchor))

    if missing_anchors:
        errors.append(f"Broken Table of Contents Anchors ({len(missing_anchors)}):")
        for title, anchor in missing_anchors:
            errors.append(f"  - [{title}](#{anchor}) -> No matching heading for slug '{anchor}'")

    # 3. Extract local relative file links (excluding http/https, mailto, and anchors)
    link_pattern = re.compile(r'\[([^\]]+)\]\((?!https?://|mailto:|#)([^)]+)\)')
    for title, target in link_pattern.findall(content):
        # Ignore query params or sub-anchors
        clean_target = target.split('#')[0].split('?')[0].strip()
        if not clean_target:
            continue
        target_path = Path(clean_target)
        if not target_path.exists():
            errors.append(f"Broken local link: [{title}]({target}) -> File not found: {clean_target}")

    # 4. Extract image references: ![alt](path)
    img_pattern = re.compile(r'!\[([^\]]*)\]\((?!https?://)([^)]+)\)')
    for alt, img_path_str in img_pattern.findall(content):
        clean_img = img_path_str.split('#')[0].split('?')[0].strip()
        if not Path(clean_img).exists():
            errors.append(f"Missing image asset: ![{alt}]({img_path_str}) -> File not found: {clean_img}")

    if errors:
        print("\n❌ README Linter Errors Found:")
        for err in errors:
            print(f"  {err}")
        return False

    print("✅ README verification passed: All anchors, file links, and image assets are valid!")
    return True

if __name__ == "__main__":
    success = lint_readme()
    sys.exit(0 if success else 1)
