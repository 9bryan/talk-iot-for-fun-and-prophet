import os
import duckdb
import pandas as pd
from prophet import Prophet
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ─────────────────────────────
# Configuration
# ─────────────────────────────
AWS_REGION = "us-west-2"
S3_TABLE_PATH = (
    "s3://redpanda-cloud-storage-xxxxxxxxxx/"
    "redpanda-iceberg-catalog/redpanda/environment-data"
)

# ─────────────────────────────
# Load AWS credentials from environment
# ─────────────────────────────
aws_key = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")

if not aws_key or not aws_secret:
    raise EnvironmentError("❌ AWS credentials are missing from environment variables.")

# ─────────────────────────────
# Connect to DuckDB and configure Iceberg + S3
# ─────────────────────────────
con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs;")
con.execute("INSTALL iceberg; LOAD iceberg;")
con.execute(f"SET s3_region='{AWS_REGION}'")
con.execute(f"SET s3_access_key_id='{aws_key}'")
con.execute(f"SET s3_secret_access_key='{aws_secret}'")
con.execute("SET unsafe_enable_version_guessing = true;")

# ─────────────────────────────
# Query the last 7 days of data
# ─────────────────────────────
query = f"""
    SELECT device_id, time, temperature, humidity
    FROM iceberg_scan('{S3_TABLE_PATH}')
    WHERE 
        temperature IS NOT NULL AND
        humidity IS NOT NULL AND
        CAST(time AS TIMESTAMPTZ) >= now() - INTERVAL 7 DAY
    ORDER BY device_id, time
"""
df = con.execute(query).df()

# ─────────────────────────────
# Forecast per device using Prophet
# ─────────────────────────────
for device_id in df["device_id"].unique():
    device_df = df[df["device_id"] == device_id].copy()

    # Convert timestamp to datetime (assumed UTC)
    device_df["timestamp"] = pd.to_datetime(device_df["time"], utc=True)

    # Create plots for temperature and humidity
    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    for metric, ax in zip(["temperature", "humidity"], axes):
        regressor = "humidity" if metric == "temperature" else "temperature"

        # Prepare data for Prophet
        prophet_df = device_df[["timestamp", metric, regressor]].copy()
        prophet_df["ds"] = prophet_df["timestamp"].dt.tz_localize(None)
        prophet_df.rename(columns={metric: "y"}, inplace=True)
        prophet_df = prophet_df[["ds", "y", regressor]]

        # Train Prophet model
        model = Prophet(daily_seasonality=False, weekly_seasonality=False)
        model.add_regressor(regressor)
        model.fit(prophet_df)

        # Forecast 24 hours ahead (1440 minutes)
        future = model.make_future_dataframe(periods=1440, freq="min")
        last_val = prophet_df[regressor].iloc[-1]
        future[regressor] = (
            prophet_df.set_index("ds")[regressor]
            .reindex(future["ds"])
            .fillna(last_val)
            .values
        )
        forecast = model.predict(future)

        # Plot observed vs forecast
        ax.plot(prophet_df["ds"], prophet_df["y"], label="Observed", alpha=0.6)
        ax.plot(forecast["ds"], forecast["yhat"], label="Forecast", linestyle="--")

        # Annotate last prediction
        final_time = forecast["ds"].iloc[-1]
        final_val = forecast["yhat"].iloc[-1]
        ax.annotate(
            f"{final_val:.2f}",
            xy=(final_time, final_val),
            xytext=(final_time, final_val + 1),
            arrowprops=dict(arrowstyle="->"),
            fontsize=9,
        )

        ax.set_ylabel(metric.capitalize())
        ax.grid(True)
        ax.legend()

    # Format and save plot
    axes[1].set_xlabel("Time")
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%b %d %H:%M"))
    axes[1].xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate(rotation=45)

    axes[0].set_title(f"Temperature Forecast for {device_id}")
    axes[1].set_title(f"Humidity Forecast for {device_id}")
    plt.suptitle(
        f"IoT Forecast for {device_id} Using Prophet with Cross-Regressors",
        fontsize=16,
    )
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    filename = f"forecast_{device_id}_prophet.png"
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"✅ Saved forecast for {device_id} as {filename}")
