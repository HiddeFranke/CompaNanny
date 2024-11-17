import re
from datetime import datetime
from difflib import SequenceMatcher
import pandas as pd


def clean_text(text):
    """Verwijder ongewenste tekens en patronen, en verbeter de leesbaarheid."""
    
    # Verwijder bullets, symbolen en speciale opsommingstekens
    text = re.sub(r"[•●▪▶◦·]", "", text)  # Veelvoorkomende bullets en opsommingstekens
    text = re.sub(r"", "", text)  # Verwijder specifieke bullets zoals ''
    
    # Verwijder HTML en XML tags (indien van toepassing in sommige tekstbestanden)
    text = re.sub(r"<[^>]*>", "", text)
    
    # Verwijder hyperlinks
    text = re.sub(r"http\S+|www.\S+", "", text)

    # Verwijder e-mailadressen
    text = re.sub(r"\S+@\S+", "", text)

    # Verwijder telefoonnummers (algemene vormen)
    text = re.sub(r"\b\d{2,3}[-.\s]??\d{3}[-.\s]??\d{4}\b", "", text)
    text = re.sub(r"\b\d{2,3}[-.\s]??\d{2}[-.\s]??\d{2}[-.\s]??\d{2}\b", "", text)  # NL-formaat

    # Verwijder postcode-achtige patronen
    text = re.sub(r"\b\d{4}\s?[A-Z]{2}\b", "", text)

    # Verwijder overbodige tekens zoals dubbele of ongewenste symbolen
    text = re.sub(r"[^a-zA-Z0-9\s.,;:()\-']", "", text)

    # Verwijder overmatig gebruik van leestekens (bv. meerdere punten, uitroeptekens)
    text = re.sub(r"(\!|\?|\.){2,}", ".", text)  # Meer dan één leesteken wordt vervangen door één punt

    # Converteer meerdere spaties en witregels naar één spatie
    text = re.sub(r"\s+", " ", text).strip()

    # Verwijder toonaangevende en afsluitende leestekens en symbolen
    text = text.strip(" .,-")

    return text


def is_unique_text(new_text, train_data, drempel=0.8):
    """Controleert of een nieuwe tekst uniek genoeg is ten opzichte van de teksten in train_data."""
    for existing_text in train_data["text"].dropna():
        if is_gelijk_genoeg(new_text, existing_text, drempel):
            return False  # Tekst is niet uniek genoeg
    return True  # Tekst is uniek genoeg om te annoteren
            
def is_gelijk_genoeg(context1, context2, drempel):
    """Controleert of twee contexten voldoende op elkaar lijken."""
    return SequenceMatcher(None, context1, context2).ratio() > drempel

# Mockup functie voor het test_algoritme (vervang deze door je eigen algoritme)
def text_algoritme(pdf_text, context_zinnen=5, gelijkenis_drempel=0.5):
    """
    Verwerkt de tekst uit een PDF en zoekt naar specifieke contexten rond zoekwoorden.
    Retourneert een lijst van tekstfragmenten die mogelijke overtredingen beschrijven.
    """
    # Definieer zoekwoorden die een tekortkoming kunnen aanduiden
    zoekwoorden = [
        r"\bConclusie\b", r"\bniet voldaan\b", r"\bonvoldoende\b", r"\boverschreden\b", r"\bbeschikt niet\b", r"\bbeschikken niet\b", r"\bovertredingen\b", r"\bovertreding\b"
    ]
    niet_zoekwoorden = [
        r"\bwordt voldaan\b", r"\bword voldaan\b", r"\bgeen overtreding\b", r"\bgeen overtredingen\b"
    ]

    bestaande_contexten = []
    result = []  # Lijst om elke context afzonderlijk op te slaan
    for woord in zoekwoorden:
        for match in re.finditer(woord, pdf_text, re.IGNORECASE):
            # Vind het begin van de zin door het laatste leesteken vóór `match.start()`
            start_index = pdf_text.rfind('.', 0, match.start())
            start_index = pdf_text.rfind('!', 0, start_index) if start_index == -1 else start_index
            start_index = pdf_text.rfind('?', 0, start_index) if start_index == -1 else start_index
            start_index = start_index + 1 if start_index != -1 else 0

            # Vind het einde van de context door `context_zinnen` zinnen verder te gaan
            following_text = pdf_text[start_index:]
            sentences = re.split(r'(?<=[.!?])\s+', following_text)  # Split op zinnen
            context = " ".join(sentences[:context_zinnen]).strip()  # Combineer de eerste `context_zinnen` zinnen

            # Opschonen van context
            context = clean_text(context)
            
            # Check of de context geen duplicaat is en geen niet-zoekwoorden bevat
            if not any(re.search(niet_zoekwoord, context, re.IGNORECASE) for niet_zoekwoord in niet_zoekwoorden):
                # Controleer de context op gelijkenis met bestaande overtredingen
                if not any(is_gelijk_genoeg(context, bestaande_context, gelijkenis_drempel) for _, bestaande_context in bestaande_contexten):
                    bestaande_contexten.append((woord, context))  # Voeg alleen toe als het geen duplicaat is
                    result.append(context)  # Voeg context toe aan de result-lijst

    return result  # Retourneer de lijst met contexten

# Functie om geannoteerde data op te slaan in Excel
def save_annotation_to_excel(annotations, path="train_data.xlsx"):
    # Laad de bestaande database
    data = pd.read_excel(path)

    # Converteer annotaties naar DataFrame en voeg toe aan bestaande data
    new_data = pd.DataFrame([annotations])
    data = pd.concat([data, new_data], ignore_index=True)

    # Sla het bijgewerkte bestand op
    data.to_excel(path, index=False)


