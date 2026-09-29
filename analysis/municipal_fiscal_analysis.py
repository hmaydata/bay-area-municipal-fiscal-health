import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


# ============================================================
# Municipal Fiscal Health Analysis
# ============================================================


# ------------------------------------------------------------
# 1. File paths
# ------------------------------------------------------------

data_path = Path("data/municipal_kpi_raw.xlsx")
figures_path = Path("figures")

figures_path.mkdir(exist_ok=True)


# ------------------------------------------------------------
# 2. Cities and consistent chart colors
# ------------------------------------------------------------

cities = [
    "Burlingame",
    "Saratoga",
    "Campbell",
    "Los Gatos",
    "Morgan Hill",
    "Los Altos"
]

city_colors = {
    "Burlingame": "tab:blue",
    "Saratoga": "tab:orange",
    "Campbell": "tab:green",
    "Los Gatos": "tab:red",
    "Morgan Hill": "tab:purple",
    "Los Altos": "tab:brown"
}


# ------------------------------------------------------------
# 3. Load and clean city worksheets
# ------------------------------------------------------------

all_cities = []

for city in cities:

    df = pd.read_excel(
        data_path,
        sheet_name=city,
        header=1
    )

    # Remove leading/trailing spaces from column names
    df.columns = df.columns.astype(str).str.strip()

    # Standardize column names that vary across city worksheets
    df = df.rename(columns={

        # General Fund expenditures
        "Expenditure":
            "Expenditure (General Fund)",

        # Capital spending
        "CIP Spending/ Capital Outlay":
            "CIP Spending",

        # Miscellaneous pension funding ratio
        "Misc Pension Funding Ratio -RSI":
            "Misc Pension Funding Ratio",

        "Misc Plan Pension Funding Ratio":
            "Misc Pension Funding Ratio",

        # Safety pension funding ratio
        "Safety Pension Funding Ratio- RSI":
            "Safety Pension Funding Ratio",

        "Safety Plan Pension Funding Ration":
            "Safety Pension Funding Ratio",

        # Net pension liability
        "Net pension liability":
            "Net Pension Liability"
    })

    # Keep only variables used in this analysis
    df = df[[
        "Year",
        "Population",
        "Revenue (General Fund)",
        "Expenditure (General Fund)",
        "CIP Spending",
        "Unassigned Fund Balance",
        "Property Tax",
        "Misc Pension Funding Ratio",
        "Safety Pension Funding Ratio",
        "Net Pension Liability"
    ]].copy()

    df["City"] = city

    all_cities.append(df)


# ------------------------------------------------------------
# 4. Combine cities into one dataframe
# ------------------------------------------------------------

municipal = pd.concat(
    all_cities,
    ignore_index=True
)


# ------------------------------------------------------------
# 5. Rename variables for Python analysis
# ------------------------------------------------------------

municipal = municipal.rename(columns={
    "Year": "year",
    "Population": "population",
    "Revenue (General Fund)": "revenue",
    "Expenditure (General Fund)": "expenditures",
    "CIP Spending": "cip_spending",
    "Unassigned Fund Balance": "unassigned_fund_balance",
    "Property Tax": "property_tax",

    "Misc Pension Funding Ratio":
        "misc_pension_funded_ratio",

    "Safety Pension Funding Ratio":
        "safety_pension_funded_ratio",

    "Net Pension Liability":
        "net_pension_liability",

    "City": "city"
})


municipal = (
    municipal
    .sort_values(["city", "year"])
    .reset_index(drop=True)
)


# ------------------------------------------------------------
# 6. Create fiscal metrics
# ------------------------------------------------------------

municipal["operating_surplus"] = (
    municipal["revenue"]
    - municipal["expenditures"]
)

municipal["operating_margin"] = (
    municipal["operating_surplus"]
    / municipal["revenue"]
)

municipal["revenue_per_capita"] = (
    municipal["revenue"]
    / municipal["population"]
)

municipal["expenditures_per_capita"] = (
    municipal["expenditures"]
    / municipal["population"]
)

municipal["reserve_ratio"] = (
    municipal["unassigned_fund_balance"]
    / municipal["expenditures"]
)

municipal["property_tax_share"] = (
    municipal["property_tax"]
    / municipal["revenue"]
)

municipal["npl_to_revenue"] = (
    municipal["net_pension_liability"]
    / municipal["revenue"]
)

municipal["npl_per_capita"] = (
    municipal["net_pension_liability"]
    / municipal["population"]
)

municipal["revenue_growth"] = (
    municipal.groupby("city")["revenue"]
    .pct_change()
)

municipal["expenditure_growth"] = (
    municipal.groupby("city")["expenditures"]
    .pct_change()
)


# ------------------------------------------------------------
# 7. City-level summary statistics
# ------------------------------------------------------------

summary = (
    municipal
    .groupby("city")
    .agg(
        avg_revenue_growth=(
            "revenue_growth",
            "mean"
        ),

        avg_expenditure_growth=(
            "expenditure_growth",
            "mean"
        ),

        avg_operating_margin=(
            "operating_margin",
            "mean"
        ),

        avg_reserve_ratio=(
            "reserve_ratio",
            "mean"
        ),

        avg_property_tax_share=(
            "property_tax_share",
            "mean"
        ),

        avg_npl_to_revenue=(
            "npl_to_revenue",
            "mean"
        ),

        revenue_volatility=(
            "revenue_growth",
            "std"
        )
    )
    .reset_index()
)


