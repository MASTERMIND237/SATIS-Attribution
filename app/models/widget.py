from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class WidgetBase(SQLModel):
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None
    category: Optional[str] = None  # ← AJOUTER CETTE LIGNE


class Widget(WidgetBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    properties: List["WidgetProperty"] = Relationship(back_populates="widget", sa_relationship_kwargs={"lazy": "selectin"})
    assignments: List["Assignment"] = Relationship(back_populates="widget", sa_relationship_kwargs={"lazy": "selectin"})


class WidgetCreate(WidgetBase):
    pass


class WidgetRead(WidgetBase):
    id: int


class WidgetPropertyBase(SQLModel):
    name: str
    widget_id: int = Field(foreign_key="widget.id")


class WidgetProperty(WidgetPropertyBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    widget: Widget = Relationship(back_populates="properties")


class WidgetPropertyCreate(WidgetPropertyBase):
    pass


class WidgetPropertyRead(WidgetPropertyBase):
    id: int


Widget.update_forward_refs()