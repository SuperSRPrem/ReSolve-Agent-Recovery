import json
import re

from backend.LLM_Integration.llm_client import (
    LLMClient
)


class ResolutionExtractor:
    """
    Uses the LLM to extract structured resolution
    information from historical incident records.

    This does not decide which recovery strategy to use.

    It only converts unstructured historical incident
    and resolution text into structured data.
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
    # JSON EXTRACTION
    # ==================================================

    def _extractJson(
        self,
        text
    ):
        """
        Extracts JSON from an LLM response.

        Supports responses such as:

        ```json
        {
            ...
        }
        ```

        or plain JSON.
        """

        if not text:
            return None

        cleaned = text.strip()

        # Remove markdown JSON fences.
        cleaned = re.sub(
            r"^```json\s*",
            "",
            cleaned,
            flags=re.IGNORECASE
        )

        cleaned = re.sub(
            r"^```\s*",
            "",
            cleaned
        )

        cleaned = re.sub(
            r"\s*```$",
            "",
            cleaned
        )

        try:
            return json.loads(
                cleaned.strip()
            )

        except json.JSONDecodeError:
            pass

        # Fallback: find JSON object inside response.
        match = re.search(
            r"\{.*\}",
            cleaned,
            re.DOTALL
        )

        if match:

            try:
                return json.loads(
                    match.group()
                )

            except json.JSONDecodeError:
                return None

        return None

    # ==================================================
    # NORMALIZE RESULT
    # ==================================================

    def _normalizeResult(
        self,
        data
    ):
        """
        Ensures the returned structure is predictable.
        """

        if not isinstance(
            data,
            dict
        ):
            return None

        resolutionSteps = data.get(
            "resolutionSteps",
            []
        )

        if not isinstance(
            resolutionSteps,
            list
        ):
            resolutionSteps = []

        return {
            "rootCause": (
                data.get(
                    "rootCause"
                )
                or ""
            ),

            "resolutionAction": (
                data.get(
                    "resolutionAction"
                )
                or ""
            ),

            "resolutionSteps": [
                str(step)
                for step in resolutionSteps
                if step
            ],

            "result": (
                data.get(
                    "result"
                )
                or "unknown"
            ),

            "resolutionTimeMinutes": (
                data.get(
                    "resolutionTimeMinutes"
                )
            )
        }

    # ==================================================
    # EXTRACT RESOLUTION
    # ==================================================

    def extract(
        self,
        incident
    ):
        """
        Extracts structured resolution information
        from a historical incident.

        Expected input can contain fields such as:

            title
            description
            symptoms
            actionsTried
            rootCause
            resolution
            resolutionNotes
        """

        incidentText = json.dumps(
            incident,
            indent=2,
            default=str
        )

        prompt = f"""
You are an incident resolution extraction system.

Your task is to analyze the historical incident
record below and extract ONLY information that is
explicitly present or strongly supported by the record.

Do not invent missing information.

Return ONLY valid JSON.

Use exactly this structure:

{{
    "rootCause": "",
    "resolutionAction": "",
    "resolutionSteps": [],
    "result": "unknown",
    "resolutionTimeMinutes": null
}}

Rules:

- rootCause:
  The identified cause of the incident.
  Use an empty string if unknown.

- resolutionAction:
  The main action that resolved or attempted to resolve
  the incident.

- resolutionSteps:
  A chronological list of concrete steps taken.

- result:
  Must be one of:
  "success"
  "failed"
  "partial"
  "unknown"

- resolutionTimeMinutes:
  Use a number only if the incident explicitly provides
  enough information to determine it.
  Otherwise return null.

Historical Incident:

{incidentText}
"""

        response = (
            self.llmClient.generate(
                prompt
            )
        )

        if not response.get(
            "success",
            False
        ):

            return {
                "success": False,
                "data": None,
                "rawResponse": (
                    response.get(
                        "text"
                    )
                ),
                "error": response.get(
                    "error"
                )
            }

        rawResponse = response.get(
            "text",
            ""
        )

        extractedData = (
            self._extractJson(
                rawResponse
            )
        )

        normalizedData = (
            self._normalizeResult(
                extractedData
            )
        )

        if normalizedData is None:

            return {
                "success": False,
                "data": None,
                "rawResponse": rawResponse,
                "error": (
                    "Unable to parse structured "
                    "resolution information."
                )
            }

        return {
            "success": True,
            "data": normalizedData,
            "rawResponse": rawResponse,
            "error": None
        }