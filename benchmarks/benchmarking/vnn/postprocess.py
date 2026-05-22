import sys
import os
import json
import re
from pathlib import Path
from ruamel.yaml import YAML

# 初始化 YAML
yaml = YAML(typ="safe")
yaml.default_flow_style = False

# 狀態對照表
STATUS_MAP = {
    "sat": "SATISFIED",
    "unsat": "UNSATISFIABLE",
    "satisfied": "SATISFIED",
    "unsatisfiable": "UNSATISFIABLE",
    "unknown": "UNKNOWN",
    "timeout": "UNKNOWN"
}

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

    if input_file.exists():
        with open(input_file, "r") as f:
            for line in f:
                clean_line = line.strip()
                if not clean_line: continue

                try:
                    # 1. 嘗試解析為 JSON
                    output = json.loads(clean_line)

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

    # 寫入檔案
    os.makedirs(output_dir, exist_ok=True)
    if solutions:
        with open(sol_filename, "w") as f:
            yaml.dump(solutions, f)
    with open(stats_filename, "w") as f:
        yaml.dump(statistics, f)


