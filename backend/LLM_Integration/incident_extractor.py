import json
import re

from backend.LLM_Integration.llm_client import (
    LLMClient
)


class IncidentExtractor:
    """
    Uses the LLM to convert unstructured incident text
    into a structured incident understanding.

    This class does not modify existing ReSolve incidents
    and does not execute recovery actions.

    It only performs extraction and normalization.
    """

    def __init__(
        self,
        llmClient=None
    ):

        self.llmClient = (
            llmClient
            or LLMClient()
        )

    # ==================================================
    # DEFAULT STRUCTURE
    # ==================================================

    def _defaultResult(self):

        return {
            "service": "unknown",
            "environment": "unknown",
            "symptoms": [],
            "errorCodes": [],
            "actionsTried": [],
            "likelyRootCause": ""
        }

    # ==================================================
    # BUILD PROMPT
    # ==================================================

    def _buildPrompt(
        self,
        title="",
        description="",
        conversations=None
    ):

        conversations = conversations or []

        conversationText = ""

        if conversations:

            conversationParts = []

            for conversation in conversations:

                if isinstance(
                    conversation,
                    dict
                ):

                    body = (
                        conversation.get(
                            "body_text"
                        )
                        or conversation.get(
                            "body"
                        )
                        or conversation.get(
                            "description"
                        )
                        or ""
                    )

                    if body:

                        conversationParts.append(
                            str(body)
                        )

                elif conversation:

                    conversationParts.append(
                        str(conversation)
                    )

            conversationText = "\n".join(
                conversationParts
            )

        prompt = f"""
You are an incident information extraction system.

Your job is to analyze an IT incident and extract only
information supported by the provided text.

Do not invent infrastructure, services, actions, causes,
error codes, or environments.

If information is not available, use:

- "unknown" for service or environment
- [] for lists
- "" for likelyRootCause

Return ONLY valid JSON.

Use exactly this structure:

{{
    "service": "string",
    "environment": "string",
    "symptoms": [
        "string"
    ],
    "errorCodes": [
        "string"
    ],
    "actionsTried": [
        {{
            "action": "string",
            "result": "success | failed | unknown"
        }}
    ],
    "likelyRootCause": "string"
}}

INCIDENT TITLE:
{title}

INCIDENT DESCRIPTION:
{description}

INCIDENT CONVERSATIONS:
{conversationText}
"""

        return prompt

    # ==================================================
    # CLEAN LLM RESPONSE
    # ==================================================

    def _cleanJson(
        self,
        text
    ):
        """
        Removes common markdown formatting around JSON.
        """

        if not text:
            return ""

        text = text.strip()

        text = re.sub(
            r"^```json\s*",
            "",
            text,
            flags=re.IGNORECASE
        )

        text = re.sub(
            r"^```\s*",
            "",
            text
        )

        text = re.sub(
            r"\s*```$",
            "",
            text
        )

        return text.strip()

    # ==================================================
    # NORMALIZE RESULT
    # ==================================================

    def _normalizeResult(
        self,
        data
    ):

        result = self._defaultResult()

        if not isinstance(
            data,
            dict
        ):
            return result

        # ----------------------------------------------
        # SERVICE
        # ----------------------------------------------

        service = data.get(
            "service"
        )

        if isinstance(
            service,
            str
        ) and service.strip():

            result["service"] = (
                service.strip()
            )

        # ----------------------------------------------
        # ENVIRONMENT
        # ----------------------------------------------

        environment = data.get(
            "environment"
        )

        if isinstance(
            environment,
            str
        ) and environment.strip():

            result["environment"] = (
                environment.strip()
            )

        # ----------------------------------------------
        # SYMPTOMS
        # ----------------------------------------------

        symptoms = data.get(
            "symptoms"
        )

        if isinstance(
            symptoms,
            list
        ):

            result["symptoms"] = [
                str(symptom).strip()
                for symptom in symptoms
                if str(symptom).strip()
            ]

        # ----------------------------------------------
        # ERROR CODES
        # ----------------------------------------------

        errorCodes = data.get(
            "errorCodes"
        )

        if isinstance(
            errorCodes,
            list
        ):

            result["errorCodes"] = [
                str(code).strip()
                for code in errorCodes
                if str(code).strip()
            ]

        # ----------------------------------------------
        # ACTIONS TRIED
        # ----------------------------------------------

        actionsTried = data.get(
            "actionsTried"
        )

        if isinstance(
            actionsTried,
            list
        ):

            normalizedActions = []

            for item in actionsTried:

                if not isinstance(
                    item,
                    dict
                ):
                    continue

                action = str(
                    item.get(
                        "action",
                        ""
                    )
                ).strip()

                actionResult = str(
                    item.get(
                        "result",
                        "unknown"
                    )
                ).strip().lower()

                if not action:
                    continue

                if actionResult not in [
                    "success",
                    "failed",
                    "unknown"
                ]:

                    actionResult = "unknown"

                normalizedActions.append(
                    {
                        "action": action,
                        "result": actionResult
                    }
                )

            result[
                "actionsTried"
            ] = normalizedActions

        # ----------------------------------------------
        # LIKELY ROOT CAUSE
        # ----------------------------------------------

        likelyRootCause = data.get(
            "likelyRootCause"
        )

        if isinstance(
            likelyRootCause,
            str
        ):

            result[
                "likelyRootCause"
            ] = likelyRootCause.strip()

        return result

    # ==================================================
    # EXTRACT INCIDENT
    # ==================================================

    def extract(
        self,
        title="",
        description="",
        conversations=None
    ):
        """
        Extracts structured incident information.

        Returns a stable result shape even if the LLM
        request or JSON parsing fails.
        """

        prompt = self._buildPrompt(
            title=title,
            description=description,
            conversations=conversations
        )

        llmResult = self.llmClient.generate(
            prompt
        )

        if not llmResult.get(
            "success"
        ):

            return {
                "success": False,
                "data": self._defaultResult(),
                "error": llmResult.get(
                    "error"
                ),
                "rawResponse": ""
            }

        rawText = llmResult.get(
            "text",
            ""
        )

        cleanText = self._cleanJson(
            rawText
        )

        try:

            parsedData = json.loads(
                cleanText
            )

        except (
            json.JSONDecodeError,
            TypeError
        ):

            return {
                "success": False,
                "data": self._defaultResult(),
                "error": (
                    "LLM returned invalid JSON."
                ),
                "rawResponse": rawText
            }

        normalizedData = (
            self._normalizeResult(
                parsedData
            )
        )

        return {
            "success": True,
            "data": normalizedData,
            "error": None,
            "rawResponse": rawText
        }