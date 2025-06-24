# SLA Monitoring Service

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)  
[![FastAPI](https://img.shields.io/badge/FastAPI-b000b5)](https://fastapi.tiangolo.com/)  
[![Streamlit](https://img.shields.io/badge/Streamlit-orange)](https://streamlit.io/)  
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14-blue)](https://www.postgresql.org/)

A **service** for real-time SLA (Service-Level Agreement) monitoring of customer support tickets, featuring:

- **Ticket ingestion** via FastAPI with idempotent upsert logic  
- **PostgreSQL persistence** of tickets, status history, and alert/breach events  
- **Background scheduler** that raises alerts (≤15% remaining) and breaches (≤0s) on response & resolution clocks  
- **Streamlit dashboard** for ticket management and SLA visibility  
- **Hot-reload** of SLA thresholds from `sla_config.yaml` using Watchdog  

---

## Table of Contents

- [Prerequisites](#prerequisites)  
- [Installation & Run](#installation--run)  
- [Usage](#usage)  
  - [Ingest Tickets](#ingest-tickets)  
  - [Dashboard](#dashboard)  
- [Configuration](#configuration)  
- [Architecture](#architecture)  
- [Design Document](#design-document)  
- [Next Steps & Improvements](#next-steps--improvements)  

---

## Prerequisites

- Docker & Docker Compose  
- (Optional) Python 3.10+ for local development  

---

## Installation & Run

1. **Clone the repository**  
   ```bash
   git clone <repo-url>
   cd sla_monitoring
