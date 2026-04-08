from spss_mcp.method_registry import build_registered_syntax


def test_logistic_template_contains_expected_sections():
    syntax = build_registered_syntax(
        "spss_logistic_regression",
        "F:/data/example.sav",
        dependent="outcome",
        predictors=["x1", "x2"],
    )
    assert "LOGISTIC REGRESSION VARIABLES outcome" in syntax
    assert "/METHOD=ENTER x1 x2" in syntax
    assert "/PRINT=GOODFIT CI(95)" in syntax


def test_twostep_template_uses_auto_clusters_by_default():
    syntax = build_registered_syntax(
        "spss_twostep_cluster",
        "F:/data/example.sav",
        continuous=["x1", "x2"],
    )
    assert "TWOSTEP CLUSTER" in syntax
    assert "/NUMCLUSTERS=AUTO(15)" in syntax


def test_manova_template_contains_design_block():
    syntax = build_registered_syntax(
        "spss_manova",
        "F:/data/example.sav",
        dependents=["y1", "y2"],
        factors=["group"],
    )
    assert "MANOVA y1 y2 BY group" in syntax
    assert "/DESIGN." in syntax
