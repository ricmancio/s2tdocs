#!/usr/bin/env python3
"""Simple static site builder to replace Couscous.
Reads Markdown files, applies the Twig-like template, outputs HTML."""

import os
import re
import markdown
import yaml

SITE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SITE_DIR, '_site')
BASE_URL = ''

# Load config
with open(os.path.join(SITE_DIR, 'couscous.yml')) as f:
    config = yaml.safe_load(f)

title = config.get('title', 'Documentazione')
menu_items = config.get('menu', {}).get('items', {})

# Read template
with open(os.path.join(SITE_DIR, 'default.twig')) as f:
    template = f.read()


def build_menu_html(current_menu):
    html = ''
    for item_id, item in menu_items.items():
        current_class = 'current' if item_id == current_menu else ''
        href = item.get('absoluteUrl', BASE_URL + '/' + item.get('relativeUrl', ''))
        text = item.get('text', '')
        html += f'''<li class="toctree-l1 {current_class}">
            <a class="reference internal {current_class}" href="{href}">{text}</a>
        </li>\n'''
    return html


def render_template(content_html, current_menu):
    html = template
    # Replace Twig variables
    html = html.replace('{{ title }}', title)
    html = re.sub(r"\{\{\s*title\|default\('The title'\)\s*\}\}", title, html)
    html = html.replace('{{ baseUrl }}', BASE_URL)
    html = html.replace('{{ content|raw }}', content_html)

    # Replace menu loop
    menu_html = build_menu_html(current_menu)
    loop_pattern = r'\{%\s*for\s+itemId,\s*item\s+in\s+menu\.items\s*%\}.*?\{%\s*endfor\s*%\}'
    html = re.sub(loop_pattern, menu_html, html, flags=re.DOTALL)

    return html


def process_markdown(filepath):
    with open(filepath) as f:
        raw = f.read()

    # Extract YAML front matter
    front_matter = {}
    if raw.startswith('---'):
        parts = raw.split('---', 2)
        if len(parts) >= 3:
            front_matter = yaml.safe_load(parts[1]) or {}
            raw = parts[2]

    content_html = markdown.markdown(raw, extensions=['tables', 'fenced_code'])
    current_menu = front_matter.get('currentMenu', '')
    return render_template(content_html, current_menu)


def copy_static(src, dst):
    """Recursively copy static files."""
    import shutil
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            if item in ('.git', '_site', '.github', '__pycache__'):
                continue
            shutil.copytree(s, d, dirs_exist_ok=True)
        elif not item.endswith(('.md', '.twig', '.yml', '.py')):
            shutil.copy2(s, d)


def main():
    import shutil
    # Clean output
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

    # Copy static assets (css, js, fonts, images)
    copy_static(SITE_DIR, OUTPUT_DIR)

    # Build markdown pages
    md_files = {
        'README.md': 'index.html',
        'changelog.md': 'changelog.html',
        'privacy.md': 'privacy.html',
        'editor.md': 'editor.html',
    }

    for md_file, html_file in md_files.items():
        md_path = os.path.join(SITE_DIR, md_file)
        if os.path.exists(md_path):
            html = process_markdown(md_path)
            out_path = os.path.join(OUTPUT_DIR, html_file)
            with open(out_path, 'w') as f:
                f.write(html)
            print(f'  Built: {html_file}')

    print(f'\nSite generated in {OUTPUT_DIR}')


if __name__ == '__main__':
    main()
