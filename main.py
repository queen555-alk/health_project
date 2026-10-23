from datetime import date, timedelta

from fastapi import Depends, FastAPI, HTTPException, HTTPException
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy.orm import Session

import models
from database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="MamaCare")


class MotherCreate(BaseModel):
    name: str
    phone: str
    lmp_date: date

    @field_validator("lmp_date")
    @classmethod
    def lmp_must_be_plausible(cls, v: date) -> date:
        today = date.today()
        if v > today:
            raise ValueError("LMP date cannot be in the future")
        if today - v > timedelta(days=294):
            raise ValueError("LMP date is more than 42 weeks ago; please check it")
        return v


class MotherOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str
    lmp_date: date
    due_date: date


def estimated_due_date(lmp: date) -> date:
    return lmp + timedelta(days=280)


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


@app.get("/")
def home():
    return {"message": "MamaCare is running"}


@app.get("/due-date")
def due_date(lmp: date):
    return {"lmp": lmp, "due_date": estimated_due_date(lmp)}


@app.get("/antenatal-schedule")
def antenatal(lmp: date):
    return antenatal_schedule(lmp)


@app.post("/mothers", response_model=MotherOut)
def register_mother(data: MotherCreate, db: Session = Depends(get_db)):
    mother = models.Mother(
        name=data.name,
        phone=data.phone,
        lmp_date=data.lmp_date,
        due_date=estimated_due_date(data.lmp_date),
    )
    db.add(mother)
    db.flush()
    for visit in antenatal_schedule(data.lmp_date):
        if visit["date"] >= date.today():
            db.add(models.Appointment(
                mother_id=mother.id,
                visit_number=visit["visit"],
                week=visit["week"],
                due_date=visit["date"],
            ))
    db.commit()
    db.refresh(mother)
    return mother


@app.get("/mothers", response_model=list[MotherOut])
def list_mothers(db: Session = Depends(get_db)):
    return db.query(models.Mother).all()


