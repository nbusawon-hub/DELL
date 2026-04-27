import ast
import os
from datetime import datetime, timezone, timedelta

from anthropic import beta_tool


@beta_tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression and return the result.

    Args:
        expression: A mathematical expression to evaluate, e.g. "2**10 + 15".
    """
    tree = ast.parse(expression, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(
            node,
            (
                ast.Expression,
                ast.BinOp,
                ast.UnaryOp,
                ast.Constant,
                ast.operator,
                ast.unaryop,
            ),
        ):
            return f"Error: unsupported operation in expression: {type(node).__name__}"
    result = eval(compile(tree, "<expr>", "eval"))
    return str(result)


TIMEZONE_OFFSETS = {
    "UTC": 0, "GMT": 0,
    "US/Eastern": -5, "US/Central": -6, "US/Mountain": -7, "US/Pacific": -8,
    "Europe/London": 0, "Europe/Paris": 1, "Europe/Berlin": 1,
    "Asia/Tokyo": 9, "Asia/Shanghai": 8, "Asia/Kolkata": 5,
    "Australia/Sydney": 10,
}


@beta_tool
def get_current_time(timezone_name: str = "UTC") -> str:
    """Get the current date and time in a given timezone.

    Args:
        timezone_name: Timezone name, e.g. "UTC", "US/Eastern", "Asia/Tokyo".
    """
    offset_hours = TIMEZONE_OFFSETS.get(timezone_name)
    if offset_hours is None:
        available = ", ".join(sorted(TIMEZONE_OFFSETS))
        return f"Unknown timezone '{timezone_name}'. Available: {available}"
    tz = timezone(timedelta(hours=offset_hours))
    now = datetime.now(tz)
    return f"{now.strftime('%Y-%m-%d %H:%M:%S')} ({timezone_name})"


@beta_tool
def read_file(file_path: str) -> str:
    """Read the contents of a local file.

    Args:
        file_path: Path to the file to read.
    """
    resolved = os.path.realpath(file_path)
    if not os.path.isfile(resolved):
        return f"Error: '{file_path}' is not a file or does not exist."
    try:
        with open(resolved, "r") as f:
            content = f.read(50_000)
        return content
    except Exception as e:
        return f"Error reading file: {e}"


ALL_TOOLS = [calculate, get_current_time, read_file]
