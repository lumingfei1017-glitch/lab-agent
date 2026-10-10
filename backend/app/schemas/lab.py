from xml.dom import Node
from anyio import CapacityLimiter
from pydantic import BaseModel, ConfigDict


class LabResponse(BaseModel):
    id: int
    name: str
    location: str | None
    capacity: int
    open_time: str | None
    close_time: str | None
    description: str | None
    img: str | None
    status: int

    model_config = ConfigDict(from_attributes=True)


class LabCreateResquest(BaseModel):
    name: str
    location: str | None
    capacity: int = 0
    open_time: str
    close_time: str
    description: str | None
    img: str | None = None
    status: int = 1


class LabUpdateResquest(BaseModel):
    name: str | None = None
    location: str | None = None
    capacity: int | None = None
    open_time: str | None = None
    close_time: str | None = None
    description: str | None = None
    img: str | None = None
    status: int | None = None
