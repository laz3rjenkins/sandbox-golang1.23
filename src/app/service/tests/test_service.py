# Тесты запускать только в контейнере!
import pytest
from pytest_mock import MockerFixture
import subprocess
from unittest.mock import call
from app.service.main import GoService
from app import config
from app.service import messages
from app.entities import (
    DebugData,
    TestsData,
    TestData
)
from app.service.entities import ExecuteResult
from app.service.entities import GoFile
from app.service.exceptions import CheckerException
from app.service import exceptions


def test_execute__float_result__ok():
    """ Задача "Дробная часть" """

    # arrange
    data_in = '9.08'
    code = (
        'package main\n'
        '\n'
        'import (\n'
        '    "fmt"\n'
        '    "math"\n'
        ')\n'
        '\n'
        'func main() {\n'
        '    var x float64\n'
        '    fmt.Scan(&x)\n'
        '    fmt.Println(x - math.Floor(x))\n'
        '}'
    )

    file = GoFile(code)
    GoService._compile(file)

    # act
    exec_result = GoService._execute(
        data_in=data_in,
        file=file
    )

    # assert
    assert round(float(exec_result.result), 2) == 0.08
    assert exec_result.error is None
    file.remove()


def test_execute__data_in_is_integer__ok():
    """ Задача "Делёж яблок" """

    # arrange
    data_in = (
        '6\n'
        '50'
    )
    code = (
        'package main\n'
        '\n'
        'import "fmt"\n'
        '\n'
        'func main() {\n'
        '    var n, k int\n'
        '    fmt.Scan(&n)\n'
        '    fmt.Scan(&k)\n'
        '    fmt.Println(k / n)\n'
        '    fmt.Println(k - (k/n)*n)\n'
        '}'
    )

    file = GoFile(code)
    GoService._compile(file)

    # act
    exec_result = GoService._execute(
        file=file,
        data_in=data_in
    )

    # assert
    assert exec_result.result == (
        '8\n'
        '2'
    )
    assert exec_result.error is None
    file.remove()


def test_execute__data_in_is_string__ok():
    """ Задача "Удаление фрагмента" """

    # arrange
    data_in = 'In the hole in the ground there lived a hobbit'
    code = (
        'package main\n'
        '\n'
        'import (\n'
        '    "fmt"\n'
        '    "bufio"\n'
        '    "os"\n'
        '    "strings"\n'
        ')\n'
        '\n'
        'func main() {\n'
        '    reader := bufio.NewReader(os.Stdin)\n'
        '    s, _ := reader.ReadString(\'\\n\')\n'
        '    s = strings.TrimSpace(s)\n'
        '    first := strings.Index(s, "h")\n'
        '    last := strings.LastIndex(s, "h")\n'
        '    if first != -1 && last != -1 && first < last {\n'
        '        s = s[:first] + s[last+1:]\n'
        '    }\n'
        '    fmt.Print(s)\n'
        '}'
    )
    file = GoFile(code)
    GoService._compile(file)

    # act
    exec_result = GoService._execute(
        data_in=data_in,
        file=file
    )

    # assert
    assert exec_result.result == 'In tobbit'
    assert exec_result.error is None
    file.remove()


def test_execute__empty_result__return_none():
    # arrange
    code = (
        'package main\n'
        '\n'
        'func main() {\n'
        '}'
    )
    file = GoFile(code)
    GoService._compile(file)

    # act
    exec_result = GoService._execute(
        file=file
    )

    # assert
    assert exec_result.result is None
    assert exec_result.error is None
    file.remove()


def test_execute__timeout__return_error(mocker: MockerFixture):

    # arrange
    code = (
        'package main\n'
        '\n'
        'func main() {\n'
        '    for {\n'
        '    }\n'
        '}'
    )
    file = GoFile(code)
    GoService._compile(file)
    mocker.patch('app.config.TIMEOUT', 1)

    # act
    execute_result = GoService._execute(file=file)

    # assert
    assert execute_result.error == messages.MSG_1
    assert execute_result.result is None
    file.remove()


def test_execute__deep_recursive__error(mocker):
    """ Числа Фибоначчи """

    # arrange
    code = (
        'package main\n'
        '\n'
        'import "fmt"\n'
        '\n'
        'func fibonacci(N int) int {\n'
        '    if N == 0 {\n'
        '        return 0\n'
        '    } else if N == 1 {\n'
        '        return 1\n'
        '    } else {\n'
        '        return fibonacci(N-1) + fibonacci(N-2)\n'
        '    }\n'
        '}\n'
        '\n'
        'func main() {\n'
        '    fmt.Println(fibonacci(50))\n'
        '}'
    )
    file = GoFile(code)
    GoService._compile(file)
    mocker.patch('app.config.TIMEOUT', 1)

    # act
    execute_result = GoService._execute(file=file)

    # assert
    assert execute_result.error == messages.MSG_1
    assert execute_result.result is None
    file.remove()


