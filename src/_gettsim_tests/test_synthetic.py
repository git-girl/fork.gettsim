from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from _gettsim.synthetic import create_synthetic_data


@pytest.fixture()
def synthetic_data_with_defaults():
    return create_synthetic_data()


@pytest.fixture()
def synthetic_data_couple_with_children():
    return create_synthetic_data(n_adults=2, n_children=2)


@pytest.fixture()
def synthetic_data_alleinerziehend():
    return create_synthetic_data(n_adults=1, n_children=1)


@pytest.fixture()
def synthetic_data_no_children():
    return create_synthetic_data(n_adults=2, n_children=0)


@pytest.fixture()
def synthetic_data_spec_variables():
    df = create_synthetic_data(
        n_adults=2,
        n_children=1,
        specs_constant_over_households={
            "alter": [50, 30, 5],
            "bruttolohn_m": [1000, 2000, 0],
        },
    )
    return df


@pytest.fixture()
def synthetic_data_spec_heterogeneous():
    df = create_synthetic_data(
        n_adults=2,
        n_children=1,
        specs_constant_over_households={"alter": [50, 30, 5]},
        specs_heterogeneous={
            "bruttolohn_m": [[i / 2, i / 2, 0] for i in range(0, 1001, 100)]
        },
    )
    return df


synthetic_data_fixtures_not_heterogeneous = [
    ("synthetic_data_with_defaults"),
    ("synthetic_data_couple_with_children"),
    ("synthetic_data_spec_variables"),
]

synthetic_data_fixtures = [
    *synthetic_data_fixtures_not_heterogeneous,
    "synthetic_data_spec_heterogeneous",
]


@pytest.mark.parametrize(
    "df",
    synthetic_data_fixtures,
)
def test_positive_rent(df, request):
    df = request.getfixturevalue(df)
    assert df["bruttokaltmiete_m_hh"].min() > 0


@pytest.mark.parametrize(
    "df",
    synthetic_data_fixtures,
)
def test_no_nans(df, request):
    df = request.getfixturevalue(df)
    assert df["bruttokaltmiete_m_hh"].notna().all().all()


@pytest.mark.parametrize(
    "df",
    synthetic_data_fixtures_not_heterogeneous,
)
def test_unique_p_id(df, request):
    df = request.getfixturevalue(df)
    assert df["p_id"].is_unique


@pytest.mark.parametrize(
    "df",
    synthetic_data_fixtures_not_heterogeneous,
)
def test_constant_hh_id(df, request):
    df = request.getfixturevalue(df)
    assert (df["hh_id"].max() == df["hh_id"]).all()


@pytest.mark.parametrize(
    "df, exp_n_rows",
    [
        ("synthetic_data_with_defaults", 1),
        ("synthetic_data_couple_with_children", 4),
        ("synthetic_data_spec_variables", 3),
        ("synthetic_data_spec_heterogeneous", 33),
    ],
)
def test_correct_size(df, exp_n_rows, request):
    df = request.getfixturevalue(df)
    assert df.shape[0] == exp_n_rows


def test_alleinerziehend(synthetic_data_alleinerziehend):
    pd.testing.assert_series_equal(
        synthetic_data_alleinerziehend["alleinerz"],
        pd.Series([True, False], name="alleinerz"),
    )


@pytest.mark.parametrize(
    "col, expected",
    [
        ("alter", [50, 30, 5]),
        ("bruttolohn_m", [1000, 2000, 0]),
    ],
)
def test_specs_constant_over_households(col, expected, synthetic_data_spec_variables):
    pd.testing.assert_series_equal(
        synthetic_data_spec_variables[col], pd.Series(expected, name=col)
    )


@pytest.mark.parametrize(
    "col, expected",
    [
        ("alter", [50, 30, 5] * 11),
        (
            "bruttolohn_m",
            np.concatenate([[i / 2, i / 2, 0] for i in range(0, 1001, 100)]),
        ),
    ],
)
def test_specs_heterogeneous(col, expected, synthetic_data_spec_heterogeneous):
    pd.testing.assert_series_equal(
        synthetic_data_spec_heterogeneous[col], pd.Series(expected, name=col)
    )


@pytest.mark.parametrize(
    "n_adults, n_children, specs_constant_over_households,"
    " specs_heterogeneous, expectation",
    [
        (0, 2, None, None, pytest.raises(ValueError, match="'n_adults' must be")),
        (3, 2, None, None, pytest.raises(ValueError, match="'n_adults' must be")),
        (2, 11, None, None, pytest.raises(ValueError, match="'n_children' must be")),
        (2, 0, {"alter": [30]}, None, pytest.raises(ValueError, match="Length of")),
        (
            2,
            0,
            None,
            {"alter": [[30, 20], [40, 30]], "bruttolohn_m": [[300, 200]]},
            pytest.raises(ValueError, match="Length of"),
        ),
    ],
)
def test_fail_if_functions_and_columns_overlap(
    n_adults,
    n_children,
    specs_constant_over_households,
    specs_heterogeneous,
    expectation,
):
    with expectation:
        create_synthetic_data(
            n_adults=n_adults,
            n_children=n_children,
            specs_constant_over_households=specs_constant_over_households,
            specs_heterogeneous=specs_heterogeneous,
        )


@pytest.mark.parametrize(
    "fixture, expected",
    [
        (
            "synthetic_data_spec_heterogeneous",
            {
                "p_id": list(range(33)),
                "p_id_elternteil_1": [-1 if i % 3 != 2 else i - 2 for i in range(33)],
                "p_id_elternteil_2": [-1 if i % 3 != 2 else i - 1 for i in range(33)],
                "p_id_kindergeld_empf": [
                    -1 if i % 3 != 2 else i - 2 for i in range(33)
                ],
                "p_id_erziehgeld_empf": [
                    -1 if i % 3 != 2 else i - 2 for i in range(33)
                ],
            },
        ),
        (
            "synthetic_data_alleinerziehend",
            {
                "p_id": [0, 1],
                "p_id_elternteil_1": [-1, 0],
                "p_id_elternteil_2": [-1, -1],
                "p_id_kindergeld_empf": [-1, 0],
                "p_id_erziehgeld_empf": [-1, 0],
            },
        ),
        (
            "synthetic_data_no_children",
            {
                "p_id": [0, 1],
                "p_id_elternteil_1": [-1, -1],
                "p_id_elternteil_2": [-1, -1],
                "p_id_kindergeld_empf": [-1, -1],
                "p_id_erziehgeld_empf": [-1, -1],
            },
        ),
    ],
)
def test_p_id_elternteil(fixture, expected, request):
    df = request.getfixturevalue(fixture)
    for col, values in expected.items():
        pd.testing.assert_series_equal(df[col], pd.Series(values, name=col))
