# utils.py

from datetime import datetime
from langchain.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.memory import ConversationBufferMemory
from langchain.tools import tool
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
load_dotenv()

# Datos de ejemplo
calendarios = [
    {"persona": 0, "eventos": [0, 1]},
    {"persona": 1, "eventos": [2]},
    {"persona": 2, "eventos": [2, 3]},
]

personas = [
    {"id": 0, "nombre": "Juan Pérez", "puesto": "Senior Manager"},
    {"id": 1, "nombre": "María Gómez", "puesto": "Consultor Junior I"},
    {"id": 2, "nombre": "Carlos Ramírez", "puesto": "Senior III"},
]

eventos = [
    {"id": 0, "titulo": "Conferencia en línea", "fecha": "2025-03-01", "hora": "17:00", "lugar": "Microsoft Teams", "duracion": "1:30"},
    {"id": 1, "titulo": "Capacitación interna", "fecha": "2025-02-20", "hora": "09:00", "lugar": "Sala de reuniones 2", "duracion": "2:00"},
    {"id": 2, "titulo": "Llamada con cliente", "fecha": "2025-02-16", "hora": "15:00", "lugar": "Microsoft Teams", "duracion": "0:45"},
    {"id": 3, "titulo": "Reunión de equipo", "fecha": "2025-02-15", "hora": "10:00", "lugar": "Sala de conferencias 3", "duracion": "1:00"},
]

contactos = [
    {"persona": 0, "contactos": [1, 2]},
    {"persona": 1, "contactos": [0]},
    {"persona": 2, "contactos": [0]},
]

def convertir_a_minutos(hora: str) -> int:
    """Convierte una hora en formato 'HH:MM' a minutos."""
    horas, minutos = map(int, hora.split(':'))
    return horas * 60 + minutos

def convertir_a_horas(minutos: int) -> str:
    """Convierte minutos a una hora en formato 'HH:MM'."""
    horas = minutos // 60
    minutos = minutos % 60
    return f"{horas:02d}:{minutos:02d}"

def no_disponibilidad(personas_list):
    """
    Devuelve los periodos de tiempo en los que las personas especificadas no están disponibles.
    Retorna una lista de diccionarios con 'fecha', 'hora_inicio' y 'hora_fin'.
    """
    if not personas_list:
        return None
    # Obtener todos los IDs de eventos asociados a las personas indicadas
    event_ids = {
        evento_id
        for calendario in calendarios
        if calendario["persona"] in personas_list
        for evento_id in calendario["eventos"]
    }
    no_disp = []
    for e in eventos:
        if e["id"] in event_ids:
            inicio = e["hora"]
            fin = convertir_a_horas(convertir_a_minutos(e["hora"]) + convertir_a_minutos(e["duracion"]))
            no_disp.append({"fecha": e["fecha"], "hora_inicio": inicio, "hora_fin": fin})
    return no_disp

@tool
def obtener_persona(nombre: str):
    """Devuelve la persona cuyo nombre coincide con el especificado."""
    for p in personas:
        if p["nombre"] == nombre:
            return p
    return None

@tool
def obtener_calendario(persona: int):
    """Devuelve el calendario (lista de eventos) de la persona especificada."""
    if persona is None:
        return "Debe especificar una persona"
    eventos_persona = next((c["eventos"] for c in calendarios if c["persona"] == persona), None)
    if not eventos_persona:
        return "No hay eventos para esta persona"
    return [e for e in eventos if e["id"] in eventos_persona]

@tool
def obtener_ids_personas(nombres):
    """
    Devuelve los IDs de las personas especificadas.
    'nombres' debe ser una lista de nombres y se retorna una lista de IDs.
    """
    if not nombres:
        return None
    ids_personas = []
    for nombre in nombres:
        p = obtener_persona(nombre)
        if not p:
            return None
        ids_personas.append(p["id"])
    return ids_personas

@tool
def crear_evento(personas_ids, nuevo_evento):
    """Crea un evento para la lista de personas especificadas y actualiza sus calendarios."""
    eventos.append(nuevo_evento)
    for persona_id in personas_ids:
        for c in calendarios:
            if c["persona"] == persona_id:
                c["eventos"].append(nuevo_evento["id"])

