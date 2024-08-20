from langchain_core.exceptions import OutputParserException
from textstat import textstat

from lab_gen.datatypes.calls import Call
from lab_gen.services.llm.parsers import StrictJsonOutputParser


def reading_ease(example: str, completion: str) -> float: # noqa: ARG001
    """
    Calculate the Flesch-Kincaid Reading Ease score for a given text.

    Args:
        example (str): The text to calculate the score for.
        completion (str): The completed text to calculate the score for.

    Returns:
        float: The Flesch-Kincaid Reading Ease score.
    """
    return textstat.flesch_reading_ease(completion)

def grade_level(example: str, completion: str) -> float: # noqa: ARG001
    """
    Calculate the Flesch-Kincaid Grade Level score for a given text.

    Args:
        example (str): The text to calculate the score for.
        completion (str): The completed text to calculate the score for.

    Returns:
        float: The Flesch-Kincaid Grade Level score.
    """
    return textstat.flesch_kincaid_grade(completion)

def json_validator(example: str, completion: str) -> float: # noqa: ARG001
    """
    Validates a JSON completion against a provided example.

    Args:
        example (str): The example to validate against.
        completion (str): The completion to be validated.

    Returns:
        float: A score indicating the validity of the completion.
    """
    strict_parser = StrictJsonOutputParser(pydantic_object=Call)
    try:
        strict_parser.parse(completion)
        return 1  # noqa: TRY300
    except OutputParserException:
        return 0

def character_count_percentage(example: str, completion: str) -> float:
    """
    Calculate the percentage of characters in the completion string compared to the example string.

    Args:
        example (str): The example string.
        completion (str): The completion string.

    Returns:
        float: The percentage of characters in the completion string compared to the example string.
    """
    return len(completion) / len(example) * 100

def sentence_count_percentage(example: str, completion: str) -> float:
    """
    Calculate the percentage of sentences in the completion string compared to the example string.

    Args:
        example (str): The example string.
        completion (str): The completion string.

    Returns:
        float: The percentage of sentences in the completion string compared to the example string.
    """
    return textstat.sentence_count(completion) / textstat.sentence_count(example) * 100
