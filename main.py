from datetime import date, timedelta

from fastapi import FastAPI

app = FastAPI(title="MamaCare")


def estimated_due_date(lmp: date) -> date:
    return lmp + timedelta(days=280)


@app.get("/")
def home():
    return {"message": "MamaCare is running"}


@app.get("/due-date")
def due_date(lmp: date):
    return {"lmp": lmp, "due_date": estimated_due_date(lmp)}


ANTENATAL_WEEKS = [12, 20, 26, 30, 34, 36, 38, 40]


def antenatal_schedule(lmp: date) -> list:
    visits = []
    for number, weeks in enumerate(ANTENATAL_WEEKS, start=1):
        visits.append({
            "visit": number,
            "week": weeks,
            "date": lmp + timedelta(weeks=weeks),
        })
    return visits


@app.get("/antenatal-schedule")
def antenatal(lmp: date):
    return antenatal_schedule(lmp)