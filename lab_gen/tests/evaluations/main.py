from typing import Any

from evaluator import execute_eval_and_score
from heuristics import character_count_percentage, grade_level, json_validator, reading_ease
from langchain.evaluation.criteria.eval_chain import Criteria
from langfuse import Langfuse
from models import get_llm_client
from prompts import trulens_comprehensiveness_template


# List of supported LLM criteria to be used in EVAL_TYPES dictionary
SUPPORTED_CRITERIA ={
    Criteria.CONCISENESS,
    Criteria.RELEVANCE,
    Criteria.COHERENCE,
    Criteria.HARMFULNESS,
    Criteria.MALICIOUSNESS,
    Criteria.HELPFULNESS,
    Criteria.CONTROVERSIALITY,
    Criteria.MISOGYNY,
    Criteria.CRIMINALITY,
    Criteria.INSENSITIVITY,
    Criteria.CORRECTNESS,
    Criteria.DETAIL,
    Criteria.DEPTH,
}

# Select the criteria you want to evaluate - custom criteria can be added here too
EVAL_TYPES = [
    {"name": "Comprehensiveness",
     "description": "Modified comprehensiveness prompt from TruLens",
     "prompt": trulens_comprehensiveness_template},
    {"name": Criteria.CORRECTNESS},
    {"name": Criteria.CONCISENESS},
    {"name": Criteria.COHERENCE},
]
# Dictionary of custom heuristic scoring functions to be used in the evaluation
CUSTOM_SCORING_FUNCTIONS = {
    "Reading Ease": reading_ease,
    "Grade Level": grade_level,
    "Character Count Percentage": character_count_percentage,
    "JSON Validator": json_validator,
}

# Name of the dataset in Langfuse
DATASET_NAME = "DATASET_NAME"

# Name of the evaluation run
EVAL_RUN_NAME = "LLMMODEL-EVALMODELEvaluator"

langfuse = Langfuse()
langfuse.auth_check()

llm_client = get_llm_client()

def run_my_langchain_llm_app(data_input: str, callback_handler: Any) -> Any: # noqa: ANN401
    """
    Runs the client with the given `input` and `callback_handler`.

    Parameters:
        data_input (str): The input to be passed to the client.
        callback_handler (Any): The callback handler to be used by the client.

    Returns:
        Any: The result of the client invocation.
    """
    return llm_client.invoke(
      input=data_input,
      config={"callbacks": [callback_handler]},
    )


def main() -> None:
    """
    Main function.

    Executes the main function that iterates over a dataset, retrieves a langchain handler for each dataset item,
    retrieves the input and expected output for each dataset item, invokes a language model to generate a completion,
    and executes the evaluation and scoring process.

    Parameters:
    None

    Returns:
    None
    """
    dataset = langfuse.get_dataset(DATASET_NAME)

    for item in dataset.items:
        handler = item.get_langchain_handler(run_name=EVAL_RUN_NAME)

        dataset_input = item.input[0]["content"]
        dataset_output = item.expected_output["content"]
        completion = run_my_langchain_llm_app(dataset_input, handler)

        execute_eval_and_score(dataset_input, dataset_output, completion,
                               handler, EVAL_TYPES, CUSTOM_SCORING_FUNCTIONS)

if __name__ == "__main__":
    main()
