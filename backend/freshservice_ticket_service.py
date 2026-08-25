import ast
import json

from backend.freshservice_mcp_client import (
    FreshserviceMCPClient,
)


class FreshserviceTicketService:
    """
    High-level Freshservice ticket operations.

    This class hides raw MCP tool names and MCP response
    structures from the rest of ReSolve.

    Every public method returns:

        {
            "success": True / False,
            "tool": "...",
            "data": ...,
            "error": None / "..."
        }
    """

    def __init__(
        self,
        client=None,
    ):
        self.client = (
            client
            or FreshserviceMCPClient()
        )

    # ==================================================
    # RESPONSE NORMALIZATION
    # ==================================================

    def _normalizeResponse(
        self,
        response,
        toolName,
    ):
        """
        Converts raw MCP responses into a predictable format.

        Important:

        Some Freshservice MCP tools can return:

            {
                "success": True,
                "data": "Error: ..."
            }

        ReSolve must not treat that as a successful operation.
        """

        if response is None:
            return {
                "success": False,
                "tool": toolName,
                "data": None,
                "error": (
                    "Freshservice returned no response."
                ),
            }

        # ==================================================
        # ALREADY-NORMALIZED DICTIONARY
        # ==================================================

        if isinstance(
            response,
            dict,
        ):
            if "success" in response:
                normalized = dict(
                    response
                )

                normalized.setdefault(
                    "tool",
                    toolName,
                )

                normalized.setdefault(
                    "data",
                    None,
                )

                normalized.setdefault(
                    "error",
                    None,
                )

                # MCP wrappers sometimes put a Python
                # dictionary inside a success string.
                normalized["data"] = (
                    self._normalizeDataPayload(
                        normalized.get(
                            "data"
                        )
                    )
                )

                detectedError = (
                    normalized.get(
                        "error"
                    )
                    or self._extractError(
                        normalized.get(
                            "data"
                        )
                    )
                )

                if detectedError:
                    normalized[
                        "success"
                    ] = False

                    normalized[
                        "error"
                    ] = detectedError

                return normalized

            # Raw dictionary response.
            detectedError = (
                self._extractError(
                    response
                )
            )

            return {
                "success": (
                    detectedError is None
                ),
                "tool": toolName,
                "data": response,
                "error": detectedError,
            }

        # ==================================================
        # MCP CallToolResult
        # ==================================================

        isError = getattr(
            response,
            "is_error",
            False,
        )

        content = getattr(
            response,
            "content",
            None,
        )

        if content:
            parsedContent = []

            for item in content:
                text = getattr(
                    item,
                    "text",
                    None,
                )

                if text is None:
                    continue

                parsedContent.append(
                    self._normalizeDataPayload(
                        self._parseTextContent(
                            text
                        )
                    )
                )

            if len(
                parsedContent
            ) == 1:
                data = parsedContent[0]

            else:
                data = parsedContent

            error = (
                self._extractError(
                    data
                )
            )

            if (
                isError
                or error
            ):
                return {
                    "success": False,
                    "tool": toolName,
                    "data": data,
                    "error": (
                        error
                        or (
                            "Freshservice MCP tool "
                            "execution failed."
                        )
                    ),
                }

            return {
                "success": True,
                "tool": toolName,
                "data": data,
                "error": None,
            }

        # ==================================================
        # STRUCTURED MCP CONTENT
        # ==================================================

        structuredContent = getattr(
            response,
            "structured_content",
            None,
        )

        if (
            structuredContent
            is not None
        ):
            detectedError = (
                self._extractError(
                    structuredContent
                )
            )

            if (
                isError
                or detectedError
            ):
                return {
                    "success": False,
                    "tool": toolName,
                    "data": structuredContent,
                    "error": (
                        detectedError
                        or (
                            "Freshservice MCP tool "
                            "execution failed."
                        )
                    ),
                }

            return {
                "success": True,
                "tool": toolName,
                "data": structuredContent,
                "error": None,
            }

        # ==================================================
        # FINAL FALLBACK
        # ==================================================

        text = str(
            response
        )

        detectedError = (
            self._extractError(
                text
            )
        )

        return {
            "success": (
                not isError
                and detectedError is None
            ),
            "tool": toolName,
            "data": text,
            "error": (
                detectedError
                or (
                    "Freshservice MCP tool "
                    "execution failed."
                    if isError
                    else None
                )
            ),
        }

    # ==================================================
    # TEXT / PAYLOAD PARSING
    # ==================================================

    def _parseTextContent(
        self,
        text,
    ):
        """
        Freshservice MCP tools frequently return JSON
        inside TextContent.
        """

        if not isinstance(
            text,
            str,
        ):
            return text

        cleanedText = (
            text.strip()
        )

        if not cleanedText:
            return ""

        try:
            return json.loads(
                cleanedText
            )

        except json.JSONDecodeError:
            return cleanedText

    def _normalizeDataPayload(
        self,
        data,
    ):
        """
        Normalizes MCP payloads.

        Example MCP response:

            "Ticket created successfully:
             {'ticket': {'id': 6, ...}}"

        That is not JSON, but the payload after the prefix
        is a safe Python literal. Parse it so callers receive
        a normal dictionary and can access the ticket ID.
        """

        if not isinstance(
            data,
            str,
        ):
            return data

        text = data.strip()

        if not text:
            return text

        # First attempt normal JSON.
        try:
            return json.loads(
                text
            )

        except json.JSONDecodeError:
            pass

        # MCP package currently returns successful ticket
        # operations using strings containing Python dicts.
        lowered = text.lower()

        if (
            "successfully:"
            in lowered
        ):
            markerIndex = (
                lowered.find(
                    "successfully:"
                )
            )

            payload = text[
                markerIndex
                + len("successfully:")
                :
            ].strip()

            if payload:
                try:
                    parsed = (
                        ast.literal_eval(
                            payload
                        )
                    )

                    if isinstance(
                        parsed,
                        (
                            dict,
                            list,
                        ),
                    ):
                        return parsed

                except (
                    ValueError,
                    SyntaxError,
                ):
                    pass

        return text

    # ==================================================
    # ERROR DETECTION
    # ==================================================

    def _extractError(
        self,
        data,
    ):
        """
        Detects errors in structured and string MCP payloads.
        """

        if isinstance(
            data,
            str,
        ):
            text = data.strip()

            lowered = (
                text.lower()
            )

            # The Freshservice MCP package can return an error
            # as ordinary text while still wrapping the call
            # inside success=True.
            if lowered.startswith(
                "error:"
            ):
                return text

            if lowered.startswith(
                "error "
            ):
                return text

            if lowered.startswith(
                "failed:"
            ):
                return text

            if (
                "bad request"
                in lowered
                and (
                    "400"
                    in lowered
                )
            ):
                return text

            if (
                "unauthorized"
                in lowered
                and (
                    "401"
                    in lowered
                )
            ):
                return text

            if (
                "forbidden"
                in lowered
                and (
                    "403"
                    in lowered
                )
            ):
                return text

            return None

        if isinstance(
            data,
            dict,
        ):
            if data.get(
                "error"
            ):
                return str(
                    data[
                        "error"
                    ]
                )

            if (
                data.get(
                    "message"
                )
                and (
                    data.get(
                        "code"
                    )
                    or data.get(
                        "status"
                    )
                    or data.get(
                        "statusCode"
                    )
                )
            ):
                return str(
                    data[
                        "message"
                    ]
                )

            if data.get(
                "code"
            ) in [
                "access_denied",
                "unauthorized",
                "forbidden",
                "not_found",
            ]:
                return str(
                    data.get(
                        "message",
                        data[
                            "code"
                        ],
                    )
                )

            # Inspect nested structures as well.
            for value in (
                data.values()
            ):
                nestedError = (
                    self._extractError(
                        value
                    )
                )

                if nestedError:
                    return nestedError

            return None

        if isinstance(
            data,
            list,
        ):
            for value in data:
                nestedError = (
                    self._extractError(
                        value
                    )
                )

                if nestedError:
                    return nestedError

        return None

    # ==================================================
    # INTERNAL MCP CALL
    # ==================================================

    def _call(
        self,
        toolName,
        arguments=None,
    ):
        try:
            response = (
                self.client.callTool(
                    toolName,
                    arguments
                    or {},
                )
            )

            return (
                self._normalizeResponse(
                    response,
                    toolName,
                )
            )

        except Exception as error:
            return {
                "success": False,
                "tool": toolName,
                "data": None,
                "error": str(
                    error
                ),
            }

    # ==================================================
    # FETCH TICKETS
    # ==================================================

    def getTickets(
        self,
        page=1,
        perPage=30,
    ):
        return self._call(
            "get_tickets",
            {
                "page": page,
                "per_page": perPage,
            },
        )

    def getTicket(
        self,
        ticketId,
    ):
        return self._call(
            "get_ticket_by_id",
            {
                "ticket_id": (
                    ticketId
                ),
            },
        )

    # ==================================================
    # CONVERSATIONS
    # ==================================================

    def getConversations(
        self,
        ticketId,
    ):
        return self._call(
            "list_all_ticket_conversation",
            {
                "ticket_id": (
                    ticketId
                ),
            },
        )

    # ==================================================
    # NOTES
    # ==================================================

    def addNote(
        self,
        ticketId,
        body,
    ):
        return self._call(
            "create_ticket_note",
            {
                "ticket_id": (
                    ticketId
                ),
                "body": body,
            },
        )

    # ==================================================
    # UPDATE TICKET
    # ==================================================

    def updateTicket(
        self,
        ticketId,
        ticketFields,
    ):
        return self._call(
            "update_ticket",
            {
                "ticket_id": (
                    ticketId
                ),
                "ticket_fields": (
                    ticketFields
                ),
            },
        )

    # ==================================================
    # RESOLVE TICKET
    # ==================================================

    def resolveTicket(
        self,
        ticketId,
        resolutionNotes=None,
    ):
        """
        Freshservice status:

            4 = Resolved
            5 = Closed

        Freshservice may require resolution notes when
        resolving a ticket.

        ReSolve therefore always provides a resolution note
        with the status transition.
        """

        if not resolutionNotes:
            resolutionNotes = (
                "Resolved by ReSolve after the recovery "
                "action completed and independent "
                "post-recovery verification confirmed "
                "that the expected service state was "
                "restored."
            )

        return self.updateTicket(
            ticketId,
            {
                "status": 4,
                "resolution_notes": (
                    resolutionNotes
                ),
            },
        )

    # ==================================================
    # CREATE TICKET
    # ==================================================

    def createTicket(
        self,
        subject,
        description,
        source=2,
        priority=3,
        status=2,
        email=None,
        requesterId=None,
        customFields=None,
    ):
        arguments = {
            "subject": subject,
            "description": (
                description
            ),
            "source": source,
            "priority": priority,
            "status": status,
        }

        if email is not None:
            arguments[
                "email"
            ] = email

        if (
            requesterId
            is not None
        ):
            arguments[
                "requester_id"
            ] = requesterId

        if (
            customFields
            is not None
        ):
            arguments[
                "custom_fields"
            ] = customFields

        return self._call(
            "create_ticket",
            arguments,
        )