# coding=utf-8
'''
Created on Jul 7, 2012

@author: Matias
'''

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
               }

PRIVATE_CMDS = {
                'say': builtincommands.SayCommand,
                'join': builtincommands.JoinCommand,
                'part': builtincommands.PartCommand,
                }
