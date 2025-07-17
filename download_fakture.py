import os
import time
import shutil
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL_SALES = os.getenv("BASE_URL_SALES")
BASE_URL_PURCHASE = os.getenv("BASE_URL_PURCHASE")
OUTPUT_DIR_BASE = os.getenv("OUTPUT_DIR_BASE", "eFakture")
MAX_ARCHIVE_FOLDERS = int(os.getenv("MAX_ARCHIVE_FOLDERS", 5))

HEADERS = {
    "ApiKey": API_KEY,
    "Content-Type": "application/json",
    "accept": "*/*"
}

OUTPUT_DIR_SALES = os.path.join(OUTPUT_DIR_BASE, "Izlazne fakture")
OUTPUT_DIR_PURCHASE = os.path.join(OUTPUT_DIR_BASE, "Ulazne fakture")
ARCHIVE_DIR = os.path.join(OUTPUT_DIR_BASE, "Archived")

for folder in [OUTPUT_DIR_BASE, OUTPUT_DIR_SALES, OUTPUT_DIR_PURCHASE,
               os.path.join(OUTPUT_DIR_SALES, "xml"),
               os.path.join(OUTPUT_DIR_PURCHASE, "xml"),
               ARCHIVE_DIR]:
    os.makedirs(folder, exist_ok=True)

