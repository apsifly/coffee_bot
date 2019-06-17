import argparse
import random
import sqlite3
import psycopg2
import MySQLdb
from peewee import *
import logging
import telebot



parser = argparse.ArgumentParser(description='Formats Consul data.')
parser.add_argument('--db-driver', help='DB driver postgres|mysql|sqlite', type=str, default="postgres")
parser.add_argument('--db-name', help='DB name', type=str, default="coffee_bot")
parser.add_argument('--db-host', help='DB host', type=str, default="127.0.0.1")
parser.add_argument('--db-port', help='DB port', type=int, default=5432)
parser.add_argument('--db-user', help='DB user', type=str, default="user")
parser.add_argument('--db-password', help='DB password', type=str, default="password")
parser.add_argument('--token', help='telegram token', type=str, required=True)
parser.add_argument('--send-at-start', help='send invites at program start', type=bool, nargs='?',const=True, default=False)
args = parser.parse_args()

if args.db_driver == "postgres":
    db = PostgresqlDatabase(args.db_name, user=args.db_user, password=args.db_password,
                           host=args.db_host, port=args.db_port)
elif args.db_driver == "mysql":
    db = MySQLDatabase(args.db_name, user=args.db_user, password=args.db_password,
                           host=args.db_host, port=args.db_port)
elif args.db_driver == "mysql":
    db = SqliteDatabase(args.db_name)
else:
    raise Exception("database driver unknown")

class User(Model):
    event_id = AutoField()
    id = BigIntegerField(unique=True)
    nickname = CharField(index=True, null = True)
    first = CharField(null = True)
    last = CharField(null = True)
    enabled = BooleanField()

    class Meta:
        database = db


User.create_table()

bot = telebot.TeleBot(args.token)

@bot.message_handler(commands=['start'])
def register(message):
    new_guy = User(
        first=message.from_user.first_name,
        last=message.from_user.last_name,
        nickname=message.from_user.username,
        id=message.from_user.id,
        enabled=True
        )
    if not User.select().where(User.id == new_guy.id):
        new_guy.save()
        bot.reply_to(message, f"Hi, {message.from_user.first_name} you are now in the list")
    else:
        bot.reply_to(message, f"Hi, {message.from_user.first_name} you are already in the list")
    print(f"{new_guy.nickname} registered")
    
@bot.message_handler(commands=['off'])
def go_off(message):
    u = User.get(User.id == message.from_user.id)
    u = User.update(enabled=False).where(User.id == message.from_user.id)
    u.execute()
    bot.reply_to(message, "You will not receive invitations from now on")

@bot.message_handler(commands=['on'])
def go_on(message):
    u = User.get(User.id == message.from_user.id)
    u = User.update(enabled=True).where(User.id == message.from_user.id)
    u.execute()
    bot.reply_to(message, "You will receive invitations from now on")

@bot.message_handler(commands=['help'])
def send_help(message):
    m="""/off to stop receiving coffee invitations
/on to enable them again"""
    bot.reply_to(message, m)

def construct(user1, user2):
    s="Hi, "
    if user1.nickname:
        s += f"@{user1.nickname}. "
    if user2.nickname:
        s += f"@{user2.nickname} ("
    if user2.first:
        s += f"{user2.first} "
    if user2.last:
        s += f"{user2.last}"
    if user2.nickname:
        s += ")"
    s += " will be your coffee mate today"
    return s

def send_invites():
    users=list(User.select().where(User.enabled == True))
    random.shuffle(users)
    while len(users) > 1:
        user1=users.pop()
        user2=users.pop()
        print(construct(user1, user2), "|||", construct(user2, user1))
        bot.send_message(user1.id, construct(user1, user2))
        bot.send_message(user2.id, construct(user2, user1))

if args.send_at_start:
    send_invites()
bot.polling(none_stop=True, interval=0)