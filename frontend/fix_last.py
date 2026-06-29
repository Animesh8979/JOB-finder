import os
import re

FRONTEND_DIR = r"d:\Ai job finder\frontend\src"

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    orig_content = content

    if 'Apply.tsx' in filepath:
        # replace `const _ =` with `` or `await fetch`
        content = re.sub(r'const _\s*=\s*await fetch', 'await fetch', content)
        content = re.sub(r'const _\s*=\s*.*?fetch', 'await fetch', content) # in case it's on multiple lines
        
    if 'Outreach.tsx' in filepath:
        content = content.replace(', Job }', ' }')
        
    if 'Tailor.tsx' in filepath:
        content = content.replace(', Job }', ' }')
        content = re.sub(r'const appDetail = apps\.find.*?;', '', content)

    if content != orig_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {os.path.basename(filepath)}")

for root, dirs, files in os.walk(FRONTEND_DIR):
    for f in files:
        if f.endswith('.tsx') or f.endswith('.ts'):
            process_file(os.path.join(root, f))

print("Done")
