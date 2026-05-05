from typing import Optional
from pydantic import BaseModel


class WidgetPropertyBase(BaseModel):
    name: str


class WidgetPropertyCreate(WidgetPropertyBase):
    pass


class WidgetPropertyRead(WidgetPropertyBase):
    id: int


class WidgetBase(BaseModel):
    name: str
    description: Optional[str] = None


class WidgetCreate(WidgetBase):
    pass


class WidgetRead(WidgetBase):
    id: int


class WidgetWithProperties(WidgetRead):
    properties: list[WidgetPropertyRead] = []
