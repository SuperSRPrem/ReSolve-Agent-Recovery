from backend.llm_reasoner import LLMReasoner
from backend.outcome_tracker import computeErrorSignature
from backend.recovery_memory import RecoveryMemory
from backend.runbook_store import RunbookStore


class ReasonedRecoveryMemory:
    """
    Combines two trusted evidence sources:

        1. Historical recovery incidents
        2. Approved recovery runbooks

    RecoveryMemory remains authoritative for historical retrieval,
    ranking, conditioned success statistics, and risk scoring.

    RunbookStore contributes approved procedures that may not yet
    have historical outcome data.

    LLMReasoner may only select from these trusted candidates or
    recommend escalation. It cannot create executable actions.
    """

    def __init__(
        self,
        baseMemory=None,
        reasoner=None,
        environment=None,
        runbookStore=None,
    ):
        self.baseMemory = (
            baseMemory
            if baseMemory is not None
            else RecoveryMemory()
        )

        self.reasoner = (
            reasoner
            if reasoner is not None
            else LLMReasoner()
        )

        self.environment = environment

        self.runbookStore = (
            runbookStore
            if runbookStore is not None
            else RunbookStore()
        )

        self.lastReasoning = None
        self.lastDecisionSource = None
        self.lastCandidates = []

    def getRecovery(
        self,
        currentIncident,
        attemptHistory=None,
        limit=5,
    ):
        attemptHistory = attemptHistory or []

        # ==================================================
        # 1. HISTORICAL EVIDENCE
        # ==================================================

        historicalRecovery = (
            self.baseMemory.getRecovery(
                currentIncident,
                attemptHistory,
                limit,
            )
        )

        historicalChoices = []

        if (
            historicalRecovery.get("status")
            == "MATCH_FOUND"
        ):
            historicalChoices = [
                self._markHistoricalCandidate(
                    choice
                )
                for choice in historicalRecovery.get(
                    "choices",
                    [],
                )
            ]

        # ==================================================
        # 2. APPROVED RUNBOOK EVIDENCE
        # ==================================================

        runbookChoices = (
            self.runbookStore.getRecoveryCandidates(
                currentIncident,
                limit=limit,
            )
        )

        unavailableActions = (
            self._getUnavailableActions(
                attemptHistory
            )
        )

        runbookChoices = [
            choice
            for choice in runbookChoices
            if self._normalizeAction(
                choice.get("action", "")
            )
            not in unavailableActions
        ]

        # ==================================================
        # 3. MERGE TRUSTED CANDIDATES
        # ==================================================

        choices = self._mergeCandidates(
            historicalChoices,
            runbookChoices,
        )

        self.lastCandidates = list(
            choices
        )

        errorSignature = (
            historicalRecovery.get(
                "errorSignature"
            )
            or computeErrorSignature(
                currentIncident
            )
        )

        if not choices:
            self.lastReasoning = None
            self.lastDecisionSource = (
                "no-evidence"
            )

            return {
                "status": "NO_MATCH",
                "message": (
                    "No reliable untried historical "
                    "or approved-runbook recovery "
                    "strategy was found."
                ),
                "errorSignature": errorSignature,
                "strategies": [],
            }

        # ==================================================
        # 4. CURRENT ENVIRONMENT STATE
        # ==================================================

        environmentState = {}

        if self.environment is not None:
            try:
                environmentState = (
                    self.environment.getState()
                )

            except Exception:
                environmentState = {}

        # ==================================================
        # 5. LLM REASONING
        # ==================================================

        reasoning = (
            self.reasoner.analyzeRecovery(
                incident=currentIncident,
                choices=choices,
                environmentState=(
                    environmentState
                ),
                attemptHistory=(
                    attemptHistory
                ),
            )
        )

        self.lastReasoning = reasoning

        self.lastDecisionSource = (
            "llm"
            if reasoning.get("llmUsed")
            else "deterministic-fallback"
        )

        # ==================================================
        # 6. OPTIONAL ESCALATION
        # ==================================================

        if (
            reasoning.get("decision")
            == "ESCALATE"
        ):
            return {
                "status": "NO_MATCH",
                "message": (
                    "Trusted recovery evidence was "
                    "available, but the reasoning layer "
                    "recommended escalation."
                ),
                "errorSignature": errorSignature,
                "strategies": choices,
                "llmReasoning": reasoning,
                "decisionSource": (
                    self.lastDecisionSource
                ),
                "reason": "LLM_ESCALATION",
            }

        # ==================================================
        # 7. TRUSTED CANDIDATE SELECTION
        # ==================================================

        selectedChoice = (
            reasoning.get(
                "selectedChoice"
            )
        )

        if selectedChoice not in choices:
            selectedChoice = (
                self._deterministicFallback(
                    historicalChoices,
                    runbookChoices,
                )
            )

            self.lastDecisionSource = (
                "deterministic-fallback"
            )

        enrichedChoice = dict(
            selectedChoice
        )

        enrichedChoice[
            "decisionSource"
        ] = self.lastDecisionSource

        enrichedChoice[
            "llmReasoning"
        ] = reasoning

        return {
            "status": "MATCH_FOUND",
            "message": (
                "Trusted recovery options found "
                "from historical evidence and/or "
                "approved runbooks."
            ),
            "errorSignature": errorSignature,
            "bestChoice": enrichedChoice,
            "choices": choices,
            "llmReasoning": reasoning,
            "decisionSource": (
                self.lastDecisionSource
            ),
        }

    # ======================================================
    # CANDIDATE PROVENANCE
    # ======================================================

    def _markHistoricalCandidate(
        self,
        choice,
    ):
        candidate = dict(
            choice
        )

        candidate.setdefault(
            "sourceType",
            "historical-incident",
        )

        candidate.setdefault(
            "source",
            "recovery-memory",
        )

        candidate.setdefault(
            "historicalOutcomeAvailable",
            True,
        )

        return candidate

    # ======================================================
    # MERGING
    # ======================================================

    def _mergeCandidates(
        self,
        historicalChoices,
        runbookChoices,
    ):
        """
        Historical candidates remain first.

        This is intentional: deterministic fallback should retain
        the previous RecoveryMemory behavior when the LLM is
        unavailable.

        The LLM can still choose any candidate from either source.
        """

        merged = []
        seenActions = set()

        for choice in (
            list(historicalChoices)
            + list(runbookChoices)
        ):
            action = self._normalizeAction(
                choice.get(
                    "action",
                    "",
                )
            )

            if not action:
                continue

            if action in seenActions:
                continue

            seenActions.add(
                action
            )

            merged.append(
                choice
            )

        return merged

    # ======================================================
    # SAFE DETERMINISTIC FALLBACK
    # ======================================================

    def _deterministicFallback(
        self,
        historicalChoices,
        runbookChoices,
    ):
        if historicalChoices:
            return historicalChoices[0]

        if runbookChoices:
            return runbookChoices[0]

        return None

    # ======================================================
    # ATTEMPT EXCLUSION
    # ======================================================

    def _getUnavailableActions(
        self,
        attemptHistory,
    ):
        unavailableResults = {
            "failed",
            "rejected",
            "pending-approval",
        }

        actions = set()

        for attempt in attemptHistory:
            if (
                attempt.get("result")
                not in unavailableResults
            ):
                continue

            action = self._normalizeAction(
                attempt.get(
                    "action",
                    "",
                )
            )

            if action:
                actions.add(
                    action
                )

        return actions

    def _normalizeAction(
        self,
        action,
    ):
        return (
            str(action)
            .lower()
            .strip()
        )