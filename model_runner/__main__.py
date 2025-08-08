import argparse
import os
import json
import itertools


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

    # Extract the parameter_ranges from runner_parameters
    parameter_ranges = validated_parameters.runner_parameters.pop("parameter_ranges", None)

    if parameter_ranges:

        print (f" Error, currently not supported, please use the original workflow without parameter ranges.")

        # Generate all combinations of parameter values
        keys, values = zip(*[list(d.items())[0] for d in parameter_ranges])
        combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]

        # Read the original JSON file specified in the "data" field

        # Throw if more than one data file is specified
        if len(validated_parameters.runner_parameters["data"]) > 1:
            raise ValueError("More than one data file specified in runner_parameters during a parameter range screening op.")

        data_file_path = validated_parameters.runner_parameters["data"][0]
        with open(data_file_path, "r") as f:
            base_data = json.load(f)

        # Create and launch jobs for each combination
        for idx, combo in enumerate(combinations):
            # Update the base data with the current combination
            modified_data = base_data.copy()
            for key, value in combo.items():
                key = key[1:]
                print(key)
                if key in modified_data:
                    modified_data[key] = value  # Replace if key exists
                else:
                    # Throw if the key doesn't exist in the base data
                    raise KeyError(f"Key '{key}' not found in base data.")
                    # modified_data[key] = value  # Add if key doesn't exist

            # Save the modified data to a new JSON file
            modified_data_fname = f"simulation_config_{idx}.json"
            modified_data_path = os.path.join(validated_parameters.output_base_dir, modified_data_fname)
            with open(modified_data_path, "w") as f:
                json.dump(modified_data, f, indent=4)

            #     print(f"Modified data saved to {modified_data_path}")
            # print(f"Idx: {idx}, Combo: {combo}, Modified data: {modified_data}")
            # return 

            # Update the "data" field in the runner_parameters to point to the new file
            modified_config = validated_parameters.dict()
            modified_config["runner_parameters"]["data"] = [modified_data_path]

            # Save the modified configuration to a new JSON file
            runner_params_fname = f"{validated_parameters.job_prefix}_params_{idx}.json"
            runner_params_path = os.path.join(validated_parameters.output_base_dir, runner_params_fname)
            with open(runner_params_path, "w") as f:
                json.dump(modified_config, f, indent=4)

            print(modified_config)

            # Launch the program with the modified configuration
            job_array_command = _write_job_array(
                array_config=modified_config, runner_params_path=runner_params_path
            )
            print(f"Launching job with command: {job_array_command}")
            os.system(job_array_command)

    
    else: # Original workflow without parameter ranges

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
        os.system(job_array_command)
        # Debug, print the job instead:
        # print(f"Launching job with command: {job_array_command}")