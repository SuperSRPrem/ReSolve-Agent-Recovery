import json
from pathlib import Path

from backend.outcome_tracker import computeErrorSignature
from backend.risk_tiering import RiskTierer


class RunbookStore:
    """
    Trusted recovery procedure source.

    Runbooks are different from historical incidents:

        Historical incident
            -> action was actually attempted previously
            -> may have measured success statistics

        Approved runbook
            -> organization-approved recovery procedure
            -> may have no historical outcome statistics yet

    The runbook store never executes actions.
    It only exposes trusted candidate strategies.
    """

    def __init__(
        self,
        path=None,
        minScore=0.45,
    ):
        if path is None:
            projectRoot = (
                Path(__file__)
                .resolve()
                .parent
                .parent
            )

            path = (
                projectRoot
                / "data"
                / "recovery_runbooks.json"
            )

        self.path = Path(path)
        self.minScore = minScore
        self.runbooks = self._loadRunbooks()

    # ==================================================
    # LOADING
    # ==================================================

    def _loadRunbooks(self):
        if not self.path.exists():
            return []

        with self.path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError(
                "recovery_runbooks.json must contain a list."
            )

        return data

    # ==================================================
    # PUBLIC SEARCH
    # ==================================================

    def getRecoveryCandidates(
        self,
        incident,
        limit=5,
    ):
        """
        Finds approved runbooks matching the current incident.

        Matching uses:

            65% error-signature match
            35% keyword overlap

        Historical success is intentionally NOT invented.
        """

        errorSignature = computeErrorSignature(
            incident
        )

        normalizedSignature = (
            str(errorSignature)
            .upper()
            .strip()
        )

        incidentText = self._buildIncidentText(
            incident
        )

        candidates = []

        for runbook in self.runbooks:

            if not runbook.get(
                "approved",
                False,
            ):
                continue

            if not runbook.get(
                "enabled",
                True,
            ):
                continue

            signatureScore = (
                self._signatureScore(
                    normalizedSignature,
                    runbook,
                )
            )

            keywordScore = (
                self._keywordScore(
                    incidentText,
                    runbook,
                )
            )

            evidenceScore = (
                (signatureScore * 0.65)
                + (keywordScore * 0.35)
            )

            if evidenceScore < self.minScore:
                continue

            action = runbook.get(
                "action",
                "",
            )

            if not action:
                continue

            risk = RiskTierer.classify(
                action
            )

            candidate = {
                # Preserve RecoveryMemory-compatible fields.
                "incidentId": runbook.get(
                    "runbookId"
                ),

                "title": runbook.get(
                    "title",
                    "",
                ),

                "similarity": evidenceScore,

                # IMPORTANT:
                # No fake historical outcome statistics.
                "successRate": None,

                "successRateIsConditioned": False,

                "riskTier": risk[
                    "riskTier"
                ],

                "riskScore": risk[
                    "riskScore"
                ],

                # For runbooks this is an evidence-match score,
                # not the historical ranking formula.
                "score": evidenceScore,

                "action": action,

                "steps": runbook.get(
                    "steps",
                    [],
                ),

                "rootCause": "",

                # Extra provenance fields.
                "sourceType": (
                    "approved-runbook"
                ),

                "source": runbook.get(
                    "source",
                    "approved-runbook",
                ),

                "historicalOutcomeAvailable": False,

                "verificationFocus": (
                    runbook.get(
                        "verificationFocus",
                        [],
                    )
                ),

                "matchedErrorSignature": (
                    normalizedSignature
                ),
            }

            candidates.append(
                candidate
            )

        candidates.sort(
            key=lambda candidate: candidate[
                "score"
            ],
            reverse=True,
        )

        return candidates[:limit]

    # ==================================================
    # MATCHING
    # ==================================================

    def _signatureScore(
        self,
        errorSignature,
        runbook,
    ):
        signatures = [
            str(value)
            .upper()
            .strip()

            for value in runbook.get(
                "errorSignatures",
                [],
            )
        ]

        if errorSignature in signatures:
            return 1.0

        return 0.0

    def _keywordScore(
        self,
        incidentText,
        runbook,
    ):
        keywords = [
            str(keyword)
            .lower()
            .strip()

            for keyword in runbook.get(
                "keywords",
                [],
            )

            if str(keyword).strip()
        ]

        if not keywords:
            return 0.0

        matched = sum(
            1
            for keyword in keywords
            if keyword in incidentText
        )

        return matched / len(
            keywords
        )

    def _buildIncidentText(
        self,
        incident,
    ):
        parts = [
            incident.get(
                "title",
                "",
            ),

            incident.get(
                "description",
                "",
            ),

            incident.get(
                "rootCause",
                "",
            ),
        ]

        errorCodes = incident.get(
            "errorCodes",
            [],
        )

        if isinstance(
            errorCodes,
            list,
        ):
            parts.extend(
                errorCodes
            )

        return (
            " ".join(
                str(part)
                for part in parts
            )
            .lower()
            .strip()
        )
