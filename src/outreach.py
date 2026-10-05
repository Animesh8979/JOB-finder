"""Draft personalized recruiter emails — targeted, capped, and DRAFT-ONLY.

Nothing here sends email. It produces text and a .eml file (a draft you open in your own
mail client). Compliance guardrails: real identity, an opt-out line, and a daily cap.
"""
from __future__ import annotations

from email.message import EmailMessage

from . import config, db, llm
from .documents import slugify
from .profile_parser import profile_context
from .anti_slop import audit_and_sanitize


def usage_today(prefs: dict) -> tuple[int, int]:
    cap = int(prefs.get("outreach_daily_cap", 15) or 15)
    return db.count_outreach_today(), cap


def compliance_footer(prefs: dict) -> str:
    ident = prefs.get("identity", {}) or {}
    lines = ["Best regards,", ident.get("full_name", "") or "(your name)"]
    contact = " · ".join(b for b in (ident.get("email", ""), ident.get("phone", "")) if b)
    if contact:
        lines.append(contact)
    physical = ident.get("physical_address") or ident.get("location") or "[User Physical Address - Required by CAN-SPAM]"
    lines.append(f"Office: {physical} | To unsubscribe, reply with \"STOP\" or \"unsubscribe\"")
    return "\n".join(lines)


def draft_email(contact: dict, job: dict | None, profile: dict, prefs: dict,
                tone: str = "Professional", extra: str = "") -> tuple[str, str]:
    used, cap = usage_today(prefs)
    if used >= cap:
        raise ValueError(f"Outreach daily cap of {cap} has been reached for today ({used} sent/drafted).")

    name = (prefs.get("identity", {}) or {}).get("full_name") or (profile or {}).get("name", "")
    company = contact.get("company") or (job or {}).get("company", "")
    role = (job or {}).get("title", "") or contact.get("role", "")
    jd = ((job or {}).get("description") or "")[:1200]
    recipient = contact.get("name") or "there"
    notes = f"Extra context to include: {extra}\n" if extra.strip() else ""
    jd_block = f"Job description excerpt:\n{jd}\n" if jd else ""

    prompt = (
        f"Write a short, {tone.lower()} outreach email from the candidate to a recruiter/hiring "
        f"contact.\n\n"
        f"Recipient name: {recipient}\nRecipient company: {company}\n"
        f"Role of interest: {role or '(general interest)'}\n"
        f"{jd_block}{notes}\n"
        "RULES:\n"
        "- 110-170 words, 2-3 short paragraphs.\n"
        "- Personalized to the company/role; reference the candidate's MOST relevant real "
        "experience (no exaggeration, nothing invented).\n"
        "- Polite, confident, specific. A clear, low-pressure ask (consideration or a brief chat).\n"
        "- Do NOT add a signature, closing, or contact details, those are appended automatically.\n"
        "- CRITICAL ANTI-AI-SLOP RULES: Never use em-dashes (—) or double hyphens (--). Use commas or hyphens (-).\n"
        "- Never use cliché buzzwords like delve/tapestry/spearheaded/fostered/leverage/robust/seamless.\n"
        "- Greet the recipient by name if provided.\n\n"
        "Return JSON: {\"subject\": str (<=70 chars), \"body\": str}."
    )
    data = llm.generate_json(
        prompt,
        system=(
            "You write concise, genuine, non-spammy professional outreach emails. "
            "Never use em-dashes (—) or cliché AI buzzwords (delve, tapestry, spearheaded, fostered). "
            "Write authentically like a human engineer."
        ),
        cached_context=profile_context(profile),
        model=prefs.get("writing_model"),
        max_tokens=600,
    )
    subject = (data.get("subject") or "").strip() if isinstance(data, dict) else ""
    body = (data.get("body") or "").strip() if isinstance(data, dict) else ""
    if not subject:
        subject = f"Interested in {role} at {company}".strip() or f"Hello from {name}"
    subject = audit_and_sanitize(subject).cleaned_text
    body = audit_and_sanitize(body).cleaned_text
    body = f"{body}\n\n{compliance_footer(prefs)}"
    return subject, body


def save_eml(contact: dict, subject: str, body: str, prefs: dict) -> str:
    ident = prefs.get("identity", {}) or {}
    msg = EmailMessage()
    msg["To"] = contact.get("email", "")
    msg["From"] = ident.get("email", "")
    msg["Subject"] = subject
    msg.set_content(body)
    stem = slugify(contact.get("email") or contact.get("name") or "contact")
    path = config.OUTPUTS_DIR / f"email_{stem}.eml"
    path.write_bytes(bytes(msg))
    return str(path)


def record(contact: dict, job: dict | None, subject: str, body: str,
           channel: str = "eml", status: str = "draft") -> None:
    cid = db.add_contact(
        name=contact.get("name", ""), email=contact.get("email", ""),
        company=contact.get("company", ""), role=contact.get("role", ""),
        source=contact.get("source", "manual"),
        job_id=(job or {}).get("id"),
    )
    db.add_outreach(
        contact_id=cid, job_id=(job or {}).get("id"),
        subject=subject, body=body, channel=channel, status=status,
    )

class OutreachQueue:
    """SQLite-backed defensive queue for safely throttling outgoing emails via MCP."""
    
    @staticmethod
    def enqueue(contact: dict, subject: str, body: str, prefs: dict) -> None:
        """Adds an email to the database queue."""
        cid = db.add_contact(
            name=contact.get("name", ""), email=contact.get("email", ""),
            company=contact.get("company", ""), role=contact.get("role", ""),
            source=contact.get("source", "manual")
        )
        db.add_outreach(contact_id=cid, job_id=None, subject=subject, body=body, channel="mcp", status="queued")

    @staticmethod
    def pop_ready(daily_limit: int = 30) -> list[dict]:
        """Gets up to `daily_limit` queued emails, respecting the daily cap."""
        used = db.count_outreach_today()
        if used >= daily_limit:
            return []
            
        with db.get_conn() as cur:
            cur.execute(
                "SELECT id, contact_id, subject, body FROM outreach_log WHERE status = 'queued' LIMIT ?",
                (daily_limit - used,)
            )
            return [{"id": r[0], "contact_id": r[1], "subject": r[2], "body": r[3]} for r in cur.fetchall()]

    @staticmethod
    def mark_sent(outreach_id: int) -> None:
        """Marks the email as successfully sent via MCP."""
        with db.get_conn() as cur:
            cur.execute("UPDATE outreach_log SET status = 'sent', sent_at = ? WHERE id = ?", (db._now(), outreach_id))

