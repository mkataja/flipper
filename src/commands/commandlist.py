# coding=utf-8

from commands import builtincommands, weathercommand


PUBLIC_CMDS = {
               'help': builtincommands.HelpCommand,
               'list': builtincommands.ListCommand,
               'flip': builtincommands.FlipCommand,
               'flippaa': builtincommands.FlipCommand,
               'reload': builtincommands.ReloadCommand,
               'quit': builtincommands.QuitCommand,
               'sää': weathercommand.WeatherCommand,
               'todellinensää': builtincommands.RealWeatherCommand,
               'roll': builtincommands.RollCommand,
               }

PRIVATE_CMDS = {
                'say': builtincommands.SayCommand,
                'join': builtincommands.JoinCommand,
                'part': builtincommands.PartCommand,
                'hop': builtincommands.HopCommand,
                }

ALL_CMDS = PUBLIC_CMDS.copy()
ALL_CMDS.update(PRIVATE_CMDS)
