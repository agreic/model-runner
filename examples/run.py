import json
import os


file_dir = os.path.dirname(os.path.abspath(__file__))
runner_file = os.path.join(file_dir, 'example_runner.py')

# create the job params
config = {
    "job_prefix": "my_experiment",
    "runner_parameters": {
        "data": [file_dir],
        "augment": [True, False],
        "batch_size": [2, 16, 32],
        "lr": [5e-05, 0.001],
    },
    "job_parameters": {
        "gpu_type": "v100",
        "logfile_dir": file_dir,
        "memory": 200,
        "ngpus": 1,
        "njobs_parallel": 4,
        "processor_cores": 1,
        "run_time": "00:00:30",
        "scratch": 200,
    },
    "runner": runner_file,
    "output_base_dir": file_dir,
}

# write the config
config_path = os.path.join(file_dir, 'config.json')
with open(config_path, 'w') as f:
    json.dump(config, f)

# run
run_command = f'model_runner --params {config_path}'
os.system(run_command)
