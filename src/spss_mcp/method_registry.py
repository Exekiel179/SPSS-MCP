from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from spss_mcp.method_templates import (
    render_cluster_hierarchical,
    render_cox_regression,
    render_discriminant,
    render_genlin,
    render_genlinmixed,
    render_glm_univariate,
    render_kaplan_meier,
    render_logistic_regression,
    render_manova,
    render_mixed,
    render_ordinal_regression,
    render_twostep_cluster,
)
from spss_mcp.method_validation import (
    CoxRegressionParams,
    DiscriminantParams,
    GenlinMixedParams,
    GenlinParams,
    GlmUnivariateParams,
    HierarchicalClusterParams,
    KaplanMeierParams,
    LogisticRegressionParams,
    ManovaParams,
    MixedParams,
    OrdinalRegressionParams,
    TwoStepClusterParams,
)


@dataclass(frozen=True)
class MethodDefinition:
    tool_name: str
    command_family: str
    support_level: str
    schema: type
    renderer: Any
    assertions: tuple[str, ...]
    doc_tags: tuple[str, ...]


METHOD_REGISTRY: dict[str, MethodDefinition] = {
    "spss_logistic_regression": MethodDefinition(
        tool_name="spss_logistic_regression",
        command_family="LOGISTIC REGRESSION",
        support_level="registry-backed",
        schema=LogisticRegressionParams,
        renderer=render_logistic_regression,
        assertions=("Variables in the Equation", "Model Summary"),
        doc_tags=("advanced-regression", "validated", "template-based"),
    ),
    "spss_ordinal_regression": MethodDefinition(
        tool_name="spss_ordinal_regression",
        command_family="PLUM",
        support_level="registry-backed",
        schema=OrdinalRegressionParams,
        renderer=render_ordinal_regression,
        assertions=("Model Fitting Information", "Parameter Estimates"),
        doc_tags=("advanced-regression", "validated", "template-based"),
    ),
    "spss_genlin": MethodDefinition(
        tool_name="spss_genlin",
        command_family="GENLIN",
        support_level="registry-backed",
        schema=GenlinParams,
        renderer=render_genlin,
        assertions=("Parameter Estimates", "Model Information"),
        doc_tags=("advanced-regression", "validated", "template-based"),
    ),
    "spss_mixed": MethodDefinition(
        tool_name="spss_mixed",
        command_family="MIXED",
        support_level="registry-backed",
        schema=MixedParams,
        renderer=render_mixed,
        assertions=("Estimates of Fixed Effects", "Covariance Parameters"),
        doc_tags=("mixed-model", "validated", "template-based"),
    ),
    "spss_genlinmixed": MethodDefinition(
        tool_name="spss_genlinmixed",
        command_family="GENLINMIXED",
        support_level="registry-backed",
        schema=GenlinMixedParams,
        renderer=render_genlinmixed,
        assertions=("Tests of Fixed Effects", "Parameter Estimates"),
        doc_tags=("mixed-model", "validated", "template-based"),
    ),
    "spss_cox_regression": MethodDefinition(
        tool_name="spss_cox_regression",
        command_family="COXREG",
        support_level="registry-backed",
        schema=CoxRegressionParams,
        renderer=render_cox_regression,
        assertions=("Variables in the Equation", "Omnibus Tests of Model Coefficients"),
        doc_tags=("survival", "validated", "template-based"),
    ),
    "spss_kaplan_meier": MethodDefinition(
        tool_name="spss_kaplan_meier",
        command_family="KM",
        support_level="registry-backed",
        schema=KaplanMeierParams,
        renderer=render_kaplan_meier,
        assertions=("Survival Table", "Means and Medians for Survival Time"),
        doc_tags=("survival", "validated", "template-based"),
    ),
    "spss_discriminant": MethodDefinition(
        tool_name="spss_discriminant",
        command_family="DISCRIMINANT",
        support_level="registry-backed",
        schema=DiscriminantParams,
        renderer=render_discriminant,
        assertions=("Classification Results", "Functions at Group Centroids"),
        doc_tags=("multivariate", "validated", "template-based"),
    ),
    "spss_cluster_hierarchical": MethodDefinition(
        tool_name="spss_cluster_hierarchical",
        command_family="CLUSTER",
        support_level="registry-backed",
        schema=HierarchicalClusterParams,
        renderer=render_cluster_hierarchical,
        assertions=("Agglomeration Schedule", "Cluster Membership"),
        doc_tags=("clustering", "validated", "template-based"),
    ),
    "spss_twostep_cluster": MethodDefinition(
        tool_name="spss_twostep_cluster",
        command_family="TWOSTEP CLUSTER",
        support_level="registry-backed",
        schema=TwoStepClusterParams,
        renderer=render_twostep_cluster,
        assertions=("Model Summary", "Cluster Sizes"),
        doc_tags=("clustering", "validated", "template-based"),
    ),
    "spss_manova": MethodDefinition(
        tool_name="spss_manova",
        command_family="MANOVA",
        support_level="registry-backed",
        schema=ManovaParams,
        renderer=render_manova,
        assertions=("Multivariate Tests", "Tests of Between-Subjects Effects"),
        doc_tags=("multivariate", "validated", "template-based"),
    ),
    "spss_glm_univariate": MethodDefinition(
        tool_name="spss_glm_univariate",
        command_family="UNIANOVA",
        support_level="registry-backed",
        schema=GlmUnivariateParams,
        renderer=render_glm_univariate,
        assertions=("Tests of Between-Subjects Effects", "Descriptive Statistics"),
        doc_tags=("multivariate", "validated", "template-based"),
    ),
}


def get_method_definition(tool_name: str) -> MethodDefinition:
    return METHOD_REGISTRY[tool_name]


def list_registered_methods() -> list[MethodDefinition]:
    return [METHOD_REGISTRY[name] for name in sorted(METHOD_REGISTRY)]


def build_registered_syntax(tool_name: str, file_path: str, **params: Any) -> str:
    method = get_method_definition(tool_name)
    validated = method.schema(**params)
    return method.renderer(file_path, validated)


def get_method_schema(tool_name: str) -> dict[str, Any]:
    method = get_method_definition(tool_name)
    return method.schema.model_json_schema()
