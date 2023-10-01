import distutils.spawn
import io
import json
import logging
import subprocess
import sys
import os
import tempfile

logger = logging.getLogger(__name__)

_current_module = sys.modules[__name__]

_current_module_path = _current_module.__file__
_base_dir = os.path.dirname(_current_module_path)
_java_plugin_file = os.path.join(_base_dir, 'java', 'aws-apigateway-velocity-repl.jar')

if not os.path.isfile(_java_plugin_file):
    raise RuntimeError(f'Java plugin file not found: {_java_plugin_file}')


def evaluate(template: str,
             data: dict = None,
             stage_variables: dict = None) -> str:
    if data is None:
        data = {}

    if stage_variables is None:
        stage_variables = {}

    java_exec = distutils.spawn.find_executable('java')
    if java_exec is None:
        print('java not found')
        raise RuntimeError('java executable not found')

    with tempfile.TemporaryDirectory() as work_dir:
        with open(f'{work_dir}/template.vtl', 'w') as tf:
            logger.debug(f'Writing template to {tf.name}')
            tf.write(template)
            tf.flush()

            with open(f'{work_dir}/data.json', 'w') as df:
                logger.debug(f'Writing test data to {df.name}')
                json.dump(data, df)
                df.flush()

                with open(f'{work_dir}/stage_variables.json', 'w') as svf:
                    logger.debug(f'Writing stage variables to {svf.name}')
                    json.dump(stage_variables, svf)
                    svf.flush()

                    with open(f'{work_dir}/output', 'w') as of:
                        p = subprocess.run(
                            args=[
                                java_exec,
                                '-jar',
                                _java_plugin_file,
                                '-d',
                                df.name,
                                '-t',
                                tf.name,
                                '-s',
                                svf.name,
                            ],
                            stdout=of,
                        )

                        of.flush()

                        return_code = p.returncode
                        if return_code != 0:
                            raise RuntimeError(f'vtl exit code: {return_code}')

                        logger.debug(f'vtl exit code: {p.returncode}')
                        logger.debug(f'processed file is at {work_dir}/output')

                        with open(f'{work_dir}/output', 'r') as f:
                            return f.read()
