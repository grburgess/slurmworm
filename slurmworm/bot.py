import logging
import os

import telegram

from .package_utils import get_access_file

logger = logging.getLogger("slurmworm.bot")

if os.environ.get("SLURMWORM_DEBUG") is not None:

    if os.environ.get("SLURMWORM_DEBUG") == "True":

        _DEBUG = True

    else:

        _DEBUG = False
else:

    _DEBUG = False


class Bot(object):
    def __init__(self, name, token, chat_id, identify=True):
        """
        A generic telegram bot

        :param name: the name of the bot
        :param token: the bot token
        :param chat_id: the chat id to talk to
        :returns:
        :rtype:

        """
        logger.debug(f"{name} bot is being constructed")

        # create the bot

        self._name = name
        self._chat_id = chat_id

        self._bot = telegram.Bot(token=token)

        if identify:
            self._msg_header = f"{self._name} says:\n"

        else:

            self._msg_header = ""

    def speak(self, message):
        """
        send a message

        :param message:
        :returns:
        :rtype:

        """

        full_msg = f"{self._msg_header}{message}"

        logger.info(f"{self._name} bot is sending: {message}")

        self._bot.send_message(chat_id=self._chat_id, text=full_msg)

    def show(self, image, description):
        """
        send an image

        :param image:
        :param description:
        :returns:
        :rtype:

        """

        full_msg = f"{self._msg_header}{description}"

        logger.info(f"{self._name} bot is sending the {description} image")

        self._bot.send_photo(
            chat_id=self._chat_id, photo=open(image, "rb"), caption=full_msg
        )


class SlurmBot(Bot):
    def __init__(self):
        """
        A Slurm bot

        :returns:
        :rtype:

        """

        token = None
        chat_id = None

        access = get_access_file()
        chat_id = access["chat_id"]
        token = access["token"]

        super(SlurmBot, self).__init__(
            name="SLURM", token=token, chat_id=chat_id, identify=False
        )
