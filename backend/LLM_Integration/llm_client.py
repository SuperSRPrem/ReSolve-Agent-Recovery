import os

from dotenv import load_dotenv
from google import genai


load_dotenv()


class LLMClient:
    """
    Provider-specific client for communicating with
    the Gemini API.

    The rest of the ReSolve system should not directly
    depend on Gemini.

    Future extractors communicate only through this
    class.
    """

    def __init__(
        self,
        model="gemini-3.6-flash"
    ):

        self.apiKey = os.getenv(
            "GEMINI_API_KEY"
        )

        if not self.apiKey:

            raise ValueError(
                "GEMINI_API_KEY is not set. "
                "Add it to your .env file."
            )

        self.client = genai.Client(
            api_key=self.apiKey
        )

        self.model = model

    def generate(
        self,
        prompt,
        temperature=0.2
    ):
        """
        Sends a prompt to Gemini and returns
        the generated text.

        The caller is responsible for interpreting
        the response.
        """

        try:

            response = (
                self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config={
                        "temperature": temperature
                    }
                )
            )

            if not response:

                return {
                    "success": False,
                    "text": "",
                    "error": (
                        "Gemini returned no response."
                    )
                }

            text = getattr(
                response,
                "text",
                None
            )

            if not text:

                return {
                    "success": False,
                    "text": "",
                    "error": (
                        "Gemini returned an empty response."
                    )
                }

            return {
                "success": True,
                "text": text.strip(),
                "error": None
            }

        except Exception as error:

            return {
                "success": False,
                "text": "",
                "error": str(error)
            }