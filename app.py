import streamlit as st
from PyPDF2 import PdfReader
import pandas as pd
from datetime import datetime
from Model import *
from utils import *

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
        # Data laden
        configure_git_user()
        data = load_file("CompaNanny_Database.xlsx", parse_dates=["Rapportdatum"])
        response = None

    #=======================================================================================
        # Creëer meerdere tabbladen
        tab_model, tab_data, tab_dev, tab_handleiding = st.tabs(["Inspectierapport Analyser", "Overzicht Database", "Developer", "Handleiding"])

        # Tabblad 1: Inspectierapport Analyser
        with tab_model:
            st.header("Inspectierapport Analyser")
            
            # if st.button("Push to github"):
            #     import subprocess
                
            #     # Voeg een lege regel met alleen nullen toe
            #     empty_row = pd.DataFrame([[0] * len(data.columns)], columns=data.columns)
            #     data = pd.concat([data, empty_row], ignore_index=True)
            #     st.write(data.tail(5))
            #     # push_to_github("CompaNanny_Database.xlsx", commit_message="Nieuwe data toegevoegd na analyse")
            #     save_and_push_to_github(data=data, file_name="CompaNanny_Database.xlsx", commit_message="Nieuwe data toegevoegd via Streamlit")
                
            # Upload PDF voor analyse
            uploaded_file = st.file_uploader("Upload een PDF van het inspectierapport", type="pdf")
            
            if uploaded_file:
                # Lees de voorpagina van de PDF
                reader = PdfReader(uploaded_file)
                front_page = "".join(reader.pages[0].extract_text())
                pdf_pages = [2,3]
                pdf_text = "\n".join([reader.pages[i].extract_text() for i in pdf_pages])
                # Verwijder lege regels
                # pdf_text = "\n".join([line for line in pdf_text.splitlines() if line.strip() != ""])

                # Zoek naar bestaand bedrijf en vestiging op voorpagina
                bedrijf, vestiging, type_oko = vind_bedrijf_vestiging(front_page)

                # Zoek naar "Datum inspectie" op de voorpagina in de tekst en sla de datum op
                inspection_date = find_or_input_inspection_date(front_page)
                # st.write(f"Inspectierapport datum: <span style='color: green; font-weight: bold;'>{inspection_date}</span>", unsafe_allow_html=True)
                

            
                if bedrijf and vestiging and type_oko and inspection_date:
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
                            "Type Opvangvoorziening": type_oko,
                            "Rapportdatum": inspection_date.strftime("%Y-%m-%d"),
                        }

                        # Controleer of de nieuwe rij al bestaat in de DataFrame
                        is_duplicate = data[
                            (data["Bedrijfnaam"] == new_row["Bedrijfnaam"]) &
                            (data["Vestiging"] == new_row["Vestiging"]) &
                            (data["Type Opvangvoorziening"] == new_row["Type Opvangvoorziening"]) &
                            (data["Rapportdatum"] == new_row["Rapportdatum"])
                        ].shape[0] > 0


                        if is_duplicate:
                            st.warning("Deze combinatie van Bedrijf, Vestiging en Rapportdatum bestaat al in de database.")
                        else:
                            response = chat_with_gpt(pdf_text, inspection_date)

                            # Probeer de response om te zetten naar een dictionary en voeg toe aan new_row
                            new_row = update_row_with_response(new_row, response)
                            st.write("Output: ", new_row)

                            new_row_df = pd.DataFrame([new_row])
                            data = pd.concat([data, new_row_df], ignore_index=False)

                            # # Sla de bijgewerkte DataFrame op in het Excel-bestand
                            # data.to_excel("CompaNanny_Database.xlsx", index=False)
                            # push_to_github("CompaNanny_Database.xlsx", commit_message="Nieuwe data toegevoegd na analyse")
                            save_and_push_to_github(data=data, file_name="CompaNanny_Database.xlsx", commit_message=f"Nieuwe data toegevoegd via Streamlit op {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}")
                            
                            # Controleer of er een back-up nodig is
                            if len(data) % 20 == 0:
                                make_backup(data)
                                # data_backup = make_backup(data, backup_dir="backups", filename_prefix="CompaNanny_Database_backup")
                                

                            st.success("Output toegevoegd aan database.")

