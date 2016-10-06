import config


def has_admin_access(nickmask):
    return (nickmask.nick == config.SUPERUSER_NICK and
            (nickmask.user == config.SUPERUSER_NAME or
             nickmask.user == "~{}".format(config.SUPERUSER_NAME)))
