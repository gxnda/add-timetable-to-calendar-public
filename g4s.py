from json import loads
from util import start_end_of_week, get_academic_year
from datetime import datetime
import requests


class G4S:
    def __init__(self, username: str, password: str, verbose=False):
        """Takes in a username and password as parameters and logs into the Go4Schools website using the Requests
        library. It extracts the student ID and bearer token from the HTML response and stores them as attributes of
        the class. """
        self.verbose = verbose

        session = requests.Session()
        login_url = "https://www.go4schools.com/sso/account/login?site=Student"
        response = session.get(login_url)
        # Parse the CSRF token from the HTML form.
        csrf_token = response.text.split('name="__RequestVerificationToken" type="hidden" value="')[1].split('"')[0]
        # Login using the username and password.
        login_data = {
            "username": username,
            "password": password,
            "__RequestVerificationToken": csrf_token
        }
        response = session.post(login_url, data=login_data)

        # Extract the student ID and bearer token from the HTML.
        if "login" in response.url:
            raise Exception("Incorrect Username or Password.")

        self.school_id = response.text.split("var s_schoolID = ")[1].split(";")[0]
        self.student_id = response.text.split("?sid=")[1].split('"')[0]
        self.bearer = "Bearer " + response.text.split("var accessToken = ")[1].split('"')[1]

        results = {"username": username,
                   "school_id": self.school_id,
                   "student_id": self.student_id,
                   "bearer": self.bearer}
        if verbose:
            print(f"G4S Login: {results}")

    def get_timetable(self, start_date: str = None, end_date: str = None) -> list[dict]:
        """Retrieves the student's timetable for a given start and end date (formatted as "Sat, 1 Jan 2000 00:00:00
        GMT") from the Go4Schools API. If no dates are specified, it uses the StartEnd_OfWeek method to get the start
        and end dates of the current week. The method returns a list of dictionaries representing the lessons. """
        if not (start_date or end_date):
            start_date, end_date = start_end_of_week()
            start_date = start_date.strftime("%a, %d %b %Y %H:%M:%S") + " GMT"
            end_date = end_date.strftime("%a, %d %b %Y %H:%M:%S") + " GMT"

        if self.verbose:
            print(f": Fetching timetable...")

        headers = {
            "authorization": self.bearer,
            "origin": "https://www.go4schools.com",
            "referer": "https://www.go4schools.com/"
        }

        base_url = "https://api.go4schools.com/web/stars/v1/timetable/student/academic-years/"
        timetable_url = (base_url + str(get_academic_year()) + "/school-id/" + self.school_id +
                         "/user-type/1/student-id/" + self.student_id +
                         "/from-date/" + str(start_date) + "/to-date/" + str(end_date) + "?caching=true")

        response = requests.get(timetable_url, headers=headers)

        if self.verbose:
            print(f"Status code from 'api.go4schools.com':", response.status_code)

        lessons = loads(response.text)["student_timetable"]

        # replace all weird names
        for i in range(len(lessons)):
            if lessons[i]["subject_name"] == "Rg":
                lessons[i]["subject_name"] = "Form"
            elif lessons[i]["subject_name"] == "Computer Sci":
                lessons[i]["subject_name"] = "Computer Science"

        return lessons

    def get_homework(self) -> list[dict]:
        """Gets homework using the Go4Schools API"""
        headers = {
            "authorization": self.bearer,
            "origin": "https://www.go4schools.com",
            "referer": "https://www.go4schools.com/"
        }
        url = "https://api.go4schools.com/web/stars/v1/homework/student/academic-years/" + get_academic_year() + \
              "/school-id/" + self.school_id + "/user-type/1/student-id/" + self.student_id + \
              "?caching=true&includeSettings=true"

        response = requests.get(url, headers=headers)
        homework = loads(response.text)["student_homework"]["homework"]

        future_tasks = []
        start_of_week = start_end_of_week()[0]

        for task in homework:
            date_str = task["due_date"]
            date_str_as_datetime = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
            if date_str_as_datetime >= start_of_week:
                future_tasks.append(task)

        return future_tasks
