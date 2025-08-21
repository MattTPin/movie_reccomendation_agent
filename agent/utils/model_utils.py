# model_utils.py
from typing import List, Set, Dict, Any
from pydantic import BaseModel
from textwrap import dedent
import json

def generate_system_prompt_from_model_instance(
    action_prompt_template: str,
    model_instance: BaseModel,
    placeholder: str = "{+json+}"
) -> str:
    """
    Inserts the provided model_instance as JSON into the prompt template.

    Args:
        action_prompt_template: The prompt containing a placeholder string.
        model_instance: A fully formed BaseModel instance.
        placeholder: The string in the action_prompt_template to replace with JSON.

    Returns:
        The prompt with the placeholder replaced by JSON from the model_instance,
        excluding any fields that were not explicitly set.
    """
    if not isinstance(model_instance, BaseModel):
        raise TypeError("model_instance must be a Pydantic BaseModel")

    example_json = json.dumps(
        model_instance.get_example_from_instance(),
        indent=4
    )

    return dedent(action_prompt_template).replace(placeholder, example_json)


def extract_populated_optional_fields(
    model_instance: BaseModel,
    always_include: Set[str]
) -> List[str]:
    """
    Extracts which optional fields are populated in a model instance.

    Args:
        model_instance: The instance to inspect.
        always_include: Fields always included, and therefore excluded from optionals.

    Returns:
        A list of optional fields that are populated.
    """
    return [
        field_name
        for field_name in model_instance.model_fields_set  # Tracks explicitly set fields
        if field_name not in always_include and getattr(model_instance, field_name) not in (None, [], {}, "", 0)
    ]


def build_example_dict(
    model_class: type,
    fields_to_include: Set[str]
) -> Dict[str, Any]:
    """
    Builds an example dict using the model class and field names to include.

    Args:
        model_class: The Pydantic model class.
        fields_to_include: Field names to include in the example.

    Returns:
        A dictionary containing example values for the specified fields.
    """
    example_data = {}
    for name in fields_to_include:
        field = model_class.model_fields.get(name)
        if not field:
            continue
        example = (field.json_schema_extra or {}).get("example")
        if example is not None:
            example_data[name] = example
    return example_data