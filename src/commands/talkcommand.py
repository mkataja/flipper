from __future__ import unicode_literals
from commands.command import Command
import random
import sqlite3


class TalkCommand(Command):
    helpstr = "Käyttö: syötä komennon jälkeen avainsana, muutoin satunnainen lausahdus"

    # helper
    def _continue_link(self, cursor, d):
        
        if ( d == 'next'):
            for ret in cursor:
                if ( ret[2] > 15 ):
                    return False
        else:
            for ret in cursor:
                if ( ret[1] > 15):
                    return False
        return True

    # get a word from the database
    # cursor = db.cursor, d = 'next' or 'prev', word = source
    def _get_word(self, cursor, d, word):
        try:
            cursor.execute('SELECT id, first, last, next, prev FROM words WHERE id="{key}"'.format(key = word))
            freqs = []
            words = []
            wordsum = 0
            for res in cursor:
                msg = res[d]
                if ( len(msg) > 0 ):
                    msg = msg.split('§')
                    for i in msg:
                        pair = i.split(' ')
                        wordsum += int(pair[1])
                        words.append( pair[0] )
                        freqs.append( wordsum )
                    rando = random.randint(0, wordsum)
                    for i in range(0, len(freqs)):
                        if ( rando < freqs[i] ):
                            cont = True
                            try:
                                cursor.execute('SELECT id, first, last FROM words WHERE id="{key}"'.format(key = words[i]))
                                cont = self._continue_link(cursor, d)
                                return [words[i], cont]
                            except sqlite3.Error as e:
                                print('2: '+str(e))
                                return ['', False]
            return ['', False]
        except sqlite3.Error as e:
            print('1: '+str(e))
            return ['', False]




    # get a sentence in the chosen direction (d)
    def _get_sentence(self, cursor, d, s):
        # superintelligently built word length algorithm for natural sentence length
        sl = random.randint(0, 1) + random.randint(0, 2) + random.randint(0, 3) + random.randint(1, 3)
        w = [s, True]
        ret = s + ' '
        for i in range(0, sl):
            w = self._get_word(cursor, d, w[0])
            if ( len(w[0]) > 0):
                if ( d == 'next' ):
                    ret += w[0] + ' '
                else:
                    ret = w[0] + ' ' + ret
            else:
                break
        count = 0
        while ( count < 8 and w[1] == True ):
            count += 1
            w = self._get_word(cursor, d, w[0])
            if ( len(w[0]) > 0):
                if ( d == 'next' ):
                    ret += w[0] + ' '
                else:
                    ret = w[0] + ' ' + ret 
            else:
                break
        return ret

    # get a random sentence
    def _get_random_sentence(self, cursor):
        try:
            cursor.execute('SELECT id, first FROM words')
            allr = cursor.fetchall()
            r = len(allr)
            ret = ['lol', 0]
            while ( ret[1] < 20 ):
                ret = allr[random.randint(0, r)]	
            return self._get_sentence(cursor, 'next', ret[0])
        except sqlite3.Error as e:
            return 'errori :D '+str(e)

    # get a sentence based on a word
    def _get_keyword_sentence(self, cursor, w):
        a = self._get_sentence(cursor, 'prev', w)
        b = self._get_sentence(cursor, 'next', w)
        return a + b.split(' ', 1)[1]

    # get a sentence based on a sentence
    def _get_sentence_sentence(self, cursor, w):
        a = self._get_sentence(cursor, 'prev', w[0].strip())
        b = self._get_sentence(cursor, 'next', w[len(w)-1].strip())
        return a + ' '.join(w).split(' ', 1)[1] + ' ' + b.split(' ', 1)[1]

    
    def handle(self, message):
        db = sqlite3.connect('vocabulary')
        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        words = message.params.split(" ")
        words = [x.strip() for x in words if x.strip() != ""]
        
        if not words:
            message.reply_to( self._get_random_sentence(cursor) )
        else:
            if ( len(words) > 1):
                print(words)
                message.reply_to( self._get_sentence_sentence(cursor, words) )                    
            else:
                message.reply_to( self._get_keyword_sentence(cursor, words[0].strip()) )

        db.close()
