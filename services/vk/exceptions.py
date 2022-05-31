"""Bots creation module exceptions"""


class PhoneStockUnavailableException(Exception):
    """Phone stock unavailable exception"""
    pass


class StopBoostException(Exception):
    """Exception if something goes wrong while boost bots"""
    pass


class StopCreatingBotsException(Exception):
    """Exception if something goes wrong while creating bots"""
    pass


class TaskFailed(Exception):
    """Exception for set failed state for a task"""
    pass
