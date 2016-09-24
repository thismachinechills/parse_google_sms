#!/usr/bin/env python3

#
# Copyright 2016 thismachinechills (Alex)
#

from collections import namedtuple
from datetime import datetime
from glob import glob
from typing import List, Generator, Iterable

import click
from bs4 import BeautifulSoup


DT_FMT = "%Y-%m-%dT%H:%M:%S.%f"
PRETTY_FMT = "%d %b, %Y %I:%M:%S"
FILE_FMT = "%d_%b_%Y_%I_%M_%S"
SMS_GLOB_FMT = "* - Text - *"

CHAT_FILENAME = 'chat_%s_'
CHAT_FILE_TYPE = ".txt"


class Sms(namedtuple('Sms', 'time sender msg')):
    def __repr__(self):
        return str(self)

    def __str__(self):
        pretty_date = self.time.strftime(PRETTY_FMT)

        return "[%s] %s: %s" % (pretty_date, self.sender, self.msg)


class Chat(namedtuple('Chat', 'senders msgs')):
    def __str__(self):
        return '\n'.join(map(str, self.msgs))

    def save(self, filename: str = None) -> str:
        if filename is None:
            date = self.msgs[0].time.strftime(FILE_FMT)
            subs = '_'.join('%s' for sub in range(len(self.senders)))
            fmt = CHAT_FILENAME + subs
            filename = (fmt + CHAT_FILE_TYPE) % (date, *self.senders)

        with open(filename, 'w') as file:
            file.write(str(self))

        return filename


def read(filename: str) -> str:
    with open(filename, 'r') as f:
        return f.read()


def get_chatlog_filenames(location: str) -> List[str]:
    return glob(location + "/" + SMS_GLOB_FMT)


def wrap_chat(chat_html: str) -> BeautifulSoup:
    return BeautifulSoup(chat_html, 'lxml')


def get_smses(chat: BeautifulSoup) -> List[BeautifulSoup]:
    return chat.find_all('div', 'message')


def parse_dt(sms: BeautifulSoup, fmt: str = DT_FMT) -> datetime:
    dt_str = sms.find("abbr", "dt")['title'][:-6]

    return datetime.strptime(dt_str, fmt)


def parse_sender(sms: BeautifulSoup) -> str:
    return sms.find("a", "tel").text.strip()


def parse_msg(sms: BeautifulSoup) -> str:
    return sms.find('q').text.strip()


def parse_sms(sms: BeautifulSoup) -> Sms:
    time = parse_dt(sms)
    sender = parse_sender(sms)
    msg = parse_msg(sms)

    return Sms(time, sender, msg)


def parse_chat(chat: BeautifulSoup) -> Chat:
    smses = [parse_sms(sms) for sms in get_smses(chat)]
    senders = sorted({sms.sender for sms in smses})

    return Chat(senders, smses)


def gen_chats(filenames: List[str]) -> Iterable[Chat]:
    for filename in filenames:
        yield parse_chat(wrap_chat(read(filename)))


def save_chats(chats: Iterable[Chat]):
    for chat in chats:
        print(chat.save())


@click.command()
@click.argument("location")
def cmd(location: str):
    save_chats(gen_chats(get_chatlog_filenames(location)))


if __name__ == "__main__":
    cmd()

