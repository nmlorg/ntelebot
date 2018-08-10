"""A thread-based long-poll watcher and synchronizer."""

from __future__ import absolute_import, division, print_function, unicode_literals

try:
    import queue
except ImportError:
    import Queue as queue
import threading


class Loop(object):
    """A thread-based long-poll watcher and synchronizer."""

    stopped = False

    def __init__(self):
        self.queue = queue.Queue()

    def add(self, bot, dispatcher):
        """Begin polling bot for updates to be fed into dispatcher by Loop.run."""

        thr = threading.Thread(target=self._poll_bot, args=(bot, dispatcher))
        thr.daemon = True
        thr.start()

    def _poll_bot(self, bot, dispatcher):
        offset = None
        while not self.stopped:
            updates = bot.get_updates(offset=offset, timeout=max(0, bot.timeout - 2))
            if not self.stopped and updates:
                offset = updates[-1]['update_id'] + 1
                for update in updates:
                    self.queue.put((bot, dispatcher, update))

    def run(self):
        """Wait for updates received from Loop.add and feed them through the given dispatcher."""

        while not self.stopped:
            try:
                bot, dispatcher, update = self.queue.get(True, 10000)
            except queue.Empty:
                continue
            else:
                if dispatcher and update:
                    dispatcher(bot, update)
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
            self.queue.put((None, None, None))
