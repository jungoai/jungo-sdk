from collections.abc    import Callable
from functools          import reduce
from typing             import TypeVar
from jsonrpc.utils      import inspect
from pydantic           import BaseModel

#------------------------------------------------------------------------------
#-- General

T = TypeVar('T')
I = TypeVar('I')

# TODO: constraint x to sum of the primitive types and BaseModel
def to_json(x: T) -> str | T :
    if isinstance(x, BaseModel):
        return x.model_dump_json()
    else:
        return x

# TODO: constraint x to sum of the primitive types and BaseModel
def from_json(x) -> T:              # type: ignore
    try:
        return T.model_validate(x)  # type: ignore
    except:
        return x

def current_func_name() -> str:
    return inspect.stack()[1].function

def cfn() -> str:
    """
    Alias for current_func_name()
    """
    return inspect.stack()[1].function

def guard(p: bool, e: Exception):
    if not p: raise e

#------------------------------------------------------------------------------
#-- FP

def lmap(f: Callable[[T], I] ,l: list[T]) -> list[I]:
    return list(map(f, l))

def compose(fs: list[Callable]) -> Callable:
    lastf = fs.pop()
    return lambda x: reduce(lambda f, x_: f(x_), fs, lastf(x))

def unOpt(x: T | None) -> T:
    if x is None:
        raise Exception("unexpected None")
    else:
        return x

#------------------------------------------------------------------------------
#-- debuging

def debug(x: T) -> T:
    print("[debug line " + str(current_line()) + "]:" + str(x))
    return x

def current_line() -> int:
    frame = inspect.currentframe()
    if frame is None: return -1
    else: return frame.f_lineno