def test_execute__write_access__error():
    """ Тест работает только в контейнере
        т.к. там ограничены права на запись в файловую систему """

    # arrange
    code = (
        'package main\n'
        '\n'
        'import (\n'
        '    "fmt"\n'
        '    "os"\n'
        ')\n'
        '\n'
        'func main() {\n'
        '    path := "/proc/"\n'
        '    fileInfo, err := os.Stat(path)\n'
        '    if err != nil {\n'
        '        if os.IsNotExist(err) {\n'
        '            fmt.Println("No such file or directory.")\n'
        '        } else {\n'
        '            fmt.Println("Write Permission denied.")\n'
        '        }\n'
        '        return\n'
        '    }\n'
        '    mode := fileInfo.Mode().Perm()\n'
        '    _, err = os.OpenFile(path+"test.tmp", os.O_WRONLY|os.O_CREATE, mode)\n'
        '    if err != nil {\n'
        '        fmt.Println("Write Permission denied.")\n'
        '    } else {\n'
        '        fmt.Println("Write allowed.")\n'
        '    }\n'
        '}'
    )

    file = GoFile(code)
    GoService._compile(file)

    # act
    exec_result = GoService._execute(file=file)

    # assert
    assert 'Write Permission denied.' in exec_result.result
    assert exec_result.error is None

    file.remove()


def test_execute__clear_error_message__ok(mocker):
    # arrange
    code = (
        'package main\n'
        '\n'
        'func main() {\n'
        '    adqeqwd\n'
        '}'
    )
    raw_error_message = (
        "/sandbox/1aab26a5-980c-4aae-9c8d-75cc78394aff.go:"
        " In function ‘main.main()’:\n"
        "/sandbox/1aab26a5-980c-4aae-9c8d-75cc78394aff.go:2:5:"
        " error: undefined: adqeqwd\n"
        "     adqeqwd\n"
        "     ^~~~~~~\n"
    )
    clear_error_message = (
        "main.go:"
        " In function ‘main.main()’:\n"
        "main.go:2:5:"
        " error: undefined: adqeqwd\n"
        "     adqeqwd\n"
        "     ^~~~~~~\n"
    )
    file = GoFile(code)
    mocker.patch.object(subprocess.Popen, '__init__', return_value=None)
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        return_value=(None, raw_error_message)
    )
    kill_mock = mocker.patch('subprocess.Popen.kill')

    # act
    exec_result = GoService._execute(file=file)

    # assert
    communicate_mock.assert_called_once_with(
        input=None,
        timeout=config.TIMEOUT
    )
    kill_mock.assert_called_once()
    assert exec_result.result is None
    assert exec_result.error == clear_error_message
    file.remove()


def test_execute__proc_exception__raise_exception(mocker):

    # arrange
    code = (
        'package main\n'
        '\n'
        'func main() {\n'
        '    // Некорректный код для генерации ошибки исполнения\n'
        '    Some code\n'
        '}'
    )
    data_in = 'Some data in'
    file = GoFile(code)
    mocker.patch.object(subprocess.Popen, '__init__', return_value=None)
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        side_effect=Exception()
    )
    kill_mock = mocker.patch('subprocess.Popen.kill')

    # act
    with pytest.raises(exceptions.ExecutionException) as ex:
        GoService._execute(file=file, data_in=data_in)

    # assert
    assert ex.value.message == messages.MSG_6
    communicate_mock.assert_called_once_with(
        input=data_in,
        timeout=config.TIMEOUT
    )
    kill_mock.assert_called_once()
    file.remove()


def test_compile__timeout__error(mocker):

    # arrange
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(GoFile, '__new__', return_value=file_mock)

    code = (
        'package main\n'
        '\n'
        'func main() {\n'
        '    for {\n'
        '    }\n'
        '}'
    )
    file_mock.code = code

    mocker.patch.object(subprocess.Popen, '__init__', return_value=None)
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        side_effect=subprocess.TimeoutExpired(cmd='', timeout=config.TIMEOUT)
    )
    kill_mock = mocker.patch('subprocess.Popen.kill')

    # act
    error = GoService._compile(file_mock)

    # assert
    assert error == messages.MSG_1
    communicate_mock.assert_called_once_with(timeout=config.TIMEOUT)
    kill_mock.assert_called_once()


