from __future__ import annotations

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


def _slash_file(file_path: str) -> str:
    return file_path.replace(chr(92), "/")


def render_logistic_regression(file_path: str, params: LogisticRegressionParams) -> str:
    syntax = f"GET FILE='{_slash_file(file_path)}'.\n"
    syntax += f"LOGISTIC REGRESSION VARIABLES {params.dependent}\n"
    syntax += f"  /METHOD={params.method} {' '.join(params.predictors)}\n"
    if params.categorical:
        cat_spec = ' '.join(params.categorical)
        if params.contrast:
            syntax += f"  /CATEGORICAL={cat_spec}({params.contrast})\n"
        else:
            syntax += f"  /CATEGORICAL={cat_spec}\n"
    if params.save_predicted:
        syntax += "  /SAVE=PRED PGROUP\n"
    if params.print_options:
        syntax += f"  /PRINT={' '.join(params.print_options)}\n"
    else:
        syntax += "  /PRINT=GOODFIT CI(95)\n"
    syntax += "  /CRITERIA=PIN(0.05) POUT(0.10) ITERATE(20) CUT(0.5).\n"
    return syntax


def render_ordinal_regression(file_path: str, params: OrdinalRegressionParams) -> str:
    syntax = f"GET FILE='{_slash_file(file_path)}'.\n"
    syntax += f"PLUM {params.dependent} WITH {' '.join(params.predictors)}\n"
    syntax += f"  /LINK={params.link}\n"
    if params.categorical:
        syntax += f"  /CATEGORICAL={' '.join(params.categorical)}\n"
    if params.save_predicted:
        syntax += "  /SAVE=PCPROB ACPROB\n"
    syntax += "  /PRINT=FIT PARAMETER SUMMARY\n"
    if params.test_parallel:
        syntax += "  /TEST=PARALLEL\n"
    syntax += "  /CRITERIA=CIN(95) DELTA(0) LCONVERGE(0) MXITER(100) MXSTEP(5) PCONVERGE(1.0E-6) SINGULAR(1.0E-8).\n"
    return syntax


def render_genlin(file_path: str, params: GenlinParams) -> str:
    syntax = f"GET FILE='{_slash_file(file_path)}'.\n"
    syntax += f"GENLIN {params.dependent}"
    if params.predictors:
        syntax += f" WITH {' '.join(params.predictors)}\n"
    else:
        syntax += "\n"
    if params.categorical:
        syntax += f"  /CATEGORICAL={' '.join(params.categorical)}\n"
    syntax += f"  /MODEL {' '.join(params.predictors)} DISTRIBUTION={params.distribution}"
    if params.link:
        syntax += f" LINK={params.link}\n"
    else:
        syntax += "\n"
    if params.scale:
        syntax += f"  /SCALE={params.scale}\n"
    if params.save_predicted:
        syntax += "  /SAVE=PRED RESID\n"
    syntax += "  /PRINT=SOLUTION SUMMARY\n"
    syntax += "  /CRITERIA=SCALE=1 COVB=MODEL PCONVERGE=1E-6 SINGULAR=1E-12 ANALYSISTYPE=3(WALD) CILEVEL=95 CITYPE=WALD LIKELIHOOD=FULL.\n"
    return syntax


def render_mixed(file_path: str, params: MixedParams) -> str:
    syntax = f"GET FILE='{_slash_file(file_path)}'.\n"
    syntax += f"MIXED {params.dependent}"
    if params.fixed_effects:
        syntax += f" WITH {' '.join(params.fixed_effects)}\n"
    else:
        syntax += "\n"
    syntax += f"  /FIXED={' '.join(params.fixed_effects)}\n"
    if params.random_effects and params.subject:
        random_spec = ' '.join(params.random_effects) if params.random_effects else "INTERCEPT"
        syntax += f"  /RANDOM={random_spec} | SUBJECT({params.subject})"
        if params.covtype_random:
            syntax += f" COVTYPE({params.covtype_random})\n"
        else:
            syntax += "\n"
    if params.repeated and params.subject:
        syntax += f"  /REPEATED={params.repeated} | SUBJECT({params.subject})"
        if params.repeated_type:
            syntax += f" COVTYPE({params.repeated_type})\n"
        else:
            syntax += " COVTYPE(AR1)\n"
    syntax += f"  /METHOD={params.method}\n"
    syntax += "  /PRINT=SOLUTION TESTCOV\n"
    syntax += "  /CRITERIA=CIN(95) MXITER(100) MXSTEP(10) SCORING(1) SINGULAR(0.000000000001) HCONVERGE(0, ABSOLUTE) LCONVERGE(0, ABSOLUTE) PCONVERGE(0.000001, ABSOLUTE).\n"
    return syntax


