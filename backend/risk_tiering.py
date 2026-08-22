from typing import Dict


class RiskTierer:
    """
    Rule-based risk classifier for recovery actions.

    Uses explicit rules so that risk decisions are deterministic
    and easy to explain.
    """

    RISK_SCORES: Dict[str, float] = {
        "low": 1.0,
        "medium": 0.6,
        "high": 0.2,
    }

    HIGH_RISK_KEYWORDS = [
        "delete",
        "drop",
        "destroy",
        "terminate",
        "wipe",
        "purge",
        "format",
        "remove database",
        "remove infrastructure",
        "reset production",
    ]

    MEDIUM_RISK_KEYWORDS = [
        "modify",
        "change config",
        "change configuration",
        "update config",
        "update configuration",
        "rotate credential",
        "rotate credentials",
        "change credential",
        "change credentials",
        "restart database",
        "restart db",
        "restart server",
        "redeploy",
        "deploy",
        "migrate",
        "failover",
        "rollback",
        "flush cache",
    ]

    LOW_RISK_KEYWORDS = [
        "restart application",
        "restart backend",
        "restart api",
        "restart service",
        "restart worker",
        "clear cache",
        "clear application cache",
        "clear the cache",
        "invalidate cache",
        "retry",
        "reconnect",
        "refresh connection",
        "check health",
        "run health check",
        "inspect",
        "diagnose",
        "verify",
    ]

    @classmethod
    def getRiskTier(cls, action):
        """
        Returns:
            low / medium / high

        Priority matters:
        high -> medium -> low

        Unknown actions default to medium because an unknown
        action should not automatically be treated as safe.
        """

        if not action:
            return "medium"

        normalizedAction = action.lower().strip()

        for keyword in cls.HIGH_RISK_KEYWORDS:
            if keyword in normalizedAction:
                return "high"

        for keyword in cls.MEDIUM_RISK_KEYWORDS:
            if keyword in normalizedAction:
                return "medium"

        for keyword in cls.LOW_RISK_KEYWORDS:
            if keyword in normalizedAction:
                return "low"

        return "medium"

    @classmethod
    def getRiskScore(cls, riskTier):
        """
        Converts a risk tier into the ranking score.
        """

        return cls.RISK_SCORES.get(riskTier, 0.6)

    @classmethod
    def classify(cls, action):
        """
        Returns both the risk tier and risk score.
        """

        riskTier = cls.getRiskTier(action)

        return {
            "riskTier": riskTier,
            "riskScore": cls.getRiskScore(riskTier),
        }