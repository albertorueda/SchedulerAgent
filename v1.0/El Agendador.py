# app.py

import os
import streamlit as st
from utils import agent_executor
from dotenv import load_dotenv
load_dotenv()


# Configuración de la API Key en la barra lateral


st.title("Scheduler")
st.caption("Un chatbot de Streamlit potenciado por el agente de agendamiento")

# Inicializar el estado de la conversación
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "¿En qué puedo ayudarte?"}]

# Mostrar los mensajes previos en la interfaz de chat
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Entrada del usuario en el chat
if prompt := st.chat_input("Escribe tu mensaje aquí..."):
    if not os.getenv("OPENAI_API_KEY"):
        st.info("Agrega tu OpenAI API Key para continuar.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    # Ejecutar el agente con el mensaje del usuario
    result = agent_executor({"input": prompt})
    # Si el resultado contiene una clave de salida única, por ejemplo "output", puedes extraerla:
    response = result.get("output", result)

    
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.chat_message("assistant").write(response)
