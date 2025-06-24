# Design Document

## Goals & Requirements
- Real-time SLA tracking with early warnings & breaches
- Persistent audit (ticket state, history, alerts)
- Simple, extensible UI and API

## Data Flow
- Client -> POST /tickets -> upsert in tickets, record history
- Scheduler -> compute remaining time -> record alerts and update tickets status/escalation
- UI/API -> fetch dashboard summary and display color-coded alerts/breaches

## Next Steps & Improvements
- WebSocket for real-time push updates
- Alembic for schema migrations
- Authentication & Authorization layer
- Cloud Deployment (AWS Fargate / GCP Cloud Run with managed RDS)