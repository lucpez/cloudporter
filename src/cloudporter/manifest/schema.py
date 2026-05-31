from typing import Annotated, Literal, Self

from pydantic import BaseModel, Field, model_validator


class ComputeResource(BaseModel):
    name: str
    type: Literal["compute"]
    cpu: Annotated[int, Field(ge=1)]
    memory_gb: Annotated[int, Field(ge=1)]
    os: str
    public: bool = False
    run: str | None = None


class DatabaseResource(BaseModel):
    name: str
    type: Literal["database"]
    engine: Literal["mysql", "postgres"]
    cpu: Annotated[int, Field(ge=1)]
    memory_gb: Annotated[int, Field(ge=1)]
    storage_gb: Annotated[int, Field(ge=20)]


Resource = Annotated[ComputeResource | DatabaseResource, Field(discriminator="type")]


class Manifest(BaseModel):
    name: str
    resources: list[Resource]

    @model_validator(mode="after")
    def no_duplicate_names(self) -> Self:
        seen: set[str] = set()
        duplicates: set[str] = set()
        for resource in self.resources:
            if resource.name in seen:
                duplicates.add(resource.name)
            seen.add(resource.name)
        if duplicates:
            names = ", ".join(sorted(duplicates))
            raise ValueError(f"duplicate resource names: {names}")
        return self
