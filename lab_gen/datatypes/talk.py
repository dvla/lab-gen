from langchain_core.pydantic_v1 import BaseModel, Field


class CreativeWork(BaseModel):
    """A CreativeWork."""

    name: str = Field(description="The name of the item")
    description: str | None = Field(description="A description of the item")
    type: str = Field(description="The type of the item, e.g. Book, Movie, Song, etc.")


class Quotation(BaseModel):
    """
    A quotation.

    Often from some written work, attributable to a real world author and
      - if associated with a fictional character - to any fictional Person.
    """

    creator: str = Field(
        description="The creator/author of this quotation.",
    )
    text: str = Field(description="The textual content of the quotation.")


class Organisation(BaseModel):
    """An organization such as a school, a business corporation etc."""

    name: str = Field(description="The name of the organization")
    description: str | None = Field(description="A description of the organization")
    brands: list[str] | None = Field(description="The brand(s) associated with, or maintained by the organization.")
    location: str | None = Field(
        description="""Where the organization is located. """,
    )


class Person(BaseModel):
    """A person (alive, dead, undead, or fictional)."""

    name: str = Field(description="The name of the person")
    description: str | None = Field(description="A description of the person, could be a job title or a short bio.")


class Talk(BaseModel):
    """Key details extracted from a talk/podcast transcript."""

    creativeWorks: list[CreativeWork] | None = Field(  # noqa: N815
        default=None,
        example=[
            {
                "name": "The Two Towers",
                "description": "The Two Towers is the second book in the Lord of the Rings series, and it continues the story of the Fellowship of the Ring. The book is about the Fellowship's members becoming separated and facing challenges as they try to destroy the One Ring.",  # noqa: E501
                "type": "Book",
                "author": "J. R. R. Tolkien",
            },
            {
                "name": "Willy Wonka & the Chocolate Factory",
                "description": "Willy Wonka & the Chocolate Factory is a film starring Gene Wilder.",
                "type": "Movie",
            },
            {
                "name": "Acquired",
                "description": "Acquired is a podcast about great companies and the stories and playbooks behind them.",
                "type": "Podcast",
            },
        ],
    )

    quotations: list[Quotation] | None = Field(
        default=None,
        example=[
            {
                "creator": "Franklin Delano Roosevelt",
                "text": "The only thing we have to fear is fear itself.",
            },
        ],
    )

    organizations: list[Organisation] | None = Field(
        default=None,
        example=[
            {
                "name": "The Coca-Cola Company",
                "location": "Atlanta, Georgia, USA.",
                "brands": ["Coca-Cola", "Sprite", "Fanta"],
                "description": "The Coca-Cola Company is an American multinational corporation that is best known for its flagship product, Coca-Cola. The company was founded in 1892.",  # noqa: E501
            },
            {
                "name": "Amazon.com, Inc",
                "description": "Amazon.com, is a multinational technology company focusing on e-commerce, cloud computing, and artificial intelligence. It is one of the world's largest online marketplaces.",  # noqa: E501
                "location": "Seattle, Washington, USA.",
                "brands": ["Amazon Prime", "Amazon Web Services (AWS)", "Kindle"],
            },
        ],
    )

    people: list[Person] | None = Field(
        default=None,
        example=[
            {
                "name": "Joe Montana",
                "description": "Quarterback, San Francisco 49ers.",
            },
            {
                "name": "George W. Bush",
                "description": "43rd President of the United States.",
            },
            {
                "name": "Albert Einstein",
                "description": "Professor of Physics.",
            },
        ],
    )
