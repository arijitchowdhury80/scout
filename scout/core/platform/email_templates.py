"""Branded HTML + plaintext email builders for hosted API-key delivery."""

from __future__ import annotations

from html import escape
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scout.core.platform.key_delivery import HostedApiKeyDeliveryRequest

_DOCS_URL = "https://scout.chowmes.com/docs"
_PLAYGROUND_URL = "https://scout.chowmes.com/#playground"
_SUPPORT_EMAIL = "support@scout.chowmes.com"

_RETICLE_SVG = (
    '<svg viewBox="0 0 40 40" width="26" height="26">'
    '<circle cx="20" cy="20" r="15" fill="none" stroke="#143C2B" stroke-width="4"/>'
    '<line x1="20" y1="1.5" x2="20" y2="9" stroke="#143C2B" stroke-width="4" '
    'stroke-linecap="round"/>'
    '<line x1="20" y1="31" x2="20" y2="38.5" stroke="#143C2B" stroke-width="4" '
    'stroke-linecap="round"/>'
    '<line x1="1.5" y1="20" x2="9" y2="20" stroke="#143C2B" stroke-width="4" '
    'stroke-linecap="round"/>'
    '<line x1="31" y1="20" x2="38.5" y2="20" stroke="#143C2B" stroke-width="4" '
    'stroke-linecap="round"/>'
    '<circle cx="20" cy="20" r="4.2" fill="#C77A1E"/></svg>'
)


def build_beta_key_email(request: "HostedApiKeyDeliveryRequest") -> tuple[str, str, str]:
    """Build (subject, text_body, html_body) for the branded beta key email."""
    greeting_name = request.name.strip() or "there"
    subject = "Your Scout beta tester API key is ready"
    standard_credits = f"{request.standard_credits:,}"
    browser_credits = f"{request.browser_credits:,}"
    trial_days = str(request.trial_days)
    raw_key = request.raw_api_key

    html_body = _html_body(
        greeting_name=greeting_name,
        raw_key=raw_key,
        standard_credits=standard_credits,
        browser_credits=browser_credits,
        trial_days=trial_days,
    )
    text_body = _text_body(
        greeting_name=greeting_name,
        raw_key=raw_key,
        standard_credits=standard_credits,
        browser_credits=browser_credits,
        trial_days=trial_days,
    )
    return subject, text_body, html_body


