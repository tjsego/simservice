"""
Defines basic library standard definitions
"""
from multiprocessing import current_process


def name_mangler(process_name: str, name: str) -> str:
    """
    Standard name mangling of this module by process name

    :param process_name: process name (e.g., hex( os.getpid() ) )
    :type process_name: str
    :param name: name to mangle
    :type name: str
    :return: mangled name
    :rtype: str
    """
    return f"{process_name}_{name}"


def standard_process_name() -> str:
    """
    Get standard process name

    :return: standard process name
    :rtype: str
    """
    return hex(current_process().pid)
