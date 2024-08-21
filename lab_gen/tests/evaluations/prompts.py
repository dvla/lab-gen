criteria_prompt_template = """Respond with a score on a scale of 1-10 based on how well the following response
follows the specified rubric. Grade only based on the rubric and expected response:

Grading Rubric: {criteria}
Expected Response: {reference}

DATA:
---------
Question: {input}
Response: {prediction}
---------
Write out your explanation for each criterion, then respond with a score in double brackets on a scale of 1-10
on a new line. Eg. Score: [[8]]"""

json_criteria_prompt_template = """Respond with a score on a scale of 1-10 based on how well the following response
follows the specified rubric. Grade only based on the rubric and expected correct json response:

Grading Rubric: {criteria}
Expected Correct JSON Response: {reference}

DATA:
---------
JSON Healing Prompt: {input}
Response: {prediction}
---------
Write out your explanation for each criterion, then respond with a score in double brackets on a scale of 1-10
on a new line. Eg. Score: [[8]]"""

trulens_comprehensiveness_template = """
You are tasked with evaluating summarization quality. Please follow the instructions below.
INSTRUCTIONS:

1. Given a summary, score well the source text captures that summary.

Is the summary comprehensively included in the source?

Scoring criteria:
0 - The summary is not included in the source text.
5 - The summary is vaguely mentioned or partially included in the source text.
10 - The summary is fully included in the source text.

Grading Rubric: {criteria}
Expected Response: {reference}

Source Text: {input}
Summary: {prediction}

Write out your explanation for summary, then respond with a score in double brackets on a scale of 1-10
for the overall score. Eg. Score: [[8]]
"""
