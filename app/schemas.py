from pydantic import BaseModel, Field, AfterValidator
from decimal import Decimal
from datetime import date as Date
from typing import Annotated

def round_decimal(value):
    return round(value, 2)
    
class LineItem(BaseModel):
    description: str = Field(description='name of item')
    quantity: Annotated[Decimal, Field(gt=0, description='weight/total amount of item'), AfterValidator(round_decimal)]
    unit_price: Annotated[Decimal, Field(ge=0, description='unit price of item'), AfterValidator(round_decimal)]
    line_total: Annotated[Decimal, Field(ge=0, description='quantity * unit price of item'), AfterValidator(round_decimal)]

class Invoice(BaseModel):
    vendor: str = Field(min_length=1, description='name of store/seller')
    date: Date = Field(description='date of the invoice')
    line_items: list[LineItem] = Field(description='list of LineItem Objects')
    subtotal: Annotated[Decimal, Field(ge=0, description='total before tax'), AfterValidator(round_decimal)]
    tax: Annotated[Decimal, Field(ge=0, description='tax amount'), AfterValidator(round_decimal)]
    total: Annotated[Decimal, Field(ge=0, description='total = subtotal + tax'), AfterValidator(round_decimal)]
    currency: str = Field(description='currency as ISO code')
        
class Receipt(Invoice):
    pass

DOC_TO_SCHEMA = {
    'invoice' : Invoice,
    'receipt' : Receipt,
}
    
def get_schema_from_doc(doctype: str):
    doctype = doctype.lower()
    return DOC_TO_SCHEMA[doctype]



    
    
    

    


