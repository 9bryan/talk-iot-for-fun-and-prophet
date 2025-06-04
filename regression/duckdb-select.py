import os
import duckdb

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

# ─────────────────────────────
# Query the last 7 days of non-null temperature & humidity data
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
print(df.head())
