"""
app.py — Streamlit Claims Adjudication System
Run: streamlit run app.py
"""
import os
import io
import time
import tempfile
import datetime

import streamlit as st
from pypdf import PdfReader

from db import init_db, get_claims_log, get_all_policies
from pdf_generator import generate_all_samples, generate_decision_pdf, SAMPLE_CLAIMS
from pipeline import run_pipeline

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Claims Processing Pipeline",
    #page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Init DB ───────────────────────────────────────────────────────────────────
init_db()

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_claims")
DECISION_DIR = os.path.join(os.path.dirname(__file__), "decisions")
os.makedirs(SAMPLE_DIR, exist_ok=True)
os.makedirs(DECISION_DIR, exist_ok=True)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #0D2B55; }
[data-testid="stSidebar"] * { color: #E8EFF8 !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label { color: #A8C0D8 !important; }
.main-title { font-size: 2rem; font-weight: 700; color: #0D2B55; margin-bottom: 0; }
.sub-title   { font-size: 1rem; color: #666; margin-bottom: 1.5rem; }
.pipeline-step { display:inline-flex; align-items:center; gap:6px;
                 background:#F0F4FA; border-radius:20px;
                 padding:6px 14px; font-size:0.85rem; font-weight:600;
                 color:#0D2B55; margin:2px; }
.step-arrow { color:#999; font-size:1.2rem; margin:0 4px; }
.decision-approved { background:#E8F5E9; border-left:4px solid #2E7D32;
                     border-radius:6px; padding:1rem 1.2rem; }
.decision-denied    { background:#FDEDEC; border-left:4px solid #C62828;
                      border-radius:6px; padding:1rem 1.2rem; }
.decision-review    { background:#FFF8E1; border-left:4px solid #F57F17;
                      border-radius:6px; padding:1rem 1.2rem; }
.decision-info      { background:#E3F2FD; border-left:4px solid #1565C0;
                      border-radius:6px; padding:1rem 1.2rem; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚖️ Claims AI")
    st.markdown("---")
    page = st.radio("Navigate", [
        "🏠 Adjudicate Claim",
        "📄 Sample Claims",
        "📋 Claims Log",
        "🗄️ Policy Database",
    ])
    st.markdown("---")
    st.markdown("**OpenAI API Key**")
    api_key = st.text_input("sk-...", type="password",
                             help="Required for live adjudication via GPT-4o")
    if api_key:
        st.success("API key set ✓")
    else:
        st.warning("Add key for live AI adjudication")
    st.markdown("---")
    st.markdown("""
**Pipeline**
1. 🔵 Extractor agent
2. 🟢 Validator agent
3. 🟣 Policy retriever (SQLite)
4. 🟠 Decision router
    """)
    st.markdown("---")
    st.caption("Éire Insurance Group · Demo v1.0")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Adjudicate Claim
# ═══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Adjudicate Claim":
    st.markdown('<div class="main-title">⚖️ Claims Adjudication System</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">LangGraph · ChatOpenAI · SQLite Policy DB · Auto-generated decision PDFs</div>', unsafe_allow_html=True)

    # Pipeline diagram
    col1, col2, col3, col4, col5, col6, col7 = st.columns([2,0.4,2,0.4,2,0.4,2])
    with col1:
        st.markdown('<div class="pipeline-step">🔵 Extractor agent</div>', unsafe_allow_html=True)
        st.caption("Parses claim fields")
    with col2: st.markdown('<div class="step-arrow">›</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="pipeline-step">🟢 Validator agent</div>', unsafe_allow_html=True)
        st.caption("Checks completeness")
    with col4: st.markdown('<div class="step-arrow">›</div>', unsafe_allow_html=True)
    with col5:
        st.markdown('<div class="pipeline-step">🟣 Policy retriever</div>', unsafe_allow_html=True)
        st.caption("SQLite RAG lookup")
    with col6: st.markdown('<div class="step-arrow">›</div>', unsafe_allow_html=True)
    with col7:
        st.markdown('<div class="pipeline-step">🟠 Decision router</div>', unsafe_allow_html=True)
        st.caption("Approve / Review / Deny")

    st.divider()

    tab_upload, tab_paste = st.tabs(["📎 Upload PDF claim", "📝 Paste claim text"])

    claim_text = ""

    with tab_upload:
        uploaded = st.file_uploader(
            "Upload a claim PDF", type=["pdf"],
            help="Upload any of the sample claim PDFs or your own"
        )
        if uploaded:
            with st.spinner("Reading PDF…"):
                reader = PdfReader(io.BytesIO(uploaded.read()))
                claim_text = "\n".join(
                    page.extract_text() or "" for page in reader.pages
                )
            st.success(f"Extracted {len(claim_text)} characters from {uploaded.name}")
            with st.expander("Preview extracted text"):
                st.text(claim_text[:2000] + ("…" if len(claim_text) > 2000 else ""))

    with tab_paste:
        claim_text_input = st.text_area(
            "Paste claim text",
            height=200,
            placeholder="Claimant: Patrick Murphy\nPolicy: AUTO-IE-2024-8821\nDate of incident: 14 May 2025\n…"
        )
        if claim_text_input:
            claim_text = claim_text_input

    st.divider()

    col_run, col_mode = st.columns([2, 3])
    with col_run:
        run_btn = st.button("⚖️ Adjudicate Claim", type="primary",
                             disabled=not claim_text,
                             use_container_width=True)
    with col_mode:
        if not api_key:
            st.info("💡 No API key set — will use demo mode (rule-based adjudication)")

    if run_btn and claim_text:
        with st.status("Running LangGraph pipeline…", expanded=True) as status:
            st.write("🔵 Extractor agent — parsing claim fields…")
            time.sleep(0.3)
            st.write("🟢 Validator agent — checking completeness…")
            time.sleep(0.3)
            st.write("🟣 Policy retriever — querying SQLite policy database…")
            time.sleep(0.3)
            st.write("🟠 Decision router — adjudicating claim…")

            if api_key:
                try:
                    result = run_pipeline(claim_text, api_key)
                except Exception as e:
                    st.error(f"Pipeline error: {e}")
                    st.stop()
            else:
                # Demo mode — rule-based fallback
                import re, uuid
                e = {}
                e["claim_ref"] = "CLM-" + str(uuid.uuid4())[:8].upper()
                for pattern, key in [
                    (r"claimant[:\s]+([^\n]+)", "claimant_name"),
                    (r"policy[:\s#]+([A-Z0-9\-]+)", "policy_number"),
                    (r"date of incident[:\s]+([^\n]+)", "date_of_incident"),
                    (r"claim type[:\s]+([^\n]+)", "claim_type"),
                ]:
                    m = re.search(pattern, claim_text, re.IGNORECASE)
                    e[key] = m.group(1).strip() if m else None
                amt_m = re.search(r"(?:estimated amount|amount)[:\s€£$]*([\d,]+)", claim_text, re.IGNORECASE)
                e["estimated_amount"] = int(amt_m.group(1).replace(",","")) if amt_m else None
                e["currency"] = "EUR"
                e["description_summary"] = claim_text[:100]

                required = ["claimant_name","date_of_incident","claim_type","estimated_amount"]
                missing = [f for f in required if not e.get(f)]
                flags = []
                if isinstance(e.get("estimated_amount"), (int,float)) and e["estimated_amount"] > 50000:
                    flags.append("HIGH_VALUE_CLAIM")
                if not e.get("policy_number"):
                    flags.append("NO_POLICY_NUMBER")

                from db import lookup_policy, log_claim
                policy = lookup_policy((e.get("claim_type") or "").lower())

                if missing:
                    decision = "NEEDS_INFO"
                    reason = f"Missing required fields: {', '.join(f.replace('_',' ') for f in missing)}. Please resubmit with complete documentation."
                elif "HIGH_VALUE_CLAIM" in flags:
                    decision = "MANUAL_REVIEW"
                    reason = f"Claim amount EUR {e['estimated_amount']:,.2f} exceeds the EUR 50,000 automated threshold. Escalated to senior handler."
                else:
                    decision = "APPROVED"
                    reason = f"Claim approved under {policy['clause_name']}. All required fields are present and no exclusions appear to apply. Payment will be processed within 5–7 business days."

                log_claim(e.get("claim_ref",""), e.get("claimant_name",""), e.get("claim_type",""),
                          e.get("estimated_amount"), e.get("policy_number",""), decision, reason)
                result = {"extracted": e, "validation": {"missing": missing, "flags": flags},
                          "policy": policy, "decision": decision, "reason": reason}

            status.update(label="Pipeline complete ✓", state="complete")

        # ── Results ──────────────────────────────────────────────────────────
        st.divider()
        st.subheader("Pipeline Results")

        col_l, col_r = st.columns(2)

        with col_l:
            with st.expander("🔵 Extractor — structured fields", expanded=True):
                ext = result.get("extracted", {})
                for k, v in ext.items():
                    st.markdown(f"**{k.replace('_',' ').title()}:** {v or '—'}")

            with st.expander("🟢 Validator — completeness check", expanded=True):
                val = result.get("validation", {})
                missing = val.get("missing", [])
                flags   = val.get("flags", [])
                if missing:
                    st.warning(f"Missing fields: {', '.join(missing)}")
                else:
                    st.success("All required fields present")
                if flags:
                    for f in flags:
                        st.warning(f"⚑ {f}")
                else:
                    st.success("No flags raised")

        with col_r:
            with st.expander("🟣 Policy retriever — SQLite match", expanded=True):
                pol = result.get("policy", {})
                st.markdown(f"**Clause:** {pol.get('clause_name','—')}")
                st.markdown(f"**Coverage:** {pol.get('coverage','—')}")
                st.markdown(f"**Exclusions:** {pol.get('exclusions','—')}")
                st.markdown(f"**Limit:** {pol.get('coverage_limit','—')}")

        # Decision banner
        decision = result.get("decision", "")
        reason   = result.get("reason", "")
        css_map = {
            "APPROVED":      "decision-approved",
            "DENIED":        "decision-denied",
            "MANUAL_REVIEW": "decision-review",
            "NEEDS_INFO":    "decision-info",
        }
        icon_map = {
            "APPROVED": "✅", "DENIED": "❌",
            "MANUAL_REVIEW": "⚠️", "NEEDS_INFO": "ℹ️"
        }
        css_cls = css_map.get(decision, "decision-info")
        icon    = icon_map.get(decision, "📋")
        st.markdown(f"""
<div class="{css_cls}">
  <h3>{icon} Decision: {decision}</h3>
  <p>{reason}</p>
</div>
""", unsafe_allow_html=True)

        # Generate decision PDF
        st.divider()
        with st.spinner("Generating decision PDF…"):
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            claim_ref = result["extracted"].get("claim_ref", "CLM-UNKNOWN")
            pdf_path = os.path.join(DECISION_DIR, f"decision_{claim_ref}_{ts}.pdf")
            generate_decision_pdf(
                extracted=result["extracted"],
                validation=result["validation"],
                policy=result["policy"],
                decision=decision,
                reason=reason,
                output_path=pdf_path,
            )
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="📥 Download Decision PDF",
                data=f.read(),
                file_name=f"decision_{claim_ref}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Sample Claims
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📄 Sample Claims":
    st.title("📄 Sample Claim PDFs")
    st.markdown("Download pre-generated sample claims to test the adjudication pipeline.")

    if st.button("🔄 Regenerate all sample PDFs", type="secondary"):
        with st.spinner("Generating PDFs…"):
            generate_all_samples(SAMPLE_DIR)
        st.success("All sample PDFs regenerated!")
    else:
        # Generate on first visit if not present
        if not any(f.endswith(".pdf") for f in os.listdir(SAMPLE_DIR)):
            with st.spinner("Generating sample PDFs for the first time…"):
                generate_all_samples(SAMPLE_DIR)

    st.divider()
    for claim in SAMPLE_CLAIMS:
        fname = claim["type"].lower().replace(" ", "_") + "_claim.pdf"
        fpath = os.path.join(SAMPLE_DIR, fname)

        with st.container():
            col_info, col_btn = st.columns([3, 1])
            with col_info:
                st.markdown(f"### {claim['type']}")
                st.markdown(f"**Claimant:** {claim['claimant']}  |  **Policy:** {claim.get('policy','—')}  |  **Amount:** EUR {claim['amount']:,}" if claim.get('amount') else f"**Claimant:** {claim['claimant']}  |  **Amount:** Not provided")
                st.caption(claim["description"][:160] + "…")
            with col_btn:
                if os.path.exists(fpath):
                    with open(fpath, "rb") as f:
                        st.download_button(
                            label="📥 Download",
                            data=f.read(),
                            file_name=fname,
                            mime="application/pdf",
                            key=f"dl_{fname}",
                            use_container_width=True,
                        )
            st.divider()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — Claims Log
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📋 Claims Log":
    st.title("📋 Claims Processing Log")
    st.markdown("All adjudicated claims stored in SQLite.")

    rows = get_claims_log()
    if not rows:
        st.info("No claims processed yet. Go to **Adjudicate Claim** to process your first claim.")
    else:
        import pandas as pd
        df = pd.DataFrame(rows)
        df = df[["claim_ref","claimant_name","claim_type","estimated_amount","decision","processed_at"]]
        df.columns = ["Claim Ref","Claimant","Type","Amount (EUR)","Decision","Processed At"]

        # Colour decision column
        def color_decision(val):
            c = {"APPROVED": "background-color:#E8F5E9", "DENIED": "background-color:#FDEDEC",
                 "MANUAL_REVIEW": "background-color:#FFF8E1", "NEEDS_INFO": "background-color:#E3F2FD"}
            return c.get(val, "")

        styled = df.style.applymap(color_decision, subset=["Decision"])
        st.dataframe(styled, use_container_width=True, hide_index=True)

        # Summary metrics
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Total Claims", len(df))
        with c2: st.metric("Approved", len(df[df["Decision"]=="APPROVED"]))
        with c3: st.metric("Denied", len(df[df["Decision"]=="DENIED"]))
        with c4: st.metric("Pending Review", len(df[df["Decision"].isin(["MANUAL_REVIEW","NEEDS_INFO"])]))


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — Policy Database
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🗄️ Policy Database":
    st.title("🗄️ Policy Database (SQLite)")
    st.markdown("All policy clauses stored in `claims_policy.db` — used by the Policy Retriever agent.")

    policies = get_all_policies()
    if not policies:
        st.warning("No policies found. Run the app to initialise the database.")
    else:
        for p in policies:
            with st.expander(f"📑 {p['claim_type'].title()} — {p['clause_name']}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Coverage:**\n{p['coverage']}")
                    st.markdown(f"**Exclusions:**\n{p['exclusions']}")
                with c2:
                    st.markdown(f"**Coverage Limit:** {p['coverage_limit']}")
                    st.markdown(f"**Auto-Approve Threshold:** EUR {p['auto_approve_limit']:,.0f}")
                    st.markdown(f"**Pre-Authorisation Required:** {'Yes' if p['requires_preauth'] else 'No'}")

    st.divider()
    st.caption(f"Database location: `claims_policy.db`  |  {len(policies)} policy clauses loaded")
