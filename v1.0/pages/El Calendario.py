# El Calendario.py

import streamlit as st
from streamlit_calendar import calendar
from utils import eventos, convertir_a_minutos, convertir_a_horas

st.title("Calendario Interactivo")
st.caption("Visualiza y actualiza tus reuniones con una interfaz moderna.")

# Transformar los eventos para incluir el lugar en el título y guardar detalles para el popup.
calendar_events = []
for ev in eventos:
    start_time = ev["hora"]
    duration = ev["duracion"]
    start_minutes = convertir_a_minutos(start_time)
    dur_minutes = convertir_a_minutos(duration)
    end_time = convertir_a_horas(start_minutes + dur_minutes)
    # Combina el título y el lugar: "Título (Lugar)"
    title_with_location = f"{ev['titulo']} ({ev['lugar']})"
    calendar_events.append({
        "title": title_with_location,
        "start": f"{ev['fecha']}T{start_time}:00",
        "end": f"{ev['fecha']}T{end_time}:00",
        # Guardamos el evento completo en extendedProps para usarlo en el popup
        "extendedProps": {
            "details": ev
        }
    })

# Opciones de configuración del calendario, iniciando en vista semanal (timeGridWeek)
calendar_options = {
    "editable": True,
    "selectable": True,
    "headerToolbar": {
        "left": "today prev,next",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek,timeGridDay",
    },
    "slotMinTime": "06:00:00",
    "slotMaxTime": "21:00:00",
    "initialView": "timeGridWeek",
}

# CSS personalizado para mejorar la estética (manteniendo colores por defecto)
custom_css = """
    .fc-event-past {
        opacity: 0.8;
    }
    .fc-event-time {
        font-style: italic;
    }
    .fc-event-title {
        font-weight: 700;
    }
    .fc-toolbar-title {
        font-size: 2rem;
    }
"""

# Renderizar el calendario con los eventos y opciones definidas
cal_widget = calendar(
    events=calendar_events,
    options=calendar_options,
    custom_css=custom_css,
    key='calendar',  # Asigna una key para preservar el estado
)

st.write(cal_widget)

# Verificar si el calendario devolvió un callback por clic en un evento
if isinstance(cal_widget, dict) and cal_widget.get("callback") == "eventClick":
    event_details = cal_widget["eventClick"]["event"]["extendedProps"]["details"]
    with st.expander("Detalles del Evento", expanded=False):
        st.write(f"**Título:** {event_details['titulo']}")
        st.write(f"**Fecha:** {event_details['fecha']}")
        st.write(f"**Hora:** {event_details['hora']}")
        st.write(f"**Lugar:** {event_details['lugar']}")
        st.write(f"**Duración:** {event_details['duracion']}")
