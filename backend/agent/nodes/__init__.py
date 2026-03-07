# JAWIR OS - Agent Nodes
# Supervisor, Researcher, Validator, Synthesizer nodes

from .supervisor import supervisor_node
from .researcher import researcher_node
from .validator import validator_node
from .synthesizer import synthesizer_node

__all__ = [
    "supervisor_node",
    "researcher_node", 
    "validator_node",
    "synthesizer_node",
]