def test_compile__exception__raise_exception(mocker):

    # arrange
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(GoFile, '__new__', return_value=file_mock)

    code = (
        'package main\n'
        '\n'
        'func main() {\n'
        '    Some invalid code\n'
        '}'
    )
    file_mock.code = code

    mocker.patch.object(subprocess.Popen, '__init__', return_value=None)
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        side_effect=Exception
    )
    kill_mock = mocker.patch('subprocess.Popen.kill')

    # act
    with pytest.raises(exceptions.CompileException) as ex:
        GoService._compile(file_mock)

    # assert
    assert ex.value.message == messages.MSG_7
    communicate_mock.assert_called_once_with(timeout=config.TIMEOUT)
    kill_mock.assert_called_once()


def test_compile__error__error(mocker):

    # arrange
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(GoFile, '__new__', return_value=file_mock)

    code = (
        'package main\n'
        '\n'
        'func main() {\n'
        '    Some invalid code\n'
        '}'
    )
    file_mock.code = code

    compile_error = 'some error'
    mocker.patch.object(subprocess.Popen, '__init__', return_value=None)
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        return_value=(None, compile_error)
    )
    kill_mock = mocker.patch('subprocess.Popen.kill')

    # act
    error = GoService._compile(file_mock)

    # assert
    assert error == compile_error
    communicate_mock.assert_called_once_with(timeout=config.TIMEOUT)
    kill_mock.assert_called_once()


def test_compile__ok(mocker):
    file_mock = mocker.Mock()
    file_mock.filepath_out = '/tmp/fake_out'
    file_mock.filepath_go = '/tmp/fake_go'

    mocker.patch.object(GoFile, '__new__', return_value=file_mock)

    mock_chmod = mocker.patch('os.chmod')
    mock_chown = mocker.patch('os.chown')
    mocker.patch('os.path.dirname', return_value='/tmp')

    mock_popen = mocker.patch('subprocess.Popen')
    mock_proc = mock_popen.return_value

    mock_proc.communicate.return_value = (None, None)
    mock_proc.returncode = 0

    # act
    GoService._compile(file_mock)

    # assert
    mock_popen.assert_called_once_with(
        args=['go', 'build', '-o', file_mock.filepath_out, file_mock.filepath_go],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    mock_chmod.assert_called_once()
    mock_chown.assert_called_once()


def test_check__true__ok():

    # arrange
    value = 'some value'
    right_value = 'some value'
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:\n'
        '    return right_value == value'
    )

    # act
    check_result = GoService._check(
        checker_func=checker_func,
        right_value=right_value,
        value=value
    )

    # assert
    assert check_result is True


def test_check__false__ok():

    # arrange
    value = 'invalid value'
    right_value = 'some value'
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:\n'
        '    return right_value == value'
    )

    # act
    check_result = GoService._check(
        checker_func=checker_func,
        right_value=right_value,
        value=value
    )

    # assert
    assert check_result is False


def test_check__invalid_checker_func__raise_exception():

    # arrange
    checker_func = (
        'def my_checker(right_value: str, value: str) -> bool:\n'
        '    return right_value == value'
    )

    # act
    with pytest.raises(CheckerException) as ex:
        GoService._check(
            checker_func=checker_func,
            right_value='value',
            value='value'
        )

    # assert
    assert ex.value.message == messages.MSG_2


def test_check__checker_func_no_return_instruction__raise_exception():

    # arrange
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:\n'
        '    result = right_value == value'
    )

    # act
    with pytest.raises(CheckerException) as ex:
        GoService._check(
            checker_func=checker_func,
            right_value='value',
            value='value'
        )

    # assert
    assert ex.value.message == messages.MSG_3


def test_check__checker_func_return_not_bool__raise_exception():

    # arrange
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:\n'
        '    return None'
    )

    # act
    with pytest.raises(CheckerException) as ex:
        GoService._check(
            checker_func=checker_func,
            right_value='value',
            value='value'
        )

    # assert
    assert ex.value.message == messages.MSG_4


def test_check__checker_func__invalid_syntax__raise_exception():

    # arrange
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:\n'
        '    include(invalid syntax here)\n'
        '    return True'
    )

    # act
    with pytest.raises(CheckerException) as ex:
        GoService._check(
            checker_func=checker_func,
            right_value='value',
            value='value'
        )

    # assert
    assert ex.value.message == messages.MSG_5
    assert ex.value.details.startswith('invalid syntax')


