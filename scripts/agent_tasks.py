"""Print the open agent-task issues of this repository: a quick list for Priya."""
import json
import os
import urllib.request

TOKEN = os.environ["GITHUB_TOKEN"]

URL = "https://api.github.com/repos/termidy/demosoft-incidentdesk-v2/issues?labels=agent-task"
request = urllib.request.Request(URL, headers={"Authorization": f"Bearer {TOKEN}"})
for issue in json.load(urllib.request.urlopen(request)):
    print(f"#{issue['number']} {issue['title']}")