"""
pdf_generator.py — Generate sample claim PDF documents using ReportLab
"""
import os
import random
import string
from datetime import datetime, timedelta

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

WIDTH, HEIGHT = A4

# Brand colours
NAVY   = colors.HexColor("#0D2B55")
RED    = colors.HexColor("#C0392B")
LGRAY  = colors.HexColor("#F5F5F5")
MGRAY  = colors.HexColor("#CCCCCC")
DKGRAY = colors.HexColor("#555555")


def _ref():
    return "CLM-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


def _rand_date(days_back=180):
    d = datetime.today() - timedelta(days=random.randint(1, days_back))
    return d.strftime("%d %B %Y")


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("ct", fontSize=18, textColor=NAVY,
                                 fontName="Helvetica-Bold", spaceAfter=4),
        "subtitle": ParagraphStyle("cs", fontSize=10, textColor=DKGRAY,
                                    fontName="Helvetica", spaceAfter=12),
        "section": ParagraphStyle("ch", fontSize=11, textColor=NAVY,
                                   fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=4),
        "body": ParagraphStyle("cb", fontSize=9.5, textColor=DKGRAY,
                                fontName="Helvetica", leading=15, spaceAfter=6),
        "label": ParagraphStyle("cl", fontSize=8, textColor=MGRAY,
                                 fontName="Helvetica-Bold", spaceAfter=1),
        "value": ParagraphStyle("cv", fontSize=10, textColor=colors.black,
                                 fontName="Helvetica", spaceAfter=4),
        "footer": ParagraphStyle("cf", fontSize=7.5, textColor=MGRAY,
                                  fontName="Helvetica", alignment=TA_CENTER),
        "stamp": ParagraphStyle("cst", fontSize=22, textColor=RED,
                                 fontName="Helvetica-Bold", alignment=TA_CENTER),
    }


def _field_table(pairs, col_widths=(70*mm, 90*mm)):
    data = []
    for label, value in pairs:
        data.append([label, value])
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LGRAY),
        ("TEXTCOLOR",  (0, 0), (0, -1), NAVY),
        ("FONTNAME",   (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("PADDING",    (0, 0), (-1, -1), 5),
        ("GRID",       (0, 0), (-1, -1), 0.25, MGRAY),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LGRAY, colors.white]),
    ]))
    return t


SAMPLE_CLAIMS = [
    {
        "type": "Auto Collision",
        "claimant": "Patrick Murphy",
        "policy": "AUTO-IE-2024-8821",
        "amount": 12400,
        "currency": "EUR",
        "description": (
            "The insured vehicle (2021 Toyota Corolla, reg. 211-D-14552) was struck at a roundabout "
            "on the N11 southbound near Stillorgan by a third-party vehicle (Volkswagen Golf, reg. "
            "221-KE-3301) which failed to yield. The collision caused significant damage to the front "
            "bumper, bonnet, and nearside headlight assembly. Third-party insurance details were "
            "exchanged at the scene. A Garda report was filed the same day at Dun Laoghaire Garda "
            "Station (Report No. DL-2025-04471). Two independent repair quotes have been obtained."
        ),
        "supporting_docs": ["Garda Report DL-2025-04471", "Repair Quote – Murphy's Garage (EUR 12,400)", "Third-Party Insurance Certificate"],
    },
    {
        "type": "Water Damage",
        "claimant": "Siobhan O'Brien",
        "policy": "HOME-IE-2023-4412",
        "amount": 67000,
        "currency": "EUR",
        "description": (
            "A burst pipe beneath the kitchen floor caused extensive flooding throughout the entire "
            "ground floor of the insured property at 14 Lakeview Drive, Castleknock, Dublin 15. "
            "The incident occurred overnight on 3 January 2025. The flooding resulted in severe damage "
            "to hardwood flooring, kitchen cabinetry, built-in appliances, and the structural sub-floor. "
            "An emergency plumber (O'Sullivan Plumbing, invoice no. OSP-2025-0041) attended the same day "
            "and isolated the burst section. A contractor assessment has been completed and a full "
            "remediation quote of EUR 67,000 has been submitted."
        ),
        "supporting_docs": ["Emergency Plumber Invoice OSP-2025-0041", "Contractor Remediation Quote (EUR 67,000)", "Photographic Evidence (18 images)", "Loss Adjuster Pre-Assessment"],
    },
    {
        "type": "Medical Procedure",
        "claimant": "Dr. Aoife Byrne",
        "policy": "HEALTH-IE-2024-0093",
        "amount": 8750,
        "currency": "EUR",
        "description": (
            "Elective arthroscopic knee surgery (right knee, medial meniscus repair) was performed "
            "on 22 March 2025 at Mater Private Hospital, Eccles Street, Dublin 7. The procedure was "
            "pre-authorised by the insurer on 1 March 2025 (Auth Ref: MPRIV-2025-0338). The claim "
            "covers the surgeon's fee (Mr. Conor Walsh, FRCSI), anaesthesia, theatre charges, and "
            "one night of inpatient accommodation in a semi-private room. All itemised invoices from "
            "the hospital are attached. The claimant has recovered without complication."
        ),
        "supporting_docs": ["Pre-Authorisation Ref MPRIV-2025-0338", "Mater Private Hospital Invoice (EUR 8,750)", "Surgeon's Report – Mr. C. Walsh", "Anaesthesia Invoice"],
    },
    {
        "type": "Theft",
        "claimant": "Brendan Kavanagh",
        "policy": "HOME-IE-2022-7731",
        "amount": 14200,
        "currency": "EUR",
        "description": (
            "The insured property at 7 Ashgrove Close, Portmarnock, Co. Dublin was broken into "
            "on the evening of 8 February 2025 while the claimant was attending a family event. "
            "Entry was gained via a forced rear patio door. Items stolen include a laptop, jewellery, "
            "a watch, and cash. A police report was filed with Malahide Garda Station within 24 hours "
            "(Report No. MH-2025-00921). A full itemised list of stolen property with replacement "
            "valuations is attached. A locksmith replaced the door and lock the following morning."
        ),
        "supporting_docs": ["Garda Report MH-2025-00921", "Itemised Stolen Property List", "Locksmith Invoice", "Photographic Evidence of Forced Entry"],
    },
    {
        "type": "Incomplete Claim",
        "claimant": "Anonymous Claimant",
        "policy": "",
        "amount": None,
        "currency": "EUR",
        "description": (
            "My car was hit while parked outside my house last week. The damage is quite bad and "
            "it will cost a lot to fix. I am not sure of the exact amount yet. The other driver "
            "drove off without stopping. Please process this claim as soon as possible."
        ),
        "supporting_docs": [],
    },
]