#====================================================================================================


        # Tabblad 2: Overzicht Database
        with tab_data:
            st.markdown("""
            #### Wat bevat de dataset?
            - **Locatie-informatie**:
                - De naam van de kinderopvangorganisatie.
                - De specifieke vestiging waar de inspectie is uitgevoerd.
                - Het type opvangvoorziening op de locatie (keuze uit: "VGO", "BSO", "KDV", "GOB").
            - **Inspectiedatum**:
                - De datum waarop de inspectie heeft plaatsgevonden.
            - **Overtredingen per categorie**:
                - Voor elk inspectierapport wordt aangegeven of er overtredingen zijn binnen de categorie van de kolomnaam.
            
            #### Hoe werkt de dataset?
            De dataset geeft per inspectierapport een binaire waarde aan:
            - **1**: Er is een overtreding vastgesteld binnen deze categorie.
            - **0**: Er is geen overtreding vastgesteld binnen deze categorie.
            """)
            
            # Horizontale lijn voor scheiding
            st.markdown("---")
            st.header("Overzicht Database")
            st.write(data.tail(100))

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
        with tab_dev:
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
                # Beschrijving van de functie
                st.markdown(
                    """
                    Als een bedrijf of vestiging niet voorkomt in de bestaande lijst, kun je met deze functie eenvoudig een nieuw bedrijf en de bijbehorende vestiging toevoegen aan de beschikbare opties.
                    Vul de naam van het bedrijf en de vestiging in de invoervelden in. 
                    Klik daarna op de knop **"Toevoegen"** om de gegevens op te slaan. 

                    - **Bedrijfsnaam:** Naam van het bedrijf dat je wilt toevoegen.
                    - **Vestiging:** Naam van de vestiging die bij het bedrijf hoort.
                    """
                )
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
                # Beschrijving van de functie
                st.markdown(
                    """
                    Met deze functie kun je de huidige database vervangen door nieuwe gegevens die je uploadt als een Excel- of CSV-bestand. 
                    Deze functionaliteit is handig als je bestaande data wilt overschrijven met een bijgewerkte dataset.

                    - **Bestandsformaten:** Alleen bestanden met extensies `.xlsx` (Excel) en `.csv` worden geaccepteerd.
                    - **Voorbeeldweergave:** Na het uploaden van het bestand wordt de inhoud weergegeven in een tabel, zodat je de data kunt controleren.
                    - **Bevestiging:** Klik op **"Vervang Basisdata"** om de bestaande database te vervangen met de nieuwe data.

                    **LET OP:** 
                    - Het vervangen van de basisdata is een onomkeerbare actie.
                    - De huidige database wordt volledig overschreven, en de oude data kan niet worden hersteld. Zorg ervoor dat je een back-up hebt gemaakt van de huidige data voordat je doorgaat.
                    - Het model is nog niet bijgewerkt op de kolomnamen van het nieuwe bestand. Zorg ervoor dat deze overeen komen of dat je de prompt en labels aanpast.
                    """
                )

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

                st.markdown("---")
            
#========================================================================================    
                # Titel van de pagina
                st.title("Beheer Labels voor Model")

                # Beschrijving
                st.markdown("""
                Met deze tool kun je de labels beheren die worden gebruikt door het model. Labels worden door het model gebruikt om overtredingen te identificeren en te groeperen binnen specifieke thema's of categorieën (ook wel labels genoemd).
                - Je kunt de huidige labels bekijken, aanpassen, nieuwe toevoegen of verwijderen.
                - Gebruik de knop **"+"** om een label toe te voegen.
                - Gebruik de knop **"-"** om het laatste label te verwijderen.
                """)

                # Labels laden vanuit bestand en inladen in session_state (eenmalig)
                if "labels_input" not in st.session_state:
                    try:
                        # Laad de labels als een lijst van strings
                        st.session_state.labels_input = load_file("labels.txt").splitlines()
                    except FileNotFoundError:
                        st.session_state.labels_input = []  # Start met een lege lijst als bestand niet bestaat

                # Dynamisch genereren van tekstvakken voor labels
                labels_input = st.session_state.labels_input
                for i, label in enumerate(labels_input):
                    st.session_state.labels_input[i] = st.text_input(f"Label {i+1}", value=label, key=f"label_{i}")

                # Knoppen om labels toe te voegen of te verwijderen
                col1, col2 = st.columns([1, 1])

                with col1:
                    if st.button("+ Voeg een label toe"):
                        st.session_state.labels_input.append("")  # Voeg een lege tekstvak toe
                        st.rerun()

                with col2:
                    if st.button("- Verwijder laatste label"):
                        if st.session_state.labels_input:
                            st.session_state.labels_input.pop()  # Verwijder de laatste tekstvak
                            st.rerun()

                # Opslaan van de bijgewerkte labels
                if st.button("Opslaan"):
                    # Verwijder lege labels en sla de rest op in het bestand
                    updated_labels = [label.strip() for label in st.session_state.labels_input if label.strip()]
                    save_file("\n".join(updated_labels), "labels.txt")  # Sla de lijst op als string met nieuwe regels
                    st.success("Labels succesvol opgeslagen!")
                
                    # Toon de huidige labels
                    st.markdown("### Huidige Labels:")
                    st.write(st.session_state.labels_input)
                
                    # st.rerun()  # Herlaad de pagina om de wijzigingen te tonen
