from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


class MethodParams(BaseModel):
    model_config = {"extra": "forbid"}


class CaseSelectionParams(MethodParams):
    filter_variable: Optional[str] = None
    select_if: Optional[str] = None

    @model_validator(mode="after")
    def validate_selection(self) -> "CaseSelectionParams":
        if self.filter_variable and self.select_if:
            raise ValueError("filter_variable and select_if cannot both be provided")
        if not self.filter_variable and not self.select_if:
            raise ValueError("At least one case selection option must be provided")
        return self


class LogisticRegressionParams(MethodParams):
    dependent: str
    predictors: list[str] = Field(min_length=1)
    method: Literal["ENTER", "FSTEP", "BSTEP"] = "ENTER"
    categorical: Optional[list[str]] = None
    contrast: Optional[str] = None
    save_predicted: bool = False
    print_options: Optional[list[str]] = None


class OrdinalRegressionParams(MethodParams):
    dependent: str
    predictors: list[str] = Field(min_length=1)
    link: Literal["LOGIT", "PROBIT", "CLOGLOG", "NLOGLOG", "CAUCHIT"] = "LOGIT"
    categorical: Optional[list[str]] = None
    save_predicted: bool = False
    test_parallel: bool = True


class GenlinParams(MethodParams):
    dependent: str
    predictors: list[str] = Field(min_length=1)
    distribution: Literal[
        "NORMAL", "BINOMIAL", "POISSON", "GAMMA", "IGAUSS", "NEGBIN", "MULTINOMIAL"
    ] = "NORMAL"
    link: Optional[str] = None
    scale: Optional[str] = None
    categorical: Optional[list[str]] = None
    save_predicted: bool = False


class MixedParams(MethodParams):
    dependent: str
    fixed_effects: list[str] = Field(min_length=1)
    random_effects: Optional[list[str]] = None
    subject: Optional[str] = None
    repeated: Optional[str] = None
    repeated_type: Optional[str] = None
    method: Literal["REML", "ML"] = "REML"
    covtype_random: Optional[str] = None

    @model_validator(mode="after")
    def validate_dependencies(self) -> "MixedParams":
        if self.random_effects and not self.subject:
            raise ValueError("subject is required when random_effects are provided")
        if self.repeated and not self.subject:
            raise ValueError("subject is required when repeated is provided")
        return self


class GenlinMixedParams(MethodParams):
    dependent: str
    fixed_effects: list[str] = Field(min_length=1)
    random_effects: Optional[list[str]] = None
    subject: Optional[str] = None
    distribution: Literal["NORMAL", "BINOMIAL", "POISSON", "GAMMA", "NEGBIN"] = "NORMAL"
    link: Optional[str] = None

    @model_validator(mode="after")
    def validate_subject(self) -> "GenlinMixedParams":
        if self.random_effects and not self.subject:
            raise ValueError("subject is required when random_effects are provided")
        return self


class CoxRegressionParams(MethodParams):
    time_variable: str
    status_variable: str
    status_event_value: int | str
    predictors: list[str] = Field(min_length=1)
    method: Literal["ENTER", "FSTEP", "BSTEP"] = "ENTER"
    categorical: Optional[list[str]] = None
    strata: Optional[list[str]] = None
    save_survival: bool = False


class KaplanMeierParams(MethodParams):
    time_variable: str
    status_variable: str
    status_event_value: int | str
    strata: Optional[str] = None
    compare_method: Literal["LOGRANK", "BRESLOW", "TARONE"] = "LOGRANK"
    percentiles: Optional[list[int]] = None


class DiscriminantParams(MethodParams):
    groups: str
    predictors: list[str] = Field(min_length=1)
    method: Literal["DIRECT", "WILKS", "MAHAL"] = "DIRECT"
    priors: Literal["EQUAL", "SIZE"] = "EQUAL"
    save_scores: bool = False
    save_class: bool = False


class HierarchicalClusterParams(MethodParams):
    variables: list[str] = Field(min_length=1)
    method: Literal[
        "BAVERAGE", "WAVERAGE", "SINGLE", "COMPLETE", "CENTROID", "MEDIAN", "WARD"
    ] = "WARD"
    measure: Literal[
        "SEUCLID", "EUCLID", "COSINE", "PEARSON", "CHEBYCHEV", "BLOCK", "MINKOWSKI", "CUSTOMIZED"
    ] = "SEUCLID"
    id_variable: Optional[str] = None
    dendrogram: bool = True


class TwoStepClusterParams(MethodParams):
    continuous: Optional[list[str]] = None
    categorical: Optional[list[str]] = None
    distance: Literal["EUCLID", "CHISQ"] = "EUCLID"
    num_clusters: Optional[int] = None
    max_clusters: int = 15
    outlier_handling: bool = True

    @model_validator(mode="after")
    def validate_inputs(self) -> "TwoStepClusterParams":
        if not self.continuous and not self.categorical:
            raise ValueError("Must specify at least one continuous or categorical variable")
        if self.num_clusters is not None and self.num_clusters < 1:
            raise ValueError("num_clusters must be at least 1")
        if self.max_clusters < 2:
            raise ValueError("max_clusters must be at least 2")
        return self


class ManovaParams(MethodParams):
    dependents: list[str] = Field(min_length=2)
    factors: list[str] = Field(min_length=1)
    covariates: Optional[list[str]] = None
    method: Literal["SSTYPE1", "SSTYPE2", "SSTYPE3", "SSTYPE4"] = "SSTYPE3"
    print_multivariate: bool = True
    print_univariate: bool = True


class GlmUnivariateParams(MethodParams):
    dependent: str
    factors: list[str] = Field(min_length=1)
    covariates: Optional[list[str]] = None
    emmeans: Optional[list[str]] = None
    posthoc: Optional[list[str]] = None
    posthoc_method: Optional[str] = None
    save_predicted: bool = False

    @model_validator(mode="after")
    def validate_posthoc(self) -> "GlmUnivariateParams":
        if self.posthoc and not self.posthoc_method:
            raise ValueError("posthoc_method is required when posthoc variables are provided")
        return self
