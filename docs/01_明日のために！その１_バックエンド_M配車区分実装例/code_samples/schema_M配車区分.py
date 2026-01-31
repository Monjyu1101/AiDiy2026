class M配車区分Base(BaseModel):
    配車区分名: str
    配車区分備考: Optional[str] = None
    配色枠: str
    配色背景: str
    配色前景: str

class M配車区分Create(M配車区分Base):
    配車区分ID: str

class M配車区分Update(BaseModel):
    配車区分ID: str
    配車区分名: Optional[str] = None
    配車区分備考: Optional[str] = None
    配色枠: str
    配色背景: str
    配色前景: str

class M配車区分Delete(BaseModel):
    配車区分ID: str

class M配車区分Get(BaseModel):
    配車区分ID: str

