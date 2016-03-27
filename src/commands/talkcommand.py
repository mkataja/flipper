import logging
import random
import sqlite3

from commands.command import Command


class TalkCommand(Command):
    helpstr = "Käyttö: syötä komennon jälkeen avainsana, muutoin satunnainen lausahdus"

    def _continue_link(self, cursor, d):
        """Helper"""
        if (d == 'next'):
            for ret in cursor:
                if (ret[2] > 15):
                    return False
        else:
            for ret in cursor:
                if (ret[1] > 15):
                    return False
        return True

    def _get_word(self, cursor, d, word):
        """
        Gets a word from the database.
        cursor = db.cursor, d = 'next' or 'prev', word = source
        """
        try:
            cursor.execute(
                'SELECT id, first, last, next, prev FROM words WHERE id="{key}"'
                .format(key=word))
            freqs = []
            words = []
            wordsum = 0
            for res in cursor:
                msg = res[d]
                if (len(msg) > 0):
                    msg = msg.split('§')
                    for i in msg:
                        pair = i.split(' ')
                        wordsum += int(pair[1])
                        words.append(pair[0])
                        freqs.append(wordsum)
                    rando = random.randint(0, wordsum)
                    for i in range(0, len(freqs)):
                        if (rando < freqs[i]):
                            cont = True
                            cursor.execute(
                                'SELECT id, first, last FROM words WHERE id="{key}"'
                                .format(key=words[i]))
                            cont = self._continue_link(cursor, d)
                            return [words[i], cont]
            return ['', False]
        except sqlite3.Error as e:
            logging.error('Error in talkcommand: ' + str(e))
            return ['', False]

    def _get_sentence(self, cursor, d, s):
        """Gets a sentence in the chosen direction (d)"""
        # Superintelligently built word length algorithm for natural sentence length:
        sentence_length = (random.randint(0, 1) + random.randint(0, 2) +
                           random.randint(0, 3) + random.randint(1, 3))
        w = [s, True]
        ret = s + ' '
        for _ in range(0, sentence_length):
            w = self._get_word(cursor, d, w[0])
            if (len(w[0]) > 0):
                if (d == 'next'):
                    ret += w[0] + ' '
                else:
                    ret = w[0] + ' ' + ret
            else:
                break

        count = 0
        while (count < 8 and w[1] == True):
            count += 1
            w = self._get_word(cursor, d, w[0])
            if (len(w[0]) > 0):
                if (d == 'next'):
                    ret += w[0] + ' '
                else:
                    ret = w[0] + ' ' + ret
            else:
                break
        return ret

    def _get_random_sentence(self, cursor):
        """Gets a random sentence"""
        try:
            cursor.execute('SELECT id, first FROM words')
            allr = cursor.fetchall()
            r = len(allr)
            ret = ['lol', 0]
            while (ret[1] < 20):
                ret = allr[random.randint(0, r)]
            return self._get_sentence(cursor, 'next', ret[0])
        except sqlite3.Error as e:
            logging.error('Error in talkcommand: ' + str(e))
            return 'Errori :D (sanasto puuttuu?)'

    def _get_keyword_sentence(self, cursor, w):
        """Gets a sentence based on a word"""
        a = self._get_sentence(cursor, 'prev', w)
        b = self._get_sentence(cursor, 'next', w)
        return a + b.split(' ', 1)[1]

    def _get_sentence_sentence(self, cursor, w):
        """Gets a sentence based on a sentence"""
        a = self._get_sentence(cursor, 'prev', w[0].strip())
        b = self._get_sentence(cursor, 'next', w[len(w) - 1].strip())
        return a + ' '.join(w).split(' ', 1)[1] + ' ' + b.split(' ', 1)[1]

    def handle(self, message):
        connection = sqlite3.connect('../data/talk_vocabulary.sqlite')
        try:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()

            words = message.params.split(" ")
            words = [x.strip() for x in words if x.strip() != ""]

            if not words:
                reply = self._get_random_sentence(cursor)
            else:
                if (len(words) > 1):
                    reply = self._get_sentence_sentence(cursor, words)
                else:
                    reply = self._get_keyword_sentence(cursor, words[0].strip())
            reply = (reply[0].upper() + reply[1:]).strip() + '.'
            message.reply_to(reply)
        finally:
            connection.close()
