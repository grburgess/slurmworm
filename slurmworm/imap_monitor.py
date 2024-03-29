import configparser as ConfigParser
import email
import logging
import os.path as path
import re
import sys
import traceback
from time import sleep
from datetime import datetime, time
from logging.handlers import RotatingFileHandler


import imapclient
from rich.logging import RichHandler

from .bot import SlurmBot
from .package_utils import get_imap_file, get_path_of_user_dir

formatter = logging.Formatter(
    " %(message)s",
    datefmt="%H:%M:%S",
)


# Setup the log handlers to stdout and file.
log = logging.getLogger("imap_monitor")
log.setLevel(logging.DEBUG)

handler_stdout = RichHandler(
    level="DEBUG",
    rich_tracebacks=True,
    markup=True,
)


handler_stdout.setLevel(logging.DEBUG)
handler_stdout.setFormatter(formatter)
log.addHandler(handler_stdout)


# TODO: Support SMTP log handling for CRITICAL errors.


began_match = re.compile(
    "(\w*).*Slurm Job_id=(\d*) Name=(\w*) Began, Queued time (\d{2}:\d{2}:\d{2})"
)

began_array_match = re.compile(
    "(\w*).*Slurm Array Summary Job_id=(\S*) \((\d*)\) Name=(\w*) Began"
)

failed_match = re.compile(
    "(\w*).*Slurm Job_id=(\d*) Name=(\w*) Failed, Run time (\d{2}:\d{2}:\d{2}), ([A-Z]*),.*ExitCode (\d*)"
)

ended_match = re.compile(
    "(\w*) Slurm Job_id=(\d*) Name=(\w*) Ended, Run time (\d{2}:\d{2}:\d{2}), (\w*), ExitCode (\d*)"
)


ended_array_match = re.compile(
    "(\w*) Slurm Array Summary Job_id=(\S*) \((\d*)\) Name=(\w*) Ended"
)


bot = SlurmBot()


def process_email(mail_, download_, log_):
    """Email processing to be done here. mail_ is the Mail object passed to this
    function. download_ is the path where attachments may be downloaded to.
    log_ is the logger object.

    """
    log.info(mail_["subject"])

    subject = mail_["subject"]

    if "Slurm" in subject:

        log.info("[blink]SLURM EMAIL DETECTED[/blink]")

        subject = subject.replace("\n", "").replace("\r", "")

        if "Failed" in subject:
            print("%r" % subject)

            try:

                (
                    server,
                    jobid,
                    name,
                    run_time,
                    reason,
                    exitcode,
                ) = failed_match.match(subject).groups()

                message = f"FUCK! I failed!\nServer: {server}\nJob: {name}\nReason: {reason}\nRuntime: {run_time}"

            except:

                pass

        elif "Began" in subject:

            try:

                server, jobid, name, qtime = began_match.match(subject).groups()

                message = f"Job Started!\nServer: {server}\nJob: {name}\nQueued time: {qtime}"

            except:

                try:

                    server, _, jobid, name = began_array_match.match(
                        subject
                    ).groups()

                    message = f"Job Started!\nServer: {server}\nJob: {name}"

                except Exception as e:

                    log.error(e)

        elif "Ended" in subject:

            try:

                (
                    server,
                    jobid,
                    name,
                    run_time,
                    reason,
                    exitcode,
                ) = ended_match.match(subject).groups()

                message = f"Finished!!\nServer: {server}\nJob: {name}\nReason: {reason}\nRuntime: {run_time}"

            except:

                try:

                    server, _, jobid, name = ended_array_match.match(
                        subject
                    ).groups()

                    message = f"Job ENDED!\nServer: {server}\nJob: {name}"

                except Exception as e:

                    log.error(e)

        bot.speak(message)

    return "return meaningful result here"


