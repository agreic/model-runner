import json
import os
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, validator


def which(program: str) -> Optional[str]:
    """
    Test if program is a file or an executable.
    """

    def is_exe(fpath):
        return os.path.isfile(
            fpath
        )  # and os.access(fpath, os.X_OK) TODO: pytest fixture with executable permission

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


class JobArrayModel(BaseModel):
    """
    pydantic BaseModel that handles the job_parameters.

    Parameters
    ----------
    run_time: Union[str, int]
        The time resources on the compute note are reservered for a single job. Corresponds to the slurm sbatch "--time"-flag.
    processor_cores: int
        Number of processor cores requested for a single job. Corresponds to the slurm sbatch "--ntasks"-flag.
    memory: int
        Amount of memory requested per processor core. Corresponds to slurm sbatch "--mem-per-cpu"-flag.
    scratch: int
        Amount of local scratch requested per node. Corresponds to slurm sbatch "--tmp"-flag.
    gpu_type: str
        Type of gpu that is accepted by slurm sbatch "--gpus={gpu_type}:{ngpus}"-flag.
    ngpus: int
        Number of GPUs of {gpu_type} requested. Corresponds to slurm sbatch "--gpus={gpu_type}:{ngpus}".
    njobs_parallel: int
        Number of jobs the job array will submit in parallel.
    logfile_dir: str
        Path to directory to which slurm output files are saved.
    """

    run_time: Union[str, int]
    processor_cores: int
    memory: int
    scratch: int
    njobs_parallel: int
    logfile_dir: str
    gpu_type: Optional[str] = None
    ngpus: Optional[int] = None

    @validator("logfile_dir")
    def logfile_dir_is_dir(cls, v):
        """
        Validate if logfile_dir is an existing directory.
        """
        if not os.path.isdir(v):
            raise ValueError(f'"{v}" is not a directory.')
        elif not v.endswith(os.path.sep):
            v += os.path.sep

        return v

    @validator("ngpus", always=True)
    def ngpus_and_gpu_type_match(cls, v, values):
        if (None in (v, values.get("gpu_type"))) and (v != values.get("gpu_type")):
            gpu_type = values.get("gpu_type")
            raise ValueError(
                f'gpu_type and ngpus either both have to be declared or omitted, but type(gpu_type) is "{type(gpu_type)}" and type(ngpus) is "{type(v)}".'
            )

        return v

    @validator("gpu_type")
    def gpu_type_exists(cls, v):
        """
        Validate if submitted gpu_type is currently available at Euler
        (https://scicomp.ethz.ch/wiki/Getting_started_with_clusters#GPU).
        """
        gpu_list = [
            "gtx_1080",
            "gtx_1080_ti",
            "rtx_2080_ti",
            "rtx_3090",
            "titan_rtx",
            "quadro_rtx_6000",
            "v100",
            "a100_40gb",
            "a100_80gb",
            "rtx_4090"
        ]

        if v not in gpu_list:
            raise ValueError(
                f'"{v}" is currently not available on Euler. Check the list of available GPUs '
                "at https://scicomp.ethz.ch/wiki/Getting_started_with_clusters#GPU."
            )

        return v

    @validator("run_time")
    def validate_and_coerce_run_time(cls, v):
        """
        Validate if submitted run_time adheres to the slurm format specified in
        https://scicomp.ethz.ch/wiki/LSF_to_Slurm_quick_reference#Frequently_used_bsub.2Fsbatch_options.
        """
        if type(v) == str:
            v_split = v.split(":")
            if "-" in v:
                day_split = v.split("-")
                sub_split = day_split[1].split[":"]

                days = int(day_split[0])
                hours = int(sub_split[0])

                v = (24 * days + hours) * 60

                if len(sub_split) == 2:
                    minutes = int(sub_split[1])
                    v += minutes
                else:
                    raise ValueError(
                        "run_time string must adhere to the format specified in "
                        "https://scicomp.ethz.ch/wiki/LSF_to_Slurm_quick_reference#Frequently_used_bsub.2Fsbatch_options."
                    )
            elif len(v_split) == 1:
                try:
                    minutes = int(v_split[0])
                    v = minutes
                except ValueError:
                    raise ValueError(
                        "run_time string must adhere to the format specified in "
                        "https://scicomp.ethz.ch/wiki/LSF_to_Slurm_quick_reference#Frequently_used_bsub.2Fsbatch_options."
                    )
            elif len(v_split) == 3:
                try:
                    minutes = int(v_split[1])  # ignore seconds, no relevant use-case?
                    hours = int(v_split[0])

                    if (minutes > 59) or (minutes < 0):
                        raise ValueError(
                            "run_time string must adhere to the format specified in "
                            "https://scicomp.ethz.ch/wiki/LSF_to_Slurm_quick_reference#Frequently_used_bsub.2Fsbatch_options."
                        )

                    v = minutes + hours * 60
                except ValueError:
                    raise ValueError(
                        "run_time string must adhere to the format specified in "
                        "https://scicomp.ethz.ch/wiki/LSF_to_Slurm_quick_reference#Frequently_used_bsub.2Fsbatch_options."
                    )
            else:
                raise ValueError(
                    "run_time string must adhere to the format specified in "
                    "https://scicomp.ethz.ch/wiki/LSF_to_Slurm_quick_reference#Frequently_used_bsub.2Fsbatch_options."
                )

        return v


class ConfigModel(BaseModel):
    """
    pydantic BaseModel that handles the job_config.json.

    Parameters
    ----------
    runner: str
        Path to the runner file.
    job_prefix: str
        Prefix that precedes all results folders and experiment specific files.
    output_base_dir: str
        Directory to which all config files and results folders are saved.
    job_parameters: Dict[str, Any]
        Dictionary of parameters for the job array command that are handled by the JobArrayModel.
    runner_parameters: Dict[str, List[Any]]
        Dictionary containing the parameters grid submitted to the runner.
    """

    job_prefix: str
    runner: str
    output_base_dir: str
    job_parameters: JobArrayModel
    runner_parameters: Dict[str, List[Any]]

    @validator("output_base_dir")
    def output_base_dir_is_dir(cls, v):
        """
        Validate if output_base_dir is an existing directory.
        """
        if not os.path.isdir(v):
            raise ValueError(f'"{v}" is not a directory.')
        elif not v.endswith(os.path.sep):
            v += os.path.sep

        return v

    @validator("runner_parameters")
    def data_in_runner_parameters_and_file_or_path(cls, v):
        """
        Validate if "data" key is in runner_parameters and if it is either file or directory.
        """
        # check if runner_parameters contains data key
        assert "data" in v.keys()

        # check if all paths in "data" are existing files or directories
        for i, f in enumerate(v["data"]):
            if not (os.path.isfile(f) or os.path.isdir(f)):
                raise ValueError(f'"{f}" is not a file/directory.')
            else:
                if os.path.isdir(f) and not f.endswith(os.path.sep):
                    v["data"][i] = f + os.path.sep
        return v

    @validator("runner")
    def runner_exists(cls, v):
        """
        Validate if "runner" is an existing file or an executable.
        """
        runner_file = which(v)
        if runner_file is None:
            raise ValueError('"runner" is not a file and not an executable.')
        return v


def _validation_func(params_path: Union[str, os.PathLike]) -> ConfigModel:
    with open(params_path, "r") as f:
        parameters = json.load(f)
    validated_parameters = ConfigModel(**parameters)
    return validated_parameters
