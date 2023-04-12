import pandas as pd
import numpy as np
import re
import PyPDF2
import streamlit as st

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import io
import os
import tempfile
from PyPDF2 import PdfReader

import gspread as gs
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import storage


# Set the path to your service account credentials file
creds_path = 'https://www.dropbox.com/s/ukkafo8d5dkb2xh/credentials.json?dl=0'


# Build the credentials object from your service account credentials file
creds = service_account.Credentials.from_service_account_file(creds_path)

# Scopes links used to connect the script to the Google Drive and Google sheets
scope = ['https://www.googleapis.com/auth/drive',
         'https://www.googleapis.com/auth/spreadsheets']

# Creating the credentials variable to connect to the API
credentials = ServiceAccountCredentials.from_json_keyfile_name(creds_path,scope)

st.title("**PO Medmen Reader**")

file_uploaded = st.file_uploader("Upload PDF File",accept_multiple_files=True)

# Define a function to read PDF files
def read_pdf(file):
    try:
        # Download the PDF file
        file = file
        # Create a temporary file to store the PDF contents
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file)
            temp_file.seek(0)
            # Read the PDF file using PyPDF2
            pdf_reader = PdfReader(temp_file)
                        
            # Extract text from file
            text = ''
            for page in range(pdf_reader._get_num_pages()):
                page_obj = pdf_reader._get_page(page)
                text += page_obj.extract_text()
            # Regular expresion to find field needed
            pattern = r"(Subtotal|Invoice Discount|Tax|Excise Tax|Total|Total Ordered Qty):\s*([\d,.]+)"
            # pattern_2 = r"(Subtotal\n(\$ [\d,]+\.\d{2})\nTaxes\n(\$ [\d,]+\.\d{2})\nTotal\n(\$ [\d,]+\.\d{2}))"


            # Look for the fields needed
            campos_de_texto = re.findall(pattern, text)
            # campos_de_texto_2 = re.findall(pattern_2, text)

            # Regular expresion to get PO Number
            po_pattern = r"(PO\d+)"

            # Look for the PO Number
            text_field_po = re.findall(po_pattern,text)                 
                
    except HttpError as error:
        print(f"An error occurred: {error}")
        file = None
    return campos_de_texto,text_field_po


def write_gs_PO():
    df = pd.DataFrame(campos_de_texto,columns=['Description','Amount'])
    df['PO Number'] = text_field_po[0] 
    df_gpd = df.pivot(index='PO Number',columns='Description',values='Amount').reset_index()
    
    # Authenticate and authorize access to Google Sheets API
    client = gs.authorize(credentials=credentials)

    spreadsheet_name = ' MEDMEN METRC FILE'
    sheet_name = 'PO'
    spreadsheet = client.open(spreadsheet_name)
    sheet = spreadsheet.worksheet(sheet_name)

    # Get the data from the DataFrame
    data = df_gpd.values.tolist()

    # Opening Google sheet using the ID
    google_sheet_values = client.open_by_key('1yMJrh1qEWlU_PpDP08B_pPHiTgY6rh_DIbd-L0SonlI')
    gs_values = google_sheet_values.get_worksheet_by_id(84284142).get_values('A:V')
        

    # Write the data to the sheet
    if data[0] in gs_values:
        st.write(f'{data[0][0]} Already exists in file')
        pass
    else:
        sheet.append_rows(data)
        st.write(f'{data[0][0]} Added to file')


def show_table():
    # Authenticate and authorize access to Google Sheets API
    client = gs.authorize(credentials=credentials)

    spreadsheet_name = ' MEDMEN METRC FILE'
    sheet_name = 'PO'
    spreadsheet = client.open(spreadsheet_name)
    sheet = spreadsheet.worksheet(sheet_name)
    st.table(sheet.get_all_values())

if file_uploaded is not None:
    st.write(f'{len(file_uploaded)} POs were uploaded')
    for i in file_uploaded:
        campos_de_texto,text_field_po = read_pdf(i.read())
        write_gs_PO()
    show_table()


st.markdown('---')
left_col,center_col,right_col = st.columns(3)

with center_col:
    st.title('**Powered by HQ**')
    st.image('https://www.dropbox.com/s/twrl9exjs8piv7t/Headquarters%20transparent%20light%20logo.png?dl=1')

