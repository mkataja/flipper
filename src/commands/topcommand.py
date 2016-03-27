import json
import logging
import urllib

from commands.command import Command


class TopCommand(Command):
    helpstr = "Kaytto: Listaa tämän hetken kovimmat juomarit"

    def handle(self, message):
        # print( str(message.sender) )
        url = 'http://dementia.alakerta.org/kannit/get_top'
        values = {'from': 'irc'}

        data = urllib.parse.urlencode(values)
        binary_data = data.encode('utf-8')
        req = urllib.request.Request(url, binary_data)
        try:
            response = urllib.request.urlopen(req)
            # print( response.read() )
            msg = json.loads(response.read().decode('utf-8'))
            print(msg)
            message.reply_to(msg)
        except urllib.error.HTTPError as error:
            print(error)
            message.reply_to(u'Ei yhteyttä palvelimeen! :(')
        # print( response.read() )

        # words = message.params.split(" ")
        # words = [x.strip() for x in words if x.strip() != ""]
        # message.reply_to(reply)
