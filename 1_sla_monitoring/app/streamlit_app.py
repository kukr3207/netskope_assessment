import streamlit as st
import pandas as pd
import datetime
import requests
from sqlalchemy import create_engine
import os
from app.config import config

# Page config
st.set_page_config(page_title="SLA Dashboard", layout="wide")

# Sidebar: Add a new ticket
st.sidebar.header("Create New Ticket")
id_input = st.sidebar.text_input("Ticket ID")
priority_input = st.sidebar.selectbox("Priority", ["low", "high"], index=1)
tier_input = st.sidebar.selectbox("Customer Tier", ["silver", "gold"], index=1)
status_input = st.sidebar.selectbox("Status", ["open", "closed"], index=0)
created_date = st.sidebar.date_input("Created Date UTC", datetime.datetime.utcnow().date())
created_time = st.sidebar.time_input("Created Time UTC", datetime.datetime.utcnow().time())
created_input = datetime.datetime.combine(created_date, created_time)
if st.sidebar.button("Submit Ticket"):
    payload = [{
        "id": id_input,
        "priority": priority_input,
        "customer_tier": tier_input,
        "created_at": created_input.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_at": created_input.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": status_input
    }]
    try:
        resp = requests.post("http://localhost:8000/tickets", json=payload)
        st.sidebar.success(f"Ingested: {resp.json().get('ingested')} tickets")
    except Exception as e:
        st.sidebar.error(f"Failed to submit: {e}")

# Connect to DB
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/sla_monitoring")
engine = create_engine(DATABASE_URL)

# Load data with parse_dates
tickets_df = pd.read_sql("SELECT * FROM tickets", engine, parse_dates=["created_at","updated_at"])
history_df = pd.read_sql("SELECT * FROM ticket_history ORDER BY changed_at DESC", engine, parse_dates=["changed_at"])

# Compute remaining_response dynamically from config
def compute_remaining_response(row):
    sla_cfg = config.get(row['priority'], row['customer_tier'])
    resp_seconds = sla_cfg.get('response', 0)
    now = datetime.datetime.utcnow()
    return (row['created_at'] + pd.to_timedelta(resp_seconds, unit='s') - now).total_seconds()

tickets_df['remaining_response'] = tickets_df.apply(compute_remaining_response, axis=1)

# Compute flags
tickets_df['alert'] = tickets_df.apply(
    lambda r: r['remaining_response'] <= 0.15 * config.get(r['priority'], r['customer_tier']).get('response', 1),
    axis=1
)
tickets_df['breach'] = tickets_df['remaining_response'] <= 0

# Alerts pane
st.subheader("Current Alerts")
alerts = tickets_df[tickets_df['alert']]
if not alerts.empty:
    styled = alerts[['id','priority','customer_tier','remaining_response','breach']].style
    styled = styled.applymap(lambda v: 'background-color: red' if v else '', subset=['breach'])
    st.dataframe(styled)
else:
    st.write("No alerts at this time.")

# Current Tickets with color coding
st.subheader("Current Tickets")
def highlight(row):
    if row['breach']:
        return ['background-color: lightcoral']*len(row)
    if row['alert']:
        return ['background-color: khaki']*len(row)
    return ['']*len(row)
st.dataframe(tickets_df.style.apply(highlight, axis=1))

# Status Change History
st.subheader("Status Change History")
st.dataframe(history_df)
