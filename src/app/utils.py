import re
from typing import Optional
from src.app.service import messages


def clean_str(value: Optional[str]) -> Optional[str]:
    if isinstance(value, str):
        return value.replace('\r', '').rstrip('\n')
    return value


def clean_error(value: Optional[str]) -> Optional[str]:
    if isinstance(value, str):
        pattern = r'/(tmp|sandbox)/\S*\.go'
        value = re.sub(
            pattern=pattern,
            repl="main.go",
            string=value
        )
        if 'Terminated' in value:
            value = messages.MSG_1
        elif 'the monitored command dumped core' in value:
            value = messages.MSG_8
    return value
