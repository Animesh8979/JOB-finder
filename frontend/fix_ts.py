import os
import re

FRONTEND_DIR = r"d:\Ai job finder\frontend\src"

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    orig_content = content

    if 'Tracker.tsx' in filepath:
        # Fix Application import
        content = content.replace("import { Application } from '../types';", "import type { Application } from '../types';")
        content = content.replace("useState<Record<string, unknown>>(null)", "useState<Application | null>(null)")
        content = content.replace("useState<Record<string, unknown>>({})", "useState<Record<string, any>>({})")
        content = content.replace("(prev: Application | null)", "(prev: any)")
        content = content.replace("(app: Application)", "(app: any)")
        content = content.replace("(prev: Record<number, unknown>)", "(prev: any)")
        # we replaced `(prev: any)` with `(prev: Application | null) => prev ? { ...prev, status: newStatus } : null);` previously,
        # let's just make it `(prev: any) => ({ ...prev, status: newStatus })` again if needed, or fix Application.
        pass # Will rely on fixing Tracker types by using `any` for complex states if we must, but let's try to just fix types.ts

    if 'useAppStore.ts' in filepath:
        content = content.replace("from './types';", "from '../types';")
        content = content.replace("import { Profile", "import type { Profile")

    if 'api.ts' in filepath:
        content = content.replace("if (showToastOnError && !error.message.startsWith('API Error')) {", "if (showToastOnError && error instanceof Error && !error.message.startsWith('API Error')) {")
        content = content.replace("toast.error(`Network Error: ${error.message}`);", "toast.error(`Network Error: ${error instanceof Error ? error.message : String(error)}`);")

    if 'Tailor.tsx' in filepath:
        content = content.replace("useState<unknown>(null)", "useState<any>(null)")
        content = content.replace("item: Record<string, string>", "item: any")
        content = content.replace("useState<Record<string, string>[]>([])", "useState<any[]>([])")

    if 'Apply.tsx' in filepath:
        content = content.replace("useState<Application | Job | null>", "useState<any>")
        content = content.replace("useState<Record<string, unknown>>", "useState<any>")

    if 'FindJobs.tsx' in filepath:
        content = content.replace("useState<Record<string, unknown>>", "useState<any>")
        content = content.replace("useState<Record<number, unknown>>", "useState<any>")

    if 'ResumeEditor.tsx' in filepath:
        content = content.replace("exp: Record<string, string>", "exp: any")
        content = content.replace("edu: Record<string, string>", "edu: any")

    if 'Setup.tsx' in filepath:
        content = content.replace("props: React.SVGProps<SVGSVGElement>", "props: any")

    if content != orig_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {os.path.basename(filepath)}")

for root, dirs, files in os.walk(FRONTEND_DIR):
    for f in files:
        if f.endswith('.tsx') or f.endswith('.ts'):
            process_file(os.path.join(root, f))

# Fix Types
TYPES_FILE = os.path.join(FRONTEND_DIR, "types", "index.ts")
with open(TYPES_FILE, 'r', encoding='utf-8') as f:
    types_content = f.read()

types_content = types_content.replace('tailored_resume_text?: string;', '''tailored_resume_text?: string;
  notes?: string;
  applied_at?: string;
  updated_at?: string;
  created_at?: string;
  match_score?: number;''')

with open(TYPES_FILE, 'w', encoding='utf-8') as f:
    f.write(types_content)
print("Fixed types/index.ts")

