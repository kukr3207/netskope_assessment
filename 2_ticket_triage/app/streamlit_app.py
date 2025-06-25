# app/streamlit_app.py
import streamlit as st
import requests

API_URL = 'http://localhost:8000'

st.title('Ticket Triage Service')

# Sidebar: New Ticket
st.sidebar.header('New Ticket')
tid = st.sidebar.text_input('Ticket ID')
text = st.sidebar.text_area('Ticket Text')
if st.sidebar.button('Classify'):
    r = requests.post(f'{API_URL}/classify', json={'id': tid, 'text': text})
    if r.status_code == 200:
        st.sidebar.success(r.json())
    else:
        st.sidebar.error(f"{r.status_code}: {r.text}")

# Sidebar: Get a Response
st.sidebar.header('Get Response')
resp_tid = st.sidebar.text_input('Ticket ID for response')
q = st.sidebar.text_input('Query')
if st.sidebar.button('Respond'):
    r = requests.post(
        f'{API_URL}/respond',
        json={'ticket_id': resp_tid, 'query': q}
    )
    if r.status_code == 200:
        st.write(r.json())
    else:
        # avoid calling r.json() on HTML or empty bodies
        st.error(f"Error {r.status_code}: {r.text}")
