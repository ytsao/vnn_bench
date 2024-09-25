from sys import stdin
from pathlib import Path
import sys
import os
# import minizinc
import json
import datetime

if os.environ.get("VNN_DEBUG", "OFF") == "ON":
  import logging
  logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

if __name__ == "__main__":
  output_dir = sys.argv[1]
  verifier = sys.argv[2]
  robustness_type = sys.argv[3]
  network_name = sys.argv[4]
  dataset = sys.argv[5]
  relu_transformer = sys.argv[6]
  label = sys.argv[7]
  template_method = sys.argv[8]
  template_domain = sys.argv[9]
  template_layers = sys.argv[10]
  template_with_hyperplanes = sys.argv[11]
  template_dir = sys.argv[12]
  data_dir = sys.argv[13]
  num_tests = sys.argv[14]
  epsilon = sys.argv[15]
  patch_size = sys.argv[16]
  extras = []
  
  for i in range(17, len(sys.argv)):
    arg = sys.argv[i].strip().replace(' ', '-')
    print(arg)
    if arg != "" and arg != "-s": # we use "-s" when there are "no special options to be used".
      extras.append(arg)
      # Remove leading "-" from extras (these are used for specifying options)
      if extras[-1].startswith("-"):
        extras[-1] = extras[-1][1:]

  uid = verifier.replace('.', '-') + "_" + robustness_type + "_" + network_name + "_" + dataset + "_" + epsilon
  if len(extras) > 0:
    uid += "_"
    uid += "_".join(extras)

  if(output_dir[-1] == "/"):
    output_dir = output_dir[:-1]
  if(Path(output_dir).exists() == False):
    os.mkdir(output_dir)
  log_filename = Path(output_dir + "/" + uid + ".json")

  stat_base = {
    "configuration": uid,
    "vnn_verifier": verifier,
    "robustness_type": robustness_type,
    "network_name": network_name,
    "dataset": dataset,
    "relu_transformer": relu_transformer,
    "label": label,
    "template_method": template_method,
    "template_domain": template_domain,
    "template_layers": template_layers,
    "template_with_hyperplanes": template_with_hyperplanes,
    "template_dir": template_dir,
    "data_dir": data_dir,
    "num_tests": num_tests,
    "epsilon": epsilon,
    "datetime": datetime.datetime.now().isoformat(),
    # "status": str(minizinc.result.Status.UNKNOWN)
    "status": "UNSAT"
  }

  # If the file exists, we do not delete what is already inside but append new content.
  # We start all benchmarks with a special line {"lattice-land/bench": "start"}.
  print("Writing to file: ", log_filename)
  with open(log_filename, "a") as file:
    header = {"type": "lattice-land", "lattice-land": "start"}
    json.dump(header, file)
    file.write("\n")
    msg = {"type": "statistics", "statistics": stat_base}
    json.dump(msg, file)
    file.write("\n")
    file.write("before loop\n")
    for line in stdin:
      file.write(line)
      file.flush()
    file.write("after loop\n")
