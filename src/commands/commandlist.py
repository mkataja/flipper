# coding=utf-8

from commands import (
                      systemcommands,
                      openweathermapcommand,
                      rollcommand,
                      realweathercommand,
                      flipcommand,
                      irccommands,
                      mooncommand,
                      fmiweathercommand,
                      talkcommand,
                      markovcommand,
                      )


PUBLIC_CMDS = {
               'help': systemcommands.HelpCommand,
               'list': systemcommands.ListCommand,
               'flip': flipcommand.FlipCommand,
               'flippaa': flipcommand.FlipCommand,
               'quit': irccommands.QuitCommand,
               'sää': fmiweathercommand.FmiWeatherCommand,
               'fmi': fmiweathercommand.FmiWeatherCommand,
               'openweathermap': openweathermapcommand.OpenWeatherMapCommand,
               'todellinensää': realweathercommand.RealWeatherCommand,
               'roll': rollcommand.RollCommand,
               'moon': mooncommand.MoonCommand,
               'kuu': mooncommand.MoonCommand,
               'puhu': talkcommand.TalkCommand,
               'markov': markovcommand.MarkovCommand,
               'pyhä': markovcommand.markov_command_factory('raamattu'),
               }

PRIVATE_CMDS = {
                'say': irccommands.SayCommand,
                'join': irccommands.JoinCommand,
                'part': irccommands.PartCommand,
                'hop': irccommands.HopCommand,
                }

ALL_CMDS = {}
ALL_CMDS.update(PUBLIC_CMDS)
ALL_CMDS.update(PRIVATE_CMDS)
