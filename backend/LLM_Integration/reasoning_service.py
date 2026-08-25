from backend.LLM_Integration.incident_extractor import (
    IncidentExtractor
)

from backend.LLM_Integration.resolution_extractor import (
    ResolutionExtractor
)


class ReasoningService:
    """
    Central entry point for the LLM reasoning layer.

    Responsibilities:

        - understand a current incident
        - extract structured information from a current
          incident
        - understand historical incident resolutions
        - extract structured resolution knowledge

    This service does NOT:

        - rank recovery strategies
        - calculate similarity
        - calculate success rates
        - assign risk tiers
        - approve actions
        - execute actions

    Those responsibilities remain in the existing
    deterministic ReSolve recovery system.
    """

    def __init__(
        self,
        incidentExtractor=None,
        resolutionExtractor=None
    ):

        self.incidentExtractor = (
            incidentExtractor
            or IncidentExtractor()
        )

        self.resolutionExtractor = (
            resolutionExtractor
            or ResolutionExtractor()
        )

    # ==================================================
    # CURRENT INCIDENT UNDERSTANDING
    # ==================================================

    def understandIncident(
        self,
        incident
    ):
        """
        Converts an unstructured current incident into
        structured incident information.
        """

        result = (
            self.incidentExtractor.extract(
                incident
            )
        )

        if not result.get(
            "success",
            False
        ):

            return {
                "success": False,
                "type": "incident",
                "data": None,
                "error": result.get(
                    "error"
                ),
                "rawResponse": result.get(
                    "rawResponse"
                )
            }

        return {
            "success": True,
            "type": "incident",
            "data": result.get(
                "data"
            ),
            "error": None,
            "rawResponse": result.get(
                "rawResponse"
            )
        }

    # ==================================================
    # HISTORICAL RESOLUTION UNDERSTANDING
    # ==================================================

    def understandResolution(
        self,
        incident
    ):
        """
        Extracts structured resolution knowledge from
        a historical incident.
        """

        result = (
            self.resolutionExtractor.extract(
                incident
            )
        )

        if not result.get(
            "success",
            False
        ):

            return {
                "success": False,
                "type": "resolution",
                "data": None,
                "error": result.get(
                    "error"
                ),
                "rawResponse": result.get(
                    "rawResponse"
                )
            }

        return {
            "success": True,
            "type": "resolution",
            "data": result.get(
                "data"
            ),
            "error": None,
            "rawResponse": result.get(
                "rawResponse"
            )
        }

    # ==================================================
    # FULL HISTORICAL INCIDENT UNDERSTANDING
    # ==================================================

    def understandHistoricalIncident(
        self,
        incident
    ):
        """
        Extracts both:

            - incident information
            - resolution information

        from a historical incident record.

        This is useful later when historical Freshservice
        tickets are ingested into ReSolve.
        """

        incidentResult = (
            self.understandIncident(
                incident
            )
        )

        resolutionResult = (
            self.understandResolution(
                incident
            )
        )

        success = (
            incidentResult["success"]
            and resolutionResult["success"]
        )

        return {
            "success": success,

            "incident": incidentResult,

            "resolution": resolutionResult,

            "error": (
                None
                if success
                else {
                    "incident": incidentResult.get(
                        "error"
                    ),
                    "resolution": resolutionResult.get(
                        "error"
                    )
                }
            )
        }