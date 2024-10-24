from pathlib import Path
from typing import Any

import requests

from langchain.output_parsers import OutputFixingParser
from langchain.prompts import PromptTemplate
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers.base import BaseOutputParser
from loguru import logger

from lab_gen.datatypes.models import Model, ModelFamily, ModelProvider, ModelVariant
from lab_gen.services.llm.lifetime import get_llm, init_models


INPUT_FILE = Path(__file__).resolve().parent / "input_gherkin.txt"
STATUS_CODE_500 = 500
# Initialize models
init_models()
llm = get_llm(Model.compute_key(ModelProvider.AZURE, ModelVariant.ADVANCED, ModelFamily.GPT))

# Define prompt templates
fix_document_template = PromptTemplate(
    input_variables=["completion"],
    template="""You must output a correctly formatted Gherkin document.
Look at the supplied linting issues and modify the Completion to match the required syntax.
Remove any parts of the document that are incorrect or incomplete as per the linting rules provided.
Do not change any valid syntax or content.
If a required field is missing in the Gherkin structure, make sure to remove the surrounding structure.
Do not output any gherkin markdown tags or backticks.
Instructions:
--------------
{instructions}
--------------
Completion:
--------------
{completion}
--------------

Above, the Completion did not meet the linting rules and contains the following issues:
Error:
--------------
{error}
--------------

Please try again. Provide a corrected Gherkin document that adheres to the above Instructions.""",
)


fix_lint_template = PromptTemplate(
    input_variables=["completion", "instructions"],
    template="""Fix the following linting issues in the Gherkin document:

{instructions}

Here are the specific rules to follow:
1. Add a description to the Feature, explaining its importance and value.
2. Remove any full stops (periods) at the end of steps.
3. Ensure all Gherkin syntax keywords (Feature, Scenario, Given, When, Then, And, But) are present
   and correctly formatted with colons after each one.
4. Do not output any gherkin markdown tags or backticks.

Original document:
{completion}

Please provide the corrected Gherkin document that addresses all these issues.""",
)


def send_lint_request(gherkin_doc: str) -> requests.Response:
    """
    Send a POST request to the linting API with the given Gherkin document.

    Args:
        gherkin_doc (str): The Gherkin document to lint.

    Returns:
        requests.Response: The response from the linting API.

    Raises:
        OutputParserException: If the response status code is not 200.
    """
    url = "http://0.0.0.0:9292/lint"
    payload = {"gherkin": gherkin_doc}
    return requests.post(url, json=payload, timeout = 30)




class LintingParser(BaseOutputParser):
    """
    Parser to handle Gherkin linting by sending the document to the linting API.

    Methods:
        parse: Parse the Gherkin document and return the response and the document.
    """

    def parse(self, gherkin_doc: Any) -> Any:  # noqa: ANN401
        """
        Send the Gherkin document for linting and handle errors.

        Args:
            gherkin_doc (Any): The Gherkin document to parse.

        Returns:
            Tuple[requests.Response, str]: The response from the linting API and the original Gherkin document.

        Raises:
            OutputParserException: If the response status code is 500.
        """
        response = send_lint_request(gherkin_doc)
        logger.info(response)
        if response.status_code == STATUS_CODE_500:
            logger.error(f"BAD GHERKIN ERROR {response.status_code}")
            raise OutputParserException(response.json()) from None
        return response, gherkin_doc


class FixingParser(BaseOutputParser):
    """
    Parser to handle fixing Gherkin linting issues by sending the document to the linting API.

    Methods:
        parse: Parse the Gherkin document and return the fixed document.
    """
    lint_issues: list[Any]

    def get_format_instructions(self) -> Any:  # noqa: ANN401
        """
        Returns the format instructions for parsing.

        :return: A string containing the format instructions.
        """
        return self.lint_issues

    def parse(self, gherkin_doc: Any) -> Any:  # noqa: ANN401
        """
        Send the Gherkin document for linting and raise an error if issues are found.

        Args:
            gherkin_doc (Any): The Gherkin document to parse.

        Returns:
            str: The Gherkin document if no issues are found.

        Raises:
            OutputParserException: If linting issues are found.
        """
        response = send_lint_request(gherkin_doc)
        try:
            issues = response.json()
            if issues:
                self.lint_issues = issues
                raise OutputParserException(issues)
        except requests.exceptions.JSONDecodeError:
            logger.error("Failed to decode JSON from linting response")
            msg = "Invalid response from linting service"
            raise OutputParserException(msg) from None
        else:
            return gherkin_doc

def get_gherkin_document(file_path: Path) -> str | None:
    """
    Read the Gherkin document from the specified file path.

    Args:
        file_path (str): Path to the Gherkin document file.

    Returns:
        str | None: The contents of the Gherkin document, or None if the file is not found.
    """
    try:
        with Path.open(file_path) as file:
            return file.read()
    except FileNotFoundError:
        logger.error("Input file not found.")
        return None


def process_gherkin_document() -> None:
    """
    Process the Gherkin document by checking linting issues and fixing them if needed.

    Attempts to fix linting issues up to a maximum number of retries.
    """
    gherkin_doc = get_gherkin_document(INPUT_FILE)
    if gherkin_doc is None:
        return

    lint_parser = LintingParser()

    try:
        linting_parser = OutputFixingParser.from_llm(
            llm=llm,
            parser=lint_parser,
            prompt=fix_document_template,
            max_retries=5,
        )
        lint_response, gherkin_doc = linting_parser.parse(gherkin_doc)
        lint_ret_response = lint_response.json()
        logger.info(f"Linting issues: {lint_ret_response}")

        if not lint_ret_response:
            logger.info("No linting issues found. Document is correct.")
            logger.info(f"Final Gherkin document:\n{gherkin_doc}")
            return

        logger.info("Linting issues found. Attempting to fix...")
        fix_parser = FixingParser(lint_issues=lint_ret_response)
        fixing_parser = OutputFixingParser.from_llm(
            llm=llm,
            parser=fix_parser,
            prompt=fix_lint_template,
            max_retries=5,
        )
        gherkin_doc = fixing_parser.parse(gherkin_doc)
        logger.info("Document fixed successfully.")
        logger.info(f"Final Gherkin document:\n{gherkin_doc}")
    except OutputParserException as e:
        logger.error(f"Failed to process Gherkin document: {e}")
    except Exception as e:  # noqa: BLE001
        logger.error(f"Unexpected error occurred: {e}")


def techlab_header() -> None:
    """Display the jar with a gherkin and the application header side by side."""
    logger.info(r"""
      ___                   _______        _    _     _____  _____
    .'   '.                |__   __|      | |  | |   |    | |     |
   / _   _ \                  | | ___  ___| |_ | |   |____| |_____|
  | (_) (_) |                 | |  __/|   |   || |___|    | |     |
  |         |                 |_|\___||___|   ||_____|    | |_____|
   \       /
    '.___.'

    """)


def main_menu() -> str:
    """
    Display the main menu options and return the user's choice.

    Returns:
        str: The user's choice as a string.
    """
    logger.info("1. Lint Gherkin Document")
    logger.info("2. Exit")
    return input("Choose an option: ")


def main() -> None:
    """Main function to drive the application by displaying the menu and processing user input."""
    while True:
        techlab_header()
        choice = main_menu()

        if choice == "1":
            logger.info("Processing Gherkin document...")
            process_gherkin_document()
        elif choice == "2":
            logger.info("Exiting the application.")
            break
        else:
            logger.error("Invalid choice. Please choose 1 or 2.")


if __name__ == "__main__":
    main()