def generate_sample_pdf(claim_data: dict, output_path: str) -> str:
    S = _styles()
    ref = claim_data.get("ref", _ref())
    date_filed = claim_data.get("date_filed", datetime.today().strftime("%d %B %Y"))
    incident_date = claim_data.get("incident_date", _rand_date())

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=18*mm, bottomMargin=18*mm,
    )

    story = []

    # Header bar (simulated with a table)
    header_data = [[
        Paragraph("ÉIRE INSURANCE GROUP", ParagraphStyle(
            "hd", fontSize=14, textColor=colors.white,
            fontName="Helvetica-Bold")),
        Paragraph("INSURANCE CLAIM FORM", ParagraphStyle(
            "hd2", fontSize=11, textColor=colors.white,
            fontName="Helvetica", alignment=TA_RIGHT))
    ]]
    header_tbl = Table(header_data, colWidths=[110*mm, 70*mm])
    header_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("PADDING",    (0, 0), (-1, -1), 8),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 6*mm))

    # Claim reference + date row
    meta_data = [[
        f"Claim Reference: {ref}",
        f"Date Filed: {date_filed}",
        f"Status: SUBMITTED"
    ]]
    meta_tbl = Table(meta_data, colWidths=[65*mm, 60*mm, 55*mm])
    meta_tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), LGRAY),
        ("TEXTCOLOR",   (0, 0), (-1, -1), NAVY),
        ("FONTNAME",    (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8.5),
        ("PADDING",     (0, 0), (-1, -1), 5),
        ("GRID",        (0, 0), (-1, -1), 0.25, MGRAY),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 5*mm))

    # Section 1: Claimant details
    story.append(Paragraph("1. Claimant Details", S["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=NAVY))
    story.append(Spacer(1, 2*mm))

    claimant_fields = [
        ("Full Name",      claim_data.get("claimant", "")),
        ("Policy Number",  claim_data.get("policy", "Not provided")),
        ("Claim Type",     claim_data.get("type", "")),
        ("Date of Incident", incident_date),
    ]
    story.append(_field_table(claimant_fields))
    story.append(Spacer(1, 4*mm))

    # Section 2: Financial details
    story.append(Paragraph("2. Financial Summary", S["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=NAVY))
    story.append(Spacer(1, 2*mm))

    amount = claim_data.get("amount")
    amount_str = f"{claim_data.get('currency','EUR')} {amount:,.2f}" if amount else "Not provided"
    fin_fields = [
        ("Estimated Claim Amount", amount_str),
        ("Currency",               claim_data.get("currency", "EUR")),
        ("Excess Applicable",      "EUR 500.00 (subject to policy terms)"),
        ("Net Payable (est.)",     f"{claim_data.get('currency','EUR')} {max(0,(amount or 0)-500):,.2f}" if amount else "TBD"),
    ]
    story.append(_field_table(fin_fields))
    story.append(Spacer(1, 4*mm))

    # Section 3: Incident description
    story.append(Paragraph("3. Description of Incident", S["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=NAVY))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(claim_data.get("description", ""), S["body"]))
    story.append(Spacer(1, 4*mm))

    # Section 4: Supporting documents
    docs = claim_data.get("supporting_docs", [])
    story.append(Paragraph("4. Supporting Documents Submitted", S["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=NAVY))
    story.append(Spacer(1, 2*mm))
    if docs:
        doc_data = [[f"  {chr(9679)}  {d}"] for d in docs]
        doc_tbl = Table(doc_data, colWidths=[170*mm])
        doc_tbl.setStyle(TableStyle([
            ("FONTNAME",  (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE",  (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 0), (-1, -1), DKGRAY),
            ("PADDING",   (0, 0), (-1, -1), 3),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LGRAY, colors.white]),
        ]))
        story.append(doc_tbl)
    else:
        story.append(Paragraph("No supporting documents provided.", S["body"]))
    story.append(Spacer(1, 6*mm))

    # Declaration
    story.append(Paragraph("5. Declaration", S["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=NAVY))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "I declare that the information provided in this claim form is true and accurate to the best of my "
        "knowledge and belief. I understand that providing false information may result in the claim being "
        "declined and may constitute insurance fraud, which is a criminal offence.",
        S["body"]
    ))
    story.append(Spacer(1, 8*mm))

    sig_data = [
        ["Claimant Signature:", "_______________________________", "Date:", date_filed],
    ]
    sig_tbl = Table(sig_data, colWidths=[40*mm, 75*mm, 15*mm, 50*mm])
    sig_tbl.setStyle(TableStyle([
        ("FONTNAME",  (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",  (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, 0), DKGRAY),
        ("TEXTCOLOR", (2, 0), (2, 0), DKGRAY),
        ("PADDING",   (0, 0), (-1, -1), 4),
    ]))
    story.append(sig_tbl)
    story.append(Spacer(1, 8*mm))

    # Footer
    story.append(HRFlowable(width="100%", thickness=0.3, color=MGRAY))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "Eire Insurance Group · Claims Department · Block 3, Grand Canal Square, Dublin 2, D02 Y690 · "
        "claims@eireinsurance.ie · 1800 555 888  |  This document is auto-generated for demonstration purposes.",
        S["footer"]
    ))

    doc.build(story)
    return output_path


def generate_all_samples(output_dir: str) -> list[str]:
    os.makedirs(output_dir, exist_ok=True)
    paths = []
    for claim in SAMPLE_CLAIMS:
        fname = claim["type"].lower().replace(" ", "_") + "_claim.pdf"
        path = os.path.join(output_dir, fname)
        generate_sample_pdf(claim, path)
        paths.append(path)
    return paths


def generate_decision_pdf(extracted: dict, validation: dict,
                           policy: dict, decision: str,
                           reason: str, output_path: str) -> str:
    S = _styles()
    ref = extracted.get("claim_ref", _ref())
    today = datetime.today().strftime("%d %B %Y")

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=18*mm, bottomMargin=18*mm,
    )
    story = []

    # Header
    header_data = [[
        Paragraph("ÉIRE INSURANCE GROUP", ParagraphStyle(
            "hd", fontSize=14, textColor=colors.white, fontName="Helvetica-Bold")),
        Paragraph("ADJUDICATION DECISION", ParagraphStyle(
            "hd2", fontSize=11, textColor=colors.white,
            fontName="Helvetica", alignment=TA_RIGHT))
    ]]
    header_tbl = Table(header_data, colWidths=[110*mm, 70*mm])
    header_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("PADDING",    (0, 0), (-1, -1), 8),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 5*mm))

    meta_data = [[f"Claim Reference: {ref}", f"Decision Date: {today}", f"Processed By: AI Adjudication System v1.0"]]
    meta_tbl = Table(meta_data, colWidths=[65*mm, 55*mm, 60*mm])
    meta_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LGRAY),
        ("TEXTCOLOR",  (0, 0), (-1, -1), NAVY),
        ("FONTNAME",   (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 8),
        ("PADDING",    (0, 0), (-1, -1), 5),
        ("GRID",       (0, 0), (-1, -1), 0.25, MGRAY),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 5*mm))

    # Decision stamp
    d_color = colors.HexColor("#1A7A3A") if decision == "APPROVED" else \
              colors.HexColor("#C0392B") if decision == "DENIED" else \
              colors.HexColor("#D68910")
    stamp_bg = colors.HexColor("#E8F5E9") if decision == "APPROVED" else \
               colors.HexColor("#FDEDEC") if decision == "DENIED" else \
               colors.HexColor("#FEF9E7")

    stamp_tbl = Table([[Paragraph(f"DECISION: {decision}", ParagraphStyle(
        "st", fontSize=20, textColor=d_color,
        fontName="Helvetica-Bold", alignment=TA_CENTER))]],
        colWidths=[170*mm])
    stamp_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), stamp_bg),
        ("PADDING",    (0, 0), (-1, -1), 10),
        ("BOX",        (0, 0), (-1, -1), 1.5, d_color),
    ]))
    story.append(stamp_tbl)
    story.append(Spacer(1, 5*mm))

    # Claim summary
    story.append(Paragraph("Claim Summary", S["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=NAVY))
    story.append(Spacer(1, 2*mm))
    amount = extracted.get("estimated_amount")
    fields = [
        ("Claimant",         extracted.get("claimant_name", "—")),
        ("Policy Number",    extracted.get("policy_number", "Not provided")),
        ("Claim Type",       extracted.get("claim_type", "—")),
        ("Date of Incident", extracted.get("date_of_incident", "—")),
        ("Claimed Amount",   f"{extracted.get('currency','EUR')} {amount:,.2f}" if amount else "—"),
    ]
    story.append(_field_table(fields))
    story.append(Spacer(1, 4*mm))

    # Validation results
    story.append(Paragraph("Validation Results", S["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=NAVY))
    story.append(Spacer(1, 2*mm))
    missing = validation.get("missing", [])
    flags = validation.get("flags", [])
    val_fields = [
        ("Missing Fields", ", ".join(missing) if missing else "None"),
        ("Flags Raised",   ", ".join(flags) if flags else "None"),
    ]
    story.append(_field_table(val_fields))
    story.append(Spacer(1, 4*mm))

    # Policy clause
    story.append(Paragraph("Applicable Policy Clause", S["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=NAVY))
    story.append(Spacer(1, 2*mm))
    pol_fields = [
        ("Clause",      policy.get("clause_name", "—")),
        ("Coverage",    policy.get("coverage", "—")),
        ("Exclusions",  policy.get("exclusions", "—")),
        ("Limit",       policy.get("coverage_limit", "—")),
    ]
    story.append(_field_table(pol_fields, col_widths=(45*mm, 125*mm)))
    story.append(Spacer(1, 4*mm))

    # Decision reasoning
    story.append(Paragraph("Decision Reasoning", S["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=NAVY))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(reason, S["body"]))
    story.append(Spacer(1, 6*mm))

    # Next steps
    story.append(Paragraph("Next Steps", S["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=NAVY))
    story.append(Spacer(1, 2*mm))
    if decision == "APPROVED":
        next_steps = "Payment will be processed within 5–7 business days to the bank account on file. You will receive a separate payment confirmation. Please retain this document for your records."
    elif decision == "DENIED":
        next_steps = "If you wish to appeal this decision, please submit a written appeal within 30 days to appeals@eireinsurance.ie quoting your claim reference. You may also contact the Financial Services and Pensions Ombudsman (FSPO) if you remain dissatisfied."
    elif decision == "MANUAL_REVIEW":
        next_steps = "Your claim has been assigned to a senior claims handler. You will be contacted within 2 business days. An independent loss adjuster may be appointed. Estimated decision time: 5–10 business days."
    else:
        next_steps = "Please resubmit this claim with all required information. Contact claims@eireinsurance.ie or call 1800 555 888 for assistance."
    story.append(Paragraph(next_steps, S["body"]))
    story.append(Spacer(1, 8*mm))

    story.append(HRFlowable(width="100%", thickness=0.3, color=MGRAY))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "Eire Insurance Group · Claims Department · Block 3, Grand Canal Square, Dublin 2, D02 Y690 · "
        "claims@eireinsurance.ie · 1800 555 888  |  This decision letter was generated by the AI Adjudication System.",
        S["footer"]
    ))

    doc.build(story)
    return output_path
