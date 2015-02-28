# coding=utf-8

from commands import systemcommands, weathercommand, rollcommand


PUBLIC_CMDS = {
               'help': systemcommands.HelpCommand,
               'list': systemcommands.ListCommand,
               'flip': systemcommands.FlipCommand,
               'flippaa': systemcommands.FlipCommand,
               'reload': systemcommands.ReloadCommand,
               'quit': systemcommands.QuitCommand,
               'sää': weathercommand.WeatherCommand,
               'todellinensää': systemcommands.RealWeatherCommand,
               'roll': rollcommand.RollCommand,
               }

PRIVATE_CMDS = {
                'say': systemcommands.SayCommand,
                'join': systemcommands.JoinCommand,
                'part': systemcommands.PartCommand,
                'hop': systemcommands.HopCommand,
                }

ALL_CMDS = PUBLIC_CMDS.copy()
ALL_CMDS.update(PRIVATE_CMDS)
