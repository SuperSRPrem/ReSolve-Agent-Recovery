import json
import os

from dotenv import load_dotenv


load_dotenv()


class LLMReasoner:
    """
    Evidence-grounded reasoning layer for ReSolve.

    IMPORTANT:
    The LLM does NOT execute infrastructure actions.

    It may only review recovery candidates that were already produced
    by RecoveryMemory and select one of those candidates.

    The selected object is copied from the trusted candidate list.
    We never execute model-generated action text.
    """

    def __init__(
        self,
        model=None,
        client=None,
    ):
        self.model = (
            model
            or os.getenv(
                "OPENAI_MODEL",
                "gpt-5.6-luna",
            )
        )

        self.apiKey = os.getenv(
            "OPENAI_API_KEY"
        )

        self.client = client

        if (
            self.client is None
            and self.apiKey
        ):
            self.client = (
                self._createClient()
            )

    # ======================================================
    # PUBLIC API
    # ======================================================

    def analyzeRecovery(
        self,
        incident,
        choices,
        environmentState=None,
        attemptHistory=None,
    ):
        """
        Reviews evidence-backed recovery candidates.

        Returns:
        {
            "llmUsed": bool,
            "decision": "USE_CANDIDATE" | "ESCALATE",
            "selectedIndex": int,
            "selectedChoice": dict | None,
            "incidentSummary": str,
            "reasoning": str,
            "riskNotes": str,
            "verificationFocus": list[str],
            "confidence": float,
            "model": str | None
        }
        """

        choices = choices or []
        attemptHistory = (
            attemptHistory or []
        )
        environmentState = (
            environmentState or {}
        )

        if not choices:
            return self._escalationResult(
                reason=(
                    "No evidence-backed recovery "
                    "candidates were available."
                )
            )

        if self.client is None:
            return self._fallbackResult(
                choices,
                reason=(
                    "LLM unavailable; using deterministic "
                    "top-ranked recovery strategy."
                ),
            )

        try:
            modelResult = (
                self._callModel(
                    incident=incident,
                    choices=choices,
                    environmentState=(
                        environmentState
                    ),
                    attemptHistory=(
                        attemptHistory
                    ),
                )
            )

            return self._validateDecision(
                modelResult,
                choices,
            )

        except Exception as error:
            return self._fallbackResult(
                choices,
                reason=(
                    "LLM reasoning failed safely; "
                    "using deterministic top-ranked "
                    "strategy. "
                    f"{type(error).__name__}: {error}"
                ),
            )

    # ======================================================
    # OPENAI CLIENT
    # ======================================================

    def _createClient(self):
        try:
            from openai import OpenAI

        except ImportError as error:
            raise RuntimeError(
                "The 'openai' package is required "
                "for LLM reasoning."
            ) from error

        return OpenAI(
            api_key=self.apiKey
        )

    # ======================================================
    # MODEL CALL
    # ======================================================

    def _callModel(
        self,
        incident,
        choices,
        environmentState,
        attemptHistory,
    ):
        evidence = (
            self._buildEvidence(
                incident=incident,
                choices=choices,
                environmentState=(
                    environmentState
                ),
                attemptHistory=(
                    attemptHistory
                ),
            )
        )

        response = (
            self.client.responses.create(
                model=self.model,

                instructions=(
                    "You are the reasoning layer of "
                    "ReSolve, an incident recovery agent. "
                    "\n\n"
                    "You are NOT an execution engine. "
                    "You may not invent shell commands, "
                    "Docker commands, database commands, "
                    "credentials, configuration values, "
                    "or new recovery actions."
                    "\n\n"
                    "You may ONLY choose one candidate "
                    "from the supplied candidate list, "
                    "or recommend escalation."
                    "\n\n"
                    "Evaluate candidates using the supplied "
                    "incident evidence, current system "
                    "state, historical similarity, "
                    "historical success rate, risk tier, "
                    "prior attempts, and verification "
                    "requirements."
                    "\n\n"
                    "Approved runbook evidence may have no "
                    "historical success rate. Do not treat a "
                    "missing success rate as either success "
                    "or failure, and do not invent one."
                    "\n\n"
                    "Prefer an evidence-supported strategy "
                    "that has not already failed. "
                    "Do not treat execution success as "
                    "recovery success. Recovery must later "
                    "be independently verified by ReSolve."
                    "\n\n"
                    "If none of the candidates are "
                    "sufficiently supported, choose "
                    "ESCALATE."
                ),

                input=json.dumps(
                    evidence,
                    indent=2,
                    default=str,
                ),

                text={
                    "format": {
                        "type": "json_schema",
                        "name": (
                            "resolve_recovery_reasoning"
                        ),
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "decision": {
                                    "type": "string",
                                    "enum": [
                                        "USE_CANDIDATE",
                                        "ESCALATE",
                                    ],
                                },
                                "selectedIndex": {
                                    "type": "integer",
                                },
                                "incidentSummary": {
                                    "type": "string",
                                },
                                "reasoning": {
                                    "type": "string",
                                },
                                "riskNotes": {
                                    "type": "string",
                                },
                                "verificationFocus": {
                                    "type": "array",
                                    "items": {
                                        "type": "string",
                                    },
                                },
                                "confidence": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                },
                            },
                            "required": [
                                "decision",
                                "selectedIndex",
                                "incidentSummary",
                                "reasoning",
                                "riskNotes",
                                "verificationFocus",
                                "confidence",
                            ],
                            "additionalProperties": False,
                        },
                    }
                },
            )
        )

        outputText = (
            response.output_text
        )

        if not outputText:
            raise RuntimeError(
                "LLM returned no reasoning output."
            )

        return json.loads(
            outputText
        )

    # ======================================================
    # EVIDENCE
    # ======================================================

    def _buildEvidence(
        self,
        incident,
        choices,
        environmentState,
        attemptHistory,
    ):
        candidateEvidence = []

        for index, choice in enumerate(
            choices
        ):
            candidateEvidence.append({
                "index": index,

                "incidentId": (
                    choice.get(
                        "incidentId"
                    )
                ),

                "historicalTitle": (
                    choice.get(
                        "title",
                        ""
                    )
                ),

                "action": (
                    choice.get(
                        "action",
                        ""
                    )
                ),

                "sourceType": (
                    choice.get(
                        "sourceType",
                        "historical-incident",
                    )
                ),

                "historicalOutcomeAvailable": (
                    choice.get(
                        "historicalOutcomeAvailable",
                        True,
                    )
                ),

                "similarity": (
                    choice.get(
                        "similarity",
                        0,
                    )
                ),

                "successRate": (
                    choice.get(
                        "successRate"
                    )
                ),

                "successRateIsConditioned": (
                    choice.get(
                        "successRateIsConditioned",
                        False,
                    )
                ),

                "riskTier": (
                    choice.get(
                        "riskTier",
                        "unknown",
                    )
                ),

                "riskScore": (
                    choice.get(
                        "riskScore",
                        0,
                    )
                ),

                "deterministicScore": (
                    choice.get(
                        "score",
                        0,
                    )
                ),

                "rootCause": (
                    choice.get(
                        "rootCause",
                        "",
                    )
                ),

                "steps": (
                    choice.get(
                        "steps",
                        [],
                    )
                ),

                "verificationFocus": (
                    choice.get(
                        "verificationFocus",
                        [],
                    )
                ),
            })

        sanitizedAttempts = []

        for attempt in attemptHistory:
            sanitizedAttempts.append({
                "action": (
                    attempt.get(
                        "action",
                        ""
                    )
                ),
                "result": (
                    attempt.get(
                        "result",
                        ""
                    )
                ),
                "note": (
                    attempt.get(
                        "note",
                        ""
                    )
                ),
            })

        return {
            "incident": {
                "incidentId": (
                    incident.get(
                        "incidentId"
                    )
                ),
                "title": (
                    incident.get(
                        "title",
                        ""
                    )
                ),
                "description": (
                    incident.get(
                        "description",
                        ""
                    )
                ),
                "priority": (
                    incident.get(
                        "priority"
                    )
                ),
                "status": (
                    incident.get(
                        "status"
                    )
                ),
            },

            "currentEnvironmentState": (
                environmentState
            ),

            "previousAttempts": (
                sanitizedAttempts
            ),

            "candidateStrategies": (
                candidateEvidence
            ),

            "decisionConstraint": (
                "Select only a candidate index "
                "listed above, or escalate."
            ),
        }

    # ======================================================
    # MODEL OUTPUT VALIDATION
    # ======================================================

    def _validateDecision(
        self,
        modelResult,
        choices,
    ):
        decision = modelResult.get(
            "decision"
        )

        if decision == "ESCALATE":
            return {
                "llmUsed": True,
                "decision": "ESCALATE",
                "selectedIndex": -1,
                "selectedChoice": None,
                "incidentSummary": (
                    modelResult.get(
                        "incidentSummary",
                        "",
                    )
                ),
                "reasoning": (
                    modelResult.get(
                        "reasoning",
                        "",
                    )
                ),
                "riskNotes": (
                    modelResult.get(
                        "riskNotes",
                        "",
                    )
                ),
                "verificationFocus": (
                    modelResult.get(
                        "verificationFocus",
                        [],
                    )
                ),
                "confidence": (
                    self._normalizeConfidence(
                        modelResult.get(
                            "confidence",
                            0,
                        )
                    )
                ),
                "model": self.model,
            }

        if decision != "USE_CANDIDATE":
            return self._fallbackResult(
                choices,
                reason=(
                    "LLM returned an invalid decision."
                ),
            )

        selectedIndex = modelResult.get(
            "selectedIndex"
        )

        if (
            not isinstance(
                selectedIndex,
                int,
            )
            or selectedIndex < 0
            or selectedIndex >= len(
                choices
            )
        ):
            return self._fallbackResult(
                choices,
                reason=(
                    "LLM selected an invalid "
                    "candidate index."
                ),
            )

        # CRITICAL SAFETY PROPERTY:
        #
        # The trusted recovery action comes from our
        # candidate list, never from generated model text.
        selectedChoice = (
            choices[selectedIndex]
        )

        return {
            "llmUsed": True,
            "decision": (
                "USE_CANDIDATE"
            ),
            "selectedIndex": (
                selectedIndex
            ),
            "selectedChoice": (
                selectedChoice
            ),
            "incidentSummary": (
                modelResult.get(
                    "incidentSummary",
                    "",
                )
            ),
            "reasoning": (
                modelResult.get(
                    "reasoning",
                    "",
                )
            ),
            "riskNotes": (
                modelResult.get(
                    "riskNotes",
                    "",
                )
            ),
            "verificationFocus": (
                modelResult.get(
                    "verificationFocus",
                    [],
                )
            ),
            "confidence": (
                self._normalizeConfidence(
                    modelResult.get(
                        "confidence",
                        0,
                    )
                )
            ),
            "model": self.model,
        }

    # ======================================================
    # SAFE FALLBACKS
    # ======================================================

    def _fallbackResult(
        self,
        choices,
        reason,
    ):
        """
        Deterministic fail-safe.

        If the LLM is missing, unavailable, malformed,
        rate-limited, or otherwise fails, ReSolve continues
        to use the already-ranked RecoveryMemory result.
        """

        if not choices:
            return self._escalationResult(
                reason
            )

        return {
            "llmUsed": False,
            "decision": (
                "USE_CANDIDATE"
            ),
            "selectedIndex": 0,
            "selectedChoice": (
                choices[0]
            ),
            "incidentSummary": "",
            "reasoning": reason,
            "riskNotes": (
                "Existing deterministic risk "
                "controls remain authoritative."
            ),
            "verificationFocus": [],
            "confidence": 0,
            "model": None,
        }

    def _escalationResult(
        self,
        reason,
    ):
        return {
            "llmUsed": False,
            "decision": "ESCALATE",
            "selectedIndex": -1,
            "selectedChoice": None,
            "incidentSummary": "",
            "reasoning": reason,
            "riskNotes": "",
            "verificationFocus": [],
            "confidence": 0,
            "model": None,
        }

    def _normalizeConfidence(
        self,
        value,
    ):
        try:
            value = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            return 0

        return max(
            0,
            min(
                1,
                value,
            ),
        )