def log(msg):
    print(msg)
    with open("eFakture.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def sanitize_filename(name):
    return "".join(c for c in name if c.isalnum() or c in ("-", "_", "#")).rstrip()

def get_invoice_ids(base_url, status=None, date_from=None, date_to=None):
    url = f"{base_url}/ids"
    params = {}
    if status:
        params["status"] = status
    if date_from:
        params["dateFrom"] = date_from
    if date_to:
        params["dateTo"] = date_to

    log(f"\n📥 Preuzimam ID-jeve faktura sa {url} sa parametrima: {params}")
    response = requests.post(url, headers=HEADERS, params=params)

    if response.status_code != 200:
        log(f"❌ Greška pri preuzimanju ID-jeva: {response.status_code} - {response.text}")
        return []

    data = response.json()
    if "SalesInvoiceIds" in data:
        return data["SalesInvoiceIds"]
    if "PurchaseInvoiceIds" in data:
        return data["PurchaseInvoiceIds"]
    if isinstance(data, list):
        return data

    log(f"❌ Nepoznat format odgovora: {data}")
    return []

def download_file(url, filename):
    max_retries = 3
    retry_delay = 5

    for attempt in range(1, max_retries + 1):
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
            log(f"✅ Sačuvan fajl: {filename}")
            return True
        elif response.status_code == 202:
            log(f"[{attempt}/{max_retries}] Fajl nije spreman, čekam {retry_delay} sekundi...")
            time.sleep(retry_delay)
        else:
            log(f"❌ Greška: {response.status_code} - {response.text}")
            return False
    log(f"❌ Fajl nije spreman nakon {max_retries} pokušaja: {filename}")
    return False

def parse_invoice_number_from_xml(xml_path):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        for elem in root.iter():
            tag = elem.tag.split('}')[-1]
            if tag == "ID" and elem.text:
                return sanitize_filename(elem.text)
        for elem in root.iter():
            tag = elem.tag.split('}')[-1]
            if tag == "PaymentID" and elem.text:
                return sanitize_filename(elem.text)
    except Exception as e:
        log(f"❌ Greška pri parsiranju XML-a {xml_path}: {e}")
    return None

def get_invoice_status(invoice_type, invoice_id):
    if invoice_type == "purchase":
        url = f"{BASE_URL_PURCHASE}?invoiceId={invoice_id}"
    else:
        url = f"{BASE_URL_SALES}?invoiceId={invoice_id}"

    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        status = data.get("Status")
        if status:
            time.sleep(1)
            return sanitize_filename(status)
    else:
        log(f"❌ Greška pri dohvatanju statusa za ID {invoice_id}: {response.status_code}")
        time.sleep(1)
    return "Unknown"

def archive_existing_file(path, archive_dir):
    if not os.path.exists(path):
        return
    filename = os.path.basename(path)
    archive_path = os.path.join(archive_dir, filename)
    base, ext = os.path.splitext(filename)

    counter = 1
    while os.path.exists(archive_path):
        archive_path = os.path.join(archive_dir, f"{base}({counter}){ext}")
        counter += 1

    shutil.move(path, archive_path)
    log(f"📦 Arhiviran fajl: {path} -> {archive_path}")

def clean_old_archives():
    folders = [os.path.join(ARCHIVE_DIR, f) for f in os.listdir(ARCHIVE_DIR) if os.path.isdir(os.path.join(ARCHIVE_DIR, f))]
    folders.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    if len(folders) > MAX_ARCHIVE_FOLDERS:
        for old_folder in folders[MAX_ARCHIVE_FOLDERS:]:
            try:
                shutil.rmtree(old_folder)
                log(f"🗑️ Obrisan stari arhivski folder: {old_folder}")
            except Exception as e:
                log(f"❌ Greška pri brisanju foldera {old_folder}: {e}")

def download_invoices(base_url, invoice_ids, output_dir, invoice_type, archive_dir):
    xml_dir = os.path.join(output_dir, "xml")

    for invoice_id in invoice_ids:
        log(f"\n⬇️ Preuzimam status fakture ID: {invoice_id}...")
        status = get_invoice_status(invoice_type, invoice_id)
        log(f"Status fakture: {status}")

        log(f"⬇️ Preuzimam XML {invoice_type} fakture ID: {invoice_id}...")
        xml_temp_path = os.path.join(xml_dir, f"Approved_{invoice_type}_{invoice_id}.xml")
        xml_url = f"{base_url}/xml?invoiceId={invoice_id}"

        if not download_file(xml_url, xml_temp_path):
            log(f"❌ Preskačem fakturu ID {invoice_id} zbog greške pri preuzimanju XML.")
            continue

        invoice_number = parse_invoice_number_from_xml(xml_temp_path) or str(invoice_id)

        xml_final_name = f"{invoice_number}_{status}_{invoice_id}.xml"
        xml_final_path = os.path.join(xml_dir, xml_final_name)

        pdf_name = f"{invoice_number}_{status}_{invoice_id}.pdf"
        pdf_path = os.path.join(output_dir, pdf_name)
        pdf_url = f"{base_url}/pdf?invoiceId={invoice_id}"

        archive_existing_file(xml_final_path, archive_dir)
        archive_existing_file(pdf_path, archive_dir)

        download_file(pdf_url, pdf_path)
        os.rename(xml_temp_path, xml_final_path)
        log(f"✏️ Preimenovan XML: {xml_temp_path} -> {xml_final_path}")

def main():
    while True:
        today = datetime.now()
        date_to = today.replace(hour=23, minute=59, second=59, microsecond=0)
        date_from = date_to - timedelta(days=30)

        SALES_DATE_FROM = date_from.strftime("%Y-%m-%dT%H:%M:%S")
        SALES_DATE_TO = date_to.strftime("%Y-%m-%dT%H:%M:%S")
        PURCHASE_DATE_FROM = SALES_DATE_FROM
        PURCHASE_DATE_TO = SALES_DATE_TO

        SALES_STATUS = ""
        PURCHASE_STATUS = ""

        timestamp_folder = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        archive_sales = os.path.join(ARCHIVE_DIR, timestamp_folder, "sales")
        archive_purchase = os.path.join(ARCHIVE_DIR, timestamp_folder, "purchase")
        os.makedirs(archive_sales, exist_ok=True)
        os.makedirs(archive_purchase, exist_ok=True)

        sales_ids = get_invoice_ids(BASE_URL_SALES, status=SALES_STATUS, date_from=SALES_DATE_FROM, date_to=SALES_DATE_TO)
        log(f"\n🔎 Pronađeno sales faktura: {len(sales_ids)}")
        download_invoices(BASE_URL_SALES, sales_ids, OUTPUT_DIR_SALES, "sales", archive_sales)

        purchase_ids = get_invoice_ids(BASE_URL_PURCHASE, status=PURCHASE_STATUS, date_from=PURCHASE_DATE_FROM, date_to=PURCHASE_DATE_TO)
        log(f"\n🔎 Pronađeno purchase faktura: {len(purchase_ids)}")
        download_invoices(BASE_URL_PURCHASE, purchase_ids, OUTPUT_DIR_PURCHASE, "purchase", archive_purchase)

        clean_old_archives()

        log("\n⌛ Čekam 6 sat/i pre sledećeg pokušaja...\n")
        time.sleep(21600)

if __name__ == "__main__":
    main()
