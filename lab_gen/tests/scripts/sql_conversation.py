import sys

from langchain.chains import create_sql_query_chain
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase

from lab_gen.services.llm.lifetime import get_llm, init_models


DB_NAME = "chinook"

# Initialise the models and retrieve the specified LLM
init_models()
llm = get_llm()

def init_db(db_name: str) -> SQLDatabase:
    """
    Initializes a SQL database connection using the provided database name.

    Args:
        db_name (str): The name of the database to connect to.

    Returns:
        SQLDatabase: An instance of the SQLDatabase class representing the initialized database connection.

    Raises:
        None
    """
    db_uri = f"mysql+mysqlconnector://root:labgensql@localhost:3306/{db_name}"
    return SQLDatabase.from_uri(db_uri)

def query_wizard() -> None:
    """
    Runs a query wizard for generating SQL commands.

    This function initializes the chosen database using the `init_db` function.

    It then prompts the user to enter a question for the prompt. The user can choose to quit
    by entering 'q' or return to the main menu by entering 'm'.

    If the user enters a valid question, the function creates an SQL query chain using the
    `create_sql_query_chain` function and invokes the chain with the user's input.

    The response from the chain is printed to the console.

    Parameters:
    None

    Returns:
    None
    """
    db = init_db(DB_NAME)

    while True:
        prompt = input("\nEnter the question for the prompt ('q' to quit, 'm' for main menu): ")

        # Check if the user wants to quit
        if prompt.lower() == "q":
            break

        # Check if the user wants to return to the main menu
        if prompt.lower() == "m":
            main()

        chain = create_sql_query_chain(llm, db)

        response = chain.invoke({"question" : prompt})

        print("\n" + response)  # noqa: T201

def run_db_query() -> None:
    """
    Runs a database query based on user input.

    This function initializes the chosen database using the `init_db` function.

    It then prompts the user to enter a question for the prompt.

    The user can choose to quit by entering 'q' or return to the main menu by entering 'm'.

    If the user enters a valid question, the function creates an SQL agent using the `create_sql_agent`
    function and invokes the agent with the user's input.

    The response from the agent is printed to the console.

    Parameters:
    None

    Returns:
    None
    """
    db = init_db(DB_NAME)

    # Prompt the user for the prompt question
    while True:
        prompt = input("\nEnter the question for the prompt ('q' to quit, 'm' for main menu): ")

        # Check if the user wants to quit
        if prompt.lower() == "q":
            break

        # Check if the user wants to return to the main menu
        if prompt.lower() == "m":
            main()

        # Create the SQL Agent
        agent_executor = create_sql_agent(llm, db=db, agent_type="openai-tools", verbose=False)

        response = agent_executor.invoke(
            {
                "input": prompt,
            },
        )

        print("\n" + response["output"])  # noqa: T201

def main() -> None:
    """
    A function that presents a menu to the user and performs different actions based on the user's choice.

    Parameters:
    None

    Returns:
    None
    """
    choice = input("\nWhich service would you like to use? \n1. Query Wizard \n2. Database Chat \n3. Exit \n")

    if choice.lower() == "1":
        query_wizard()
    elif choice.lower() == "2":
        run_db_query()
    elif choice.lower() == "3":
        sys.exit()

main()
