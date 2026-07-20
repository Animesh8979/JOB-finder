import json

with open('data/profiles/default.json', encoding='utf-8') as f:
    profile = json.load(f)

# Re-build the full raw_text using ALL data in the profile
raw = f"{profile.get('name', '').upper()}\n"
raw += f"{profile.get('headline', '')}\n"
raw += f"{profile.get('email', '')} | {profile.get('phone', '')} | {profile.get('location', '')} | {' | '.join(profile.get('links', []))}\n\n"

raw += "PROFESSIONAL SUMMARY\n"
raw += f"{profile.get('summary', '')}\n\n"

raw += "WORK EXPERIENCE\n"
for exp in profile.get('experience', []):
    raw += f"{exp.get('title')}   {exp.get('dates')}\n"
    raw += f"{exp.get('company')} | {exp.get('location')}\n"
    for bullet in exp.get('details', []):
        raw += f"- {bullet}\n"
    raw += "\n"

raw += "PROJECTS\n"
for proj in profile.get('projects', []):
    raw += f"{proj.get('name')} | {proj.get('role')}\n"
    for bullet in proj.get('details', []):
        raw += f"- {bullet}\n"
    raw += "\n"

raw += "SKILLS\n"
raw += ", ".join(profile.get('skills', [])) + "\n\n"

raw += "EDUCATION\n"
for edu in profile.get('education', []):
    raw += f"{edu.get('degree')}   {edu.get('dates')}\n"
    raw += f"{edu.get('institution')}\n"
    for detail in edu.get('details', []):
        raw += f"{detail}\n"
    raw += "\n"

raw += "CERTIFICATIONS & AWARDS\n"
for cert in profile.get('certifications', []):
    raw += f"- {cert}\n"

profile['raw_text'] = raw.strip()

with open('data/profiles/default.json', 'w', encoding='utf-8') as f:
    json.dump(profile, f, indent=2)

print("Full raw_text rebuilt!")
