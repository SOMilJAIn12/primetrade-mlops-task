import pandas as pd
import json
import time
import argparse
import yaml
import numpy as np
import logging

parser = argparse.ArgumentParser()

parser.add_argument("--input", required=True)
parser.add_argument("--config", required=True)
parser.add_argument("--output", required=True)
parser.add_argument("--log-file", required=True)

args = parser.parse_args()
start_time = time.time()

logging.basicConfig(
    filename=args.log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
try:
    logging.info("Job started")

    # Load config
    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    required_keys = ["seed", "window", "version"]

    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing config key: {key}")

    window = config["window"]
    seed = config["seed"]
    version = config["version"]

    logging.info(f"Config loaded: seed={seed}, window={window}, version={version}")
    np.random.seed(seed)


    
    df = pd.read_csv(args.input)

    if df.empty:
        raise ValueError("Input file is empty")

    if len(df.columns) == 1 and "close" not in df.columns:
        df = df.iloc[:, 0].str.split(",", expand=True)

        if df.shape[1] != 7:
            raise ValueError("Invalid CSV format")

        df.columns = [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume_btc",
            "volume_usd"
        ]

    if "close" not in df.columns:
        raise ValueError("Missing required column: close")
    df["close"] = pd.to_numeric(df["close"],errors="raise")
    logging.info(f"Rows loaded: {len(df)}")

    # processing
    

    df["rolling_mean"] = df["close"].rolling(window).mean()
    
    logging.info("Rolling mean computed")

    df["signal"] = (
        df["close"] > df["rolling_mean"]
    ).astype(int)
    logging.info("Signal generated")

    signal_rate = df["signal"].mean()

    latency_ms = round(
        (time.time() - start_time) * 1000
    )
    
    #output metrics
    metrics = {
        "version": version,
        "rows_processed": len(df),
        "metric": "signal_rate",
        "value": float(round(signal_rate, 4)),
        "latency_ms": latency_ms,
        "seed": seed,
        "status": "success"
    }
    logging.info(f"Metrics: {metrics}")
    logging.info("Job completed successfully")

except Exception as e:
    logging.error(str(e))

    metrics = {
        "version": "v1",
        "status": "error",
        "error_message": str(e)
    }

finally:

    with open(args.output, "w") as f:
        json.dump(metrics, f, indent=4)

print(metrics)