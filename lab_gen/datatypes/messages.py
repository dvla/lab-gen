from langchain_core.messages import AIMessage, HumanMessage


MESSAGE_TYPE_AI = AIMessage(content="").type
MESSAGE_TYPE_HUMAN = HumanMessage(content="").type