#========================================================================================
                st.markdown("---")
                # Titel en beschrijving
                st.title("Prompt Editor")
                st.markdown("""
                Met deze tool kunt u de prompt aanpassen die het model gebruikt. Voer hieronder de nieuwe prompt in en klik op 'Opslaan wijzigingen' om de prompt bij te werken.
                De oude prompt wordt automatisch opgeslagen als `prompt_oud.txt`.
                """)

                # prompt laden vanuit bestand
                current_prompt = load_file("prompt.txt")

                # Tekstvak om de prompt te bewerken
                new_prompt = st.text_area("Pas de prompt aan:", value=current_prompt, height=300)

                # Opslaan knop
                if st.button("Opslaan wijzigingen"):
                    # Sla de oude prompt op
                    save_file(current_prompt, "prompt_oud.txt")
                    # Sla de nieuwe prompt op
                    save_file(new_prompt, "prompt.txt")
                    st.success("De nieuwe prompt is succesvol opgeslagen! De oude prompt is opgeslagen als `prompt_oud.txt`.")
                    st.rerun()  # Herlaad de pagina om de nieuwste prompt te tonen

        # HANDLEIDING
        with tab_handleiding:
            st.markdown("""
            # Handleiding voor de Inspectierapporten Analysetool

            Welkom bij de Inspectierapporten Analysetool, ontworpen voor medewerkers van CompaNanny om efficiënt en nauwkeurig inspectierapporten te analyseren. Deze tool maakt gebruik van een slim model om inspectierapporten automatisch te kwantificeren, waardoor handmatig werk aanzienlijk wordt verminderd.

            ---

            ## Inhoudsopgave
            1. [Functionaliteit van de Webapp](#1-functionaliteit-van-de-webapp)
                - [Inspectierapport Analyseren](#inspectierapport-analyseren)
                - [Overzicht Database](#overzicht-database)
                - [Developer Pagina](#developer-pagina)
                - [Kosten en Beveiliging](#kosten-en-beveiliging)
            2. [Hoe werkt het?](#2-hoe-werkt-het)
                - [Stap 1: Inspectierapport Uploaden](#stap-1-inspectierapport-uploaden)
                - [Stap 2: Resultaten Bekijken](#stap-2-resultaten-bekijken)
                - [Stap 3: Database Downloaden](#stap-3-database-downloaden)
            3. [Belangrijke Informatie](#3-belangrijke-informatie)
                - [Automatische Detecties](#automatische-detecties)
                - [Betrouwbare Bronnen](#betrouwbare-bronnen)
                - [Beperkingen](#beperkingen)
            4. [Over de App](#4-over-de-app)
            5. [Veelgestelde Vragen](#5-veelgestelde-vragen)

            ---

            ## 1. Functionaliteit van de Webapp

            ### Inspectierapport Analyseren
            Met deze functionaliteit kan een gebruiker een inspectierapport (PDF-bestand) uploaden naar de app. Het model analyseert het rapport en kwantificeert overtredingen binnen vooraf opgestelde categorieën. Op dit moment (01-Dec-2024) zijn dit:
            - Algemene voorwaarden kwaliteit en naleving
            - Veiligheid en gezondheid
            - Personeel en groepen
            - Pedagogisch klimaat
            - Accommodatie
            - Ouderrecht

            De resultaten worden weergegeven als een binaire waarde:
            - **1**: Een overtreding is vastgesteld.
            - **0**: Geen overtreding.

            De analyse wordt automatisch toegevoegd aan de database (zie **Pagina 2**). Wanneer essentiële gegevens, zoals de bedrijfsnaam of inspectiedatum, niet automatisch kunnen worden gedetecteerd, kan de gebruiker deze handmatig invoeren via dropdowns en tekstvelden.

            ---

            ### Overzicht Database
            De database bevat een overzicht van alle geanalyseerde rapporten, inclusief de bedrijfsnaam, vestiging, inspectiedatum en overtredingen per categorie. Gebruikers kunnen:
            - De database bekijken in een tabelweergave.
            - De volledige database downloaden als **CSV** of **XLSX** voor verdere analyse in bijvoorbeeld Excel.

            Op dit moment biedt de app geen ingebouwde trendanalyses, maar door de database te exporteren, kunnen deze eenvoudig extern worden uitgevoerd.

            ---

            ### Developer Pagina
            De developer pagina is bedoeld voor geautoriseerde gebruikers om:
            - Bedrijven en vestigingen toe te voegen aan de beschikbare opties.
            - Originele database vervangen.
            - De prompt voor het model aan te passen, inclusief de categorieën en instructies.
            - De input- en outputparameters te beheren om kosten te optimaliseren.

            Let op: wijzigingen op deze pagina kunnen invloed hebben op de kosten en prestaties van het model.

            ---

            ### Kosten en Beveiliging
            Het gebruik van het model kost geld, afhankelijk van de hoeveelheid tekst in het inspectierapport en de output. Hieronder een samenvatting van de kosten:
            - **Input**: $0.0025 per 750 woorden.
            - **Output**: $0.0100 per 750 woorden.

            De app toont een schatting van de kosten voordat een analyse wordt uitgevoerd. Pas als op **Analyseer** wordt gedrukt, worden kosten in rekening gebracht.

            **Beveiliging**:
            - De webapp is beveiligd met een wachtwoord- en inlogsysteem, zowel voor gebruikers als developers.
            - API-sleutels en wachtwoorden worden opgeslagen in beveiligde (secret) variabelen.

            ---

            ## 2. Hoe werkt het?

            ### Stap 1: Inspectierapport Uploaden
            1. Ga naar de **Analyseer Model**-pagina.
            2. Upload een PDF-bestand met een inspectierapport.
            3. Controleer of alle essentiële gegevens automatisch worden gedetecteerd (zoals bedrijfsnaam en inspectiedatum). Indien nodig, vul ontbrekende gegevens handmatig in.
            4. Klik op **Analyseer** om het rapport te laten verwerken door het model.

            ---

            ### Stap 2: Resultaten Bekijken
            - Na analyse worden de resultaten weergegeven op de pagina. Deze bevatten:
            - De overtredingen per categorie.
            - Informatie zoals bedrijfsnaam, vestiging en inspectiedatum.
            - De resultaten worden automatisch toegevoegd aan de database.

            ---

            ### Stap 3: Database Downloaden
            1. Ga naar de **Overzicht Database**-pagina.
            2. Bekijk de bestaande gegevens in de tabel.
            3. Download de volledige database via de downloadknoppen als **CSV** of **XLSX**.

            ---

            ## 3. Belangrijke Informatie

            ### Automatische Detecties
            De app maakt gebruik van slimme algoritmen om automatisch:
            - Bedrijfsnamen
            - Vestigingen
            - Type opvangvoorziening
            - Inspectiedata

            te detecteren uit de tekst in een PDF. Wanneer deze niet automatisch worden gevonden, biedt de app opties om deze handmatig in te vullen via dropdowns en tekstvelden.

            ---

            ### Betrouwbare Bronnen
            De inspectierapporten die worden geanalyseerd, moeten afkomstig zijn van betrouwbare en openbare bronnen, zoals:
            - [Landelijk Register Kinderopvang](https://www.landelijkregisterkinderopvang.nl/)
            - [Data Overheid](https://data.overheid.nl/)

            Alle rapporten zijn wettelijk openbaar en mogen worden gebruikt voor analyse.

            ---

            ### Beperkingen
            De app richt zich uitsluitend op overtredingen die op de inspectiedatum zijn geconstateerd. Historische data of samenvattingen van eerdere inspecties worden niet meegenomen in de analyse.

            ---

            ## 4. Over de App

            - **Ontwikkelaar**: Deze app is ontwikkeld door Hidde Franke. Voor technische problemen kan hij worden bereikt via LinkedIn.
            - **Toegang**: De app is uitsluitend bedoeld voor medewerkers van CompaNanny. Inloggegevens worden gedeeld op verzoek en kunnen worden gewijzigd.
            - **Toekomstige Mogelijkheden**: De functionaliteit van de app kan in de toekomst worden uitgebreid om meer informatie uit rapporten te extraheren.

            ---

            ## 5. Veelgestelde Vragen

            1. **Kan ik de app gebruiken zonder technische kennis?**
                - Nee, deze app is ontworpen voor technisch onderlegde gebruikers. 

            2. **Wat gebeurt er als mijn inspectierapport niet volledig wordt gedetecteerd?**
                - De app biedt opties om ontbrekende gegevens handmatig in te voeren.

            3. **Hoe beheer ik de kosten van de API?**
                - We raden aan om geen automatische incasso te gebruiken en losse bedragen toe te voegen via [OpenAI Billing](https://platform.openai.com/).

            4. **Kan ik de database delen met anderen?**
                - Ja, de database kan worden gedownload en extern worden gedeeld of geanalyseerd.

            ---

            Bedankt voor het gebruik van de Inspectierapporten Analysetool!
            """)



    if __name__ == "__main__":
        main()
