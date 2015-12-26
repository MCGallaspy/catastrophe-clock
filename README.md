# What
A countdown until known catastrophes occur.
Just a simple Django app.

# Why
Is your highly-refined sense of panic alarmingly subsiding? Are you feeling claustrophobic due to your oppressive feelings of security?
Then look no further! Click through the list of catastrophes -- some imminent, some not so much -- and feel that fantastic apprehension envelop your whole body and paralyze your mind with anxiety as you watch the seconds tick by with bated breath.
Just remember to breathe every now and then -- you don't want to pass out and miss your favorite catastrophe!

# How catastrophe countdowns are determined
Catastrophe objects represent a known catastrophe (like `Miami will sink due to sea level rise`, or `lions will go extinct`) and when it will occur (its `arrival_date`).
The app defines management commands which create/update Catastrophe objects.
For instance, the `get_sea_level` management command updates the Catastrophe named "Miami sinks" by scraping data from a public website, estimating the rate of sea level rise (a bit naively), and calculating the `arrival_date` from Miami's average elevation.

In order to learn more about how a Catastrophe's `arrival_date` is calculated see the relevant management command.
Pains are taken to use publicly available data, but all the countdowns are "back of the envelope" calculations -- this is for "amusement" only. ;)
