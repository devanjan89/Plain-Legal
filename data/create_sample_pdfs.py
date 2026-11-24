"""Generate 3 realistic public-style sample PDFs for testing and evaluation."""

from pathlib import Path
import fitz

DOCS: dict[str, tuple[str, list[str]]] = {
    "sample_rental_agreement.pdf": (
        "STANDARD RESIDENTIAL LEASE",
        [
            """RESIDENTIAL RENTAL AGREEMENT

Section 1. Parties and Premises
1.1 This Rental Agreement is made between Alex Sharma ("Landlord") and Priya Nair ("Tenant") for Flat 4B, Greenview Apartments, Pune.
1.2 The premises shall be used strictly for residential purposes.

Section 2. Term and Rent
2.1 The lease term is 11 months, starting January 1, 2026 and ending November 30, 2026.
2.2 Monthly rent is INR 22,000, payable on or before the 5th of each month.
2.3 The Landlord may not increase the monthly rent during the 11-month lease term. Any revision applies only upon renewal with 30 days written notice.""",
            """Section 3. Security Deposit
3.1 The Tenant shall pay a refundable security deposit of INR 66,000 before moving in.
3.2 The deposit shall be refunded within 30 days of vacating the premises, after deducting unpaid rent or documented repair costs beyond normal wear and tear.

Section 4. Termination and Notice Period
4.1 Either party may terminate this agreement early by giving 60 days written notice.
4.2 If the Tenant vacates without serving the full notice period, rent for the remaining notice days may be deducted from the security deposit.

Section 5. Late Fees and Penalties
5.1 Rent paid after the 5th of the month incurs a late fee of INR 500 per day, capped at INR 5,000 per month.""",
            """Section 6. Maintenance and Subletting
6.1 Minor day-to-day repairs up to INR 1,000 are the Tenant's responsibility. Major structural and plumbing repairs are the Landlord's responsibility.
6.2 Subletting or assigning the premises without prior written consent of the Landlord is strictly prohibited.

Section 7. Auto-Renewal
7.1 Unless either party gives 30 days written notice before expiry, this agreement automatically renews for another 11 months with a 7% rent increase.""",
        ],
    ),
    "sample_terms_of_service.pdf": (
        "CLOUDNOTE TERMS OF SERVICE",
        [
            """CLOUDNOTE TERMS OF SERVICE

Section 1. Accounts and Eligibility
1.1 You must be at least 18 years old to create a CloudNote account.
1.2 You are responsible for keeping your password confidential and for all activity under your account.

Section 2. Subscription and Auto-Renewal
2.1 Paid plans are billed monthly or annually in advance.
2.2 Subscriptions automatically renew at the end of each billing cycle unless cancelled at least 7 days before the renewal date.
2.3 Refunds are available within 14 days of initial purchase; renewal charges are non-refundable.""",
            """Section 3. Data Privacy and Third-Party Sharing
3.1 CloudNote collects usage analytics, device identifiers, and account email addresses.
3.2 CloudNote may share anonymized usage data with advertising and analytics partners, but will never sell your private notes.

Section 4. Termination and Suspension
4.1 You may delete your account at any time from account settings.
4.2 CloudNote may suspend or terminate accounts immediately without prior notice for spam, illegal content, or payment chargebacks.""",
        ],
    ),
    "sample_pm_kisan_guidelines.pdf": (
        "PM-KISAN SCHEME GUIDELINES",
        [
            """PM-KISAN SCHEME OPERATIONAL GUIDELINES

Section 1. Objective and Benefit
1.1 Under the PM-KISAN scheme, eligible landholding farmer families receive financial support of INR 6,000 per year.
1.2 The benefit is transferred directly into Aadhaar-seeded bank accounts in three equal installments of INR 2,000 every four months.

Section 2. Eligibility Criteria
2.1 All landholding farmer families having cultivable landholding in their names are eligible, subject to exclusion criteria.
2.2 A family is defined as husband, wife, and minor children.""",
            """Section 3. Exclusion Categories
3.1 Institutional landholders are excluded from receiving benefits under the scheme.
3.2 Farmers who paid income tax in the previous assessment year are not eligible.
3.3 Serving or retired officers and employees of Central or State Government ministries (excluding Multi-Tasking Staff / Class IV) are excluded.

Section 4. Verification and Grievance
4.1 Beneficiaries must complete e-KYC via Aadhaar OTP or biometric authentication at a Common Service Centre to receive installments.
4.2 Farmers can check installment status or register grievances on the official PM-KISAN portal.""",
        ],
    ),
}


def main() -> None:
    out_dir = Path("data/samples")
    out_dir.mkdir(parents=True, exist_ok=True)

    for filename, (header_text, pages) in DOCS.items():
        doc = fitz.open()
        for i, body in enumerate(pages, start=1):
            page = doc.new_page(width=595, height=842)
            page.insert_text((50, 35), f"{header_text} - PUBLIC SAMPLE", fontsize=9)
            page.insert_textbox(fitz.Rect(50, 100, 545, 740), body, fontsize=11)
            page.insert_text((50, 800), "Plain Legal Sample Corpus", fontsize=9)
            page.insert_text((500, 800), f"Page {i} of {len(pages)}", fontsize=9)
        out_path = out_dir / filename
        doc.save(out_path)
        doc.close()
        print(f"Created {out_path}")


if __name__ == "__main__":
    main()
