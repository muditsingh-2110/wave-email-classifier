"""
Wave Email Agent - Email Classifier (local demo)
=================================================
Reads 10 dummy emails and classifies each one as:
  * SERVICE_REQUEST  - maintenance / repair / physical issue in property
  * COMPLAINT        - strong dissatisfaction / escalation / legal threat / misconduct
  * GENERAL_QUERY    - pricing / possession timeline / amenity status / process questions

No external API needed - uses a keyword + rule-based classifier that mirrors
what watsonx.ai Granite would do in production.

Run:
    python classify_emails.py
"""

import json
import re
from pathlib import Path
from datetime import datetime

# ── Load dummy emails ───────────────────────────────────────────────────────
EMAILS_FILE = Path(__file__).parent / "dummy_emails.json"


def load_emails() -> list[dict]:
    with open(EMAILS_FILE, encoding="utf-8") as f:
        return json.load(f)


# ── Classifier ──────────────────────────────────────────────────────────────

# Keywords that signal each category (checked on lowercased subject + body)
COMPLAINT_SIGNALS = [
    "fraud", "cheating", "rera", "consumer court", "legal action", "police",
    "court", "rude", "dismissive", "formal complaint", "not acceptable",
    "terrible", "worst", "harassment", "threatening", "disgusting",
    "written apology", "escalate", "overcharged", "not paying",
    "6 months", "no refund", "refund not received",
]

SERVICE_REQUEST_SIGNALS = [
    "lift", "elevator", "leakage", "seepage", "crack", "repair",
    "broken", "not working", "maintenance", "technician", "plumber",
    "electrician", "parking", "not allotted", "water supply", "power cut",
    "sewage", "drainage", "pest", "painting", "gym equipment", "damage",
]

GENERAL_QUERY_SIGNALS = [
    "price", "pricing", "cost", "rate", "floor plan", "inventory",
    "available", "possession", "possession date", "when will", "timeline",
    "clubhouse", "swimming pool", "amenity", "ready", "noc",
    "home loan", "bank", "payment plan", "schedule", "query", "question",
    "when", "status", "update", "information",
]

# Negative sentiment boosters
NEGATIVE_SIGNALS = [
    "fraud", "cheating", "rera", "court", "legal", "rude", "terrible",
    "worst", "disgusting", "harassment", "overcharged", "not refunded",
    "no resolution", "no response", "urgent", "immediate", "not acceptable",
    "3 days", "1 year", "6 months", "2 months", "10 times",
]

PRIORITY_HIGH_SIGNALS = [
    "urgent", "immediate", "emergency", "3 days", "severe", "elderly",
    "children", "court", "rera", "legal", "7 days", "refund",
]


def count_signals(text: str, signals: list[str]) -> int:
    """Count how many signal phrases appear in text."""
    return sum(1 for s in signals if s in text)


def classify_email(email: dict) -> dict:
    """
    Classify a single email dict.
    Returns classification result with category, sentiment, priority, reason.
    """
    text = (email["subject"] + " " + email["body"]).lower()

    complaint_score  = count_signals(text, COMPLAINT_SIGNALS)
    sr_score         = count_signals(text, SERVICE_REQUEST_SIGNALS)
    query_score      = count_signals(text, GENERAL_QUERY_SIGNALS)
    negative_score   = count_signals(text, NEGATIVE_SIGNALS)
    priority_score   = count_signals(text, PRIORITY_HIGH_SIGNALS)

    # ── Category decision ──────────────────────────────────────────────────
    # Complaints outrank SRs — a frustrated resident raising a physical issue
    # is still a COMPLAINT if they use escalation language
    if complaint_score >= 2:
        category = "COMPLAINT"
    elif sr_score >= 2:
        category = "SERVICE_REQUEST"
    elif sr_score == 1 and complaint_score == 1:
        category = "COMPLAINT"   # anger + physical issue = complaint
    else:
        category = "GENERAL_QUERY"

    # ── Sentiment ──────────────────────────────────────────────────────────
    if negative_score >= 3:
        sentiment = "NEGATIVE"
    elif negative_score >= 1:
        sentiment = "NEUTRAL"
    else:
        sentiment = "POSITIVE"

    # ── Priority ──────────────────────────────────────────────────────────
    if priority_score >= 2 or category == "COMPLAINT":
        priority = "HIGH"
    elif priority_score == 1 or category == "SERVICE_REQUEST":
        priority = "MEDIUM"
    else:
        priority = "LOW"

    # ── Routing ───────────────────────────────────────────────────────────
    routing = {
        "COMPLAINT":       "CRM Escalation Team",
        "SERVICE_REQUEST": "Facilities / Project Team",
        "GENERAL_QUERY":   "CRM General Team",
    }[category]

    # ── One-line summary (first sentence of body, max 80 chars) ───────────
    first_sentence = re.split(r'[.!?]', email["body"].strip())[0].strip()
    summary = first_sentence[:80] + ("…" if len(first_sentence) > 80 else "")

    return {
        "email_id":  email["id"],
        "from":      email["from"],
        "subject":   email["subject"],
        "category":  category,
        "sentiment": sentiment,
        "priority":  priority,
        "route_to":  routing,
        "summary":   summary,
        "scores": {
            "complaint": complaint_score,
            "service_request": sr_score,
            "query": query_score,
        },
    }


