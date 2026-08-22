import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# Load .env from project root
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)


class FreshserviceMCPClient:

    def __init__(self, apiKey=None, domain=None):
        self.apiKey = apiKey or os.getenv("FRESHSERVICE_APIKEY")
        self.domain = domain or os.getenv("FRESHSERVICE_DOMAIN")

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

    def _serverParams(self):
        # Keep the normal Windows environment and add Freshservice variables
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

    async def _run(self, work):
        params = self._serverParams()

        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:

                await session.initialize()

                return await work(session)

    def run(self, work):
        return asyncio.run(self._run(work))

    def listAvailableTools(self):

        async def _work(session):
            result = await session.list_tools()

            return [
                (tool.name, tool.description)
                for tool in result.tools
            ]

        return self.run(_work)