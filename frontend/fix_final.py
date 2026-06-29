import os
import re

FRONTEND_DIR = r"d:\Ai job finder\frontend\src"

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    orig_content = content

    # Fix unused vars in Apply.tsx
    if 'Apply.tsx' in filepath:
        content = re.sub(r'CheckCircle,\s*', '', content)
        content = re.sub(r'const _\s*=\s*await fetch', 'await fetch', content)
        
    # Fix unused vars in Dashboard.tsx
    if 'Dashboard.tsx' in filepath:
        content = re.sub(r'BarChart2,\s*', '', content)
        content = re.sub(r'ExternalLink,\s*', '', content)
        content = re.sub(r"import { motion } from 'framer-motion';\n", '', content)

    # Fix unused vars in FindJobs.tsx
    if 'FindJobs.tsx' in filepath:
        content = re.sub(r'AlertCircle,\s*', '', content)
        content = re.sub(r'const \[apifyLoc, setApifyLoc\]', 'const [apifyLoc]', content)
        content = re.sub(r'const \[apifyLimit, setApifyLimit\]', 'const [apifyLimit]', content)

    # Fix unused vars in Outreach.tsx
    if 'Outreach.tsx' in filepath:
        content = re.sub(r'OutreachLog,\s*', '', content)
        content = re.sub(r'Job,\s*', '', content)
        content = re.sub(r'Send,\s*', '', content)

    # Fix unused vars in Tailor.tsx
    if 'Tailor.tsx' in filepath:
        content = re.sub(r'Job,\s*', '', content)
        content = re.sub(r'ClipboardCheck,\s*', '', content)
        content = re.sub(r'const appDetail = apps\.find.*?;', '', content)
        content = re.sub(r'const \[tailoredRes, setTailoredRes\].*?;', '', content)
        content = content.replace('setTailoredRes(null);', '')

    # Fix Tracker.tsx specific remaining any
    if 'Tracker.tsx' in filepath:
        content = content.replace('setSelectedApp((prev: any) => ({ ...prev, status: newStatus }));', 'setSelectedApp((prev: Application | null) => prev ? { ...prev, status: newStatus } : null);')
        content = content.replace('setSelectedApp((prev: any) => ({ ...prev, notes: notesInput }));', 'setSelectedApp((prev: Application | null) => prev ? { ...prev, notes: notesInput } : null);')

    # Fix ResumeEditor.tsx
    if 'ResumeEditor.tsx' in filepath:
        content = content.replace('useState<any>(profile', 'useState<Profile>(profile')
        content = content.replace('(exp: any, i: number)', '(exp: Record<string, string>, i: number)')
        content = content.replace('(edu: any, i: number)', '(edu: Record<string, string>, i: number)')
        
    # Fix useAppStore.ts
    if 'useAppStore.ts' in filepath:
        content = content.replace('updateProfile: (profile: any) => void;', 'updateProfile: (profile: Partial<Profile>) => void;')
        content = content.replace('updatePrefs: (prefs: any, secrets: any) => void;', 'updatePrefs: (prefs: Partial<Preferences>, secrets?: Partial<Secrets>) => void;')
        content = content.replace('updatePrefs: (prefs: any, secrets?: any)', 'updatePrefs: (prefs: Partial<Preferences>, secrets?: Partial<Secrets>)')

    if content != orig_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {os.path.basename(filepath)}")

for root, dirs, files in os.walk(FRONTEND_DIR):
    for f in files:
        if f.endswith('.tsx') or f.endswith('.ts'):
            process_file(os.path.join(root, f))

print("Done")
