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





        
        # def find_or_input_inspection_date(pdf_text):                     
        #     # Zoek naar "Datum inspectie" en haal de datum op
        #     match = re.search(r"Datum inspectie[:\s]+(\d{2}-\d{2}-\d{4})", pdf_text)
        #     if match:
        #         date_str = match.group(1)
        #         inspection_date = datetime.strptime(date_str, "%d-%m-%Y").date()
        #         # st.write(f"Datum inspectierapport gevonden (YYYY-MM-DD): {inspection_date}")
        #         st.write(f"Datum inspectierapport gevonden (YYYY-MM-DD): <span style='color: green; font-weight: bold;'>{inspection_date}</span>", unsafe_allow_html=True)
        #     else:
        #         st.warning("Geen datum gevonden. Voer handmatig een inspectie datum in.")
        #         st.text_area("Hier is een hint: \n", pdf_text, height=100)
        #         # Toon de date input voor handmatige invoer
        #         manual_date = st.date_input("Selecteer een datum", value=None)
        #         if manual_date:
        #             inspection_date = datetime.combine(manual_date, datetime.min.time()).date()
        #             # st.success(f"Handmatig ingevoerde datum (YYYY-MM-DD): {inspection_date}")
        #             st.write(f"Handmatig ingevoerde datum (YYYY-MM-DD): <span style='color: green; font-weight: bold;'>{inspection_date}</span>", unsafe_allow_html=True)
        #         else:
        #             inspection_date = None
        #     return inspection_date

        def find_or_input_inspection_date(pdf_text):
            # Initialiseer een inspectiedatum in session_state als deze nog niet bestaat
            if 'inspection_date' not in st.session_state:
                st.session_state['inspection_date'] = None

            # Zoek naar "Datum inspectie" en haal de datum op
            match = re.search(r"Datum inspectie\s*:\s*(\d{2})\s*-\s*(\d{2})\s*-\s*(\d{4})", pdf_text)
            if match:
                day, month, year = match.groups()
                date_str = f"{day}-{month}-{year}"
                inspection_date = datetime.strptime(date_str, "%d-%m-%Y").date()
                st.session_state['inspection_date'] = inspection_date
            elif st.session_state['inspection_date'] is None:
                # Toon waarschuwing en hint als er nog geen datum is ingevuld
                st.warning("Geen datum gevonden. Voer handmatig een inspectiedatum in.")
                st.text_area("Hier is een hint: \n", pdf_text, height=100)

                # Date input om handmatig een datum in te voeren
                manual_date = st.date_input("Selecteer een datum", key="manual_date", value=None)
                if manual_date:
                    inspection_date = datetime.combine(manual_date, datetime.min.time()).date()
                    st.session_state['inspection_date'] = inspection_date
                    st.rerun()  # Herlaad de app zodra de datum is ingevuld
            
            st.write(f"Inspectierapport datum (YYYY-MM-DD): <span style='color: green; font-weight: bold;'>{st.session_state['inspection_date']}</span>", unsafe_allow_html=True)
            return st.session_state['inspection_date']




        # Data inladen bij opstart
        # Laad de bestaande gegevens als ze al bestaan
        bedrijven_en_vestigingen = load_from_json("bedrijven_data.json")

        data = load_data()
        train_data = pd.read_excel("train_data.xlsx")
        response = None






    #=======================================================================================
        # Creëer meerdere tabbladen
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Inspectierapport Analyser", "Overzicht Database", "Developer", "Model", "Training Data Annotator"])

        # Tabblad 1: Inspectierapport Analyser
        with tab1:
            st.header("Inspectierapport Analyser")
            


            # Upload PDF voor analyse
            uploaded_file = st.file_uploader("Upload een PDF van het inspectierapport", type="pdf")
            
            if uploaded_file:
                st.session_state['bedrijf'], st.session_state['vestiging'], st.session_state['inspection_date'] = None, None, None

                # Lees de voorpagina van de PDF
                reader = PdfReader(uploaded_file)
                front_page = "".join(reader.pages[0].extract_text())
                pdf_pages = [2,3,4,5,-1]
                pdf_text = "\n".join([reader.pages[i].extract_text() for i in pdf_pages])
                # Verwijder lege regels
                pdf_text = "\n".join([line for line in pdf_text.splitlines() if line.strip() != ""])

                # Zoek naar bestaand bedrijf en vestiging op voorpagina
                bedrijf, vestiging = vind_bedrijf_vestiging(front_page)

                # Zoek naar "Datum inspectie" op de voorpagina in de tekst en sla de datum op
                inspection_date = find_or_input_inspection_date(front_page)
                # st.write(f"Inspectierapport datum: <span style='color: green; font-weight: bold;'>{inspection_date}</span>", unsafe_allow_html=True)
                

                

                if bedrijf and vestiging and inspection_date:
                    # Display extracted text
                    st.text_area("Extracted Text", pdf_text, height=200)
                    # st.write("Totaal aantal woorden pdf: ", len(pdf_text.split()))
                    st.write ("Verwachte prijs voor analyse: ", round(len(pdf_text.split())*0.75*0.005/1000,4), "$")
                    
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

                        if is_duplicate:
                            st.warning("Deze combinatie van Bedrijf, Vestiging en Rapportdatum bestaat al in de database.")
                        else:
                            response = chat_with_gpt(pdf_text, inspection_date)
                            st.write(response)

                            # Probeer de response om te zetten naar een dictionary en voeg toe aan new_row
                            try:
                                new_dict = ast.literal_eval(response)
                                if isinstance(new_dict, dict):
                                    new_row.update(new_dict)
                                else:
                                    st.error("De response is geen geldige dictionary.")
                            except (ValueError, SyntaxError) as e:
                                st.error(f"Fout bij het omzetten van de response naar een dictionary: {e}")
                                new_dict = None

                            if new_dict:
                                st.write("Geüpdatete dictionary:", new_row)
                            else:
                                st.write("Kon de dictionary niet updaten met de response.")


    #====================================================================================================
                            # Hier kan het model worden aangeroepen en de analyse in de database worden opgeslagen

                            new_row_df = pd.DataFrame([new_row])
                            data = pd.concat([data, new_row_df], ignore_index=True)

                            # st.write(f"Analyse uitgevoerd voor {bedrijf}, {vestiging}.")
                            st.write(data.tail(1))

                            # if st.button("Toevoegen aan database"):
                            # # Sla de bijgewerkte DataFrame op in het Excel-bestand
                            data.to_excel("CompaNanny_Database.xlsx", index=False)
            st.session_state['inspection_date'] = None
            

