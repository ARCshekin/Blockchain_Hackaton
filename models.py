from pydantic import BaseModel, Field

class DonationData(BaseModel):
    org: str = Field(..., example="Красный Крест")
    amount: float = Field(..., gt=0, example=10.0)
