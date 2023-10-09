from datetime import datetime, timedelta
from os import system
from subprocess import check_call


def start_end_of_week() -> tuple:
    """Returns start & end of current week as datetime objects."""
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=000000)
    end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)

    return start_of_week, end_of_week


def get_academic_year() -> str:
    now = datetime.now()
    if now.month >= 9:
        academic_year = str(now.year + 1)
    else:
        academic_year = str(now.year)

    return academic_year


def clear():
    """Clears the console."""
    system("cls")


def install(package):
    """Uses pip to install a package. This will error if 'pip' is not on %PATH%."""
    check_call(["pip", "install", package])


def is_daylight_savings(dt: datetime):
    if dt.astimezone().dst() == timedelta(0):
        return False
    return True
