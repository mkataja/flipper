from modules import firstshout, logging, niiloism, reminder, repeat, url

MODULES = [
    firstshout.FirstShoutModule,
    reminder.ReminderModule,
]

MESSAGE_HANDLERS = [
    url.UrlModule,
    repeat.RepeatModule,
    logging.LoggingModule,
    niiloism.NiiloismModule,
]