# ── Colour helpers ───────────────────────────────────────────────────────────
import sys

def _enable_windows_ansi():
    """Enable VT100 ANSI codes on Windows 10+ cmd/PowerShell."""
    if sys.platform == "win32":
        try:
            import ctypes
            ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            INVALID_HANDLE_VALUE = -1
            STD_OUTPUT_HANDLE = -11
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
            if handle == INVALID_HANDLE_VALUE:
                return
            cur_mode = ctypes.c_ulong()
            if not kernel32.GetConsoleMode(handle, ctypes.byref(cur_mode)):
                return
            kernel32.SetConsoleMode(handle, cur_mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING)
        except Exception:
            pass  # silently fall back to plain text if it fails

_enable_windows_ansi()

CAT_COLOUR = {
    "COMPLAINT":       "\033[91m",   # red
    "SERVICE_REQUEST": "\033[93m",   # yellow
    "GENERAL_QUERY":   "\033[92m",   # green
}
RESET = "\033[0m"

def c(text: str, colour: str) -> str:
    return f"{colour}{text}{RESET}"


# ── Runner ──────────────────────────────────────────────────────────────────

def run():
    emails = load_emails()
    results = [classify_email(e) for e in emails]

    SEP = "-" * 110

    print(f"\n{'Wave Email Agent - Classification Results':^110}")
    print(f"{'Run at: ' + datetime.now().strftime('%d %b %Y %H:%M:%S'):^110}")
    print(SEP)
    print(f"  {'ID':<12} {'CATEGORY':<18} {'SENTIMENT':<12} {'PRIORITY':<10} {'ROUTE TO':<28} {'SUBJECT'}")
    print(SEP)

    category_counts = {"COMPLAINT": 0, "SERVICE_REQUEST": 0, "GENERAL_QUERY": 0}

    for r in results:
        col = CAT_COLOUR[r["category"]]
        subject_trunc = r["subject"][:42] + ("..." if len(r["subject"]) > 42 else "")
        print(
            f"  {r['email_id']:<12} "
            f"{c(r['category']+'   ', col):<18} "
            f"{r['sentiment']:<12} "
            f"{r['priority']:<10} "
            f"{r['route_to']:<28} "
            f"{subject_trunc}"
        )
        category_counts[r["category"]] += 1

    print(SEP)

    # ── Summary ───────────────────────────────────────────────────────────
    print(f"\n  SUMMARY")
    print(f"  {'-'*40}")
    print(f"  Total emails processed  : {len(results)}")
    print(f"  {c('COMPLAINT      ', CAT_COLOUR['COMPLAINT'])}      : {category_counts['COMPLAINT']}")
    print(f"  {c('SERVICE_REQUEST', CAT_COLOUR['SERVICE_REQUEST'])} : {category_counts['SERVICE_REQUEST']}")
    print(f"  {c('GENERAL_QUERY  ', CAT_COLOUR['GENERAL_QUERY'])}  : {category_counts['GENERAL_QUERY']}")

    # ── Detail view ───────────────────────────────────────────────────────
    print(f"\n{'-'*110}")
    print(f"  DETAIL VIEW (per email)")
    print(f"{'-'*110}")
    for r in results:
        col = CAT_COLOUR[r["category"]]
        print(f"\n  [{r['email_id']}]  {r['subject']}")
        print(f"  From      : {r['from']}")
        print(f"  Category  : {c(r['category'], col)}  |  Sentiment: {r['sentiment']}  |  Priority: {r['priority']}")
        print(f"  Route to  : {r['route_to']}")
        print(f"  Summary   : {r['summary']}")

    print(f"\n{'-'*110}\n")

    # ── Save JSON output ──────────────────────────────────────────────────
    out_path = Path(__file__).parent / "classification_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"  Results saved to: {out_path}\n")


if __name__ == "__main__":
    run()
