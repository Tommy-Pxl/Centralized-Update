from dataclasses import dataclass

@dataclass
class Machine:
    id: int
    hostname: str
    ip: str
    username: str
