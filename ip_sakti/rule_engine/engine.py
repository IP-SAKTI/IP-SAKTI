"""
ip_sakti.rule_engine.engine — YAML-based rule engine.

Loads rule specifications from config/rules/ (ip_rules.yaml, regulatory_rules.yaml,
tk_abs_rules.yaml) and evaluates domain-specific rules against QueryContext.

Approved per AGENTS.md §3: The Rule Engine uses Python + YAML configuration only.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from ip_sakti.models.query import QueryContext

logger = logging.getLogger(__name__)

_RULES_DIR = Path(__file__).parent.parent.parent / "config" / "rules"


class RuleEngine:
    """
    Evaluates domain rules defined in YAML config files against QueryContext.
    """

    def __init__(self, rules_dir: Path | None = None) -> None:
        """Initialise RuleEngine loading YAML files from rules_dir."""
        self.rules_dir = rules_dir or _RULES_DIR
        self._rules: dict[str, list[dict[str, Any]]] = {}
        self.load_rules()

    def load_rules(self) -> None:
        """Load all YAML rule files from rules_dir."""
        rule_files = ["ip_rules.yaml", "regulatory_rules.yaml", "tk_abs_rules.yaml"]
        for fname in rule_files:
            fpath = self.rules_dir / fname
            if fpath.exists():
                try:
                    with fpath.open("r", encoding="utf-8") as fh:
                        content = yaml.safe_load(fh) or {}
                    rule_key = fname.replace("_rules.yaml", "")
                    self._rules[rule_key] = content.get("rules", [])
                except Exception as exc:
                    logger.error(f"Failed to parse rule file {fpath}: {exc}")
            else:
                logger.warning(f"Rule file not found: {fpath}")

    def evaluate_rules(self, context: QueryContext) -> list[str]:
        """
        Evaluate loaded rules against QueryContext and return applied constraints/guidance.

        Parameters
        ----------
        context :
            Enriched QueryContext model.

        Returns
        -------
        list[str]
            List of domain guidance/constraint strings matching context intent & jurisdiction.
        """
        applied_guidance: list[str] = []

        intent_key = context.intent.value
        rules_list = self._rules.get(intent_key, [])

        for rule in rules_list:
            if not isinstance(rule, dict):
                continue
            rule_id = rule.get("id", "")
            description = rule.get("description", "")

            # Check jurisdiction match
            req_jurisdiction = rule.get("jurisdiction")
            if req_jurisdiction and req_jurisdiction != context.jurisdiction.value and req_jurisdiction != "both":
                continue

            if description:
                applied_guidance.append(f"[{rule_id}] {description}")

        logger.debug(
            "Evaluated rules for query context",
            extra={"intent": intent_key, "rules_applied": len(applied_guidance)},
        )
        return applied_guidance
