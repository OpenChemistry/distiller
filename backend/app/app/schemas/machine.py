from typing import Optional

from pydantic import BaseModel


class Machine(BaseModel):
    name: str
    account: str
    qos: str
    qos_filter: Optional[str] = None
    nodes: int
    constraint: str
    ntasks: int
    ntasks_per_node: Optional[int] = None
    cpus_per_task: int
    bbcp_dest_dir: str
    reservation: Optional[str] = None
