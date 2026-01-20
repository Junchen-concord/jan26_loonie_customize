from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class AccountInput(BaseModel):
    accountGuid: str
    accountType: Optional[str] = "CHECKING"
    currentBalance: Union[str, int, float]
    availableBalance: Union[str, int, float] = 0.0
    currentBalanceDate: str

    @field_validator("currentBalance")
    @classmethod
    def validate_current_balance(cls, v):
        if not isinstance(v, (str, int, float)):
            raise ValueError("currentBalance must be a string, int, or float")
        return v


class TransactionInput(BaseModel):
    originalDescription: Optional[str] = None
    description: str
    guid: str
    accountGuid: str
    category: Optional[Any] = None
    amount: Union[int, float]
    date: str
    type: str
    label: Optional[str] = None

    class Config:
        extra = "allow"

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError("transaction amount must be either int or float")
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v not in ["CREDIT", "DEBIT"]:
            raise ValueError("transactions must be either CREDIT or DEBIT")
        return v


class ModelAnalyzeRequestV3(BaseModel):
    asOfDate: str = Field(..., description="Analysis as-of date")
    accounts: List[AccountInput] = Field(..., description="List of account information")
    transactions: List[TransactionInput] = Field(..., description="List of transactions")
    applicationInformation: Dict[str, Any] = Field(default_factory=dict, description="Additional application data")
    IBVAuth: Dict[str, Any] = Field(default_factory=dict, description="IBV authentication data")

    class Config:
        extra = "allow"
        schema_extra = {
            "example": {
                "asOfDate": "2024-01-15",
                "accounts": [
                    {
                        "accountGuid": "12345",
                        "accountType": "CHECKING",
                        "currentBalance": 1500.00,
                        "availableBalance": 1400.00,
                        "currentBalanceDate": "2024-01-15",
                    }
                ],
                "transactions": [
                    {
                        "originalDescription": "PAYROLL DEPOSIT",
                        "description": "PAYROLL DEPOSIT",
                        "guid": "txn-123",
                        "accountGuid": "12345",
                        "category": "Income",
                        "amount": 2500.00,
                        "date": "2024-01-01",
                        "type": "CREDIT",
                        "label": "Income",
                    }
                ],
            }
        }
