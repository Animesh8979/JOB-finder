import os
import re

FRONTEND_DIR = r"d:\Ai job finder\frontend\src"

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    orig_content = content

    if 'any' not in content:
        return

    # Special replacements for components
    if 'useAppStore.ts' in filepath:
        content = content.replace('profile: any | null', 'profile: Profile | null')
        content = content.replace('updateProfile: (p: any) => void', 'updateProfile: (p: Profile) => void')
        content = content.replace('prefs: any | null', 'prefs: Preferences | null')
        content = content.replace('secrets: any | null', 'secrets: Secrets | null')
        content = content.replace('updatePrefs: (p: any, s?: any) => void', 'updatePrefs: (p: Preferences, s?: Secrets) => void')
        content = content.replace('set({ profile: p })', 'set({ profile: p })')
        
        if 'import { Profile' not in content:
            content = "import { Profile, Preferences, Secrets } from './types';\n" + content

    if 'api.ts' in filepath:
        content = content.replace('catch (e: any)', 'catch (e: unknown)')
        content = content.replace('catch (err: any)', 'catch (err: unknown)')

    if 'Dashboard.tsx' in filepath:
        content = content.replace('useState<any[]>', 'useState<Job[]>')
        content = content.replace('useState<any>', 'useState<Record<string, unknown>>')
        content = content.replace('catch (e: any)', 'catch (e: unknown)')
        if 'import { Job' not in content:
            content = "import { Job } from '../types';\n" + content

    if 'FindJobs.tsx' in filepath:
        content = content.replace('useState<any[]>', 'useState<Job[]>')
        content = content.replace('useState<any>', 'useState<Record<string, unknown>>')
        content = content.replace('job: any', 'job: Job')
        content = content.replace('catch (err: any)', 'catch (err: unknown)')
        content = content.replace('catch (e: any)', 'catch (e: unknown)')
        content = content.replace('(prev: any)', '(prev: Record<number, unknown>)')
        content = content.replace('([cat]: any)', '([cat])')
        if 'import { Job' not in content:
            content = "import { Job } from '../types';\n" + content

    if 'Tracker.tsx' in filepath:
        content = content.replace('useState<any[]>', 'useState<Application[]>')
        content = content.replace('useState<any>', 'useState<Record<string, unknown>>')
        content = content.replace('app: any', 'app: Application')
        content = content.replace('catch (err: any)', 'catch (err: unknown)')
        content = content.replace('catch (e: any)', 'catch (e: unknown)')
        if 'import { Application' not in content:
            content = "import { Application } from '../types';\n" + content

    if 'Setup.tsx' in filepath:
        content = content.replace('updatedProfile: any', 'updatedProfile: Profile')
        content = content.replace('catch (err: any)', 'catch (err: Error | unknown)')
        content = content.replace('value: any', 'value: unknown')
        content = content.replace('props: any', 'props: React.SVGProps<SVGSVGElement>')
        if 'import { Profile' not in content:
            content = "import { Profile } from '../types';\n" + content
            
    if 'Apply.tsx' in filepath:
        content = content.replace('useState<any[]>', 'useState<Application[]>')
        content = content.replace('useState<any>', 'useState<Application | Job | null>')
        content = content.replace('catch (err: any)', 'catch (err: unknown)')
        content = content.replace('catch (e: any)', 'catch (e: unknown)')
        content = content.replace('(j: any)', '(j: Job)')
        content = content.replace('const sheet: any =', 'const sheet: Record<string, string> =')
        content = content.replace('([label, value]: any)', '([label, value])')
        if 'import { Application' not in content:
            content = "import { Application, Job } from '../types';\n" + content

    if 'Outreach.tsx' in filepath:
        content = content.replace('useState<any[]>', 'useState<Contact[]>')
        # Outreach has multiple useState<any[]>
        content = content.replace('setContacts(dContacts)', 'setContacts(dContacts)')
        content = content.replace('setOutreachLogs(dLogs)', 'setOutreachLogs(dLogs)')
        content = content.replace('setJobs(dJobs)', 'setJobs(dJobs)')
        content = content.replace('catch (err: any)', 'catch (err: unknown)')
        content = content.replace('catch (e: any)', 'catch (e: unknown)')
        if 'import { Contact' not in content:
            content = "import { Contact, OutreachLog, Job } from '../types';\n" + content
            content = content.replace('useState<Contact[]>([])\n  const [outreachLogs, setOutreachLogs] = useState<any[]>([])', 'useState<Contact[]>([])\n  const [outreachLogs, setOutreachLogs] = useState<OutreachLog[]>([])')
            content = content.replace('const [outreachLogs, setOutreachLogs] = useState<any[]>([]);', 'const [outreachLogs, setOutreachLogs] = useState<OutreachLog[]>([]);')
            content = content.replace('const [jobs, setJobs] = useState<any[]>([]);', 'const [jobs, setJobs] = useState<Job[]>([]);')

    if 'Tailor.tsx' in filepath:
        content = content.replace('useState<any[]>', 'useState<Application[]>')
        content = content.replace('useState<any>', 'useState<unknown>')
        content = content.replace('catch (err: any)', 'catch (err: unknown)')
        content = content.replace('catch (e: any)', 'catch (e: unknown)')
        content = content.replace('item: any', 'item: Record<string, string>')
        if 'import { Application' not in content:
            content = "import { Application, Job } from '../types';\n" + content
            content = content.replace('const [bulletSuggestions, setBulletSuggestions] = useState<unknown[]>([]);', 'const [bulletSuggestions, setBulletSuggestions] = useState<Record<string, string>[]>([]);')

    if 'ResumeEditor.tsx' in filepath:
        content = content.replace('profile: any;', 'profile: Profile;')
        content = content.replace('onSave: (p: any) => void;', 'onSave: (p: Profile) => void;')
        content = content.replace('handleChange = (field: string, value: any)', 'handleChange = (field: string, value: unknown)')
        content = content.replace('setEditedProfile((prev: any)', 'setEditedProfile((prev: Profile)')
        content = content.replace('e: any', 'e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>')
        if 'import { Profile' not in content:
            content = "import { Profile } from '../types';\n" + content

    if content != orig_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {os.path.basename(filepath)}")

for root, dirs, files in os.walk(FRONTEND_DIR):
    for f in files:
        if f.endswith('.tsx') or f.endswith('.ts'):
            process_file(os.path.join(root, f))

print("Done")
