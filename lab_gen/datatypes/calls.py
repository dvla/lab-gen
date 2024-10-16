from enum import Enum

from pydantic import BaseModel, Field


class Vehicle(BaseModel):
    """Represents a vehicle."""

    registrationNumber: str = Field(description="The unique UK Vehicle Registration Number for a vehicle")  # noqa: N815
    make: str | None = Field(description="vehicle make")
    model: str | None = Field(description="vehicle model")
    colour: str | None = Field(description="vehicle colour")
    registrationDocumentId: str | None = Field(  # noqa: N815
        description="The registration document ID for the vehicle",
        min_length=11,
        max_length=16,
    )


class Driver(BaseModel):
    """Represents a driver."""

    drivingLicenceNumber: str = Field(  # noqa: N815
        description="A UK driving licence number",
        min_length=5,
        max_length=16,
    )
    title: str | None = Field(description="Title in full mode of address, e.g. Mr, Miss, Lord.")
    firstNames: str = Field(  # noqa: N815
        description="One or more first names separated by a space character.",
        max_length=38,
    )
    lastName: str = Field(description="A single last name.", max_length=43)  # noqa: N815
    dateOfBirth: str | None = Field(  # noqa: N815
        description="The date on which the driver was born. Does not include time. In the format YYYY-MM-DD.",
    )
    postcode: str | None = Field(
        description="A complete UK postcode of the driver's address.",
        min_length=5,
        max_length=8,
    )


class Category(Enum):
    """Represents call categories."""

    Vehicle = "Vehicle"
    Driver = "Driver"
    Other = "Other"


class Call(BaseModel):
    """Represents a call transcript."""

    driver: Driver | None = Field(default=None)
    vehicle: Vehicle | None = Field(default=None)
    startTime: str = Field(  # noqa: N815
        description="The date and time the call started. In the format YYYY-MM-DDTHH:MM:SSZ.",
    )
    endTime: str = Field(  # noqa: N815
        description="The date and time the call ended. In the format YYYY-MM-DDTHH:MM:SSZ.",
    )
    participants: str = Field(
        description="The names of the participants in the call, separated by a comma. "
        "The call agent's name appears first, then the customer's name.",
    )
    customerSituation: str = Field(  # noqa: N815
        description="The customer's current situation, context"
        " and any specific circumstances relevant to their inquiry or issue.",
    )
    desiredOutcome: str = Field(  # noqa: N815
        description="Clearly identify the customer's desired outcome or resolution for the call.",
    )
    topics: str = Field(description="The main reason for the call.")
    steps: list[str] = Field(
        description="Each key step taken: documenting the steps taken, from the point of view of the agent,"
        " to resolve the issue or address the customer's need.",
    )
    resolution: str = Field(
        description="Was the agent able to resolve the customer's issue or request effectively"
        " and in a way that meets the customer's desired outcome.",
    )
    category: list[Category] = Field(description="Categorise the call in one or more of these ways.")
    sentiment: str = Field(description="The sentiment of the call, e.g. positive, negative, neutral.")
    fcr: bool | None = Field(
        description="First Call Resolution (FCR): Whether the customer's issue was resolved"
        " in that single interaction without the need for any follow-up",
    )


# https://osl-data-dictionary-schemas.engineering.dvla.gov.uk/docs/vehicle-enquiries/types/v1/vehicle-read-model.html
# https://osl-data-dictionary-schemas.engineering.dvla.gov.uk/docs/vehicle-enquiries/types/v1/vehicle-full-read-model.html
# https://osl-data-dictionary-schemas.engineering.dvla.gov.uk/docs/driver-enquiries/driver-advanced-find/responses/v1/advanced-driver-summary.html
# https://osl-data-dictionary-schemas.engineering.dvla.gov.uk/docs/customer/customer-channel-api/responses/v1/retrieve-customer-summary-response.html
