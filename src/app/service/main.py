import os
import stat
import subprocess
from typing import Optional
from src.app.service.entities import GoFile
from src.app.entities import (
    DebugData,
    TestsData,

)
from src.app import config
from src.app.service import exceptions, messages
from src.app.service.entities import ExecuteResult
from src.app.utils import clean_str, clean_error

class GoService:
    @classmethod
    def _preexec_fn(cls):
        def change_process_user():
            os.setgid(config.SANDBOX_USER_GID)
            os.setuid(config.SANDBOX_USER_UID)

        return change_process_user

    @classmethod
    def _compile(cls, file: GoFile) -> Optional[str]:
        """Компилирует Go-программу"""
        try:
            proc = subprocess.Popen(
                args=['go', 'build', '-o', file.filepath_out, file.filepath_go],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            _, error = proc.communicate(timeout=config.TIMEOUT)

            if not error:

                os.chmod(file.filepath_out, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                dir_path = os.path.dirname(file.filepath_out)
                # os.chmod(dir_path, 0o755)
                os.chown(dir_path, config.SANDBOX_USER_UID, config.SANDBOX_USER_GID)


        except subprocess.TimeoutExpired:
            error = messages.MSG_1
        except Exception as ex:
            raise exceptions.CompileException(details=str(ex))
        finally:
            if 'proc' in locals():
                proc.kill()

        return clean_error(error)

    @classmethod
    def _execute(
        cls,
        file: GoFile,
        data_in: Optional[str] = None
    ) -> ExecuteResult:
        """Запускает скомпилированный Go-бинарник"""

        proc = subprocess.Popen(
            args=[file.filepath_out],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=cls._preexec_fn(),
            text=True
        )
        try:
            result, error = proc.communicate(
                input=data_in,
                timeout=config.TIMEOUT
            )
        except subprocess.TimeoutExpired:
            result, error = None, messages.MSG_1
        except Exception as ex:
            raise exceptions.ExecutionException(details=str(ex))
        finally:
            proc.kill()

        return ExecuteResult(
            result=clean_str(result or None),
            error=clean_error(error or None)
        )

    @classmethod
    def _validate_checker_func(cls, checker_func: str):
        if not checker_func.startswith(
            'def checker(right_value: str, value: str) -> bool:'
        ):
            raise exceptions.CheckerException(messages.MSG_2)
        if checker_func.find('return') < 0:
            raise exceptions.CheckerException(messages.MSG_3)

    @classmethod
    def _check(cls, checker_func: str, **checker_func_vars) -> bool:
        cls._validate_checker_func(checker_func)
        try:
            exec(
                checker_func + '\nresult = checker(right_value, value)',
                globals(),
                checker_func_vars
            )
        except Exception as ex:
            raise exceptions.CheckerException(
                message=messages.MSG_5,
                details=str(ex)
            )
        else:
            result = checker_func_vars['result']
            if not isinstance(result, bool):
                raise exceptions.CheckerException(messages.MSG_4)
            return result

    @classmethod
    def debug(cls, data: DebugData) -> DebugData:
        """Компиляция и отладочный запуск"""
        file = GoFile(data.code)
        error = cls._compile(file)
        if error:
            data.error = error
        else:
            exec_result = cls._execute(
                file=file,
                data_in=data.data_in
            )
            data.result = exec_result.result
            data.error = exec_result.error
        file.remove()
        return data

    @classmethod
    def testing(cls, data: TestsData) -> TestsData:
        """Компиляция и тестовый запуск"""
        file = GoFile(data.code)
        error = cls._compile(file)
        for test in data.tests:
            if error:
                test.error = error
                test.ok = False
            else:
                exec_result = cls._execute(
                    file=file,
                    data_in=test.data_in
                )
                test.result = exec_result.result
                test.error = exec_result.error
                test.ok = cls._check(
                    checker_func=data.checker,
                    right_value=test.data_out,
                    value=test.result
                )
        file.remove()
        return data
