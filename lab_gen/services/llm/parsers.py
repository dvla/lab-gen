from typing import Any

from langchain_core.exceptions import OutputParserException
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts.prompt import PromptTemplate
from langchain_core.pydantic_v1 import ValidationError
from loguru import logger


STRICT_FIX = """You must output formatted JSON.
Look at the supplied Error and change the Completion json to match the Instructions.
Remove json properties mentioned in Error. All other properties should not be changed because they are valid.
If a nested object has a required field that is missing then remove the surrounding object.
Instructions:
--------------
{instructions}
--------------
Completion:
--------------
{completion}
--------------

Above, the Completion did not satisfy the constraints given in the Instructions.
Error:
--------------
{error}
--------------

Please try again. Please only respond with an answer that satisfies the constraints laid out in the Instructions:"""


class StrictJsonOutputParser(JsonOutputParser):
    """This class is a strict implementation of the JsonOutputParser class."""
    prompt = PromptTemplate.from_template(STRICT_FIX)

    def get_format_instructions(self) -> str:
        """
        Returns the format instructions for parsing.

        :return: A string containing the format instructions.
        """
        return super().get_format_instructions()

    def parse(self, to_parse: Any) -> Any:  # noqa: ANN401
        """
        Parses the input data and returns the parsed JSON.

        Args:
            to_parse (Any): The data to be parsed.

        Returns:
            Any: The parsed JSON.

        Raises:
            OutputParserException: If the input data is invalid JSON.
        """
        try:
            json_to_parse = to_parse
            if isinstance(to_parse, AIMessage) and to_parse.content:
                json_to_parse = to_parse.content
            if isinstance(json_to_parse, str):
                json_to_parse = super().parse(json_to_parse)
            self.pydantic_object.parse_obj(json_to_parse)
            return json_to_parse  # noqa: TRY300
        except ValidationError as pe:
            msg = f"Invalid json: {pe!s}"
            logger.info(msg)
            raise OutputParserException(msg) from None
