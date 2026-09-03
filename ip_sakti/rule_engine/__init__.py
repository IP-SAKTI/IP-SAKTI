"""
ip_sakti.rule_engine — YAML-based rule evaluation and agent routing.

Public API
----------
    from ip_sakti.rule_engine import (
        RuleEngine,
        AgentRouter,
    )
"""

from ip_sakti.rule_engine.engine import RuleEngine
from ip_sakti.rule_engine.router import AgentRouter

__all__ = [
    "AgentRouter",
    "RuleEngine",
]
