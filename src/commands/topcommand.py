import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from commands.command import Command


class TopCommand(Command):
    helpstr = "Kaytto: Listaa tämän hetken kovimmat juomarit"

    def handle(self, message):
        url = 'https://dementia.alakerta.org/kannit/get_top'
        values = {'from': 'irc'}

        data = urllib.parse.urlencode(values)
        binary_data = data.encode('utf-8')
        req = urllib.request.Request(url, binary_data)
        try:
            response = urllib.request.urlopen(req)
            msg = json.loads(response.read().decode('utf-8'))
            message.reply_to(msg)
        except urllib.error.HTTPError as error:
            logging.error('Error in TopCommand: ' + str(error))
            message.reply_to(u'Ei yhteyttä palvelimeen! :(')
