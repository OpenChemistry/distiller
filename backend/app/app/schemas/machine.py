from typing import Optional
from pydantic import BaseModel


class Machine(BaseModel):
    name: str
    account: str
    qos: str
    nodes: int
    constraint: str
    ntasks_per_node: Optional[str]
    cpus_per_task: int
    cpu_bind: Optional[str]
    bbcp_dest_dir: str