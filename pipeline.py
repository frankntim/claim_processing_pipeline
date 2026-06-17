"""
pipeline.py — LangGraph + ChatOpenAI claims adjudication pipeline
"""
import json
import re
import os
import uuid
from typing import TypedDict, Annotated

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI

from db import lookup_policy, log_claim


# ── State ────────────────────────────────────────────────────────────────────

class ClaimsState(TypedDict):
    messages:   Annotated[list, add_messages]
    claim_text: str
    extracted:  dict
    validation: dict
    policy:     dict
    decision:   str
    reason:     str


# ── LLM ─────────────────────────────────────────────────────────────────────

def get_llm(api_key: str):
    return ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=api_key)


# ── Agent nodes ──────────────────────────────────────────────────────────────

def make_extractor(llm):
    def extractor_agent(state: ClaimsState) -> dict:
        prompt = f"""You are the Extractor agent in a LangGraph claims processing pipeline.
Extract structured data from the insurance claim document below.

Return ONLY a valid JSON object with these exact keys (use null if not found):
{{
  "claim_ref": string,
  "claimant_name": string,
  "policy_number": string,
  "date_of_incident": string,
  "claim_type": string,
  "estimated_amount": number or null,
  "currency": string,
  "description_summary": string
}}

Claim document:
{state['claim_text']}"""
        res = llm.invoke([{"role": "user", "content": prompt}])
        text = res.content
        m = re.search(r'\{.*\}', text, re.DOTALL)
        try:
            extracted = json.loads(m.group()) if m else {}
        except Exception:
            extracted = {}
        if not extracted.get("claim_ref"):
            extracted["claim_ref"] = "CLM-" + str(uuid.uuid4())[:8].upper()
        return {"extracted": extracted}
    return extractor_agent


def validator_agent(state: ClaimsState) -> dict:
    required = ["claimant_name", "date_of_incident", "claim_type", "estimated_amount"]
    missing = [f for f in required if not state["extracted"].get(f)]
    flags = []
    amt = state["extracted"].get("estimated_amount")
    if isinstance(amt, (int, float)) and amt > 50000:
        flags.append("HIGH_VALUE_CLAIM")
    if not state["extracted"].get("policy_number"):
        flags.append("NO_POLICY_NUMBER")
    return {"validation": {"missing": missing, "flags": flags}}


def policy_retriever_agent(state: ClaimsState) -> dict:
    claim_type = state["extracted"].get("claim_type", "") or ""
    policy = lookup_policy(claim_type.lower().strip())
    return {"policy": policy}


def make_router(llm):
    def decision_router(state: ClaimsState) -> dict:
        v = state["validation"]
        policy = state["policy"]
        extracted = state["extracted"]
        missing = v.get("missing", [])
        flags = v.get("flags", [])
        amt = extracted.get("estimated_amount") or 0

        if missing:
            decision = "NEEDS_INFO"
            reason = (
                f"This claim cannot be processed. The following required fields are missing: "
                f"{', '.join(f.replace('_', ' ') for f in missing)}. "
                "Please resubmit with complete documentation."
            )
            return {"decision": decision, "reason": reason}

        if "HIGH_VALUE_CLAIM" in flags:
            decision = "MANUAL_REVIEW"
            reason = (
                f"This claim (EUR {amt:,.2f}) exceeds the EUR 50,000 automated processing threshold "
                f"under {policy.get('clause_name', 'policy terms')}. "
                "It has been escalated to a senior claims handler for independent assessment. "
                "Expected review time: 5–10 business days."
            )
            return {"decision": decision, "reason": reason}

        # LLM makes the approve/deny decision
        prompt = f"""You are the Decision Router — the final node in a LangGraph claims adjudication pipeline for an Irish insurance company.

Claim data:
{json.dumps(extracted, indent=2)}

Validation flags: {flags if flags else 'none'}

Applicable policy clause:
Clause: {policy.get('clause_name')}
Coverage: {policy.get('coverage')}
Exclusions: {policy.get('exclusions')}
Coverage limit: {policy.get('coverage_limit')}
Pre-authorisation required: {'Yes' if policy.get('requires_preauth') else 'No'}

Based on the above, decide whether this claim should be APPROVED or DENIED.
Start your response with exactly "APPROVED" or "DENIED" on the first line.
Then provide 2–3 clear sentences explaining the decision in plain English suitable for the claimant.
Be specific about which policy clause applies and why."""

        res = llm.invoke([{"role": "user", "content": prompt}])
        text = res.content.strip()
        first_line = text.split('\n')[0].strip().upper()
        decision = "APPROVED" if "APPROVED" in first_line else "DENIED"
        reason = text
        return {"decision": decision, "reason": reason}
    return decision_router


# ── Graph builder ─────────────────────────────────────────────────────────────

def build_graph(api_key: str):
    llm = get_llm(api_key)
    builder = StateGraph(ClaimsState)
    builder.add_node("extractor", make_extractor(llm))
    builder.add_node("validator", validator_agent)
    builder.add_node("retriever", policy_retriever_agent)
    builder.add_node("router",    make_router(llm))
    builder.set_entry_point("extractor")
    builder.add_edge("extractor", "validator")
    builder.add_edge("validator", "retriever")
    builder.add_edge("retriever", "router")
    builder.add_edge("router",    END)
    return builder.compile()


def run_pipeline(claim_text: str, api_key: str) -> dict:
    graph = build_graph(api_key)
    result = graph.invoke({
        "claim_text": claim_text,
        "messages":   [],
        "extracted":  {},
        "validation": {},
        "policy":     {},
        "decision":   "",
        "reason":     "",
    })
    # Log to DB
    e = result.get("extracted", {})
    log_claim(
        claim_ref=e.get("claim_ref", ""),
        claimant_name=e.get("claimant_name", ""),
        claim_type=e.get("claim_type", ""),
        estimated_amount=e.get("estimated_amount"),
        policy_number=e.get("policy_number", ""),
        decision=result.get("decision", ""),
        decision_reason=result.get("reason", ""),
    )
    return result