def render_genlinmixed(file_path: str, params: GenlinMixedParams) -> str:
    syntax = f"GET FILE='{_slash_file(file_path)}'.\n"
    syntax += "GENLINMIXED\n"
    syntax += f"  /DATA_STRUCTURE SUBJECTS={params.subject}\n" if params.subject else ""
    syntax += f"  /FIELDS TARGET={params.dependent} TRIALS=NONE OFFSET=NONE\n"
    if params.fixed_effects:
        syntax += f"  /FIXED EFFECTS={' '.join(params.fixed_effects)} USE_INTERCEPT=TRUE\n"
    else:
        syntax += "  /FIXED USE_INTERCEPT=TRUE\n"
    if params.random_effects and params.subject:
        syntax += f"  /RANDOM EFFECTS={' '.join(params.random_effects)} USE_INTERCEPT=TRUE SUBJECTS={params.subject}\n"
    syntax += "  /BUILD_OPTIONS TARGET_CATEGORY_ORDER=ASCENDING INPUTS_CATEGORY_ORDER=ASCENDING MAX_ITERATIONS=100 CONFIDENCE_LEVEL=95 DF_METHOD=RESIDUAL COVB=ROBUST\n"
    syntax += f"  /TARGET_OPTIONS DISTRIBUTION={params.distribution}"
    if params.link:
        syntax += f" LINK={params.link}\n"
    else:
        syntax += "\n"
    syntax += "  /PRINT SOLUTION.\n"
    return syntax


def render_cox_regression(file_path: str, params: CoxRegressionParams) -> str:
    syntax = f"GET FILE='{_slash_file(file_path)}'.\n"
    syntax += f"COXREG {params.time_variable}\n"
    syntax += f"  /STATUS={params.status_variable}({params.status_event_value})\n"
    syntax += f"  /METHOD={params.method} {' '.join(params.predictors)}\n"
    if params.categorical:
        syntax += f"  /CATEGORICAL={' '.join(params.categorical)}\n"
    if params.strata:
        syntax += f"  /STRATA={' '.join(params.strata)}\n"
    if params.save_survival:
        syntax += "  /SAVE=SURVIVAL HAZARD\n"
    syntax += "  /PRINT=CI(95)\n"
    syntax += "  /CRITERIA=PIN(.05) POUT(.10) ITERATE(20).\n"
    return syntax


def render_kaplan_meier(file_path: str, params: KaplanMeierParams) -> str:
    syntax = f"GET FILE='{_slash_file(file_path)}'.\n"
    syntax += f"KM {params.time_variable}"
    if params.strata:
        syntax += f" BY {params.strata}\n"
    else:
        syntax += "\n"
    syntax += f"  /STATUS={params.status_variable}({params.status_event_value})\n"
    if params.strata:
        syntax += f"  /COMPARE={params.compare_method}\n"
    syntax += "  /PRINT=TABLE MEAN\n"
    if params.percentiles:
        syntax += f"  /PERCENTILES={' '.join(map(str, params.percentiles))}\n"
    syntax += "  /PLOT=SURVIVAL.\n"
    return syntax