def test_debug__compile_is_success__ok(mocker):
    # arrange
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    file_mock.filepath_go = '/tmp/main.go'
    file_mock.filepath_out = '/tmp/main_out'
    mocker.patch.object(GoFile, '__new__', return_value=file_mock)

    compile_mock = mocker.patch.object(GoService, '_compile', return_value=None)
    execute_result = ExecuteResult(
        result='some execute code result',
        error='some compilation error'
    )
    execute_mock = mocker.patch.object(GoService, '_execute', return_value=execute_result)

    data = DebugData(
        code='package main\nfunc main() {}',
        data_in='some data_in'
    )

    # act
    debug_result = GoService.debug(data)

    # assert
    file_mock.remove.assert_called_once()
    compile_mock.assert_called_once_with(file_mock)
    execute_mock.assert_called_once_with(
        file=file_mock,
        data_in=data.data_in
    )
    assert debug_result.result == execute_result.result
    assert debug_result.error == execute_result.error


def test_debug__compile_return_error__ok(mocker):
    # arrange
    compile_error = 'some error'
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(GoFile, '__new__', return_value=file_mock)

    # патчим методы класса напрямую
    compile_mock = mocker.patch.object(GoService, '_compile', return_value=compile_error)
    execute_mock = mocker.patch.object(GoService, '_execute')

    data = DebugData(
        code='some code',
        data_in='some data_in'
    )

    # act
    debug_result = GoService.debug(data)

    # assert
    file_mock.remove.assert_called_once()
    compile_mock.assert_called_once_with(file_mock)
    execute_mock.assert_not_called()
    assert debug_result.result is None
    assert debug_result.error == compile_error


def test_testing__compile_is_success__ok(mocker):
    # arrange
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(GoFile, '__new__', return_value=file_mock)

    # патчим методы класса напрямую
    compile_mock = mocker.patch.object(GoService, '_compile', return_value=None)
    execute_result = ExecuteResult(
        result='some execute code result',
        error='some compilation error'
    )
    execute_mock = mocker.patch.object(GoService, '_execute', return_value=execute_result)
    check_result = mocker.Mock()
    check_mock = mocker.patch.object(GoService, '_check', return_value=check_result)

    test_1 = TestData(data_in='some test input 1', data_out='some test out 1')
    test_2 = TestData(data_in='some test input 2', data_out='some test out 2')

    data = TestsData(
        code='some code',
        checker='some checker',
        tests=[test_1, test_2]
    )

    # act
    testing_result = GoService.testing(data)

    # assert
    compile_mock.assert_called_once_with(file_mock)
    assert execute_mock.call_args_list == [
        call(file=file_mock, data_in=test_1.data_in),
        call(file=file_mock, data_in=test_2.data_in)
    ]
    assert check_mock.call_args_list == [
        call(checker_func=data.checker, right_value=test_1.data_out, value=execute_result.result),
        call(checker_func=data.checker, right_value=test_2.data_out, value=execute_result.result)
    ]
    file_mock.remove.assert_called_once()
    tests_result = testing_result.tests
    assert len(tests_result) == 2
    assert tests_result[0].result == execute_result.result
    assert tests_result[0].error == execute_result.error
    assert tests_result[0].ok == check_result
    assert tests_result[1].result == execute_result.result
    assert tests_result[1].error == execute_result.error
    assert tests_result[1].ok == check_result


def test_testing__compile_return_error__ok(mocker):
    # arrange
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(GoFile, '__new__', return_value=file_mock)

    compile_error = 'some error'
    compile_mock = mocker.patch.object(GoService, '_compile', return_value=compile_error)
    execute_mock = mocker.patch.object(GoService, '_execute')
    check_mock = mocker.patch.object(GoService, '_check')

    test_1 = TestData(data_in='some test input 1', data_out='some test out 1')
    test_2 = TestData(data_in='some test input 2', data_out='some test out 2')

    data = TestsData(
        code='some code',
        checker='some checker',
        tests=[test_1, test_2]
    )

    # act
    testing_result = GoService.testing(data)

    # assert
    compile_mock.assert_called_once_with(file_mock)
    execute_mock.assert_not_called()
    check_mock.assert_not_called()
    file_mock.remove.assert_called_once()

    tests_result = testing_result.tests
    assert len(tests_result) == 2
    for test_res in tests_result:
        assert test_res.result is None
        assert test_res.error == compile_error
        assert test_res.ok is False
