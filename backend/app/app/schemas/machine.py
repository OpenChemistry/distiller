from typing import Optional

from pydantic import BaseModel


class Machine(BaseModel):
    name: str
    account: str
    qos: str
    qos_filter: Optional[str]
    nodes: int
    constraint: str
    ntasks: int
    ntasks_per_node: Optional[int]
    cpus_per_task: int
    bbcp_dest_dir: str
    reservation: Optional[str]