def render_discriminant(file_path: str, params: DiscriminantParams) -> str:
    syntax = f"GET FILE='{_slash_file(file_path)}'.\n"
    syntax += "DISCRIMINANT\n"
    syntax += f"  /GROUPS={params.groups}\n"
    syntax += f"  /VARIABLES={' '.join(params.predictors)}\n"
    syntax += "  /ANALYSIS ALL\n"
    syntax += f"  /METHOD={params.method}\n"
    syntax += f"  /PRIORS={params.priors}\n"
    if params.save_scores or params.save_class:
        save_opts = []
        if params.save_scores:
            save_opts.append("SCORES")
        if params.save_class:
            save_opts.append("CLASS")
        syntax += f"  /SAVE={' '.join(save_opts)}\n"
    syntax += "  /STATISTICS=MEAN STDDEV UNIVF BOXM COEF RAW CORR COV GCOV TABLE\n"
    syntax += "  /CLASSIFY=NONMISSING POOLED.\n"
    return syntax


def render_cluster_hierarchical(file_path: str, params: HierarchicalClusterParams) -> str:
    syntax = f"GET FILE='{_slash_file(file_path)}'.\n"
    syntax += f"CLUSTER {' '.join(params.variables)}\n"
    if params.id_variable:
        syntax += f"  /ID={params.id_variable}\n"
    syntax += f"  /METHOD={params.method}\n"
    syntax += f"  /MEASURE={params.measure}\n"
    syntax += "  /PRINT=SCHEDULE CLUSTER(2,4)\n"
    if params.dendrogram:
        syntax += "  /PLOT=DENDROGRAM VICICLE.\n"
    else:
        syntax += ".\n"
    return syntax


def render_twostep_cluster(file_path: str, params: TwoStepClusterParams) -> str:
    syntax = f"GET FILE='{_slash_file(file_path)}'.\n"
    syntax += "TWOSTEP CLUSTER\n"
    if params.continuous:
        syntax += f"  /CONTINUOUS {' '.join(params.continuous)}\n"
    if params.categorical:
        syntax += f"  /CATEGORICAL {' '.join(params.categorical)}\n"
    syntax += f"  /DISTANCE={params.distance}\n"
    if params.num_clusters:
        syntax += f"  /NUMCLUSTERS=FIXED({params.num_clusters})\n"
    else:
        syntax += f"  /NUMCLUSTERS=AUTO({params.max_clusters})\n"
    if params.outlier_handling:
        syntax += "  /OUTLIERS=YES\n"
    syntax += "  /PRINT=MODELINFO CLUSTERINFO\n"
    syntax += "  /PLOT=SILHOUETTE.\n"
    return syntax


def render_manova(file_path: str, params: ManovaParams) -> str:
    syntax = f"GET FILE='{_slash_file(file_path)}'.\n"
    syntax += f"MANOVA {' '.join(params.dependents)} BY {' '.join(params.factors)}"
    if params.covariates:
        syntax += f" WITH {' '.join(params.covariates)}\n"
    else:
        syntax += "\n"
    syntax += f"  /METHOD={params.method}\n"
    print_opts = []
    if params.print_multivariate:
        print_opts.append("SIGNIF(MULTIV)")
    if params.print_univariate:
        print_opts.append("SIGNIF(UNIV)")
    if print_opts:
        syntax += f"  /PRINT={' '.join(print_opts)}\n"
    syntax += "  /DESIGN.\n"
    return syntax


def render_glm_univariate(file_path: str, params: GlmUnivariateParams) -> str:
    syntax = f"GET FILE='{_slash_file(file_path)}'.\n"
    syntax += f"UNIANOVA {params.dependent} BY {' '.join(params.factors)}"
    if params.covariates:
        syntax += f" WITH {' '.join(params.covariates)}\n"
    else:
        syntax += "\n"
    if params.emmeans:
        for var in params.emmeans:
            syntax += f"  /EMMEANS=TABLES({var})\n"
    if params.posthoc and params.posthoc_method:
        syntax += f"  /POSTHOC={' '.join(params.posthoc)}({params.posthoc_method})\n"
    if params.save_predicted:
        syntax += "  /SAVE=PRED RESID\n"
    syntax += "  /PRINT=DESCRIPTIVE ETASQ HOMOGENEITY\n"
    syntax += "  /CRITERIA=ALPHA(.05)\n"
    syntax += "  /DESIGN.\n"
    return syntax
