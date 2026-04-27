"""Email Triage Council — 5 Claude agents deliberate on each inbox message.

Roles:
  1. Spam-Spotter   — classify legitimate / promotional / spam / phishing
  2. Urgency-Rater  — 1-5 time sensitivity score
  3. Reply-Drafter  — draft a response if warranted
  4. Tone-Checker   — characterize tone, surface flags
  5. Synthesizer    — fuse the four verdicts into a single recommendation

The four specialists run in parallel; the synthesizer runs on their verdicts.
Requires ANTHROPIC_API_KEY in the environment (override the model with
COUNCIL_MODEL).
"""

import asyncio
import json
import os
import sys

import anthropic

from hotmail_client import HotmailGraphClient, load_config

MODEL = os.environ.get("COUNCIL_MODEL", "claude-opus-4-7")
MAX_BODY_CHARS = 8000


SPAM_SPOTTER = """You are the Spam-Spotter on an email triage council.
Judge whether the message is legitimate, promotional/marketing, spam, or
phishing. Look for red flags: unfamiliar senders, urgency manipulation,
suspicious links, generic greetings, credential or money asks, and mismatched
display name vs. sender domain. Be skeptical but precise — false positives
cost the user real mail. Return JSON conforming to the provided schema."""

URGENCY_RATER = """You are the Urgency-Rater on an email triage council.
Rate how time-sensitive the message is on a 1-5 scale:
  1 = no action needed (newsletter, FYI)
  2 = read this week
  3 = respond within a few days
  4 = respond today
  5 = drop everything (deadline, outage, emergency)
Justify briefly. Return JSON conforming to the provided schema."""

REPLY_DRAFTER = """You are the Reply-Drafter on an email triage council.
If a reply is warranted, draft a concise response (<=150 words) in the same
register as the inbound message. Sign off as the recipient (do not invent a
name). If no reply is needed, set should_reply=false, leave draft empty,
and explain why in notes. Return JSON conforming to the provided schema."""

TONE_CHECKER = """You are the Tone-Checker on an email triage council.
Characterize the inbound message's tone (e.g. friendly, formal, frustrated,
demanding, anxious, neutral) and flag anything the recipient should be aware
of when responding (e.g. escalation risk, sensitive topic, passive-aggression,
legal exposure). Return JSON conforming to the provided schema."""

SYNTHESIZER = """You are the Synthesizer on an email triage council.
You receive verdicts from four specialists: Spam-Spotter, Urgency-Rater,
Reply-Drafter, and Tone-Checker. Produce a single coherent recommendation
the user can act on at a glance: a one-line verdict, a short rationale, and
the final suggested reply (or "none" if no reply is warranted). Resolve
conflicts using your own judgement — the specialists may be wrong. Return
JSON conforming to the provided schema."""


SPAM_SCHEMA = {
    "type": "object",
    "properties": {
        "classification": {
            "type": "string",
            "enum": ["legitimate", "promotional", "spam", "phishing"],
        },
        "confidence": {"type": "number"},
        "reasoning": {"type": "string"},
    },
    "required": ["classification", "confidence", "reasoning"],
    "additionalProperties": False,
}

URGENCY_SCHEMA = {
    "type": "object",
    "properties": {
        "level": {"type": "integer", "enum": [1, 2, 3, 4, 5]},
        "reasoning": {"type": "string"},
    },
    "required": ["level", "reasoning"],
    "additionalProperties": False,
}

REPLY_SCHEMA = {
    "type": "object",
    "properties": {
        "should_reply": {"type": "boolean"},
        "draft": {"type": "string"},
        "notes": {"type": "string"},
    },
    "required": ["should_reply", "draft", "notes"],
    "additionalProperties": False,
}

TONE_SCHEMA = {
    "type": "object",
    "properties": {
        "tone": {"type": "string"},
        "flags": {"type": "array", "items": {"type": "string"}},
        "reasoning": {"type": "string"},
    },
    "required": ["tone", "flags", "reasoning"],
    "additionalProperties": False,
}

