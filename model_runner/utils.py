import json
import os
from itertools import product
from typing import Any, Dict, List, Tuple, Union

from .validator import ConfigModel


def _create_runner_param(
    param_names: List[str],
    param_values: Tuple[Any],
    job_prefix: str,
    runner: str,
    output_base_dir: str,
    job_index: int,
) -> Dict[str, Any]:

    params = {k: v for k, v in zip(param_names, param_values)}
    params.update(
        {
            "job_prefix": job_prefix,
            "runner": runner,
            "output_base_dir": output_base_dir,
            "job_index": job_index,
        }
    )
    return params


def _create_runner_params(
    job_params: Dict[str, List[Any]],
    job_prefix: str,
    runner: str,
    output_base_dir: str,
) -> Dict[int, Dict[str, Any]]:
    param_names = list(job_params.keys())
    param_values = list(job_params.values())

    param_combinations = product(*param_values)

    runner_params = {
        i: _create_runner_param(
            param_names=param_names,
            param_values=values,
            job_prefix=job_prefix,
            runner=runner,
            output_base_dir=output_base_dir,
            job_index=i,
        )
        for i, values in enumerate(param_combinations, start=1)
    }

    return runner_params


def _write_runner_params(
    array_config: ConfigModel, output_path: Union[str, os.PathLike]
):
    """Write the parameters file for the job array runners to disk

    Parameters
    ----------
    array_config : ConfigModel
        The parameters for the job array. The dictionary should have
        string keys, each being a parameter name. The values should be
        a list of values. The resulting job array will have jobs that are
        the combinations of all of the parameters.

    output_path : os.PathLike
        The path to the file to save the job array parameters to.
        Should have the extension .json.
    """
    job_params = array_config.runner_parameters
    runner_params = _create_runner_params(
        job_params,
        job_prefix=array_config.job_prefix,
        runner=array_config.runner,
        output_base_dir=array_config.output_base_dir,
    )

    with open(output_path, "w") as f_out:
        json.dump(runner_params, f_out, indent=4, sort_keys=True)


def _write_job_array(array_config: ConfigModel, runner_params_path: str) -> str:
    """
    Write job array command as defined in https://github.com/kevinyamauchi/model-runner/issues/7.

    Parameters
    ----------

    array_config : ConfigModel
        The parameters for the job array. The dictionary should have
        string keys, each being a parameter name. The values should be
        a list of values. The resulting job array will have jobs that are
        the combinations of all of the parameters.

    runner_params_path: str
        Path to runner dictionary.

    Return
    ------
    Job array str formated as in https://github.com/kevinyamauchi/model-runner/issues/7.
    """
    job_prefix = array_config.job_prefix
    logfile_dir = os.path.join(array_config.job_parameters.logfile_dir, job_prefix)
    memory = array_config.job_parameters.memory
    njobs_parallel = array_config.job_parameters.njobs_parallel
    processor_cores = array_config.job_parameters.processor_cores
    run_time = array_config.job_parameters.run_time
    scratch = array_config.job_parameters.scratch
    ngpus = array_config.job_parameters.ngpus
    gpu_type = array_config.job_parameters.gpu_type

    with open(runner_params_path, "r") as f:
        runner_params = json.load(f)

    n_ids = len(runner_params)

    # write command str
    job_array_command = f"sbatch --array=1-{n_ids}%{njobs_parallel}"
    job_array_command += f" --job-name={job_prefix}"
    job_array_command += f" --output={logfile_dir}%a"
    job_array_command += f" --time={run_time}"
    job_array_command += f" --ntasks-per-node=1"
    job_array_command += f" --cpus-per-task={processor_cores}"
    job_array_command += f" --tmp={scratch}"
    job_array_command += f" --mem-per-cpu={memory}"

    if (ngpus is not None) and (gpu_type is None):
        job_array_command += f" --gpus={ngpus}"
    elif (ngpus is not None) and (gpu_type is not None):
        job_array_command += f" --gpus={gpu_type}:{ngpus}"

    job_array_command += f' --wrap="model_dispatcher --job_id \\$SLURM_ARRAY_TASK_ID --params {runner_params_path}"'

    return job_array_command
