from os.path import exists
import pickle
from util import *

try:
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
except ImportError:
    install("google-api-python-client")
    install("google-auth-httplib2")
    install("google-auth-oauthlib")
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request


class GoogleCalendarSession(object):
    """
    Session for the user to create events in their Google Calendar.
    Not really designed to be used externally, the formatting is heavily balanced towards usage in this specific
    project, therefore the syntax and formatting of parameters may be very strange in other circumstances.
    """

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.prefix = "[Google Calendar]"
        self.service = None
        if exists("credentials.json"):
            scopes = ['https://www.googleapis.com/auth/calendar']
            credentials_file = 'credentials.json'
            creds = None
            # The file token.pickle stores the user's access and refresh tokens, and is
            # created automatically when the authorization flow completes for the first
            # time.
            if exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    creds = pickle.load(token)
            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(credentials_file, scopes)
                    creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open('token.pickle', 'wb') as token:
                    pickle.dump(creds, token)

            self.service = build('calendar', 'v3', credentials=creds)
        else:
            raise Exception(
                "'credentials.json' cannot not found. This can be fetched from "
                "https://console.cloud.google.com/apis/credentials. A guide for "
                "generating these credentials can be found at "
                "https://karenapp.io/articles/how-to-automate-google-calendar-with-python-using-the-calendar-api/")

    def event_exists(self, event_body: dict) -> bool:
        """
        Checks if an event specified by "eventBody" already exists in the users calendar. This is to prevent duplicates
        when creating events in the users calendar.

        "eventBody" should contain eventBody['start']['dateTime'], eventBody['end']['dateTime'] and
        eventBody['summary']. These are all strings I think.

        I may sort this out at some point because this hard coding is very poor from me.
        """
        events_result = self.service.events().list(calendarId='primary', timeMin=event_body['start']['dateTime'],
                                                   timeMax=event_body['end']['dateTime'], singleEvents=True,
                                                   orderBy='startTime').execute()
        for event in events_result.get("items", []):
            if event['summary'] == event_body['summary']:
                return True
        return False

    def create_event(self, title: str, description: str, start: str, end: str, time_zone=None):
        """
        Creates an event in the users Google Calendar.
        Creates this event in the primary calendar, with a colour corresponding to the first character of the title.

        Defaults to Greenwich timezone, unless specified under the time_zone parameter. Check the Google Calendar API
        documentation for information on valid timezones.

        This will print a "Created Event" or "Event already exists" correspondingly.

        example Parameters:
        "start": {"dateTime": "2015-09-15T06:00:00+02:00", "timeZone": "Europe/Zurich"}
        - note: not actually sure if +02:00 is allowed (??)
        same format for end.
        """

        def define_colour(event_title: any, offset=1) -> str:
            """
            Defines colour by the title's first digit. Cycles through 11 possible colours, these correspond to the 11
            colours available in Google Calendar. Returns a string because I'm lazy.
            """
            event_title = str(event_title)  # idk what integer titles ppl be making but yk
            return str(ord(event_title[0]) % 11 + offset)

        # example start:
        # "start": {"dateTime": "2015-09-15T06:00:00+02:00", "timeZone": "Europe/Zurich"},

        # DAYLIGHT SAVINGS FIX - it looks like its bugged when making event but trust me (check calendar)
        start_dt = datetime.strptime(start, '%Y-%m-%dT%H:%M:%S%z')

        if is_daylight_savings(start_dt):  # takes away one hour if daylight savings is active.
            start_dt -= timedelta(hours=1)
            start = start_dt.strftime('%Y-%m-%dT%H:%M:%S%z')

            end_dt = datetime.strptime(end, '%Y-%m-%dT%H:%M:%S%z')
            end_dt -= timedelta(hours=1)
            end = end_dt.strftime('%Y-%m-%dT%H:%M:%S%z')

        if not time_zone:
            time_zone = "Greenwich"

        event_body = {"summary": title,
                      "description": description,
                      "colorId": define_colour(title),

                      "start": {"dateTime": start,
                                "timeZone": time_zone},
                      "end": {"dateTime": end,
                              "timeZone": time_zone}}

        if not self.event_exists(event_body):
            self.service.events().insert(calendarId='primary', body=event_body).execute()
            if self.verbose:
                print(f"{self.prefix}: Created Event  ({title} at {start})")
        else:
            if self.verbose:
                print(f"{self.prefix}: Event already exists  ({title} at {start})")

    def day_event_exists(self, event_body: dict) -> bool:
        """
        TLDR: basically the event_exists() method but for full day events

        Checks if a full day event specified by "eventBody" already exists in the users calendar. This is to prevent
        duplicates when creating events in the users calendar.

        "eventBody" should contain eventBody['summary']. This is a string I think.
        """

        # eventBody example: eventBody = {"summary": title,"description": description,"colorId": DefineColour(title),
        # "start": {"dateTime": start, "timeZone": 'Greenwich'},"end": {"dateTime": end, "timeZone": 'Greenwich'}}
        # events_result = self.service.events().list(calendarId='primary', timeMin=eventBody['start']['date'],
        #                                           timeMax=eventBody['end']['date'], singleEvents=True,
        #                                           orderBy='startTime').execute()

        now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        events_result = self.service.events().list(
            calendarId='primary', timeMin=now,
            singleEvents=True,
            orderBy='startTime').execute()
        events = events_result.get('items', [])
        for event in events:
            if event['summary'] == event_body['summary']:
                return True
        return False

    def create_day_event(self, title, description, start, end):
        """
        Creates a full day event in the users Google Calendar.
        Creates this event in the primary calendar, with a colour corresponding to the first character of the title.

        This will print a "Created Event" or "Event already exists" correspondingly.
        """

        def define_color(event_title) -> str:
            """
            Defines colour by the title's first digit. Cycles through 11 possible colours, these correspond to the 11
            colours available in Google Calendar. event_title must be mutable.
            """
            event_title = str(event_title)
            return str((ord(event_title[0]) % 11) + 1)

        event_body = {
            "summary": title,
            "description": description,
            "colorId": define_color(title),
            "start": {
                "date": start,
            },
            "end": {
                "date": end,
            },
        }

        if not self.day_event_exists(event_body):
            self.service.events().insert(calendarId='primary', body=event_body).execute()
            if self.verbose:
                print(f"{self.prefix}: Created Event ({title} at {start})")
        else:
            if self.verbose:
                print(f"{self.prefix}: Event already exists ({title} at {start})")
