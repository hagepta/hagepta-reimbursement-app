import streamlit as st
import gspread
import json
import os
from datetime import date, datetime # Ensure datetime is imported for current time
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import storage
import time

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

# Google Cloud Storage bucket name for receipts
GCS_BUCKET_NAME = "hage-pta-reimbursement-receipts"

# ---------- Google Sheets Setup ----------
@st.cache_resource
def get_gsheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = None

    if "GOOGLE_APPLICATION_CREDENTIALS_JSON" in os.environ:
        try:
            creds_json_string = os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"]
            creds_dict = json.loads(creds_json_string)
            st.success("Credentials loaded from GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable.")
        except json.JSONDecodeError:
            st.error("Error decoding GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable. Please check your secret format.")
        except Exception as e:
            st.error(f"Unexpected error loading env var credentials: {e}")
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
        st.stop()

    if creds_dict:
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            client = gspread.authorize(creds)
            return client.open("PTA_Reimbursements_2025-26").worksheet("reimbursements")
        except Exception as e:
            st.error(f"Error authorizing gspread with provided credentials: {e}. Ensure your service account has access to the Google Sheet.")
            st.stop()
    else:
        st.error("Credentials dictionary is empty. Cannot authorize gspread.")
        st.stop()

# Initialize the Google Sheet connection
sheet = get_gsheet()

# Cache the PDF file reading
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

# ---------- Google Cloud Storage Upload Functions ----------
@st.cache_resource
def get_gcs_client():
    if "GOOGLE_APPLICATION_CREDENTIALS_JSON" in os.environ:
        creds_json_string = os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"]
        creds_dict = json.loads(creds_json_string)
    elif "GOOGLE_CREDS" in st.secrets:
        creds_dict = json.loads(st.secrets["GOOGLE_CREDS"])
    else:
        st.error("No Google credentials found for GCS client. Please ensure setup is complete.")
        return None

    if creds_dict:
        try:
            client = storage.Client.from_service_account_info(creds_dict)
            st.success("Google Cloud Storage client initialized.")
            return client
        except Exception as e:
            st.error(f"Error initializing GCS client: {e}")
            return None
    return None

def upload_file_to_gcs(uploaded_file, folder_prefix, submitter_name, submission_time_str):
    gcs_client = get_gcs_client()
    if not gcs_client:
        return None

    try:
        bucket = gcs_client.get_bucket(GCS_BUCKET_NAME)
        original_filename = uploaded_file.name
        safe_name = "".join(c if c.isalnum() or c in ('.', '-') else '_' for c in submitter_name).lower() # Sanitize and lowercase name
        file_extension = os.path.splitext(original_filename)[1]

        # Construct a unique destination blob name
        # Example: payment_auth_forms/john_doe_2025-07-28_10-30-00_form.pdf
        # Example: supporting_receipts/john_doe_2025-07-28_10-30-00_receipt_1.jpg
        destination_blob_name = f"{folder_prefix}/{safe_name}_{submission_time_str}_{os.path.basename(original_filename)}"

        blob = bucket.blob(destination_blob_name)
        uploaded_file.seek(0) # Ensure file pointer is at the beginning
        blob.upload_from_file(uploaded_file, content_type=uploaded_file.type)

        # Consider making objects public if needed for direct viewing, or use signed URLs for security
        # blob.make_public() # Uncomment if you want public read access

        receipt_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{destination_blob_name}"
        return receipt_url
    except Exception as e:
        st.error(f"Failed to upload file '{uploaded_file.name}' to Cloud Storage: {e}")
        return None

# ---------- Streamlit UI ----------
st.title(":money_with_wings: PTA Payment Authorization Form :money_with_wings:")

st.markdown("""
            1. Download the payment authorization PDF & fill it out.
            2. Upload your completed payment authorization PDF.
            3. Upload any supporting receipts for your expenses.
            4. Fill out the reimbursement form details.
            """)

pdf_data = get_pdf_data("PaymentAuthorizationRequestforReimbursement.pdf")
if pdf_data:
    st.download_button(
        "📄 Download payment authorization form",
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

    # File Uploader for Payment Authorization Form (single file)
    uploaded_payment_auth_form = st.file_uploader(
        "Upload Completed Payment Authorization Form (PDF, JPG, PNG)",
        type=["pdf", "jpg", "jpeg", "png"],
        key="payment_auth_uploader" # Unique key for this uploader
    )

    # New File Uploader for Supporting Receipts (multiple files allowed)
    uploaded_supporting_receipts = st.file_uploader(
        "Upload Supporting Receipts (PDF, JPG, PNG) - Multiple files allowed",
        type=["pdf", "jpg", "jpeg", "png"],
        accept_multiple_files=True, # Allow multiple files
        key="supporting_receipts_uploader" # Unique key for this uploader
    )

    submitted = st.form_submit_button("Submit")

if submitted:
    if not name or not desc:
        st.error("Please fill out all required fields.")
    else:
        payment_auth_form_url = "No Payment Auth Form Uploaded"
        supporting_receipts_urls = "No Supporting Receipts Uploaded"
        submission_time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") # Use datetime.now() for current time

        # Handle Payment Authorization Form upload
        if uploaded_payment_auth_form:
            payment_auth_form_url = upload_file_to_gcs(
                uploaded_payment_auth_form,
                "payment_auth_forms", # Folder prefix for payment auth forms
                name.strip(),
                submission_time_str
            )
            if not payment_auth_form_url:
                st.error("Payment Authorization Form upload failed. Please try again.")
                st.stop()

        # Handle Supporting Receipts upload
        if uploaded_supporting_receipts:
            temp_urls = []
            for i, file in enumerate(uploaded_supporting_receipts):
                receipt_url = upload_file_to_gcs(
                    file,
                    "supporting_receipts", # Folder prefix for supporting receipts
                    name.strip(),
                    f"{submission_time_str}_part{i+1}" # Unique suffix for each supporting receipt
                )
                if receipt_url:
                    temp_urls.append(receipt_url)
                else:
                    st.warning(f"Failed to upload supporting receipt: {file.name}. Continuing with others.")
            if temp_urls:
                supporting_receipts_urls = ", ".join(temp_urls) # Join URLs with comma for sheet
            else:
                st.warning("No supporting receipts were successfully uploaded.")

        try:
            # Append data to Google Sheet, including both URLs
            sheet.append_row([
                str(txn_date),
                name.strip(),
                f"{amount:.2f}",
                desc.strip(),
                category,
                payment_auth_form_url,    # Column for Payment Authorization Form URL
                supporting_receipts_urls  # NEW Column for Supporting Receipts URLs
            ])
            st.success("✅ Submission received. Thank you!")
            st.markdown("📧 Please allow 5-7 business days for processing.")
            time.sleep(5)  # Optional: Pause to allow user to read success message
            st.rerun()
        except Exception as e:
            st.error(f"Failed to submit reimbursement to Google Sheet: {e}")
            st.warning("Please check your Google Sheet permissions and ensure the sheet name and worksheet name are correct, and that you have enough columns for all data.")

