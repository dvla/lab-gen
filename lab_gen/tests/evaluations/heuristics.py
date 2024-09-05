from langchain_core.exceptions import OutputParserException
from textstat import textstat

from lab_gen.datatypes.calls import Call
from lab_gen.services.llm.parsers import StrictJsonOutputParser


COMPLETION = "completion"
EXAMPLE = "example"

def reading_ease(**kwargs: str) -> float:
    """
    Calculate the Flesch-Kincaid Reading Ease score for a given text.

    The higher the score the easier it is to read. The maximum score is 121.22.
    There is no limit on how low the score can be. A negative score is valid.

    Args:
        kwargs (str): The completed text to calculate the score for.

    Returns:
        float: The Flesch-Kincaid Reading Ease score.
    """
    return textstat.flesch_reading_ease(kwargs[COMPLETION])

def grade_level(**kwargs: str) -> float:
    """
    Calculate the Flesch-Kincaid Grade Level score for a given text.

    A score of 9.3 means that a ninth grader would be able to read the text.

    Args:
        kwargs (str): The completed text to calculate the score for.

    Returns:
        float: The Flesch-Kincaid Grade Level score.
    """
    return textstat.flesch_kincaid_grade(kwargs[COMPLETION])

def json_validator(**kwargs: str) -> float:
    """
    Validates a JSON completion against a provided example.

    Args:
        kwargs (str): The completion to be validated.

    Returns:
        float: A score indicating the validity of the completion.

    Raises:
        OutputParserException: If the output parsing fails.
    """
    strict_parser = StrictJsonOutputParser(pydantic_object=Call)
    try:
        strict_parser.parse(kwargs[COMPLETION])
        return 1  # noqa: TRY300
    except OutputParserException:
        return 0

def character_count_percentage(**kwargs: str) -> float:
    """
    Calculate the percentage of characters in the completion string compared to the example string.

    Args:
        kwargs (str): The example string and the completion string.

    Returns:
        float: The percentage of characters in the completion string compared to the example string.
    """
    return len(kwargs[COMPLETION]) / len(kwargs[EXAMPLE]) * 100

def sentence_count_percentage(**kwargs: str) -> float:
    """
    Calculate the percentage of sentences in the completion string compared to the example string.

    Args:
        kwargs (str): The example string and the completion string.

    Returns:
        float: The percentage of sentences in the completion string compared to the example string.
    """
    return textstat.sentence_count(kwargs[COMPLETION]) / textstat.sentence_count(kwargs[EXAMPLE]) * 100

def difficult_words(**kwargs: str) -> float:
    """
    Calculate the number of difficult words in the completion string.

    Args:
        kwargs (str): The completion string.

    Returns:
        float: The number of difficult words in the completion string.
    """
    return textstat.difficult_words(kwargs[COMPLETION])

def automated_readability_index(**kwargs: str) -> float:
    """
    Calculate the Automated Readability Index (ARI) for the completion string.

    If the ARI is 8.0, then the grade level to read the text is 8th grade.

    Args:
        kwargs (str): The completion string.

    Returns:
        float: The Automated Readability Index (ARI) for the completion string.
    """
    return textstat.automated_readability_index(kwargs[COMPLETION])
