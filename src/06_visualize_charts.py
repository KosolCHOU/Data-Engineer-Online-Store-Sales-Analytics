from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# =========================
# Config
# =========================

OUTPUT_DIR = Path("output")
CHART_DIR = Path("charts")
CHART_DIR.mkdir(exist_ok=True)

sns.set_theme(style="whitegrid")


# =========================
# Helper: read Spark CSV output
# =========================

def read_spark_csv(folder_path: str) -> pd.DataFrame:
    """
    Spark writes CSV output as a folder with part-*.csv inside.
    This function finds the part file automatically.
    """
    folder = Path(folder_path)

    if folder.is_file():
        return pd.read_csv(folder)

    part_files = list(folder.glob("part-*.csv"))

    if not part_files:
        raise FileNotFoundError(f"No part-*.csv found in {folder_path}")

    return pd.read_csv(part_files[0])


# =========================
# 1. Top 10 countries by revenue
# =========================

def plot_top_countries():
    df = read_spark_csv(OUTPUT_DIR / "sales_by_country")

    df["total_revenue"] = pd.to_numeric(df["total_revenue"], errors="coerce")
    top_10 = df.sort_values("total_revenue", ascending=False).head(10)

    plt.figure(figsize=(10, 6))
    sns.barplot(
        data=top_10,
        x="total_revenue",
        y="country"
    )

    plt.title("Top 10 Countries by Revenue")
    plt.xlabel("Total Revenue")
    plt.ylabel("Country")
    plt.tight_layout()

    plt.savefig(CHART_DIR / "top_10_countries_by_revenue.png", dpi=300)
    plt.close()


# =========================
# 2. Top 10 products by revenue
# =========================

def plot_top_products():
    df = read_spark_csv(OUTPUT_DIR / "top_products")

    df["total_revenue"] = pd.to_numeric(df["total_revenue"], errors="coerce")

    top_10 = df.sort_values("total_revenue", ascending=False).head(10)

    # Shorten long product names for chart readability
    top_10["description_short"] = top_10["description"].astype(str).str.slice(0, 35)

    plt.figure(figsize=(11, 6))
    sns.barplot(
        data=top_10,
        x="total_revenue",
        y="description_short"
    )

    plt.title("Top 10 Products by Revenue")
    plt.xlabel("Total Revenue")
    plt.ylabel("Product")
    plt.tight_layout()

    plt.savefig(CHART_DIR / "top_10_products_by_revenue.png", dpi=300)
    plt.close()


# =========================
# 3. Monthly revenue trend
# =========================

def plot_monthly_sales():
    df = read_spark_csv(OUTPUT_DIR / "monthly_sales")

    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["month"] = pd.to_numeric(df["month"], errors="coerce").astype("Int64")
    df["total_revenue"] = pd.to_numeric(df["total_revenue"], errors="coerce")

    df = df.dropna(subset=["year", "month", "total_revenue"])
    df["year_month"] = df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2)

    df = df.sort_values(["year", "month"])

    plt.figure(figsize=(11, 6))
    plt.plot(df["year_month"], df["total_revenue"], marker="o")

    plt.title("Monthly Revenue Trend")
    plt.xlabel("Month")
    plt.ylabel("Total Revenue")
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig(CHART_DIR / "monthly_revenue_trend.png", dpi=300)
    plt.close()


# =========================
# 4. Orders by hour
# =========================

def plot_orders_by_hour():
    df = read_spark_csv(OUTPUT_DIR / "hourly_sales")

    df["hour"] = pd.to_numeric(df["hour"], errors="coerce")
    df["total_orders"] = pd.to_numeric(df["total_orders"], errors="coerce")

    df = df.dropna(subset=["hour", "total_orders"])
    df = df.sort_values("hour")

    plt.figure(figsize=(10, 6))
    sns.barplot(
        data=df,
        x="hour",
        y="total_orders"
    )

    plt.title("Orders by Hour")
    plt.xlabel("Hour of Day")
    plt.ylabel("Total Orders")
    plt.tight_layout()

    plt.savefig(CHART_DIR / "orders_by_hour.png", dpi=300)
    plt.close()


# =========================
# Run all charts
# =========================

if __name__ == "__main__":
    plot_top_countries()
    plot_top_products()
    plot_monthly_sales()
    plot_orders_by_hour()

    print("Charts generated successfully in the charts/ folder.")