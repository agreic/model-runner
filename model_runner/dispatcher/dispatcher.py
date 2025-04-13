import argparse
import json
import os

from .dispatcher_utils import create_run_command


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job_id", help="the job ID from /$LSB_JOBINDEX", type=int)
    parser.add_argument("--params", help="path to the job params file", type=str)
    args = parser.parse_args()

    job_id = args.job_id

    with open(args.params) as f_params:
        params = json.load(f_params)

    # json number keys are saved as strings
    job_params = params[str(job_id)]
    run_command = create_run_command(job_params)
    print(f"Running command: {run_command}")
    os.system(run_command)