SYNTHESIS_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string"},
        "rationale": {"type": "string"},
        "suggested_reply": {"type": "string"},
    },
    "required": ["verdict", "rationale", "suggested_reply"],
    "additionalProperties": False,
}


def _format_email(email):
    body = email["body"]
    if len(body) > MAX_BODY_CHARS:
        body = body[:MAX_BODY_CHARS] + f"\n\n[...truncated, {len(email['body'])} chars total]"
    return (
        f"From: {email['from']}\n"
        f"Subject: {email['subject']}\n"
        f"Received: {email['received']}\n"
        f"\n{body}"
    )


class EmailCouncil:
    def __init__(self, client=None, model=MODEL):
        self.client = client or anthropic.AsyncAnthropic()
        self.model = model

    async def _ask(self, system_prompt, schema, user_content):
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=[{
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{"role": "user", "content": user_content}],
            output_config={"format": {"type": "json_schema", "schema": schema}},
        )
        text = next(b.text for b in response.content if b.type == "text")
        return json.loads(text)

    async def deliberate(self, email):
        formatted = _format_email(email)
        spam, urgency, reply, tone = await asyncio.gather(
            self._ask(SPAM_SPOTTER, SPAM_SCHEMA, formatted),
            self._ask(URGENCY_RATER, URGENCY_SCHEMA, formatted),
            self._ask(REPLY_DRAFTER, REPLY_SCHEMA, formatted),
            self._ask(TONE_CHECKER, TONE_SCHEMA, formatted),
        )
        synthesis_input = (
            f"Email:\n{formatted}\n\n"
            f"Spam-Spotter: {json.dumps(spam)}\n"
            f"Urgency-Rater: {json.dumps(urgency)}\n"
            f"Reply-Drafter: {json.dumps(reply)}\n"
            f"Tone-Checker: {json.dumps(tone)}"
        )
        synthesis = await self._ask(SYNTHESIZER, SYNTHESIS_SCHEMA, synthesis_input)
        return {
            "spam": spam,
            "urgency": urgency,
            "reply": reply,
            "tone": tone,
            "synthesis": synthesis,
        }


def _render(email, verdict):
    s = verdict["synthesis"]
    print()
    print("=" * 70)
    print(f"From:    {email['from']}")
    print(f"Subject: {email['subject']}")
    print("-" * 70)
    print(f"Verdict:   {s['verdict']}")
    print(
        f"Spam:      {verdict['spam']['classification']} "
        f"(conf {verdict['spam']['confidence']:.2f})"
    )
    print(f"Urgency:   {verdict['urgency']['level']}/5")
    print(f"Tone:      {verdict['tone']['tone']}")
    if verdict["tone"]["flags"]:
        print(f"Flags:     {', '.join(verdict['tone']['flags'])}")
    print(f"Rationale: {s['rationale']}")
    reply = (s["suggested_reply"] or "").strip()
    if reply and reply.lower() != "none":
        print(f"\nSuggested reply:\n{reply}")


async def main():
    client_id, tenant_id = load_config()
    hotmail = HotmailGraphClient(client_id, tenant_id)

    user = await hotmail.get_user()
    print(f"Signed in as: {user.display_name} <{user.mail or user.user_principal_name}>")

    top = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    print(f"\nFetching {top} most recent inbox messages...")
    messages = await hotmail.list_inbox_with_body(top=top)

    council = EmailCouncil()
    print(f"Convening council ({council.model})...")

    for m in messages:
        email = {
            "from": (
                m.from_.email_address.address
                if m.from_ and m.from_.email_address
                else "?"
            ),
            "subject": m.subject or "",
            "received": str(m.received_date_time) if m.received_date_time else "",
            "body": (m.body.content if m.body else "") or "",
        }
        verdict = await council.deliberate(email)
        _render(email, verdict)


if __name__ == "__main__":
    asyncio.run(main())
