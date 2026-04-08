import pytest

from spss_mcp.method_registry import METHOD_REGISTRY, get_method_schema, list_registered_methods


def test_registry_methods_unique():
    names = [method.tool_name for method in list_registered_methods()]
    assert len(names) == len(set(names))


def test_registry_entries_are_complete():
    for name, method in METHOD_REGISTRY.items():
        assert method.tool_name == name
        assert method.command_family
        assert method.support_level == "registry-backed"
        assert method.assertions
        assert method.doc_tags
        assert method.schema is not None
        assert method.renderer is not None


def test_registry_schema_export_contains_properties():
    schema = get_method_schema("spss_logistic_regression")
    assert "properties" in schema
    assert "dependent" in schema["properties"]
    assert "predictors" in schema["properties"]
