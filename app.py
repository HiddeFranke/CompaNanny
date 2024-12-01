import streamlit as st
from PyPDF2 import PdfReader
import pandas as pd
from datetime import datetime
import json
import os
import re
import ast
from text_preprocessing import *
from Model import *

# Controleer of de loginstatus in session state bestaat, anders stel deze in op False
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Controleer of de loginstatus van de Developer in session state bestaat, anders stel deze in op False
if "logged_in_dev" not in st.session_state:
    st.session_state.logged_in_dev = False

st.header("CompaNanny Analyser")

# Als gebruiker niet is ingelogd, toon inlogvelden
if not st.session_state.logged_in:
    # Vraag om inloggegevens
    username = st.text_input("Gebruikersnaam")
    password = st.text_input("Wachtwoord", type="password")
    
    if st.button("Inloggen"):
        if username == st.secrets["Compananny_username"] and password == st.secrets["Compananny_password"]:
            st.session_state.logged_in = True  # Zet de loginstatus op True
            st.success("Succesvol ingelogd!")
            st.rerun()
        else:
            st.warning("Ongeldige gebruikersnaam of wachtwoord.")
            
else:
    def main():
        # st.cache_data
        def load_data():
            # Laad het Excel-bestand en parseer de "Rapportdatum"-kolom als datum
            data = pd.read_excel("CompaNanny_Database.xlsx", parse_dates=["Rapportdatum"])

            # Zet de datum in "Rapportdatum" om naar het formaat YYYY-MM-DD
            data["Rapportdatum"] = data["Rapportdatum"].dt.strftime("%Y-%m-%d")
            return data
        
        # Functie om een back-up te maken van de database
        def maak_backup(data, backup_path="backups/CompaNanny_Database_backup.csv"):
            # Controleer of de back-up map bestaat, zo niet, maak deze aan
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            # Sla de data op als CSV
            backup_file = backup_path.replace(".csv", f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            data.to_csv(backup_file, index=False)
            st.success(f"Back-up gemaakt: {backup_file}")


        # Functie om gegevens op te slaan in het JSON-bestand
        def save_to_json(data, path="bedrijven_data.json"):
            with open(path, "w") as json_file:
                json.dump(data, json_file, indent=4)

        # Functie om gegevens uit JSON te laden
        def load_from_json(path="bedrijven_data.json"):
            if os.path.exists(path):
                with open(path, "r") as json_file:
                    return json.load(json_file)
            else:
                return {}

        # Functie om een vestiging toe te voegen aan een bestaand bedrijf
        def voeg_vestiging_toe(bedrijf, vestiging, path="bedrijven_data.json"):
            # Laad de huidige data
            data = load_from_json(path)
            
            # Voeg het bedrijf toe als het niet bestaat
            if bedrijf not in data:
                data[bedrijf] = []
            
            # Voeg de vestiging toe als deze nog niet in de lijst staat
            if vestiging not in data[bedrijf]:
                data[bedrijf].append(vestiging)
                st.write(f"Vestiging '{vestiging}' toegevoegd aan '{bedrijf}'.")
            else:
                st.write(f"Vestiging '{vestiging}' bestaat al voor '{bedrijf}'.")
            
            # Sla de bijgewerkte data op
            save_to_json(data, path)
        
        def vind_bedrijf_vestiging(front_page):
            # Controleer of een bedrijf voorkomt in de tekst
            gevonden_bedrijf = None
            for bedrijf in bedrijven_en_vestigingen.keys():
                if bedrijf in front_page:
                    gevonden_bedrijf = bedrijf
                    break

            # Toon resultaat of geef waarschuwing
            if gevonden_bedrijf:
                st.write(f"Gevonden bedrijf: <span style='color: green; font-weight: bold;'>{gevonden_bedrijf}</span>", unsafe_allow_html=True)
                bedrijf = gevonden_bedrijf
            else:
                st.warning("Geen bedrijf gevonden in de tekst. Selecteer handmatig een bedrijf.")
                bedrijf = st.selectbox("Selecteer een bedrijf", list(bedrijven_en_vestigingen.keys()))

            # Controleer of een vestiging voorkomt in de tekst
            gevonden_vestiging = None
            for vestiging in bedrijven_en_vestigingen[bedrijf]:
                if vestiging in front_page:
                    gevonden_vestiging = vestiging
                    break

            # Toon resultaat of geef waarschuwing
            if gevonden_vestiging:
                st.write(f"Gevonden vestiging: <span style='color: green; font-weight: bold;'>{gevonden_vestiging}</span>", unsafe_allow_html=True)
                vestiging = gevonden_vestiging
            else:
                st.warning(f"Geen vestiging gevonden voor {bedrijf} in de tekst. Selecteer handmatig een vestiging.")
                vestiging = st.selectbox("Selecteer een vestiging", bedrijven_en_vestigingen[bedrijf])

            return bedrijf, vestiging

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
                st.text_area("Hier is een hint: \n", pdf_text, height=100)
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


        # Data inladen bij opstart
        # Laad de bestaande gegevens als ze al bestaan
        bedrijven_en_vestigingen = load_from_json("bedrijven_data.json")

        data = load_data()
        train_data = pd.read_excel("train_data.xlsx")
        response = None






    #=======================================================================================
        # Creëer meerdere tabbladen
        tab1, tab2, tab3 = st.tabs(["Inspectierapport Analyser", "Overzicht Database", "Developer"])

        # Tabblad 1: Inspectierapport Analyser
        with tab1:
            st.header("Inspectierapport Analyser")
            
            # Upload PDF voor analyse
            uploaded_file = st.file_uploader("Upload een PDF van het inspectierapport", type="pdf")
            
            if uploaded_file:
                # st.session_state['bedrijf'], st.session_state['vestiging'], st.session_state['inspection_date'] = None, None, None

                # Lees de voorpagina van de PDF
                reader = PdfReader(uploaded_file)
                front_page = "".join(reader.pages[0].extract_text())
                pdf_pages = [2,3]
                pdf_text = "\n".join([reader.pages[i].extract_text() for i in pdf_pages])
                # Verwijder lege regels
                # pdf_text = "\n".join([line for line in pdf_text.splitlines() if line.strip() != ""])

                # Zoek naar bestaand bedrijf en vestiging op voorpagina
                bedrijf, vestiging = vind_bedrijf_vestiging(front_page)

                # Zoek naar "Datum inspectie" op de voorpagina in de tekst en sla de datum op
                inspection_date = find_or_input_inspection_date(front_page)
                # st.write(f"Inspectierapport datum: <span style='color: green; font-weight: bold;'>{inspection_date}</span>", unsafe_allow_html=True)
                

                

                if bedrijf and vestiging and inspection_date:
                    # Display extracted text
                    st.text_area("Geëxtraheerde tekst", pdf_text, height=200)
                    # st.write("Totaal aantal woorden pdf: ", len(pdf_text.split()))
                    st.write("Verwachte prijs voor analyse: ", calculate_text_cost_with_base(pdf_text, base_tokens=200, cost_per_1k_input=0.005, cost_per_1k_output=0.015)["total_cost"], "$")
                    
                    # Placeholder voor modelanalyse
                    if st.button("Analyseer"):
                        # Voeg een nieuwe rij toe aan de DataFrame met de geselecteerde informatie
                        new_row = {
                            "Bedrijfnaam": bedrijf,
                            "Vestiging": vestiging,
                            "Rapportdatum": inspection_date.strftime("%Y-%m-%d"),
                        }

                        # Controleer of de nieuwe rij al bestaat in de DataFrame
                        is_duplicate = data[
                            (data["Bedrijfnaam"] == new_row["Bedrijfnaam"]) &
                            (data["Vestiging"] == new_row["Vestiging"]) &
                            (data["Rapportdatum"] == new_row["Rapportdatum"])
                        ].shape[0] > 0


                        #WEGHALEN
                        # is_duplicate = False

                        if is_duplicate:
                            st.warning("Deze combinatie van Bedrijf, Vestiging en Rapportdatum bestaat al in de database.")
                        else:
                            # st.markdown("---")
                            response = chat_with_gpt(pdf_text, inspection_date)
                            # Probeer de response om te zetten naar een dictionary en voeg toe aan new_row
                            new_row = update_row_with_response(new_row, response)
                            st.write("Model met alle pdf_text: ", new_row)

    #====================================================================================================
                            # Hier kan het model worden aangeroepen en de analyse in de database worden opgeslagen

                            new_row_df = pd.DataFrame([new_row])
                            data = pd.concat([data, new_row_df], ignore_index=True)


                            # if st.button("Toevoegen aan database"):
                            # # Sla de bijgewerkte DataFrame op in het Excel-bestand
                            data.to_excel("CompaNanny_Database.xlsx", index=False)

                            # Controleer of er een back-up nodig is
                            if len(data) % 20 == 0:
                                maak_backup(data)
            

#====================================================================================================


        # Tabblad 2: Overzicht Database
        with tab2:
            st.markdown("""
            #### Wat bevat de dataset?
            - **Locatie-informatie**:
                - De naam van de kinderopvangorganisatie.
                - De specifieke vestiging waar de inspectie is uitgevoerd.
            - **Inspectiedatum**:
                - De datum waarop de inspectie heeft plaatsgevonden.
            - **Overtredingen per categorie**:
                - Voor elk inspectierapport wordt aangegeven of er overtredingen zijn binnen de categorieën in de kolomnamen:
            
            #### Hoe werkt de dataset?
            De dataset geeft per inspectierapport een binaire waarde aan:
            - **1**: Er is een overtreding vastgesteld binnen deze categorie.
            - **0**: Er is geen overtreding vastgesteld binnen deze categorie.
            """)
            
            # Horizontale lijn voor scheiding
            st.markdown("---")
            st.header("Overzicht Database")
            st.write(data.head(100))

            # Voeg datum en tijd toe aan de bestandsnaam
            timestamp = datetime.now().strftime("%Y-%m-%d")
            file_name = f"inspectierapporten_analyse_{timestamp}.csv"

            # Voeg downloadknop toe om data als CSV te downloaden
            csv = data.to_csv(index=False)
            st.download_button(
                label="Download data als CSV",
                data=csv,
                file_name=file_name,
                mime='text/csv',
            )

            # Tabblad 3: Bedrijf Toevoegen (met eenvoudige wachtwoordbeveiliging)
        with tab3:
            # Als gebruiker niet is ingelogd, toon inlogvelden
            if not st.session_state.logged_in_dev:
                # Vraag om inloggegevens
                username = st.text_input("Gebruikersnaam", key="inloggen_dev")
                password = st.text_input("Wachtwoord", type="password", key="inloggen_dev_password")
                
                if st.button("Inloggen"):
                    if username == "h" and password == "f":
                        st.session_state.logged_in_dev = True  # Zet de loginstatus op True
                        st.success("Succesvol ingelogd!")
                        st.rerun()
                    else:
                        st.warning("Ongeldige gebruikersnaam of wachtwoord.")
            else:
                st.subheader("Bedrijf/Vestiging Toevoegen aan de database")
                # Input voor nieuw bedrijf en vestiging (alleen zichtbaar als gebruiker is ingelogd)
                new_bedrijf = st.text_input("Bedrijfsnaam")
                new_vestiging = st.text_input("Vestiging")
            
                # Toevoeg Button
                if st.button("Toevoegen"):
                    voeg_vestiging_toe(new_bedrijf, new_vestiging, path="bedrijven_data.json")
                    st.write(f"Bedrijf '{new_bedrijf}' met vestiging '{new_vestiging}' toegevoegd aan de database.")

                # Horizontale lijn voor scheiding
                st.markdown("---")
                
                # Sectie: Basisdata vervangen via Excel/CSV
                st.subheader("Database Vervangen")
                uploaded_file = st.file_uploader("Upload een Excel- of CSV-bestand", type=["xlsx", "csv"])
                
                if uploaded_file:
                    try:
                        # Laad de data afhankelijk van bestandstype
                        if uploaded_file.name.endswith(".xlsx"):
                            new_data = pd.read_excel(uploaded_file, engine="openpyxl")
                        elif uploaded_file.name.endswith(".csv"):
                            new_data = pd.read_csv(uploaded_file)
                        
                        # Toon de geüploade data in een tabel
                        st.write("Geüploade data:")
                        st.dataframe(new_data)
                        
                        # Vervang basisdata met een bevestigingsknop
                        if st.button("Vervang Basisdata"):
                            new_data.to_excel("CompaNanny_Database.xlsx", index=False, engine="openpyxl")
                            st.success("De basisdata is succesvol vervangen.")
                    except Exception as e:
                        st.error(f"Fout bij het verwerken van het bestand: {e}")


    if __name__ == "__main__":
        main()
