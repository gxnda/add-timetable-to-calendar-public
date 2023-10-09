import g4s
import google_calendar
from getpass import getpass
from datetime import datetime, timedelta

VERBOSE_BOOL = False
g4s_session = g4s.G4S(username=input("Username: "), password=getpass("Password: "), verbose=VERBOSE_BOOL)
google_calendar_session = google_calendar.GoogleCalendarSession(verbose=VERBOSE_BOOL)


def create_event_from_lesson(g4s_lesson: dict):
    """
    Creates an event from a single lesson. This lesson must contain the following:
    - lesson["subject_name"]
    - lesson["date"]
    - lesson["start_time"]
    - lesson["end_time"]
    - lesson["group_code"]
    - lesson["teacher_list"]
    - lesson["room_list"]
    """
    subject_name = g4s_lesson["subject_name"]
    if subject_name not in ["None", None]:
        start = g4s_lesson["date"][:-8] + g4s_lesson["start_time"] + ":00+00:00"
        end = g4s_lesson["date"][:-8] + g4s_lesson["end_time"] + ":00+00:00"
        description = g4s_lesson["group_code"] + "\n" + g4s_lesson["teacher_list"][
            list(g4s_lesson["teacher_list"].keys())[0]] + "\n" + g4s_lesson["room_list"]
        google_calendar_session.create_event(subject_name, description, start, end)


def create_events_from_timetable(g4s_timetable: list[dict]):
    for lesson in g4s_timetable:
        create_event_from_lesson(lesson)


def create_event_from_homework(task: dict):
    """
    Creates a single homework event using create_day_event(). This event must include the following:
    - task["title"]
    - task["details"]
    - task["due_date"] (which must be in the format '%Y-%m-%dT%H:%M:%S')
    """

    title = task["title"]
    description = task["details"].replace("\\r\\", "\n")
    due_date = task["due_date"]
    due_date_as_datetime = datetime.strptime(due_date, '%Y-%m-%dT%H:%M:%S')
    next_date = due_date_as_datetime + timedelta(days=1)
    due_date_as_datetime = due_date_as_datetime.strftime('%Y-%m-%d')
    next_date = next_date.strftime('%Y-%m-%d')
    google_calendar_session.create_day_event(title, description, due_date_as_datetime, next_date)


def create_events_from_homework(homework: list[dict]):
    for task in homework:
        create_event_from_homework(task)


def add_timetable():
    timetable = g4s_session.get_timetable()
    create_events_from_timetable(g4s_timetable=timetable)


def add_homework():
    homework = g4s_session.get_homework()
    create_events_from_homework(homework=homework)


if __name__ == "__main__":
    add_homework()
    add_timetable()
