import argparse
import os

from .utils import _write_job_array, _write_runner_params
from .validator import _validation_func


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--params", help="path to the job params file", type=str)
    args = parser.parse_args()

    return args


def main():
    args = _parse_args()
    validated_parameters = _validation_func(args.params)

    # create and write the runner params
    runner_params_fname = f"{validated_parameters.job_prefix}_runner_parameters.json"
    runner_params_path = os.path.join(
        validated_parameters.output_base_dir, runner_params_fname
    )
    _write_runner_params(
        array_config=validated_parameters, output_path=runner_params_path
    )

    # build the submission command from parameters
    job_array_command = _write_job_array(
        array_config=validated_parameters, runner_params_path=runner_params_path
    )

    # submit the job
    # print(f"Running command: {job_array_command}")
    os.system(job_array_command)