def _html_body(
    *,
    greeting_name: str,
    raw_key: str,
    standard_credits: str,
    browser_credits: str,
    trial_days: str,
) -> str:
    """Render the approved branded HTML email design with real substitutions."""
    safe_name = escape(greeting_name)
    safe_key = escape(raw_key)
    masked_key = escape(_mask_key(raw_key))
    return f"""<div style="background:#DCE6E0;padding:28px 12px;font-family:-apple-system,'Segoe UI',Roboto,Arial,sans-serif">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;margin:0 auto;background:#F0F4F1;border-radius:16px;overflow:hidden">
  <tr><td style="padding:26px 34px 8px">
    <table role="presentation" cellpadding="0" cellspacing="0"><tr>
      <td style="vertical-align:middle;padding-right:9px">
        {_RETICLE_SVG}
      </td>
      <td style="vertical-align:middle;font-weight:800;font-size:19px;letter-spacing:-.02em;color:#143C2B">Scout</td>
    </tr></table>
  </td></tr>

  <tr><td style="padding:14px 34px 4px">
    <h1 style="margin:0;font-size:27px;line-height:1.15;color:#1D2521;font-weight:800;letter-spacing:-.02em">Hi {safe_name}, your Scout API key is ready.</h1>
    <p style="margin:12px 0 0;font-size:15px;line-height:1.6;color:#566259">Welcome — you've got <b style="color:#1D2521">{standard_credits} credits</b> to turn any URL into clean, citable records. Here's everything to make your first call in the next five minutes.</p>
  </td></tr>

  <tr><td style="padding:20px 34px 4px">
    <p style="margin:0 0 7px;font-size:11px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#0E8A61">Your API key</p>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td style="background:#141D18;border-radius:10px;padding:14px 16px;font-family:'SF Mono',Menlo,Consolas,monospace;font-size:13px;color:#7BD4AC;word-break:break-all">{safe_key}</td></tr></table>
    <p style="margin:8px 0 0;font-size:12.5px;color:#566259">Treat it like a password. Need a new one? Reissue any time from the site.</p>
  </td></tr>

  <tr><td style="padding:22px 34px 4px">
    <p style="margin:0 0 12px;font-size:11px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#0E8A61">First 5 minutes</p>

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:12px"><tr>
      <td width="30" style="vertical-align:top"><div style="width:22px;height:22px;border-radius:7px;background:#143C2B;color:#E9F2EC;font-size:12px;font-weight:700;text-align:center;line-height:22px">1</div></td>
      <td style="font-size:14.5px;color:#1D2521;line-height:1.5"><b>Scrape your first URL.</b><br><span style="color:#566259">Run this — you'll get a typed record back.</span></td>
    </tr></table>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 16px"><tr><td style="background:#141D18;border-radius:10px;padding:14px 16px;font-family:'SF Mono',Menlo,monospace;font-size:12.5px;color:#EAF2ED;line-height:1.6">curl -X POST https://scout.chowmes.com/v1/scrape \\<br>&nbsp;&nbsp;-H "Authorization: Bearer <span style="color:#7BD4AC">{masked_key}</span>" \\<br>&nbsp;&nbsp;-d '{{"url":"https://example.com"}}'</td></tr></table>

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:12px"><tr>
      <td width="30" style="vertical-align:top"><div style="width:22px;height:22px;border-radius:7px;background:#143C2B;color:#E9F2EC;font-size:12px;font-weight:700;text-align:center;line-height:22px">2</div></td>
      <td style="font-size:14.5px;color:#1D2521;line-height:1.5"><b>Check the evidence.</b><br><span style="color:#566259">Every record carries its <span style="color:#B26A12;font-weight:700">source, citation, and a verified&nbsp;✓</span> — that's the whole point of Scout.</span></td>
    </tr></table>

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
      <td width="30" style="vertical-align:top"><div style="width:22px;height:22px;border-radius:7px;background:#143C2B;color:#E9F2EC;font-size:12px;font-weight:700;text-align:center;line-height:22px">3</div></td>
      <td style="font-size:14.5px;color:#1D2521;line-height:1.5"><b>Go further.</b><br><span style="color:#566259">Crawl a whole site, pull a product catalog, or build a company dossier — same key, every endpoint.</span></td>
    </tr></table>
  </td></tr>

  <tr><td style="padding:22px 34px 4px">
    <table role="presentation" cellpadding="0" cellspacing="0"><tr>
      <td style="padding-right:10px"><a href="{_DOCS_URL}" style="display:inline-block;background:#143C2B;color:#E9F2EC;font-size:14px;font-weight:700;text-decoration:none;padding:12px 22px;border-radius:11px">Read the docs</a></td>
      <td><a href="{_PLAYGROUND_URL}" style="display:inline-block;background:#E4EBE6;color:#143C2B;font-size:14px;font-weight:700;text-decoration:none;padding:12px 22px;border-radius:11px">Open the playground</a></td>
    </tr></table>
  </td></tr>

  <tr><td style="padding:20px 34px 4px">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td style="background:#E8EFEA;border-radius:12px;padding:16px 18px">
      <p style="margin:0;font-size:13.5px;color:#1D2521;line-height:1.55"><b>Try this first:</b> point Scout at a competitor's pricing page — you'll get back a clean record of every plan and price, each one cited to the exact source. That's a task that usually takes an afternoon.</p>
    </td></tr></table>
  </td></tr>

  <tr><td style="padding:20px 34px 4px">
    <p style="margin:0;font-size:13px;color:#566259;line-height:1.5">Trial: {standard_credits} standard credits and {browser_credits} browser credits for {trial_days} days.</p>
  </td></tr>

  <tr><td style="padding:20px 34px 8px">
    <p style="margin:0;font-size:14px;color:#566259;line-height:1.6">Stuck, or just want to tell me what you're building? <b style="color:#1D2521">Reply to this email</b> — or write <a href="mailto:{_SUPPORT_EMAIL}" style="color:#0E8A61;font-weight:700;text-decoration:none">{_SUPPORT_EMAIL}</a>. It reaches the founder directly, and replies work.</p>
    <p style="margin:14px 0 0;font-size:14px;color:#1D2521">— Arijit, Scout</p>
  </td></tr>

  <tr><td style="padding:20px 34px 26px;border-top:1px solid #DBE3DD">
    <p style="margin:0;font-family:'SF Mono',Menlo,monospace;font-size:11.5px;color:#8A948C">Scout · evidence before extraction claims · <a href="https://scout.chowmes.com" style="color:#8A948C">scout.chowmes.com</a></p>
  </td></tr>
</table>
</div>
"""


def _mask_key(raw_key: str) -> str:
    """Return a masked preview of the raw key for illustrative code samples."""
    prefix = raw_key.split("_")[0] if "_" in raw_key else raw_key
    return f"{prefix}_…"


def _text_body(
    *,
    greeting_name: str,
    raw_key: str,
    standard_credits: str,
    browser_credits: str,
    trial_days: str,
) -> str:
    """Render a clean plaintext fallback matching the HTML content."""
    return "\n".join(
        [
            f"Hi {greeting_name},",
            "",
            (
                f"Welcome — you've got {standard_credits} credits to turn any URL "
                "into clean, citable records. Here's everything to make your first "
                "call in the next five minutes."
            ),
            "",
            "YOUR API KEY",
            raw_key,
            "Treat it like a password. Need a new one? Reissue any time from the site.",
            "",
            "FIRST 5 MINUTES",
            "1. Scrape your first URL — run this, you'll get a typed record back:",
            "curl -X POST https://scout.chowmes.com/v1/scrape \\",
            f'  -H "Authorization: Bearer {raw_key}" \\',
            '  -d \'{"url":"https://example.com"}\'',
            "",
            (
                "2. Check the evidence — every record carries its source, citation, "
                "and a verified mark."
            ),
            (
                "3. Go further — crawl a whole site, pull a product catalog, or "
                "build a company dossier, same key, every endpoint."
            ),
            "",
            f"Docs: {_DOCS_URL}",
            f"Playground: {_PLAYGROUND_URL}",
            "",
            (
                "Try this first: point Scout at a competitor's pricing page — "
                "you'll get back a clean record of every plan and price, each one "
                "cited to the exact source."
            ),
            "",
            f"Trial: {standard_credits} standard credits and {browser_credits} "
            f"browser credits for {trial_days} days.",
            "",
            (
                "Stuck, or just want to tell me what you're building? Reply to this "
                f"email or write {_SUPPORT_EMAIL} — it reaches the founder directly, "
                "and replies work."
            ),
            "",
            "— Arijit, Scout",
        ]
    )
