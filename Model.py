import streamlit as st
import openai
from utils import load_file

openai.api_key = st.secrets["gpt_api_key"]

def chat_with_gpt(user_input, inspection_date, debug=False):
    """
    Communiceer met OpenAI's GPT-model om overtredingen in een inspectierapport te analyseren.
    """
    # Combineer de lijst naar een enkele string als user_input een lijst is
    if isinstance(user_input, list):
        user_input = "\n".join(user_input)
    
    labels = load_file("labels.txt").splitlines()

    # Extra informatie (eventueel leeg laten)
    extra_info = "(problemen bij Voertaal, mentorschap hoort bij P&G; \nBorging risicos, huiselijk geweld of kindermishandeling bij V&G)"
    
    # Bouw de prompt
    prompt = f"""{load_file("prompt.txt")}"""
    prompt = prompt.format(inspection_date=inspection_date, labels=labels, extra_info=extra_info, user_input=user_input)
    

    # Debug de prompt (optioneel)
    if debug:
        st.write("Prompt:\n", prompt)

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


