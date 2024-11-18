import streamlit as st
import openai
import streamlit as st

openai.api_key = st.secrets["gpt_api_key"]
# def chat_with_gpt(user_input, inspection_date):
#     standard_info = f"Analyseer pdf kinderopvanginspectierapport rond {inspection_date}; geef per label overtreding (1/0) voor: 'Algemene voorwaarden kwaliteit en naleving', 'Veiligheid en gezondheid', 'Personeel en groepen', 'Pedagogisch klimaat', 'Accommodatie', 'Ouderrecht'. Geef alleen dictionarywaarden en exacte keys zonder pythoncodeblok:\n\n"
#     prompt = standard_info + user_input

#     response = openai.ChatCompletion.create(
#         # model="gpt-3.5-turbo",
#         # model = "gpt-4o",                #IN $0.0025 / 1K tokens | OUT $0.0100 / 1K tokens
#         model = "chatgpt-4o-latest",       #IN $0.0050 / 1K tokens | OUT $0.0150 / 1K tokens (PREMIUM)
#         # model = "gpt-3.5-turbo-1106",    #IN $0.0010 / 1K tokens | OUT $0.0020 / 1K tokens
#         # model = "gpt-3.5-turbo-0125",    #IN $0.0005 / 1K tokens | OUT $0.0015 / 1K tokens
#         # model = "babbage-002",           #IN $0.0004 / 1K tokens | OUT $0.0004 / 1K tokens
#         messages=[{"role":"user", "content": prompt}]
#     )
#     return response.choices[0].message.content.strip()


def chat_with_gpt(user_input, inspection_date, debug=False):
    """
    Communiceer met OpenAI's GPT-model om overtredingen in een inspectierapport te analyseren.
    """
    # Combineer de lijst naar een enkele string als user_input een lijst is
    if isinstance(user_input, list):
        user_input = "\n".join(user_input)
    
    # Definieer de labels
    labels = [
        'Algemene voorwaarden kwaliteit en naleving',
        'Veiligheid en gezondheid',
        'Personeel en groepen',
        'Pedagogisch klimaat',
        'Accommodatie',
        'Ouderrecht'
    ]

    # Extra informatie (eventueel leeg laten)
    extra_info = "(problemen bij Voertaal, mentorschap hoort bij P&G; \nBorging risicos, huiselijk geweld of kindermishandeling bij V&G)"
    
    # Bouw de prompt
    standard_info = f"""Analyseer de onderstaande tekst uit een kinderopvanginspectierapport uitsluitend met betrekking tot de inspectiedatum {inspection_date}. 

    Belangrijke regels:
    1. **Andere datums negeren**: Informatie over andere inspectiemomenten (zoals uit de Onderzoeksgeschiedenis) of historische context mag niet worden meegenomen. 
    - Zodra je informatie tegenkomt die niet specifiek gaat over de datum {inspection_date}, stop onmiddellijk met analyseren en negeer die informatie volledig.
    - Je mag alleen bevindingen meenemen die expliciet aan {inspection_date} gekoppeld zijn.
    

    2. **Overtredingen per label**: Geef per label aan of er op de datum {inspection_date} een overtreding is (1) of niet (0): 
        {labels}
    
    3. **Uitvoerformaat**:
        - Geef alleen een dictionary met de exacte labels en de bijbehorende waarden (1/0).

    4. **Extra informatie:
        -{extra_info}
    Voorbeeld van correcte uitvoer:   
    dict(
        'Algemene voorwaarden kwaliteit en naleving': 0,
        'Veiligheid en gezondheid': 1,
        'Personeel en groepen': 0,
        'Pedagogisch klimaat': 0,
        'Accommodatie': 0,
        'Ouderrecht': 0
    )
    
    Hier heb je de pdf-informatie:
    """

    prompt = standard_info + user_input

    # Debug de prompt (optioneel)
    if debug:
        st.write("Prompt:", prompt)

    response = openai.ChatCompletion.create(
        # model="gpt-3.5-turbo",
        model = "gpt-4o",                #IN $0.0025 / 1K tokens | OUT $0.0100 / 1K tokens
        # model = "chatgpt-4o-latest",       #IN $0.0050 / 1K tokens | OUT $0.0150 / 1K tokens (PREMIUM)
        # model = "gpt-3.5-turbo-1106",    #IN $0.0010 / 1K tokens | OUT $0.0020 / 1K tokens
        # model = "gpt-3.5-turbo-0125",    #IN $0.0005 / 1K tokens | OUT $0.0015 / 1K tokens
        # model = "babbage-002",           #IN $0.0004 / 1K tokens | OUT $0.0004 / 1K tokens
        messages=[{"role":"user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()
