from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ....schemas.widget import WidgetCreate, WidgetRead, WidgetPropertyCreate
from ....models.widget import Widget, WidgetProperty
from ....db.database import get_session

router = APIRouter()


@router.post("/", response_model=WidgetRead)
def create_widget(widget: WidgetCreate, session: Session = Depends(get_session)):
    db_widget = session.exec(select(Widget).where(Widget.name == widget.name)).first()
    if db_widget:
        raise HTTPException(status_code=400, detail="Un widget avec ce nom existe déjà")
    db_widget = Widget.from_orm(widget)
    session.add(db_widget)
    session.commit()
    session.refresh(db_widget)
    return db_widget


@router.get("/", response_model=List[WidgetRead])
def list_widgets(session: Session = Depends(get_session)):
    widgets = session.exec(select(Widget)).all()
    return widgets


@router.post("/{widget_id}/properties", response_model=WidgetRead)
def add_widget_property(
    widget_id: int, 
    property: WidgetPropertyCreate, 
    session: Session = Depends(get_session)
):
    widget = session.get(Widget, widget_id)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget non trouvé")
    db_property = WidgetProperty(name=property.name, widget_id=widget_id)
    session.add(db_property)
    session.commit()
    session.refresh(widget)
    return widget