# Convert ratios to percentage points where appropriate
percent_columns = [
    "avg_revenue_growth",
    "avg_expenditure_growth",
    "avg_operating_margin",
    "avg_reserve_ratio",
    "avg_property_tax_share",
    "revenue_volatility"
]

summary[percent_columns] = (
    summary[percent_columns] * 100
)

summary = summary.round(2)


# ------------------------------------------------------------
# 8. Print summary
# ------------------------------------------------------------

pd.set_option(
    "display.max_columns",
    None
)

pd.set_option(
    "display.width",
    200
)

print()
print("CITY-LEVEL FISCAL SUMMARY")
print(summary)


# ============================================================
# GRAPH 1
# General Fund Operating Margin
# ============================================================

plt.figure(
    figsize=(10, 6)
)

for city in cities:

    city_data = municipal[
        municipal["city"] == city
    ]

    plt.plot(
        city_data["year"],
        city_data["operating_margin"] * 100,
        marker="o",
        linewidth=2,
        color=city_colors[city],
        label=city
    )

plt.axhline(
    0,
    color="black",
    linewidth=1,
    linestyle="--"
)

plt.title(
    "General Fund Operating Margin by City"
)

plt.xlabel(
    "Fiscal Year"
)

plt.ylabel(
    "Operating Margin (%)"
)

plt.legend(
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.grid(
    axis="y",
    alpha=0.25
)

plt.tight_layout()

plt.savefig(
    figures_path / "operating_margin_trend.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ============================================================
# GRAPH 2
# Average Revenue Growth vs. Revenue Volatility
# ============================================================

plt.figure(
    figsize=(8, 6)
)

for _, row in summary.iterrows():

    plt.scatter(
        row["revenue_volatility"],
        row["avg_revenue_growth"],
        s=100,
        color=city_colors[row["city"]]
    )

    plt.annotate(
        row["city"],
        (
            row["revenue_volatility"],
            row["avg_revenue_growth"]
        ),
        xytext=(6, 6),
        textcoords="offset points"
    )

plt.title(
    "Average Revenue Growth and Volatility, 2016–2025"
)

plt.xlabel(
    "Revenue Growth Volatility (%)"
)

plt.ylabel(
    "Average Annual Revenue Growth (%)"
)

plt.grid(
    alpha=0.25
)

plt.tight_layout()

plt.savefig(
    figures_path / "revenue_growth_vs_volatility.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ============================================================
# GRAPH 3
# Average Property Tax Share
# ============================================================

property_tax_summary = (
    summary
    .sort_values(
        "avg_property_tax_share",
        ascending=True
    )
)

plt.figure(
    figsize=(8, 5)
)

plt.barh(
    property_tax_summary["city"],
    property_tax_summary["avg_property_tax_share"],
    color=property_tax_summary["city"].map(city_colors)
)

plt.title(
    "Average Property Tax Share of General Fund Revenue"
)

plt.xlabel(
    "Property Tax Share (%)"
)

plt.ylabel("")

plt.grid(
    axis="x",
    alpha=0.25
)

plt.tight_layout()

plt.savefig(
    figures_path / "property_tax_share.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ============================================================
# GRAPH 4
# Net Pension Liability Relative to Revenue
# ============================================================

latest = (
    municipal[
        municipal["year"] == 2025
    ]
    .copy()
)

latest["npl_to_revenue_pct"] = (
    latest["npl_to_revenue"] * 100
)

latest = latest.sort_values(
    "npl_to_revenue_pct",
    ascending=True
)

plt.figure(
    figsize=(8, 5)
)

plt.barh(
    latest["city"],
    latest["npl_to_revenue_pct"],
    color=latest["city"].map(city_colors)
)

plt.title(
    "Net Pension Liability Relative to General Fund Revenue, 2025"
)

plt.xlabel(
    "Net Pension Liability / Revenue (%)"
)

plt.ylabel("")

plt.grid(
    axis="x",
    alpha=0.25
)

plt.tight_layout()

plt.savefig(
    figures_path / "npl_to_revenue_2025.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ============================================================
# GRAPH 5
# General Fund Reserve Ratio
# ============================================================

# Los Gatos is excluded from this graph because its reserve
# reporting is not directly comparable across the full period.

reserve_cities = [
    "Burlingame",
    "Saratoga",
    "Campbell",
    "Morgan Hill",
    "Los Altos"
]

plt.figure(
    figsize=(10, 6)
)

for city in reserve_cities:

    city_data = municipal[
        municipal["city"] == city
    ].sort_values("year")

    plt.plot(
        city_data["year"],
        city_data["reserve_ratio"] * 100,
        marker="o",
        linewidth=2,
        color=city_colors[city],
        label=city
    )

# Los Altos formal reserve policy minimum
plt.axhline(
    20,
    color="black",
    linestyle="--",
    linewidth=1.5,
    label="Los Altos 20% Policy Minimum"
)

plt.title(
    "General Fund Reserve Ratio by City"
)

plt.xlabel(
    "Fiscal Year"
)

plt.ylabel(
    "Unassigned Fund Balance / Expenditures (%)"
)

plt.legend(
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.grid(
    alpha=0.25
)

plt.tight_layout()

plt.savefig(
    figures_path / "reserve_ratio_trend.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()