from typing import List
from sqlmodel import Field, SQLModel, JSON, Column
from sqlalchemy import func
from datetime import datetime
import uuid

# Import the data contract from your central schemas file
from schemas import CareerAdviceResponse


# --- Database Table Model ---

class UserProgress(SQLModel, table=True):
    """
    Represents a user's progress data in the database.
    This model is hardened with UUIDs, data validation at the database level,
    and automated audit timestamps.
    """
    # Use UUID for a robust, non-guessable, and unique primary key.
    # We will generate this in our application logic before saving.
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )

    # Stores the career advice JSON, validated against the CareerAdviceResponse schema.
    # Note: True validation requires application-level logic before insertion,
    # as the DB's JSON type doesn't natively validate Pydantic models.
    # The type hint here serves as a crucial contract for developers.
    advice: CareerAdviceResponse = Field(sa_column=Column(JSON))

    # Stores a list of week numbers the user has marked as completed.
    completed_weeks: List[int] = Field(default_factory=list, sa_column=Column(JSON))

    # --- Auditing Fields ---

    # Timestamp for when the record was created.
    # 'server_default' tells the database to set this value.
    created_at: datetime = Field(
        default=None,
        sa_column_kwargs={"server_default": func.now()},
        nullable=False,
    )

    # Timestamp for the last time the record was updated.
    # 'onupdate' tells the database to update this value on every modification.
    updated_at: datetime = Field(
        default=None,
        sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()},
        nullable=False,
    )