#====================================================================================================


        # Tabblad 2: Overzicht Database
        with tab2:
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
            # Input voor nieuw bedrijf en vestiging (alleen zichtbaar als gebruiker is ingelogd)
            new_bedrijf = st.text_input("Bedrijfsnaam")
            new_vestiging = st.text_input("Vestiging")
            
            # Toevoeg Button
            if st.button("Toevoegen"):
                voeg_vestiging_toe(new_bedrijf, new_vestiging, path="bedrijven_data.json")
                st.write(f"Bedrijf '{new_bedrijf}' met vestiging '{new_vestiging}' toegevoegd aan de database.")


        with tab4:
            standard_prompt = "Analyseer pdf kinderopvanginspectierapport; geef per label overtreding (1/0) voor: 'Kwaliteit en naleving', 'Veiligheid en gezondheid', 'Personeel en groepen', 'Pedagogisch klimaat', 'Accommodatie', 'Ouderrecht'. Geef alleen dictionary zonder pythoncodeblok"
            user_input = st.text_area("Ask ChatGPT")   
            if st.button("Vraag"):     
                response = chat_with_gpt(standard_prompt + user_input)
                st.write("Response from ChatGPT:", response)
            
            # Bestaande dictionary met basisinformatie
            existing_dict = {
                "Bedrijfnaam": "Compananny",
                "Vestiging": "Amsterdam",
                "Rapportdatum": "14-10-2024",
            }
            
            # Probeer de response om te zetten naar een dictionary en voeg toe aan existing_dict
            try:
                new_dict = ast.literal_eval(response)
                if isinstance(new_dict, dict):
                    existing_dict.update(new_dict)
                else:
                    st.error("De response is geen geldige dictionary.")
            except (ValueError, SyntaxError) as e:
                st.error(f"Fout bij het omzetten van de response naar een dictionary: {e}")
                new_dict = None

            if new_dict:
                st.write("Geüpdatete dictionary:", existing_dict)
            else:
                st.write("Kon de dictionary niet updaten met de response.")


        # In tab5 maak je de annotatie tool voor de trainingsdata
        with tab5:
            st.write(train_data.head(100))

            # Labels die per tekst worden beoordeeld
            labels = [
                "Algemene voorwaarden kwaliteit en naleving",
                "Veiligheid en gezondheid",
                "Personeel en groepen",
                "Pedagogisch klimaat",
                "Accommodatie",
                "Ouderrecht"
            ]
            
            st.header("Training Data Annotator")
            
            # Upload PDF voor analyse
            uploaded_file = st.file_uploader("Upload een PDF van het inspectierapport", type="pdf", key="training_data_uploader")

            if uploaded_file:
                # Extract text from PDF
                reader = PdfReader(uploaded_file)
                
                # pdf_text = "\n".join([page.extract_text() for page in reader.pages])
                # Gebruik alleen pagina's 3 en 4 (index 2 en 3)
                
                pdf_text = "\n".join([reader.pages[i].extract_text() for i in [2, 3, -1]])


                # Verwijder lege regels
                pdf_text = "\n".join([line for line in pdf_text.splitlines() if line.strip() != ""])

                # Verwerk PDF tekst met test_algoritme om een lijst met teksten te krijgen
                text_list = text_algoritme(pdf_text)
                st.write("De tekst is opgesplitst voor annotatie.")

                # Annotatie per tekst
                for i, text in enumerate(text_list):
                    # Controleer of de tekst al bestaat in train_data
                    if is_unique_text(text, train_data, drempel=0.8):
                        st.subheader(f"Tekst {i+1}")
                        st.write(text)

                        # Checkboxen voor labels
                        label_dict = {}
                        for label in labels:
                            label_dict[label] = st.checkbox(label, key=f"{label}_{i}")

                        # Voeg de annotatie toe aan de lijst van geannoteerde data
                        if st.button("Opslaan annotatie", key=f"save_{i}"):
                            annotation = {
                                "text": text,
                                **{label: int(label_dict[label]) for label in labels}  # Converteer checkboxes naar 1/0
                            }
                            save_annotation_to_excel(annotation, path="train_data.xlsx")
                            st.success("Annotatie opgeslagen!")
                            st.json(annotation)
                            # st.experimental_rerun()  # Vernieuw de app om de volgende tekst te tonen




    if __name__ == "__main__":
        main()
