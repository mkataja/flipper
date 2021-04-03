# coding=utf-8

from commands import *


PUBLIC_CMDS = {
    'help': systemcommands.HelpCommand,
    'list': systemcommands.ListCommand,
    'flip': flipcommand.FlipCommand,
    'flippaa': flipcommand.FlipCommand,
    'quit': irccommands.QuitCommand,
    fmiweathercommand.FORECAST_COMMAND: fmiweathercommand.FmiWeatherCommand,
    fmiweathercommand.OBSERVATION_COMMAND: fmiweathercommand.FmiWeatherCommand,
    'openweathermap': openweathermapcommand.OpenWeatherMapCommand,
    'todellinensää': realweathercommand.RealWeatherCommand,
    'roll': rollcommand.RollCommand,
    'moon': mooncommand.MoonCommand,
    'kuu': mooncommand.MoonCommand,
    'puhu': talkcommand.TalkCommand,
    'markov': markovcommand.MarkovCommand,
    'pyhä': markovcommand.get_markov_command(corpus_name='raamattu'),
    'sanonta': markovcommand.get_markov_command(corpus_name='sanonnat'),
    'imitate': imitatecommand.ImitateCommand,
    'imitoi': imitatecommand.ImitateCommand,
    'top': topcommand.TopCommand,
    'juo': drinkcommand.DrinkCommand,
    'geocode': geocodecommand.GeocodeCommand,
    'memo': memocommand.MemoCommand,
    'kommentoi': commentcommand.CommentCommand,
    'teach': markovteachcommand.MarkovTeachCommand,
    'muistuta': remindercommand.ReminderCommand,
}

PRIVATE_CMDS = {
    'say': irccommands.SayCommand,
    'join': irccommands.JoinCommand,
    'part': irccommands.PartCommand,
    'hop': irccommands.HopCommand,
    'nick': irccommands.NickCommand,
    'op': irccommands.OpCommand,
}

ALL_CMDS = {}
ALL_CMDS.update(PUBLIC_CMDS)
ALL_CMDS.update(PRIVATE_CMDS)
