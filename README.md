# slurmworm
![alt text](https://raw.githubusercontent.com/grburgess/slurmworm/main/logo.png)

This is a rather simple tool to monitor SLURM emails and alert you via a telegram bot about your jobs.

## Installation

* install [imapclient](https://github.com/mjs/imapclient) directly from the github repo *not* pip
* clone this repo and run 
```bash
python setup install
```
* create a directory ```~/.config/slurmworm```
* in this directory you need to place two files. 
** one is the telegram bot info for the *your* bot that you must [create](https://firstwarning.net/vanilla/discussion/4/create-telegram-bot-and-get-bots-token-and-the-groups-chat-id) names access.yml
** the other is a UNIX conf file with your IMAP email info named imap_monitor.ini

## Telegram bot setup
If you read the above guide to create your bot you will have nearly everything you need. You then need to get that info into your access.yml file:
```yaml
token:
  '<your bot ID token>'

chat_id:
  '<the group ID where your bot will send messages>'

```

You should have your bot chat to a group you have created. 


## email setup
This is what should go in imap_monitor.ini:

```ini
[imap]
host = <your imap server>
username = <username>
password = <password>
ssl = True
folder = INBOX

[path]
download = <where mail will be temporarily stored>
```
