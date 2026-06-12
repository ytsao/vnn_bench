import sys
import os
import json
import re
import pandas as pd
from pathlib import Path
from ruamel.yaml import YAML

# 初始化 YAML
yaml = YAML(typ="safe")
yaml.default_flow_style = False

# 預設欄位順序
DEFAULT_STAT_COLUMNS = [
    "configuration",
    "problem",
    "model",
    "data_file",
    "mzn_solver",
    "status",
    "time",
]

# 狀態對照表
STATUS_MAP = {
    "sat": "SATISFIED",
    "unsat": "UNSATISFIABLE",
    "satisfied": "SATISFIED",
    "unsatisfiable": "UNSATISFIABLE",
    "unknown": "UNKNOWN",
    "timeout": "UNKNOWN"
}


def normalize_column_name(key: str) -> str:
    key = str(key).strip()
    key = key.lower().replace(" ", "_")
    key = re.sub(r"[^a-z0-9_]+", "_", key)
    key = re.sub(r"_+", "_", key).strip("_")
    return key or "field"


def flatten_json(value, parent_key: str = "", sep: str = "."):
    if isinstance(value, dict):
        result = {}
        for key, nested in value.items():
            full_key = f"{parent_key}{sep}{key}" if parent_key else str(key)
            result.update(flatten_json(nested, full_key, sep=sep))
        return result
    if isinstance(value, (list, tuple)):
        return {parent_key: json.dumps(value, ensure_ascii=False)}
    return {parent_key: value}


def parse_last_row(raw_line: str):
    try:
        parsed = json.loads(raw_line)
        if isinstance(parsed, dict):
            return {normalize_column_name(k): v for k, v in flatten_json(parsed).items()}
        return {"value": parsed}
    except json.JSONDecodeError:
        info = {}
        for match in re.finditer(r"([A-Za-z0-9 _%]+?)\s*[:=]\s*([^,]+)", raw_line):
            key = normalize_column_name(match.group(1))
            value = match.group(2).strip()
            info[key] = value
        return info

def get_standard_status(raw_status):
    if not raw_status: return "UNKNOWN"
    s = str(raw_status).lower().strip('= ')
    return STATUS_MAP.get(s, "UNKNOWN")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(1)

    output_dir = sys.argv[1].rstrip("/")
    input_file = Path(sys.argv[2])
    uid = input_file.stem

    stats_filename = Path(output_dir) / f"{uid}_stats.yml"
    sol_filename = Path(output_dir) / f"{uid}_sol.yml"

    # 初始化容器
    statistics = {"configuration": uid, "status": "UNKNOWN"}
    solutions = []
    unknowns = []
    errors = []
    json_rows = []
    last_line_raw = None
    last_line_info = {}

    if input_file.exists():
        with open(input_file, "r") as f:
            for line_idx, line in enumerate(f):
                clean_line = line.strip()
                if not clean_line:
                    continue
                last_line_raw = clean_line

                try:
                    # 1. 嘗試解析為 JSON
                    output = json.loads(clean_line)
                    if output.get("type") == "statistics":
                        row = {
                            "file_name": input_file.name,
                            "file_configuration": uid,
                            "line_index": line_idx,
                            "line_type": "json",
                            "json_type": output.get("type"),
                        }
                        row.update(flatten_json(output))
                        json_rows.append(row)

                    if output.get("type") == "lattice-land" and output.get("lattice-land") == "start":
                        statistics = {"configuration": uid, "status": "UNKNOWN"}
                        solutions, unknowns, errors = [], [], []
                        continue

                    if output.get("type") == "statistics":
                        s_data = output.get("statistics", {})
                        if "status" in s_data:
                            s_data["status"] = get_standard_status(s_data["status"])
                        # 若 JSON 內有 time (ms)，轉為 sec
                        if "time" in s_data:
                            s_data["time"] = float(s_data["time"]) / 1000.0
                        statistics.update(s_data)

                    elif output.get("type") == "status":
                        statistics["status"] = get_standard_status(output.get("status"))

                    elif output.get("type") == "solution":
                        statistics["status"] = "SATISFIED"
                        sol = statistics.copy()
                        sol["solution"] = output.get("output", {}).get("json", {})
                        sol["time"] = float(output.get("time", 0)) / 1000.0
                        solutions.append(sol)

                    elif output.get("type") == "error":
                        errors.append(clean_line)
                    else:
                        unknowns.append(clean_line)

                except json.JSONDecodeError:
                    # 2. 處理純文字行 (重點：抓取時間與狀態)
                    unknowns.append(clean_line)
                    upper_line = clean_line.upper()

                    # 提取時間：搜尋 %%%mzn-stat: solveTime=0.011001
                    time_match = re.search(r"solveTime=([\d\.]+)", clean_line)
                    if time_match:
                        statistics["time"] = float(time_match.group(1))

                    # 提取狀態
                    if "UNSATISFIABLE" in upper_line or clean_line.lower() == "unsat":
                        statistics["status"] = "UNSATISFIABLE"
                    elif "SATISFIED" in upper_line or clean_line.lower() == "sat" or "----------" in clean_line:
                        statistics["status"] = "SATISFIED"
                    elif "TIMEOUT" in upper_line and statistics["status"] == "UNKNOWN":
                        statistics["status"] = "UNKNOWN"

    # 確保 mzn-bench 抓得到 time 欄位 (別名處理)
    if "solve_time" in statistics and "time" not in statistics:
        statistics["time"] = statistics["solve_time"]

    # 封裝除錯資訊
    statistics["unknowns"] = unknowns
    statistics["errors"] = errors

    # 解析最後一行資訊，用於 CSV 追加欄位
    if last_line_raw is not None:
        last_line_info = parse_last_row(last_line_raw)

    # 寫入檔案
    os.makedirs(output_dir, exist_ok=True)
    if solutions:
        with open(sol_filename, "w") as f:
            yaml.dump(solutions, f)

    # Export JSON rows and last-row metadata to CSV
    json_csv_filename = Path(output_dir) / f"{uid}_json.csv"
    if json_rows or last_line_raw is not None:
        if json_rows:
            df_json = pd.DataFrame(json_rows)
        else:
            df_json = pd.DataFrame([
                {
                    "file_name": input_file.name,
                    "file_configuration": uid,
                    "line_index": 0,
                    "line_type": "none",
                }
            ])

        if last_line_raw is not None:
            df_json["last_line_raw"] = last_line_raw
            for key, value in last_line_info.items():
                df_json[f"last_{normalize_column_name(key)}"] = value

        df_json.to_csv(json_csv_filename, index=False, lineterminator="\n")

    # Use pandas DataFrame for deterministic column ordering
    df = pd.DataFrame([statistics])

    # Reorder columns: standard columns first, then any extra columns alphabetically
    cols = DEFAULT_STAT_COLUMNS.copy()
    extra_cols = sorted([c for c in df.columns if c not in cols])
    cols.extend(extra_cols)
    df = df[[c for c in cols if c in df.columns]]

    # Convert DataFrame row back to dictionary with ordered columns for YAML
    ordered_stats = df.iloc[0].to_dict()
    with open(stats_filename, "w") as f:
        yaml.dump(ordered_stats, f)



