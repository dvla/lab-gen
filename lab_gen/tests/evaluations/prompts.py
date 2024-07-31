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
