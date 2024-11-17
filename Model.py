import streamlit as st
import openai

openai.api_key = st.secrets["gpt_api_key"]
def chat_with_gpt(user_input, inspection_date):
    standard_info = f"Analyseer pdf kinderopvanginspectierapport rond {inspection_date}; geef per label overtreding (1/0) voor: 'Algemene voorwaarden kwaliteit en naleving', 'Kwaliteit en naleving', 'Veiligheid en gezondheid', 'Personeel en groepen', 'Pedagogisch klimaat', 'Accommodatie', 'Ouderrecht'. Geef alleen dictionarywaarden en exacte keys zonder pythoncodeblok:\n\n"
    prompt = standard_info + user_input

    response = openai.ChatCompletion.create(
        # model="gpt-3.5-turbo",
        # model = "gpt-4o",                #IN $0.0025 / 1K tokens | OUT $0.0100 / 1K tokens
        model = "chatgpt-4o-latest",       #IN $0.0050 / 1K tokens | OUT $0.0150 / 1K tokens (PREMIUM)
        # model = "gpt-3.5-turbo-1106",    #IN $0.0010 / 1K tokens | OUT $0.0020 / 1K tokens
        # model = "gpt-3.5-turbo-0125",    #IN $0.0005 / 1K tokens | OUT $0.0015 / 1K tokens
        # model = "babbage-002",           #IN $0.0004 / 1K tokens | OUT $0.0004 / 1K tokens
        messages=[{"role":"user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()
