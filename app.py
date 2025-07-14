import streamlit as st
import gspread
import json
from datetime import date
from oauth2client.service_account import ServiceAccountCredentials

reimbursement_categories = [
    "5th Grade Promotion",
    "Book Fair",
    "Family Night",
    "Hage Fall Festival",
    "Hospitality",
    "Panther Buck Lunch",
    "Paws on Deck",
    "PE Equipment",
    "Spirt Wear",
    "Student of the Month",
    "Student of the Month refreshments",
    "Taxes",
    "Teacher Appreciation",
    "Teacher Reimbursements",
    "Variety Show",
    "Other"
]

# ---------- Google Sheets Setup ----------
def get_gsheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = json.loads(st.secrets["GOOGLE_CREDS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open("PTA_Reimbursements_2025-26").worksheet("reimbursements")

sheet = get_gsheet()

# ---------- Streamlit UI ----------
st.title(":money_with_wings: PTA Reimbursement Form")



with open("PaymentAuthorizationRequestforReimbursement.pdf", "rb") as f:
    st.download_button("📄 Download reimbursement form",
                       data=f.read(),
                       file_name="Teacher_Reimbursement.pdf",
                       mime="application/pdf")

st.divider()

with st.form("reimb_form", clear_on_submit=True):
    name = st.text_input("Your name")
    col1, col2 = st.columns(2)
    with col1:
        amount = st.number_input("Amount ($)", min_value=0.0, step=0.5, format="%.2f")
    with col2:
        txn_date = st.date_input("Transaction date", value=date.today())
    desc = st.text_area("Transaction description", height=100)

    category = st.selectbox(
    "Category",
    reimbursement_categories
    )

    submitted = st.form_submit_button("Submit")
    




if submitted:
    if not name or not desc:
        st.error("Please fill out all required fields.")
    else:
        sheet.append_row([
            str(txn_date),
            name.strip(),
            f"{amount:.2f}",
            desc.strip(),
            category,
            "Awaiting Receipt"
        ])
        st.success("✅ Submission received. Thank you!")
        st.markdown("📧 Please [email your receipt](mailto:president.hagepta@gmail.com) with the subject 'PTA Reimbursement Receipt'.")
