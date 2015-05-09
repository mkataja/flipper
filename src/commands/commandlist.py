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
               'reload': systemcommands.ReloadCommand,
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
               }

PRIVATE_CMDS = {
                'say': irccommands.SayCommand,
                'join': irccommands.JoinCommand,
                'part': irccommands.PartCommand,
                'hop': irccommands.HopCommand,
                }

ALL_CMDS = PUBLIC_CMDS.copy()
ALL_CMDS.update(PRIVATE_CMDS)
