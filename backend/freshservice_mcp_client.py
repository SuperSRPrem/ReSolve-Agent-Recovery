import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# --------------------------------------------------
# Load environment variables
# --------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)


class FreshserviceMCPClient:
    """
    Generic wrapper around the Freshservice MCP server.

    This class knows nothing about ReSolve recovery logic.

    Its responsibility is only:

        Python
            ↓
        MCP server
            ↓
        Freshservice API
    """

    def __init__(self, apiKey=None, domain=None):

        self.apiKey = (
            apiKey
            or os.getenv("FRESHSERVICE_APIKEY")
        )

        self.domain = (
            domain
            or os.getenv("FRESHSERVICE_DOMAIN")
        )

        if not self.apiKey:
            raise ValueError(
                "FRESHSERVICE_APIKEY is missing. "
                f"Check {ENV_PATH}"
            )

        if not self.domain:
            raise ValueError(
                "FRESHSERVICE_DOMAIN is missing. "
                f"Check {ENV_PATH}"
            )

    # ==================================================
    # MCP SERVER CONFIGURATION
    # ==================================================

    def _serverParams(self):

        env = os.environ.copy()

        env.update({
            "FRESHSERVICE_APIKEY": self.apiKey,
            "FRESHSERVICE_DOMAIN": self.domain
        })

        return StdioServerParameters(
            command="uvx",
            args=[
                "--with",
                "mcp==1.9.4",
                "freshservice-mcp"
            ],
            env=env
        )

    # ==================================================
    # MCP SESSION
    # ==================================================

    async def _run(self, work):

        params = self._serverParams()

        async with stdio_client(
            params
        ) as (read, write):

            async with ClientSession(
                read,
                write
            ) as session:

                await session.initialize()

                return await work(session)

    def run(self, work):

        return asyncio.run(
            self._run(work)
        )

    # ==================================================
    # TOOL DISCOVERY
    # ==================================================

    def listAvailableTools(self):

        async def _work(session):

            result = await session.list_tools()

            return [
                {
                    "name": tool.name,
                    "description": tool.description
                }
                for tool in result.tools
            ]

        return self.run(_work)

    # ==================================================
    # TOOL SCHEMA
    # ==================================================

    def getToolSchema(self, toolName):

        async def _work(session):

            result = await session.list_tools()

            for tool in result.tools:

                if tool.name == toolName:

                    return {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.input_schema
                    }

            return None

        return self.run(_work)

    # ==================================================
    # GENERIC TOOL EXECUTION
    # ==================================================

    def callTool(self, toolName, arguments=None):

        arguments = arguments or {}

        async def _work(session):

            result = await session.call_tool(
                toolName,
                arguments
            )

            return self._normalizeResult(
                toolName,
                result
            )

        return self.run(_work)

    # ==================================================
    # RESULT NORMALIZATION
    # ==================================================

    def _normalizeResult(
        self,
        toolName,
        result
    ):
        """
        Converts MCP CallToolResult into a normal Python dict.

        MCP tools can return:

            structured_content

        or:

            content = [
                TextContent(...)
            ]

        The Freshservice MCP server currently returns
        JSON inside TextContent, so we parse that here.
        """

        response = {
            "success": True,
            "tool": toolName,
            "data": None
        }

        # --------------------------------------------------
        # MCP-level error
        # --------------------------------------------------

        if getattr(result, "is_error", False):

            response["success"] = False

        # --------------------------------------------------
        # Structured content
        # --------------------------------------------------

        structuredContent = getattr(
            result,
            "structured_content",
            None
        )

        if structuredContent is not None:

            response["data"] = structuredContent

            if isinstance(structuredContent, dict) and (
                "error" in structuredContent
                or structuredContent.get("code")
                in [
                    "access_denied",
                    "authentication_failed"
                ]
            ):
                response["success"] = False

            return response

        # --------------------------------------------------
        # Text content
        # --------------------------------------------------

        content = getattr(
            result,
            "content",
            None
        )

        if not content:

            response["data"] = {}

            return response

        parsedItems = []

        for item in content:

            text = getattr(
                item,
                "text",
                None
            )

            if text is None:
                continue

            try:

                parsed = json.loads(text)

            except (
                json.JSONDecodeError,
                TypeError
            ):

                parsed = text

            parsedItems.append(parsed)

        # --------------------------------------------------
        # Simplify single result
        # --------------------------------------------------

        if len(parsedItems) == 1:

            response["data"] = parsedItems[0]

        else:

            response["data"] = parsedItems

        # --------------------------------------------------
        # Detect API-level error payloads
        # --------------------------------------------------

        if isinstance(
            response["data"],
            dict
        ):

            if (
                "error" in response["data"]
                or "code" in response["data"]
                and response["data"].get("code")
                in [
                    "access_denied",
                    "authentication_failed"
                ]
            ):

                response["success"] = False

        return response
