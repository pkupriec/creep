"""Version-one graph syntax. Topology compilation belongs to graphs.Validator."""

import math
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, JsonValue, model_validator

SafeID = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")]
Nonempty = Annotated[str, Field(min_length=1)]
PositiveInt = Annotated[int, Field(gt=0)]


def exact_integer(value: object) -> object:
    if type(value) is not int:
        raise ValueError("Literal integer must be an integer, not a boolean or float")
    return value


ExactOne = Annotated[Literal[1], BeforeValidator(exact_integer)]
ExactZero = Annotated[Literal[0], BeforeValidator(exact_integer)]


class Contract(BaseModel):
    model_config = ConfigDict(
        extra="forbid", strict=True, validate_assignment=True, allow_inf_nan=False
    )

    @model_validator(mode="after")
    def finite_json(self):
        stack = [self]
        seen = set()
        while stack:
            item = stack.pop()
            if isinstance(item, float) and not math.isfinite(item):
                raise ValueError("JSON numbers must be finite")
            if isinstance(item, (dict, list, tuple)) and id(item) not in seen:
                seen.add(id(item))
                stack.extend(item.values() if isinstance(item, dict) else item)
            elif isinstance(item, BaseModel) and id(item) not in seen:
                seen.add(id(item))
                stack.extend(getattr(item, name) for name in type(item).model_fields)
        return self


class Position(Contract):
    x: Annotated[float, Field(allow_inf_nan=False)]
    y: Annotated[float, Field(allow_inf_nan=False)]


class Generation(Contract):
    temperature: Annotated[float, Field(ge=0, le=2)] | None = None
    top_p: Annotated[float, Field(ge=0, le=1)] | None = None
    max_tokens: PositiveInt | None = None
    stop: str | Annotated[list[str], Field(min_length=1, max_length=4)] | None = None
    # Explicit stored model-specific option, never a public client extension/default.
    reasoning_effort: Literal["none", "low", "medium", "high"] | None = None


class NamedInput(Contract):
    id: SafeID
    required: bool


class InputNode(Contract):
    id: SafeID
    type: Literal["input"]
    input_id: SafeID
    position: Position | None = None


class LLMNode(Contract):
    id: SafeID
    type: Literal["llm"]
    system_prompt: str
    tools_enabled: bool
    generation: Generation
    position: Position | None = None


class OutputNode(Contract):
    id: SafeID
    type: Literal["output"]
    position: Position | None = None


Node = Annotated[InputNode | LLMNode | OutputNode, Field(discriminator="type")]


class ForwardEdge(Contract):
    id: SafeID
    source: SafeID
    target: SafeID
    target_port: SafeID
    kind: Literal["forward"]


class FeedbackEdge(Contract):
    id: SafeID
    source: SafeID
    target: SafeID
    target_port: SafeID
    kind: Literal["feedback"]
    loop_id: SafeID
    initial_value: JsonValue


Edge = Annotated[ForwardEdge | FeedbackEdge, Field(discriminator="kind")]


class Loop(Contract):
    id: SafeID
    node_ids: Annotated[list[SafeID], Field(min_length=1)]
    controller_node_id: SafeID
    continue_value: Nonempty
    exit_value: Nonempty

    @model_validator(mode="after")
    def distinct_values_and_members(self):
        if self.continue_value == self.exit_value:
            raise ValueError("continue_value and exit_value must differ")
        if len(set(self.node_ids)) != len(self.node_ids):
            raise ValueError("Loop members must be unique")
        if self.controller_node_id not in self.node_ids:
            raise ValueError("Controller must belong to the loop")
        return self


class Graph(Contract):
    schema_version: ExactOne
    id: SafeID
    name: Nonempty
    revision: PositiveInt
    base_model: Nonempty
    inputs: Annotated[list[NamedInput], Field(min_length=1)]
    nodes: Annotated[list[Node], Field(min_length=1)]
    edges: list[Edge]
    loops: list[Loop]
    output_node_id: SafeID

    @model_validator(mode="after")
    def syntax_uniqueness(self):
        for label, values in (
            ("inputs", self.inputs),
            ("nodes", self.nodes),
            ("edges", self.edges),
            ("loops", self.loops),
        ):
            ids = [item.id for item in values]
            if len(ids) != len(set(ids)):
                raise ValueError(f"Duplicate {label} IDs")
        members = [member for loop in self.loops for member in loop.node_ids]
        if len(members) != len(set(members)):
            raise ValueError("Loop scopes must be disjoint")
        return self


class Control(Contract):
    decision: Nonempty


class ControllerOutput(Contract):
    payload: JsonValue
    control: Control


def controller_schema(loop: Loop) -> dict:
    """Constrain a controller response to that scope's distinct exit vocabulary."""
    schema = ControllerOutput.model_json_schema()
    schema["$defs"]["Control"]["properties"]["decision"] = {
        "type": "string",
        "enum": [loop.continue_value, loop.exit_value],
    }
    return schema
