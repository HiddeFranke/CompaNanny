# Gebruikt voor modules of bestanden waarin algemene hulpfuncties en tools worden opgeslagen 
# die in verschillende delen van een project kunnen worden hergebruikt. 
# Het idee is om code die niet specifiek hoort bij één bepaald onderdeel (zoals je model of je Streamlit-app),
#  maar die wel op meerdere plaatsen nuttig kan zijn, in een aparte module te plaatsen.

import os
import json
import pandas as pd
from datetime import datetime
import re
import ast
import streamlit as st
import subprocess

def load_file(file_path, parse_dates=None):
    """
    Universele functie om een bestand te laden, afhankelijk van de extensie.
    Ondersteunde formaten:
    - .txt: Laadt de inhoud als een string.
    - .json: Laadt de inhoud als een JSON-object.
    - .csv: Laadt de inhoud als een pandas DataFrame.
    - .xlsx: Laadt de inhoud als een pandas DataFrame (Excel-bestand).

    Parameters:
    - file_path (str): Pad naar het bestand.
    - parse_dates (list, optional): Kolomnamen om te parseren als datums (alleen voor CSV/Excel).

    Returns:
    - De inhoud van het bestand in het juiste formaat (str, dict, DataFrame).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Bestand niet gevonden: {file_path}")

    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext == ".txt":
        with open(file_path, "r") as file:
            return file.read()  # Retourneer de inhoud als string
    elif file_ext == ".json":
        with open(file_path, "r") as file:
            return json.load(file)  # Retourneer de inhoud als JSON-object
    elif file_ext == ".csv":
        return pd.read_csv(file_path, parse_dates=parse_dates)  # Retourneer als DataFrame
    elif file_ext == ".xlsx":
        return pd.read_excel(file_path, parse_dates=parse_dates)  # Retourneer als DataFrame
    else:
        raise ValueError(f"Onbekend bestandstype: {file_ext}. Ondersteunde formaten: .txt, .json, .csv, .xlsx")

def save_file(data, file_path):
    """
    Universele functie om data op te slaan in een bestand, afhankelijk van de extensie.
    Ondersteunde formaten:
    - .txt: Slaat de inhoud op als tekst.
    - .json: Slaat de inhoud op als JSON-object.
    - .csv: Slaat de inhoud op als een CSV-bestand.
    - .xlsx: Slaat de inhoud op als een Excel-bestand.

    Parameters:
    - data: De data die moet worden opgeslagen (str, dict, DataFrame).
    - file_path (str): Pad waar het bestand moet worden opgeslagen.
    """
    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext == ".txt":
        if not isinstance(data, str):
            raise ValueError("Data voor een .txt bestand moet een string zijn.")
        with open(file_path, "w") as file:
            file.write(data)
    elif file_ext == ".json":
        if not isinstance(data, dict):
            raise ValueError("Data voor een .json bestand moet een dictionary zijn.")
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
    elif file_ext == ".csv":
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Data voor een .csv bestand moet een pandas DataFrame zijn.")
        data.to_csv(file_path, index=False)
    elif file_ext == ".xlsx":
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Data voor een .xlsx bestand moet een pandas DataFrame zijn.")
        data.to_excel(file_path, index=False)
    else:
        raise ValueError(f"Onbekend bestandstype: {file_ext}. Ondersteunde formaten: .txt, .json, .csv, .xlsx")


# Functie om een backup te maken van de data
def make_backup(data, backup_dir="backups", filename_prefix="CompaNanny_Database_backup"):
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{backup_dir}/{filename_prefix}_{timestamp}.csv"
    data.to_csv(backup_file, index=False)
    return backup_file


# # Functie om een vestiging toe te voegen aan een bestaand bedrijf
# def voeg_vestiging_toe(bedrijf, vestiging, path="bedrijven_data.json"):
#     # Laad de huidige data
#     data = load_file(path)
    
#     # Voeg het bedrijf toe als het niet bestaat
#     if bedrijf not in data:
#         data[bedrijf] = []
    
#     # Voeg de vestiging toe als deze nog niet in de lijst staat
#     if vestiging not in data[bedrijf]:
#         data[bedrijf].append(vestiging)
#         st.write(f"Vestiging '{vestiging}' toegevoegd aan '{bedrijf}'.")
#     else:
#         st.write(f"Vestiging '{vestiging}' bestaat al voor '{bedrijf}'.")
    
#     # Sla de bijgewerkte data op
#     save_file(data, path)

# Functie om een vestiging toe te voegen aan een bestaand bedrijf
def voeg_vestiging_toe(bedrijf, vestiging, kolomwaarde, path="bedrijven_data.json"):
    """
    Voeg een vestiging toe aan een bedrijf.
    
    Parameters:
    - bedrijf (str): Naam van het bedrijf.
    - vestiging (str): Naam van de vestiging.
    - kolomwaarde (dict): Extra informatie van de vestiging, bijv. vanuit 'actuele_naam_oko'.
    - path (str): Pad naar het JSON-bestand.
    """
    # Laad de huidige data
    data = load_file(path)
    
    # Voeg het bedrijf toe als het niet bestaat
    if bedrijf not in data:
        data[bedrijf] = []
    
    # Controleer of de vestiging al bestaat
    if not any(v["actuele_naam_oko"] == vestiging for v in data[bedrijf]):
        # Voeg vestiging toe met aanvullende informatie
        nieuwe_vestiging = {
            "actuele_naam_oko": vestiging,
            **kolomwaarde  # Voeg alle extra kolomwaarden toe als dict
        }
        data[bedrijf].append(nieuwe_vestiging)
        print(f"Vestiging '{vestiging}' toegevoegd aan '{bedrijf}'.")
    else:
        print(f"Vestiging '{vestiging}' bestaat al voor '{bedrijf}'.")
    
    # Sla de bijgewerkte data op
    save_file(data, path)

# def vind_bedrijf_vestiging(front_page):
#     bedrijven_en_vestigingen = load_file("bedrijven_data.json")
#     # Controleer of een bedrijf voorkomt in de tekst
#     gevonden_bedrijf = None
#     for bedrijf in bedrijven_en_vestigingen.keys():
#         if bedrijf in front_page:
#             gevonden_bedrijf = bedrijf
#             break

#     # Toon resultaat of geef waarschuwing
#     if gevonden_bedrijf:
#         st.write(f"Gevonden bedrijf: <span style='color: green; font-weight: bold;'>{gevonden_bedrijf}</span>", unsafe_allow_html=True)
#         bedrijf = gevonden_bedrijf
#     else:
#         st.warning("Geen bedrijf gevonden in de tekst. Selecteer handmatig een bedrijf.")
#         bedrijf = st.selectbox("Selecteer een bedrijf", list(bedrijven_en_vestigingen.keys()))

#     # Controleer of een vestiging voorkomt in de tekst
#     gevonden_vestiging = None
#     for vestiging in bedrijven_en_vestigingen[bedrijf]:
#         if vestiging in front_page:
#             gevonden_vestiging = vestiging
#             break

#     # Toon resultaat of geef waarschuwing
#     if gevonden_vestiging:
#         st.write(f"Gevonden vestiging: <span style='color: green; font-weight: bold;'>{gevonden_vestiging}</span>", unsafe_allow_html=True)
#         vestiging = gevonden_vestiging
#     else:
#         st.warning(f"Geen vestiging gevonden voor {bedrijf} in de tekst. Selecteer handmatig een vestiging.")
#         vestiging = st.selectbox("Selecteer een vestiging", bedrijven_en_vestigingen[bedrijf])

#     return bedrijf, vestiging

def vind_bedrijf_vestiging(front_page):
    """
    Zoekt naar een bedrijf en vestiging op basis van tekst in de front page,
    en retourneert ook 'type_oko' als deze beschikbaar is of biedt een keuze aan als deze ontbreekt.
    
    Parameters:
    - front_page (str): De tekst waarin gezocht moet worden naar bedrijven en vestigingen.
    
    Returns:
    - tuple: Gevonden bedrijf, vestiging, en type_oko.
    """
    bedrijven_en_vestigingen = load_file("bedrijven_data.json")
    
    # Controleer of een bedrijf voorkomt in de tekst
    gevonden_bedrijf = None
    for bedrijf in bedrijven_en_vestigingen.keys():
        if bedrijf.lower() in front_page.lower():  # Hoofdletterongevoelig zoeken
            gevonden_bedrijf = bedrijf
            break

    # Toon resultaat of geef waarschuwing
    if gevonden_bedrijf:
        st.write(
            f"Gevonden bedrijf: <span style='color: green; font-weight: bold;'>{gevonden_bedrijf}</span>",
            unsafe_allow_html=True,
        )
        bedrijf = gevonden_bedrijf
    else:
        st.warning("Geen bedrijf gevonden in de tekst. Selecteer handmatig een bedrijf.")
        bedrijf = st.selectbox("Selecteer een bedrijf", list(bedrijven_en_vestigingen.keys()))

    # Controleer of een vestiging voorkomt in de tekst op basis van 'actuele_naam_oko'
    gevonden_vestiging = None
    for vestiging in bedrijven_en_vestigingen[bedrijf]:
        if vestiging.get("actuele_naam_oko", "").lower() in front_page.lower():  # Hoofdletterongevoelig zoeken
            gevonden_vestiging = vestiging
            break

    # Toon resultaat of geef waarschuwing
    if gevonden_vestiging:
        vestiging = gevonden_vestiging["actuele_naam_oko"]
        st.write(
            f"Gevonden vestiging: <span style='color: green; font-weight: bold;'>{vestiging}</span>",
            unsafe_allow_html=True,
        )
        
        # Probeer 'type_oko' op te halen
        type_oko = gevonden_vestiging.get("type_oko")
        if not type_oko:
            st.warning("Type Oko ontbreekt in de data. Kies een type uit het menu.")
            type_oko = st.selectbox("Selecteer type_oko", ["VGO", "BSO", "KDV", "GOB"])
    else:
        st.warning(f"Geen vestiging gevonden voor {bedrijf} in de tekst. Selecteer handmatig een vestiging.")
        vestiging = st.selectbox(
            "Selecteer een vestiging",
            [v["actuele_naam_oko"] for v in bedrijven_en_vestigingen[bedrijf]],
        )
        
        # Toon type_oko menu omdat vestiging niet is gevonden
        st.warning(f"Geen type opvangvoorziening gevonden. Kies handmatig uit de volgende opvangvoorzieningen.")
        type_oko = st.selectbox("Selecteer type opvangvoorziening", ["VGO", "BSO", "KDV", "GOB"])

    return bedrijf, vestiging, type_oko


def find_or_input_inspection_date(pdf_text):                     
    # Zoek naar "Datum inspectie" en haal de datum op
    match = re.search(r"Datum inspectie[:\s]+(\d{2}-\d{2}-\d{4})", pdf_text)
    if match:
        date_str = match.group(1)
        inspection_date = datetime.strptime(date_str, "%d-%m-%Y").date()
        # st.write(f"Datum inspectierapport gevonden (YYYY-MM-DD): {inspection_date}")
        st.write(f"Datum inspectierapport gevonden (YYYY-MM-DD): <span style='color: green; font-weight: bold;'>{inspection_date}</span>", unsafe_allow_html=True)
    else:
        st.warning("Geen datum gevonden. Voer handmatig een inspectie datum in.")
        cleaned_text = "\n".join([line for line in pdf_text.splitlines() if line.strip()])         # Verwijder witregels uit pdf_text
        st.text_area("Hier is een hint: \n", cleaned_text, height=100) # Gebruik de opgeschoonde tekst in je text_area

        # Toon de date input voor handmatige invoer
        manual_date = st.date_input("Selecteer een datum", value=None)
        if manual_date:
            inspection_date = datetime.combine(manual_date, datetime.min.time()).date()
            # st.success(f"Handmatig ingevoerde datum (YYYY-MM-DD): {inspection_date}")
            st.write(f"Handmatig ingevoerde datum (YYYY-MM-DD): <span style='color: green; font-weight: bold;'>{inspection_date}</span>", unsafe_allow_html=True)
        else:
            inspection_date = None
    return inspection_date


def update_row_with_response(new_row, response):
    try:
        new_dict = ast.literal_eval(response)
        if isinstance(new_dict, dict):
            new_row.update(new_dict)
        else:
            st.error("De response is geen geldige dictionary.")
    except (ValueError, SyntaxError) as e:
        st.error(f"Fout bij het omzetten van de response naar een dictionary: {e}")
        new_dict = None
    return new_row

def calculate_text_cost_with_base(pdf_text, base_tokens=150, cost_per_1k_input=0.005, cost_per_1k_output=0.015):
    """
    Calculate the total cost of processing a given text with a fixed base token count for standard info.

    Parameters:
    - pdf_text (str): The input text from the PDF.
    - base_tokens (int): Fixed token count for the standard_info part (default is 200 tokens).
    - cost_per_1k_input (float): Cost per 1,000 input tokens (default is $0.005).
    - cost_per_1k_output (float): Cost per 1,000 output tokens (default is $0.015).

    Returns:
    - dict: A dictionary containing the word count, total token count, and calculated costs.
    """
    # Calculate the word count and corresponding tokens for pdf_text
    word_count = len(pdf_text.split())
    input_tokens_dynamic = int((word_count / 750) * 1000)  # Approx. 750 words = 1,000 tokens

    # Total input tokens = base tokens + dynamic tokens
    total_input_tokens = base_tokens + input_tokens_dynamic

    # Fixed output tokens (based on the standard dictionary structure)
    output_tokens = 50  # Example size of a standard dictionary output

    # Calculate input and output costs
    input_cost = round((total_input_tokens / 1000) * cost_per_1k_input, 4)
    output_cost = round((output_tokens / 1000) * cost_per_1k_output, 4)

    # Total cost
    total_cost = round(input_cost + output_cost, 4)

    return {
        "word_count": word_count,
        "input_tokens": total_input_tokens,
        "output_tokens": output_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost
    }

#==========
def push_to_github(file_path, commit_message="Update dataset"):
    """
    Push het bestand naar GitHub.
    Parameters:
    - file_path: Het pad naar het bestand dat je wilt pushen.
    - commit_message: De commitboodschap voor de wijziging.
    """
    try:
        # Voeg het bestand toe aan de staging area
        subprocess.run(["git", "add", file_path], check=True)
        # Commit de wijziging
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        # Push naar de remote repository
        subprocess.run(["git", "push"], check=True)
        st.success(f"Bestand succesvol naar GitHub gepusht: {file_path}")
    except subprocess.CalledProcessError as e:
        st.error(f"Fout bij het pushen naar GitHub: {e}")
