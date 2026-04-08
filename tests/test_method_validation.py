import pytest
from pydantic import ValidationError

from spss_mcp.method_validation import GlmUnivariateParams, ManovaParams, MixedParams, TwoStepClusterParams


def test_twostep_cluster_requires_inputs():
    with pytest.raises(ValidationError):
        TwoStepClusterParams()


def test_twostep_cluster_rejects_small_max_clusters():
    with pytest.raises(ValidationError):
        TwoStepClusterParams(continuous=["x"], max_clusters=1)


def test_mixed_requires_subject_when_random_effects_present():
    with pytest.raises(ValidationError):
        MixedParams(dependent="y", fixed_effects=["x"], random_effects=["x"])


def test_manova_requires_two_dependents():
    with pytest.raises(ValidationError):
        ManovaParams(dependents=["y1"], factors=["group"])


def test_glm_univariate_requires_posthoc_method():
    with pytest.raises(ValidationError):
        GlmUnivariateParams(dependent="score", factors=["group"], posthoc=["group"])