@tool
def agendar_evento(personas_ids, titulo: str, fecha: str, hora: str, lugar: str, duracion: str):
    """Agenda un evento para las personas indicadas tras verificar disponibilidad."""
    if not personas_ids:
        return "Debe especificar al menos una persona"
    if not titulo:
        return "Debe especificar un título para el evento"
    if not fecha:
        return "Debe especificar una fecha para el evento"
    if not hora:
        return "Debe especificar una hora para el evento"
    if not lugar:
        return "Debe especificar un lugar para el evento"
    if not duracion:
        return "Debe especificar una duración para el evento"
    
    no_disp = no_disponibilidad(personas_ids)
    for periodo in no_disp:
        if periodo["fecha"] == fecha:
            if convertir_a_minutos(periodo["hora_inicio"]) <= convertir_a_minutos(hora) < convertir_a_minutos(periodo["hora_fin"]):
                return "No hay disponibilidad para esta hora"
    
    nuevo_evento = {
        "id": len(eventos),
        "titulo": titulo,
        "fecha": fecha,
        "hora": hora,
        "lugar": lugar,
        "duracion": duracion
    }
    eventos.append(nuevo_evento)
    for persona_id in personas_ids:
        for c in calendarios:
            if c["persona"] == persona_id:
                c["eventos"].append(nuevo_evento["id"])
    return "Reunión agendada con éxito"

@tool
def agendar_evento_urgente(personas_ids, titulo: str, lugar: str, duracion: str, fecha=""):
    """
    Agenda un evento urgente para las personas indicadas.
    Busca la siguiente franja de 15 minutos disponible en el día actual.
    """
    if not personas_ids:
        return "Debe especificar al menos una persona"
    if not titulo:
        return "Debe especificar un título para el evento"
    
    no_disp = no_disponibilidad(personas_ids)
    ahora = datetime.now()
    fecha_actual = ahora.date().isoformat()
    hora_actual = convertir_a_minutos(ahora.strftime("%H:%M"))
    
    # Buscar la próxima franja horaria en intervalos de 15 minutos
    posible_hora = hora_actual + (15 - (hora_actual % 15))
    while any(
        periodo["fecha"] == fecha_actual and convertir_a_minutos(periodo["hora_inicio"]) <= posible_hora < convertir_a_minutos(periodo["hora_fin"])
        for periodo in no_disp
    ):
        for periodo in no_disp:
            if periodo["fecha"] == fecha_actual and convertir_a_minutos(periodo["hora_inicio"]) <= posible_hora < convertir_a_minutos(periodo["hora_fin"]):
                posible_hora = convertir_a_minutos(periodo["hora_fin"])
                break
    hora_formateada = convertir_a_horas(posible_hora)
    
    nuevo_evento = {
        "id": len(eventos),
        "titulo": titulo,
        "fecha": fecha_actual,
        "hora": hora_formateada,
        "lugar": lugar,
        "duracion": duracion
    }
    # Para agregar automáticamente el evento, descomente la siguiente línea:
    # crear_evento(personas_ids, nuevo_evento)
    return nuevo_evento

# Configuración del prompt y del agente

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "Eres un asistente de agendamiento de reuniones. Para las fechas utiliza el formato ISO 8601 (YYYY-MM-DD). "
        "Introduce las horas en formato 24 horas y las duraciones en formato H:MM, por ejemplo, '0:30' para 30 minutos y '1:30' para una hora y media. "
        "Cuando se solicite agendar una reunión con varias personas, obtén primero los IDs sin mencionarlo en la respuesta. "
        "Antes de crear un evento, solicita la confirmación del usuario."
    ),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY"))
llm_with_tools = llm.bind_tools([
    obtener_persona,
    obtener_calendario,
    obtener_ids_personas,
    agendar_evento,
    agendar_evento_urgente,
    crear_evento,
])

agent = (
    {
        "input": lambda x: x["input"],
        "chat_history": lambda x: x["chat_history"],
        "agent_scratchpad": lambda x: format_to_openai_tool_messages(x["intermediate_steps"])
    }
    | prompt
    | llm_with_tools
    | OpenAIToolsAgentOutputParser()
)

memory = ConversationBufferMemory(return_messages=True, memory_key="chat_history")
agent_executor = AgentExecutor(
    agent=agent,
    tools=[
        obtener_persona,
        obtener_calendario,
        obtener_ids_personas,
        agendar_evento,
        agendar_evento_urgente,
        crear_evento,
    ],
    verbose=True,
    memory=memory
)
