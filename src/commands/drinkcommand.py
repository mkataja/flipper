import logging
import urllib
import json

from commands.command import Command


class DrinkCommand(Command):
    helpstr = "Käyttö: !juo [vahvuus(%)] [tilavuus(ml)] [nimi, ei pakollinen] = juomakomento TAI !juo = edellinen juoma TAI !juo peru = peru viimeisin juoma TAI !juo pintalaatta = tietäjät tietää"

    # Checks whether the given alcohol volume is valid: only numbers and %, delimiter is either . or ,
    def __volts(self, s):
        #if ( "," in s or "." in s):
        t = s.replace( u'\u0025',u'').replace( u'\u002E',u'').replace(u'\u002C', u'')#s.translate(None, '.,%')
        if ( t.isdigit() ):
            return float( s.replace( u'\u0025',u'').replace(u'\u002C', u'.') )#s.translate(None, '%'))
        return False

    # Checks wheter the given alcohol volume is valid
    def __vol(self, s):
        logging.error("DrinkCommand: __vol not yet implemented")

        
    def handle(self, message):

        words = message.params.split(" ")
        words = [x.strip() for x in words if x.strip() != ""]

        url = 'http://dementia.alakerta.org/kannit/add_drink'
        values = {'nick':message.sender, 'cmd':'', 'code':'secret_code'}

        ipt = len(words)
        msg = ""
        
        if ( ipt == 0): # if just !juo
            values['cmd'] = 'repeat'
        elif ( ipt == 1): # if !juo word, and at this point !juo peru
            if ( words[0].casefold() == 'peru'):
                values['cmd'] = 'cancel'
            elif ( 'pinta' in words[0].casefold() or 'laatta' in words[0].casefold() ):
                values['cmd'] = 'vomit'
            else:
                msg = 'Tuntematon komento!' 
        elif ( ipt >= 2): # if !juo number number 0.....n words, the basic case
            name = "Alkoholijuoma"
            if (ipt > 2):
                name = " ".join(words[2:]).title()
            if ( self.__volts(words[0]) and words[1].isdigit() ):
                values['cmd'] = 'drink'
                values['volts'] = self.__volts(words[0])/100.0
                values['volume'] = int(words[1])/1000.0
                values['name'] = name+" "+words[0].replace(u'\u002C',u'.').replace(u'\u0025',u'')+"% "+str(words[1])+"ml"
            else:
                msg = "Virheelliset parametrit!"# Syötä !juo [vahvuus(%)] [tilavuus(ml)] [nimi], esim. !juo 4.8 330 olut"
        else:
            msg = "Virhe jossain :("
            logging.error("DrinkCommand: LOL, something went really wrong here")
        
        #url = 'http://dementia.alakerta.org/kannit/add_drink'
        #values = {'nick':message.sender}
        if ( msg == ''):
            data = urllib.parse.urlencode(values)
            binary_data = data.encode('utf-8')
            req = urllib.request.Request(url, binary_data)
            try:
                response = urllib.request.urlopen(req, timeout=3)
                message.reply_to( json.loads(response.read().decode('utf-8')) )
            except urllib.error.HTTPError as error:
                logging.error("DrinkCommand: {}".format(error))
                message.reply_to("Nyt jokin meni pieleen palvelun päässä :(")
            except urllib.error.URLError:
                message.reply_to("Juomapalvelu ei vastannut ennen aikakatkaisua :(")
        else:
            message.reply_to(msg)
