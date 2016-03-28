from lib import niiloism


def quit_message():
    try:
        quit_message = niiloism.random_word()
    except:
        # The failure doesn't matter; a message is required nonetheless
        quit_message = "Quitting"
    return quit_message
