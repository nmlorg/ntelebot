"""A thread-based long-poll watcher and synchronizer."""

import functools
import logging
import random
import threading
import time

import ntelebot


class Loop(object):
    """A thread-based long-poll watcher and synchronizer."""

    stopped = False

    def __init__(self):
        self.queue = ntelebot.delayqueue.DelayQueue()
        self.active = set()

    def add(self, bot, dispatcher):
        """Begin polling bot for updates to be fed into dispatcher by Loop.run."""

        if bot.token not in self.active:
            self.active.add(bot.token)
            thr = threading.Thread(target=self._poll_bot, args=(bot, dispatcher))
            thr.daemon = True
            thr.start()

    def remove(self, token):
        """Stop polling for updates for the given API Token."""

        self.active.remove(token)

    def _poll_bot(self, bot, dispatcher):
        backoff = 0
        offset = None
        while not self.stopped and bot.token in self.active:
            if backoff:
                logging.debug('Backing off for %r seconds.', backoff)
                time.sleep(backoff)
            backoff = max(min(backoff * 2, 30), 1) * (random.random() + .5)
            timeout = max(0, bot.timeout - 2)
            try:
                updates = bot.get_updates(offset=offset, timeout=timeout)
            except ntelebot.errors.Conflict:
                logging.error('Another process is using this bot token.')
            except ntelebot.errors.Unauthorized:
                logging.error('Bot token is not/no longer authorized.')
            except ntelebot.errors.Timeout:
                logging.debug(
                    'Asked Telegram to return after %r seconds, then waited %r with no reply!',
                    timeout, bot.timeout)
            except Exception:  # pylint: disable=broad-except
                logging.exception('Ignoring uncaught error while polling:')
            else:
                backoff = 0
                if not self.stopped and updates and bot.token in self.active:
                    offset = updates[-1]['update_id'] + 1
                    for update in updates:
                        self.queue.put(functools.partial(dispatcher, bot, update))

    def run(self):
        """Wait for updates received from Loop.add and feed them through the given dispatcher."""

        while not self.stopped:
            callback = self.queue.get()
            if callback:
                try:
                    callback()
                except Exception:  # pylint: disable=broad-except
                    logging.exception('Ignoring uncaught error while dispatching:')
            self.queue.task_done()

    def stop(self):
        """Stop polling for updates and return as soon as all acked updates have been dispatched.

        Threads created by Loop.add will continue waiting for updates, but will either timeout or
        discard all updates received. In the latter case, an update is not marked as "acknowledged"
        until a call to Bot.get_updates with an offset of 1 higher than its update_id is made, so
        discarded updates will be resent the next time the bot is polled.
        """

        if not self.stopped:
            self.stopped = True
            self.queue.put(None)
