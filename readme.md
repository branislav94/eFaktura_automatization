# Automatsko preuzimanje i arhiviranje e-faktura (API za Srbiju) 🧾

Ova Python skripta automatizuje proces preuzimanja izlaznih (prodajnih) i ulaznih (kupovnih) e-faktura putem API-ja Poreske uprave Srbije. Skript preuzima fakture u XML i PDF formatu, organizuje ih po tipu i statusu, i obavlja automatsko arhiviranje starih fajlova kako bi se održao red i smanjila potreba za ručnim upravljanjem.

-----

## 🚀 Glavne funkcionalnosti

  * **Preuzimanje faktura**: Automatski preuzima ID-eve faktura, a zatim i same fakture u **XML** i **PDF** formatu.
  * **Organizacija fajlova**: Fakture se čuvaju u jasno definisanim folderima (`Izlazne fakture` i `Ulazne fakture`), sa posebnim podfolderima za XML fajlove. Nazivi fajlova uključuju **broj fakture, status i ID** radi lakšeg snalaženja.
  * **Automatsko arhiviranje**: Pre preuzimanja novih verzija faktura, postojeći fajlovi se premeštaju u `Archived` folder, sa automatskim dodavanjem rednog broja ako fajl sa istim imenom već postoji u arhivi.
  * **Čišćenje arhive**: Skript automatski briše najstarije arhivske foldere kako bi se održao definisan broj (podrazumevano **5**) arhivskih verzija, sprečavajući prekomerno zauzeće diska.
  * **Prilagodljivi period preuzimanja**: Konfigurišite period za preuzimanje faktura (podrazumevano poslednjih **30 dana**).
  * **Upravljanje statusima**: Preuzima status svake fakture i uključuje ga u naziv fajla (npr. "Approved", "Rejected").
  * **Logovanje**: Sve aktivnosti, uključujući greške i uspešna preuzimanja, beleže se u `eFakture.log` fajl.
  * **Automatsko izvršavanje**: Skript je dizajniran da radi kontinuirano, sa pauzom od **6 sati** između ciklusa preuzimanja.
  * **Jednostavna konfiguracija**: Koristi **`.env` fajl** za čuvanje API ključa, URL-ova i drugih podesivih parametara.

-----

## 🛠️ Podešavanje

Pratite ove korake da biste pokrenuli skript:

1.  **Klonirajte repozitorijum:**

    ```bash
    git clone https://github.com/vase_korisnicko_ime/vas_repozitorijum.git
    cd vas_repozitorijum
    ```

    *Napomena: Zamenite `vase_korisnicko_ime/vas_repozitorijum.git` sa stvarnim URL-om vašeg repozitorijuma.*

2.  **Instalirajte zavisnosti:**

    ```bash
    pip install -r requirements.txt
    ```

    Uverite se da vaš `requirements.txt` fajl sadrži sledeće:

    ```
    python-dotenv
    requests
    ```

3.  **Kreirajte `.env` fajl** u istom direktorijumu gde se nalazi vaš glavni Python skript i dodajte sledeće varijable:

    ```
    API_KEY="Vaš_API_ključ_ovde"
    BASE_URL_SALES="https://api.efaktura.mfin.gov.rs/api/publicapi/SalesInvoices"
    BASE_URL_PURCHASE="https://api.efaktura.mfin.gov.rs/api/publicapi/PurchaseInvoices"
    OUTPUT_DIR_BASE="eFakture"
    MAX_ARCHIVE_FOLDERS=5
    ```

      * `API_KEY`: Vaš API ključ za pristup sistemu e-faktura.
      * `BASE_URL_SALES`: Osnovni URL za API prodajnih faktura.
      * `BASE_URL_PURCHASE`: Osnovni URL za API kupovnih faktura.
      * `OUTPUT_DIR_BASE`: Glavni direktorijum gde će se čuvati sve fakture. Podrazumevano je `eFakture`.
      * `MAX_ARCHIVE_FOLDERS`: Maksimalan broj arhivskih foldera koji će se čuvati. Stariji će biti obrisani. Podrazumevano je `5`.

4.  **Pokrenite skript:**

    ```bash
    python your_script_name.py
    ```

    *Napomena: Zamenite `your_script_name.py` sa imenom vašeg Python fajla (npr. `main.py` ili `efakture_downloader.py`).*

-----

## 📈 Primer strukture foldera

Nakon pokretanja skripta, struktura foldera će izgledati otprilike ovako:

```
eFakture/
├── Izlazne fakture/
│   ├── xml/
│   │   ├── BrojFakture_Approved_ID.xml
│   │   └── ...
│   ├── BrojFakture_Approved_ID.pdf
│   └── ...
├── Ulazne fakture/
│   ├── xml/
│   │   ├── BrojFakture_Approved_ID.xml
│   │   └── ...
│   ├── BrojFakture_Approved_ID.pdf
│   └── ...
└── Archived/
    ├── 2025-07-17_23-30-00/
    │   ├── sales/
    │   │   ├── OriginalFile_Archived(1).pdf
    │   │   └── ...
    │   └── purchase/
    │       ├── OriginalFile_Archived(1).xml
    │       │   └── ...
    ├── 2025-07-17_17-30-00/
    │   ├── sales/
    │   └── ...
    └── ... (do MAX_ARCHIVE_FOLDERS foldera)
```

-----

Ovaj skript je idealan za preduzeća koja žele da automatizuju proces preuzimanja i arhiviranja svojih elektronskih faktura, smanjujući ručni rad i osiguravajući organizovanu evidenciju.
