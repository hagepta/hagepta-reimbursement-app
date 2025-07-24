import streamlit as st
import gspread
import json
import os # Import the os module to access environment variables
from datetime import date
from oauth2client.service_account import ServiceAccountCredentials

reimbursement_categories = [
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
    "5th Grade Promotion",
    "Other"
]

# ---------- Google Sheets Setup ----------
# Use st.cache_resource to cache the gspread client and worksheet
# This ensures the connection and authorization only happen once per app run
@st.cache_resource
def get_gsheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = None # Initialize creds_dict to None

    # --- Try to load credentials from environment variable (for Cloud Run) ---
    if "GOOGLE_APPLICATION_CREDENTIALS_JSON" in os.environ:
        try:
            creds_json_string = os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"]
            creds_dict = json.loads(creds_json_string)
            st.success("Credentials loaded from environment variable.")
        except json.JSONDecodeError:
            st.error("Error decoding GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable. Please check your secret format.")
        except Exception as e:
            st.error(f"Unexpected error loading env var credentials: {e}")
    # --- Fallback: If not in environment, try Streamlit secrets (for local/Streamlit Cloud) ---
    elif "GOOGLE_CREDS" in st.secrets:
        try:
            creds_dict = json.loads(st.secrets["GOOGLE_CREDS"])
            st.success("Credentials loaded from st.secrets['GOOGLE_CREDS'].")
        except json.JSONDecodeError:
            st.error("Error decoding st.secrets['GOOGLE_CREDS']. Please check your secrets.toml format.")
        except Exception as e:
            st.error(f"Unexpected error loading st.secrets credentials: {e}")
    else:
        st.error("No Google credentials found. Please set GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable (for Cloud Run) or st.secrets['GOOGLE_CREDS'] (for local/Streamlit Cloud).")
        st.stop() # Stop the app if no credentials are found

    if creds_dict:
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            client = gspread.authorize(creds)
            return client.open("PTA_Reimbursements_2025-26").worksheet("reimbursements")
        except Exception as e:
            st.error(f"Error authorizing gspread with provided credentials: {e}. Ensure your service account has access to the Google Sheet.")
            st.stop() # Stop the app if authorization fails
    else:
        st.error("Credentials dictionary is empty. Cannot authorize gspread.")
        st.stop()

# Initialize the Google Sheet connection
sheet = get_gsheet()

# Cache the PDF file reading as well, as it's static content
@st.cache_resource
def get_pdf_data(file_path):
    try:
        with open(file_path, "rb") as f:
            return f.read()
    except FileNotFoundError:
        st.warning("Reimbursement PDF form not found. Please ensure 'PaymentAuthorizationRequestforReimbursement.pdf' is in the same directory.")
        return None
    except Exception as e:
        st.error(f"Error loading PDF for download: {e}")
        return None

# ---------- Streamlit UI ----------
st.title(":money_with_wings: PTA Reimbursement Form")

# Download button for the PDF form
pdf_data = get_pdf_data("PaymentAuthorizationRequestforReimbursement.pdf")
if pdf_data:
    st.download_button(
        "📄 Download reimbursement form",
        data=pdf_data,
        file_name="HagepPTA_Reimbursement.pdf",
        mime="application/pdf"
    )

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
        try:
            sheet.append_row([
                str(txn_date),
                name.strip(),
                f"{amount:.2f}",
                desc.strip(),
                category,
                "Awaiting Receipt" # Assuming this is a status column
            ])
            st.success("✅ Submission received. Thank you!")
            st.markdown("📧 Please [email your receipt](mailto:president.hagepta@gmail.com) with the subject 'PTA Reimbursement Receipt'.")
        except Exception as e:
            st.error(f"Failed to submit reimbursement to Google Sheet: {e}")
            st.warning("Please check your Google Sheet permissions and ensure the sheet name and worksheet name are correct.")

