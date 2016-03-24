import random


def _weighted_choice(choices):
    total = sum(w for c, w in choices)
    r = random.uniform(0, total)
    upto = 0
    for c, w in choices:
        if upto + w >= r:
            return c
        upto += w
    assert False, "Shouldn't get here"

def _random_letters_aab(alphabet):
    doubled = random.choice(alphabet)
    return [doubled, doubled, random.choice(alphabet)]

def _random_letters_aba(alphabet):
    doubled = random.choice(alphabet)
    return [doubled, random.choice(alphabet), doubled]

def _random_letters_abb(alphabet):
    doubled = random.choice(alphabet)
    return [random.choice(alphabet), doubled, doubled]

def _random_letters_abc(alphabet):
    return [random.choice(alphabet) for _ in range(3)]

def _random_vowels(alphabet):
    algorithms = [
                  _random_letters_aab,
                  _random_letters_aba,
                  _random_letters_abb,
                  _random_letters_abc,
                  ]
    return random.choice(algorithms)(alphabet)

def _pick_vowel_type():
    return random.choice([list('äöyei'), list('aouei')])

def _random_ending(last_vowel, vowels):
    return random.choice([
        lambda l, v: "",
        lambda l, v: "s",
        lambda l, v: "l{}".format(l),
        lambda l, v: "r{}".format(l),
        lambda l, v: "r{}{}".format(l, l),
        lambda l, v: "kk{}".format(l),
        lambda l, v: "d{}r".format(l),
        lambda l, v: "t{}s".format(l),
        lambda l, v: "ts{}".format(l),
        lambda l, v: "l{}{}n{}".format(l, l, random.choice(vowels)),
        lambda l, v: "ll{}pp{}".format(l, random.choice(vowels)),
    ])(last_vowel, vowels)

def random_word():
    all_vowels = _pick_vowel_type()

    vowels = _random_vowels(all_vowels)
    first_consonant = random.choice(['s', 'ss', 'p', 'pp', 'ps', 't', 'ts', ''])

    header = _weighted_choice([['nj', 8], ['h', 1], ['p', 1]])
    ender = _random_ending(vowels[2], all_vowels)

    return "{}{}{}{}{}".format(header, vowels[0], first_consonant, vowels[1], ender)
