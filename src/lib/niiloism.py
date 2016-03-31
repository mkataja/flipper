import random

from lib.random import weighted_choice


_random_vowel_algorithms = [
    lambda l: [l[0], l[0], l[1]],
    lambda l: [l[0], l[1], l[0]],
    lambda l: [l[0], l[1], l[1]],
    lambda l: [l[0], l[1], l[2]],
]


_random_ending_algorithms = [
    lambda l, v: "",
    lambda l, v: "s",
    lambda l, v: "l{}".format(l),
    lambda l, v: "r{}".format(l),
    lambda l, v: "r{}{}".format(l, l),
    lambda l, v: "kk{}".format(l),
    lambda l, v: "nd{}r".format(l),
    lambda l, v: "t{}s".format(l),
    lambda l, v: "ts{}".format(l),
    lambda l, v: "l{}{}n{}".format(l, l, random.choice(v)),
    lambda l, v: "ll{}pp{}".format(l, random.choice(v)),
]


def _random_vowels(alphabet):
    chosen = [random.choice(alphabet) for _ in range(3)]
    return random.choice(_random_vowel_algorithms)(chosen)


def _random_ending(last_vowel, vowels):
    return random.choice(_random_ending_algorithms)(last_vowel, vowels)


def _pick_vowel_type():
    front_vowels = list('äöyei')
    back_vowels = list('aouei')
    return random.choice([front_vowels, back_vowels])


def _get_header():
    headers = [['nj', 12], ['tj', 2], ['j', 1], ['h', 1], ['p', 1]]
    return weighted_choice(headers)


def _get_second_header(first_header):
    headers = list('bhjknpt')
    return random.choice([h for h in headers if h != first_header])


def _get_body(all_vowels):
    chosen_vowels = _random_vowels(all_vowels)
    first_vowel = weighted_choice([[lambda v:v, 3],
                                   [lambda v:"{}{}".format(v, v), 1]]
                                  )(chosen_vowels[0])
    first_consonant = random.choice(['s', 'ss', 'p', 'pp', 'ps', 't', 'ts', ''])
    ender = _random_ending(chosen_vowels[2], all_vowels)
    return "{}{}{}{}".format(first_vowel, first_consonant, chosen_vowels[1], ender)


def _simple(vowels):
    return "{}{}".format(_get_header(), _get_body(vowels))


def _doubled(vowels):
    first_header = _get_header()
    body = _get_body(vowels)
    return "{}{}{}{}".format(first_header,
                             body,
                             _get_second_header(first_header),
                             body)


def _complex(vowels):
    header = _get_header()
    return "{}{}{}{}".format(header,
                             _get_body(vowels),
                             header,
                             _get_body(vowels))


def random_word():
    vowels = _pick_vowel_type()

    _get_body(vowels)

    return weighted_choice([[_simple, 10], [_doubled, 2], [_complex, 1]])(vowels)
