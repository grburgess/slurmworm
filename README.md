# slurmworm
![alt text](https://raw.githubusercontent.com/grburgess/slurmworm/main/logo.png)

This is a rather simple tool to monitor SLURM emails and alert you via a telegram bot about your jobs.

**Note!** This is under heavy development!

## Installation

* install [imapclient](https://github.com/mjs/imapclient) directly from the github repo *not* pip
* clone this repo and run 
```bash
python setup install
```
* create a directory ```~/.config/slurmworm```
* in this directory you need to place two files. 
* * one is the telegram bot info for the *your* bot that you must [create](https://firstwarning.net/vanilla/discussion/4/create-telegram-bot-and-get-bots-token-and-the-groups-chat-id) named ```access.yml```
* * the other is a UNIX conf file with your IMAP email info named ```imap_monitor.ini``` which identifies the email account to which you will send slurm messages

## Telegram bot setup
If you read the above guide to create your bot you will have nearly everything you need. You then need to get that info into your ```access.yml``` file:
```yaml
token:
  '<your bot ID token>'

chat_id:
  '<the group ID where your bot will send messages>'

```

You should have your bot chat to a group you have created. 


## email setup
This is what should go in ```imap_monitor.ini```:

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

## Running
After you have installed and set everything up, just type
```bash
slurmworm
```
in a shell and it will run and monitor your email. 

It is likely best to have this running in a tmux shell you can disconnect from.

May all your jobs exit 0!
