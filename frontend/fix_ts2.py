import os

FRONTEND_DIR = r"d:\Ai job finder\frontend\src"

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    orig_content = content

    if 'Tracker.tsx' in filepath:
        content = content.replace("import { Application } from '../types';", "import type { Application } from '../types';")
        content = content.replace("useState<Record<string, unknown>>(null)", "useState<Record<string, number> | null>(null)")
        content = content.replace("const [selectedApp, setSelectedApp] = useState<Record<string, unknown>>(null);", "const [selectedApp, setSelectedApp] = useState<Application | null>(null);")
        content = content.replace("const [followupDraft, setFollowupDraft] = useState<Record<string, unknown>>(null);", "const [followupDraft, setFollowupDraft] = useState<Record<string, string> | null>(null);")
        content = content.replace("selectedApp && selectedApp.job_id", "selectedApp && selectedApp.job_id")
        content = content.replace("app: Record<string, unknown>", "app: Application")
        content = content.replace("app: Application", "app: Application") # Just in case

    if 'Tailor.tsx' in filepath:
        content = content.replace("import { Application } from '../types';", "import type { Application } from '../types';")
        content = content.replace("useState<unknown>(null)", "useState<Record<string, any> | null>(null)") # any is blocked by eslint. We must use a Type.
        content = content.replace("useState<unknown>", "useState<Record<string, string | number | string[]> | null>")
        if 'interface TailoredRes' not in content:
            interface_str = """
interface TailoredRes {
  impact?: string;
  keywords?: string[];
  semantic_match?: number;
  [key: string]: unknown;
}
"""
            content = content.replace("export default function Tailor() {", interface_str + "export default function Tailor() {")
            content = content.replace("const [tailoredRes, setTailoredRes] = useState<Record<string, string | number | string[]> | null>(null);", "const [tailoredRes, setTailoredRes] = useState<TailoredRes | null>(null);")
            content = content.replace("const [tailoredRes, setTailoredRes] = useState<unknown>(null);", "const [tailoredRes, setTailoredRes] = useState<TailoredRes | null>(null);")
            content = content.replace("const [bulletSuggestions, setBulletSuggestions] = useState<unknown[]>([]);", "const [bulletSuggestions, setBulletSuggestions] = useState<Record<string, string>[]>([]);")

    if 'Apply.tsx' in filepath:
        content = content.replace("import { Application } from '../types';", "import type { Application } from '../types';")
        content = content.replace("useState<Application | Job | null>(null)", "useState<Application | null>(null)")
        content = content.replace("useState<Record<string, unknown>>({})", "useState<Record<string, string>>({})")
        content = content.replace("const [appDetail, setAppDetail] = useState<Application | Job | null>(null);", "const [appDetail, setAppDetail] = useState<Application | null>(null);")

    if 'FindJobs.tsx' in filepath:
        content = content.replace("useState<Record<string, unknown>>", "useState<Record<string, string>>")
        content = content.replace("useState<Record<number, unknown>>", "useState<Record<number, string>>")

    if 'ResumeEditor.tsx' in filepath:
        content = content.replace("exp: Record<string, string>", "exp: Record<string, string>") # This is fine

    if 'useAppStore.ts' in filepath:
        content = content.replace("import { Profile", "import type { Profile")

    if 'api.ts' in filepath:
        content = content.replace("catch (error: unknown)", "catch (error)")
        content = content.replace("if (showToastOnError && !error.message.startsWith('API Error'))", "if (showToastOnError && error instanceof Error && !error.message.startsWith('API Error'))")
        content = content.replace("toast.error(`Network Error: ${error.message}`);", "toast.error(`Network Error: ${error instanceof Error ? error.message : String(error)}`);")
        
    if content != orig_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed TS in {os.path.basename(filepath)}")

for root, dirs, files in os.walk(FRONTEND_DIR):
    for f in files:
        if f.endswith('.tsx') or f.endswith('.ts'):
            process_file(os.path.join(root, f))

# Fix Types
TYPES_FILE = os.path.join(FRONTEND_DIR, "types", "index.ts")
with open(TYPES_FILE, 'r', encoding='utf-8') as f:
    types_content = f.read()

if 'notes?: string;' not in types_content:
    types_content = types_content.replace('tailored_resume_text?: string;', '''tailored_resume_text?: string;
  notes?: string;
  applied_at?: string;
  updated_at?: string;
  match_score?: number;''')
    with open(TYPES_FILE, 'w', encoding='utf-8') as f:
        f.write(types_content)
    print("Fixed types/index.ts")
