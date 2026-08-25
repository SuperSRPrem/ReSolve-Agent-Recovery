import re


class LLMOutputNormalizer:
    """
    Deterministically normalizes and validates data
    returned by the LLM extraction layer.

    This prevents raw LLM output from directly entering
    the ReSolve recovery system.
    """

    VALID_RESULTS = {
        "success",
        "failed",
        "partial",
        "unknown"
    }

    # ==================================================
    # BASIC STRING NORMALIZATION
    # ==================================================

    def _cleanString(
        self,
        value
    ):
        """
        Converts a value into a clean string.
        """

        if value is None:
            return ""

        value = str(value).strip()

        value = re.sub(
            r"\s+",
            " ",
            value
        )

        return value

    # ==================================================
    # NORMALIZE ERROR CODE
    # ==================================================

    def _normalizeErrorCode(
        self,
        value
    ):
        """
        Converts different representations of an error
        into a comparable normalized form.

        Examples:

            503
            HTTP 503
            http-503

        all become:

            HTTP_503
        """

        value = self._cleanString(
            value
        ).upper()

        if not value:
            return ""

        # Numeric HTTP status code.
        if re.fullmatch(
            r"\d{3}",
            value
        ):
            return f"HTTP_{value}"

        # HTTP 503 / HTTP-503 / HTTP_503
        match = re.fullmatch(
            r"HTTP[\s\-_]*(\d{3})",
            value
        )

        if match:
            return (
                f"HTTP_{match.group(1)}"
            )

        # Generic normalization.
        value = re.sub(
            r"[^A-Z0-9]+",
            "_",
            value
        )

        value = re.sub(
            r"_+",
            "_",
            value
        )

        return value.strip(
            "_"
        )

    # ==================================================
    # NORMALIZE ERROR CODES
    # ==================================================

    def _normalizeErrorCodes(
        self,
        errorCodes
    ):
        """
        Removes invalid and duplicate error codes.
        """

        if not isinstance(
            errorCodes,
            list
        ):
            return []

        normalizedCodes = []

        seen = set()

        for code in errorCodes:

            normalized = (
                self._normalizeErrorCode(
                    code
                )
            )

            if (
                normalized
                and normalized not in seen
            ):

                normalizedCodes.append(
                    normalized
                )

                seen.add(
                    normalized
                )

        return normalizedCodes

    # ==================================================
    # NORMALIZE STRING LIST
    # ==================================================

    def _normalizeStringList(
        self,
        values
    ):
        """
        Cleans a list of strings and removes duplicates.
        """

        if not isinstance(
            values,
            list
        ):
            return []

        normalizedValues = []

        seen = set()

        for value in values:

            cleaned = self._cleanString(
                value
            )

            if not cleaned:
                continue

            comparisonKey = (
                cleaned.lower()
            )

            if comparisonKey in seen:
                continue

            normalizedValues.append(
                cleaned
            )

            seen.add(
                comparisonKey
            )

        return normalizedValues

    # ==================================================
    # NORMALIZE ACTIONS TRIED
    # ==================================================

    def _normalizeActions(
        self,
        actions
    ):
        """
        Validates and normalizes actions already tried.
        """

        if not isinstance(
            actions,
            list
        ):
            return []

        normalizedActions = []

        seen = set()

        for item in actions:

            if not isinstance(
                item,
                dict
            ):
                continue

            action = self._cleanString(
                item.get(
                    "action"
                )
            )

            result = self._cleanString(
                item.get(
                    "result"
                )
            ).lower()

            if not action:
                continue

            if result not in self.VALID_RESULTS:
                result = "unknown"

            comparisonKey = (
                action.lower(),
                result
            )

            if comparisonKey in seen:
                continue

            normalizedActions.append(
                {
                    "action": action,
                    "result": result
                }
            )

            seen.add(
                comparisonKey
            )

        return normalizedActions

    # ==================================================
    # NORMALIZE INCIDENT DATA
    # ==================================================

    def normalizeIncident(
        self,
        data
    ):
        """
        Normalizes output from IncidentExtractor.
        """

        if not isinstance(
            data,
            dict
        ):
            data = {}

        return {
            "service": self._cleanString(
                data.get(
                    "service"
                )
            ),

            "environment": self._cleanString(
                data.get(
                    "environment"
                )
            ).lower(),

            "symptoms": (
                self._normalizeStringList(
                    data.get(
                        "symptoms",
                        []
                    )
                )
            ),

            "errorCodes": (
                self._normalizeErrorCodes(
                    data.get(
                        "errorCodes",
                        []
                    )
                )
            ),

            "actionsTried": (
                self._normalizeActions(
                    data.get(
                        "actionsTried",
                        []
                    )
                )
            ),

            "likelyRootCause": (
                self._cleanString(
                    data.get(
                        "likelyRootCause"
                    )
                )
            )
        }

    # ==================================================
    # NORMALIZE RESOLUTION DATA
    # ==================================================

    def normalizeResolution(
        self,
        data
    ):
        """
        Normalizes output from ResolutionExtractor.
        """

        if not isinstance(
            data,
            dict
        ):
            data = {}

        result = self._cleanString(
            data.get(
                "result"
            )
        ).lower()

        if result not in self.VALID_RESULTS:
            result = "unknown"

        resolutionTime = data.get(
            "resolutionTimeMinutes"
        )

        if not isinstance(
            resolutionTime,
            (int, float)
        ):

            resolutionTime = None

        elif resolutionTime < 0:

            resolutionTime = None

        return {
            "rootCause": (
                self._cleanString(
                    data.get(
                        "rootCause"
                    )
                )
            ),

            "resolutionAction": (
                self._cleanString(
                    data.get(
                        "resolutionAction"
                    )
                )
            ),

            "resolutionSteps": (
                self._normalizeStringList(
                    data.get(
                        "resolutionSteps",
                        []
                    )
                )
            ),

            "result": result,

            "resolutionTimeMinutes": (
                resolutionTime
            )
        }