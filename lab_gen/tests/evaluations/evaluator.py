from typing import Any

from langchain.evaluation import EvaluatorType, load_evaluator
from langchain.evaluation.criteria.eval_chain import Criteria
from langchain_core.prompts import PromptTemplate
from models import get_eval_client


def get_evaluator_for_key(key: str, prompt: str) -> Any: # noqa: ANN401
    """
    Returns an evaluator for a given key and prompt.

    Args:
        key (str): The key to identify the evaluator.
        prompt (str): The prompt to use for the evaluator.

    Returns:
        Evaluator: The evaluator object.
    """
    eval_client = get_eval_client()
    prompt = PromptTemplate.from_template(prompt)
    return load_evaluator(EvaluatorType.LABELED_SCORE_STRING, criteria=key, llm=eval_client, prompt=prompt)

def execute_eval_and_score(dataset_input: str, dataset_output: str, completion: str, # noqa: PLR0913
                           handler: Any, eval_types: dict, prompt: str, scoring_functions: dict) -> None: # noqa: ANN401
    """
    Executes the evaluation and scoring of a completion against a dataset.

    Args:
        dataset_input (str): The dataset input.
        dataset_output (str): The expected output from the dataset.
        completion (str): The completion to be evaluated.
        handler (Any): The handler object to track the trace for the evaluation results.
        eval_types (dict): A dictionary of evaluation types and their corresponding values.
        prompt (str): The prompt to be used for the evaluation.
        scoring_functions (dict): A dictionary of scoring functions and their corresponding names.

    Returns:
        None
    """
    criteria = [[key, value] for key, value in eval_types.items()]

    for criterion in criteria:
        full_criterion = criterion[0] + ": " + criterion[1] if not isinstance(criterion[0], Criteria) else criterion[0]
        evaluator = get_evaluator_for_key(full_criterion, prompt)
        eval_result = evaluator.evaluate_strings(
            prediction=completion,
            input=dataset_input,
            reference=dataset_output,
        )

        handler.trace.score(name=criterion[0], value=eval_result["score"], comment=eval_result["reasoning"])

    # Heuristic custom scoring
    for criterion_name, scoring_function in scoring_functions.items():
        handler.trace.score(name=criterion_name, value=scoring_function(str(dataset_output), completion.content))