def listen():

    log.info("... script started")

    while True:
        # <--- Start of configuration section

        # Read config file - halt script on failure
        try:
            config_file = open(get_imap_file(), "r+")
        except IOError:

            log.critical("configuration file is missing")

            break
        config = ConfigParser.SafeConfigParser()

        config.readfp(config_file)

        # Retrieve IMAP host - halt script if section 'imap' or value
        # missing
        try:
            host = config.get("imap", "host")

        except ConfigParser.NoSectionError:

            log.critical('no "imap" section in configuration file')

            break

        except ConfigParser.NoOptionError:

            log.critical("no IMAP host specified in configuration file")

            break

        # Retrieve IMAP username - halt script if missing
        try:
            username = config.get("imap", "username")

        except ConfigParser.NoOptionError:

            log.critical("no IMAP username specified in configuration file")

            break

        # Retrieve IMAP password - halt script if missing
        try:

            password = config.get("imap", "password")

        except ConfigParser.NoOptionError:

            log.critical("no IMAP password specified in configuration file")

            break

        # Retrieve IMAP SSL setting - warn if missing, halt if not boolean
        try:

            ssl = config.getboolean("imap", "ssl")

        except ConfigParser.NoOptionError:

            # Default SSL setting to False if missing

            log.warning("no IMAP SSL setting specified in configuration file")

            ssl = False

        except ValueError:

            log.critical("IMAP SSL setting invalid - not boolean")

            break

        # Retrieve IMAP folder to monitor - warn if missing
        try:

            folder = config.get("imap", "folder")

        except ConfigParser.NoOptionError:

            # Default folder to monitor to 'INBOX' if missing
            log.warning("no IMAP folder specified in configuration file")

            folder = "INBOX"

        # Retrieve path for downloads - halt if section of value missing
        try:
            download = config.get("path", "download")
        except ConfigParser.NoSectionError:
            log.critical('no "path" section in configuration')
            break
        except ConfigParser.NoOptionError:
            # If value is None or specified path not existing, warn and default
            # to script path
            log.warn("no download path specified in configuration")
            download = None
        finally:
            download = (
                download
                if (download and path.exists(download))
                else path.abspath(__file__)
            )
        log.info("setting path for email downloads - {0}".format(download))

        while True:

            # <--- Start of IMAP server connection loop

            # Attempt connection to IMAP server
            log.info(f"connecting to IMAP server - {host}")

            try:
                imap = imapclient.IMAPClient(host, use_uid=True, ssl=True)
            except Exception:
                # If connection attempt to IMAP server fails, retry
                etype, evalue = sys.exc_info()[:2]
                estr = traceback.format_exception_only(etype, evalue)
                logstr = "failed to connect to IMAP server - "
                for each in estr:
                    logstr += "{0}; ".format(each.strip("\n"))
                log.error(logstr)
                sleep(10)
                continue

            log.info("server connection [green]established[/green]")

            # Attempt login to IMAP server
            log.info(f"logging in to IMAP server - [green]{username}[/green]")

            try:

                result = imap.login(username, password)

                log.info(f"login successful - {result}")

            except Exception:
                # Halt script when login fails
                etype, evalue = sys.exc_info()[:2]
                estr = traceback.format_exception_only(etype, evalue)
                logstr = "failed to login to IMAP server - "
                for each in estr:
                    logstr += "{0}; ".format(each.strip("\n"))
                log.critical(logstr)
                break

            # Select IMAP folder to monitor
            log.info(f"selecting IMAP folder - [green]{folder}[/green]")

            try:

                result = imap.select_folder(folder)

                log.info("folder selected")

            except Exception:

                # Halt script when folder selection fails
                etype, evalue = sys.exc_info()[:2]
                estr = traceback.format_exception_only(etype, evalue)
                logstr = "failed to select IMAP folder - "

                for each in estr:
                    logstr += "{0}; ".format(each.strip("\n"))
                log.critical(logstr)
                break

            # Retrieve and process all unread messages. Should errors occur due
            # to loss of connection, attempt restablishing connection
            try:
                result = imap.search("UNSEEN")
            except Exception:
                continue
            log.info(f"{len(result)} unread messages seen - {result}")
            for each in result:
                try:
                    result = imap.fetch(each, ["RFC822"])
                except Exception:
                    log.error(f"failed to fetch email - {each}")
                    continue

                new_result = {}

                for k, v in result[each].items():

                    new_result[k.decode("utf-8")] = v

                message = new_result["RFC822"]

                try:
                    message = message.decode("utf-8")

                except:

                    message = new_result["RFC822"]

                try:
                    mail = email.message_from_string(message)
                    process_email(mail, download, log)

                    subject = mail["subject"]

                    message = f"processing email {each} - {subject}"

                    log.info(message)

                except Exception:

                    subject = mail["subject"]

                    message = f"processing email {each} - {subject}"

                    bot.speak("Error processing mail")

                    bot.speak(message)

                    log.error(f"failed to process email {each}")

                    continue

            while True:
                # <--- Start of mail monitoring loop

                # After all unread emails are cleared on initial login, start
                # monitoring the folder for new email arrivals and process
                # accordingly. Use the IDLE check combined with occassional NOOP
                # to refresh. Should errors occur in this loop (due to loss of
                # connection), return control to IMAP server connection loop to
                # attempt restablishing connection instead of halting script.

                try:

                    imap.idle()

                except:

                    bot.speak("Something is up!")

                    log.error("something is up!")

                    sleep(5)

                # TODO: Remove hard-coded IDLE timeout; place in config file

                result = imap.idle_check(5 * 60)

                if result:

                    imap.idle_done()

                    result = imap.search("UNSEEN")

                    log.info(f"{len(result)} new unread messages - {result}")

                    for each in result:

                        fetch = imap.fetch(each, ["RFC822"])
                        new_result = {}

                        for k, v in fetch[each].items():

                            new_result[k.decode("utf-8")] = v

                        out = new_result["RFC822"]

                        mail = email.message_from_string(out.decode("utf-8"))

                        subject = mail["subject"]

                        try:

                            process_email(mail, download, log)

                            message = f"processing email {each} - {subject}"

                            log.info(message)

                        except Exception:

                            message = f"failed to process email {each}"

                            bot.speak(message)

                            log.error(message)
                            # raise
                            continue
                else:

                    try:

                        imap.idle_done()
                        imap.noop()
                        log.info("no new messages seen")

                    except:

                        bot.speak("I AM DYING")

                # End of mail monitoring loop --->
                continue

        # End of configuration section --->
        bot.speak("LEAVING!")
        break
    bot.speak("LEAVING!")
    log.info("script stopped ...")


if __name__ == "__main__":
    listen()
