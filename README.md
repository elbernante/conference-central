Conference Central
======================================

Scalable application running on Google App Engine platform.
Project 4 for Udacity Full Stack Nano Degree.
Developed with Python.


Setting Up
--------------------------------------

### Environment Requirements

The following needs to be installed:

- [Python 2.7][1]
- [Git][2]
- [Google App Engine SDK for Python][3]



### Getting the Source Code

Clone a copy of the git repo by running:

```bash
git clone https://github.com/elbernante/conference-central.git
```



### Launching the App

After getting the source code, the app can be launched using **GoogleAppEngineLauncher**

1. Launch GoogleAppEngineLauncher app.
2. Click File -> Add Existing Application.
3. Browse and select folder of the source code (**conference-central**).
4. Select app from the list (**fab-proj-102116**).
5. Click **Run**.

The server should now be up and running and can be accessed through ```http://localhost:8080```. The port may change if it is already in use.

**OR**

You can directly access the deployed app at:

[https://fab-proj-102116.appspot.com](https://fab-proj-102116.appspot.com)



Answers to Project Questions
--------------------------------------

### Task 1: Design Choice

The speaker is implemented as a full-pledged entity represented by  `Speaker()` class which inherits from `ndb.Model()` class. Making the speaker as a full-pledged entity allows adding more information about the speaker (e.g. biography and link to professional profile). It also allows adding speakers with the same name (which could happen) while remain distinguishable as different speakers.

Four new endpoints are added for speaker related operations. The function names should be self-explanatory.

```
createSpeaker()
updateSpeaker()
getSpeaker(websafeSpeakerKey)
getAllSpeakers()
```

Two helper classes `SpeakerForm()` and `SpeakerForms()` for creating and querying skeaper entities. Both of which inherit from `messages.Message()` class.


The `Session` entity is implemented as a child for `Conference` entity since a session always belongs to a conference. It is therefore ideal to implement an “ancestor” relationship between conference and session. “websafeSpeakerKey” is used to link a speaker to the session for easy retrieval of the speaker information.   The “highlights” property is implemented as “repeated” since there could be more than 1 highlight in the session. The rest of the properties are declared based on their intuitive data types.


### Task 3: Additional Queries

##### First query:
`getConferenceSessionsByDuration(websafeConferenceKey, duration)`
Returns all sessions in a conference that don't last longer than x minutes.

##### Second query:
`getConferenceSessionsByDate(websafeConferenceKey, startDate, endDate)`
Returns all sessions in a conference that is happening between a given date range.


### Task 3: Query Problem

The query would require operating inequalities on 2 properties (i.e. `typeOfSession` and `startTime`), which would raise an error when executed on the datastore. The datastore has limitation where you can only apply inequality queries on at most 1 property.

To work around this limitation, execute only the first inequality operation on the datastore. The succeeding inequality operations can be used as post filters on the result set after querying. When possible, for better efficiency, set the first inequality that is most likely will return the least number of data. Less result set means less network traffic and less post processing operations.

For the implementation, a wrapper class `MultiPropInequality()`  (can found in `utils.py`) is implemented which takes either a “kind” or a “query” object parameter. Filters can be applied on the instance like regular queries (GQL is not supported), except that you can include inequalities on several properties.

To demonstrate, a new endpoint is created `multiInequalityPlayground()` which returns all non-workshop sessions before 7pm.


[1]: https://www.python.org/downloads/release/python-279/
[2]: http://git-scm.com/downloads
[3]: https://cloud.google.com/appengine/downloads
