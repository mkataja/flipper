import random


def _weighted_choice(choices):
    total = sum(w for _, w in choices)
    r = random.uniform(0, total)
    upto = 0
    for c, w in choices:
        if upto + w >= r:
            return c
        upto += w
    assert False, "Shouldn't get here"


def _random_vowels(alphabet):
    chosen = [random.choice(alphabet) for _ in range(3)]
    return random.choice([
        lambda l: [l[0], l[0], l[1]],
        lambda l: [l[0], l[1], l[0]],
        lambda l: [l[0], l[1], l[1]],
        lambda l: [l[0], l[1], l[2]],
    ])(chosen)


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
        lambda l, v: "nd{}r".format(l),
        lambda l, v: "t{}s".format(l),
        lambda l, v: "ts{}".format(l),
        lambda l, v: "l{}{}n{}".format(l, l, random.choice(vowels)),
        lambda l, v: "ll{}pp{}".format(l, random.choice(vowels)),
    ])(last_vowel, vowels)


def random_word():
    all_vowels = _pick_vowel_type()
    vowels = _random_vowels(all_vowels)

    first_vowel = _weighted_choice([
        [lambda v: v, 3],
        [lambda v: "{}{}".format(v, v), 1],
    ])(vowels[0])
    first_consonant = random.choice(['s', 'ss', 'p', 'pp', 'ps', 't', 'ts', ''])

    header = _weighted_choice([['nj', 8], ['tj', 2], ['j', 1], ['h', 1], ['p', 1]])
    ender = _random_ending(vowels[2], all_vowels)

    return "{}{}{}{}{}".format(header, first_vowel, first_consonant, vowels[1], ender)
