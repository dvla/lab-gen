from typing import Any

from langchain.evaluation import EvaluatorType, load_evaluator
from langchain.evaluation.criteria.eval_chain import Criteria
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import PromptTemplate
from prompts import criteria_prompt_template


DEFAULT_EVAL_PROMPT = criteria_prompt_template

def get_evaluator_for_key(key: str, prompt: str, eval_client: BaseLanguageModel) -> Any: # noqa: ANN401
    """
    Returns an evaluator for a given key and prompt.

    Args:
        key (str): The key to identify the evaluator.
        prompt (str): The prompt to use for the evaluator.
        eval_client (BaseLanguageModel): The language model to use as the evaluator.

    Returns:
        Evaluator: The evaluator object.
    """
    prompt = PromptTemplate.from_template(prompt)
    return load_evaluator(EvaluatorType.LABELED_SCORE_STRING, criteria=key, llm=eval_client, prompt=prompt)

def execute_eval_and_score(dataset_input: str, dataset_output: str, completion: str, # noqa: PLR0913
                           handler: Any, eval_types: dict, scoring_functions: dict, eval_client: Any) -> None: # noqa: ANN401
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
        eval_client (Any): The language model to be used as the evaluator.

    Returns:
        None
    """
    criteria = eval_types

    for criterion in criteria:
        full_criterion = (
            criterion["name"] + ": " + criterion["description"]
            if not isinstance(criterion["name"], Criteria)
            else criterion["name"]
        )
        prompt = criterion["prompt"] if not isinstance(criterion["name"], Criteria) else DEFAULT_EVAL_PROMPT
        evaluator = get_evaluator_for_key(full_criterion, prompt, eval_client)
        eval_result = evaluator.evaluate_strings(
            prediction=completion,
            input=dataset_input,
            reference=dataset_output,
        )

        handler.trace.score(name=criterion["name"], value=eval_result["score"], comment=eval_result["reasoning"])

    # Heuristic custom scoring
    for criterion_name, scoring_function in scoring_functions.items():
        handler.trace.score(name=criterion_name, value=scoring_function(str(dataset_output), completion.content))
