# app/classifier.py
def classify_ticket(text: str):
    # TODO: replace with ML/keyword logic
    area = "CASB" if "CASB" in text else "General"
    urgency = "high" if "urgent" in text.lower() else "low"
    return area, urgency
