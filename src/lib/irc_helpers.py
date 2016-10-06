from lib import niiloism


def get_quit_message():
    try:
        message = niiloism.random_word()
    except:
        # Fallback to make sure this never fails
        message = "Quitting"
    return message
