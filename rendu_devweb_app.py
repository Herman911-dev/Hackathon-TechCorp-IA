import streamlit as st
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "phi35-financial"

st.set_page_config(page_title="TechCorp Financial Assistant", page_icon="💰")
st.title("💰 TechCorp Financial Assistant")

# Statut de connexion au serveur Ollama
try:
    r = requests.get("http://localhost:11434", timeout=2)
    st.success("🟢 Connecté au serveur d'inférence (Ollama)")
except requests.exceptions.RequestException:
    st.error("🔴 Déconnecté — vérifie que `ollama serve` tourne")

if "history" not in st.session_state:
    st.session_state.history = []

for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("Pose ta question financière...")

if user_input:
    st.session_state.history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Réflexion..."):
            try:
                response = requests.post(
                    OLLAMA_URL,
                    json={"model": MODEL_NAME, "prompt": user_input, "stream": False},
                    timeout=60,
                )
                answer = response.json().get("response", "Erreur de réponse")
            except requests.exceptions.RequestException as e:
                answer = f"Erreur de connexion au serveur : {e}"
            st.write(answer)
            st.session_state.history.append({"role": "assistant", "content": answer})
