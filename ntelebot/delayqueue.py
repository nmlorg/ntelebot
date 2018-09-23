"""A queue of (when, item) that doesn't return items until their target time has passed."""

from __future__ import absolute_import, division, print_function, unicode_literals

import heapq
try:
    import queue
except ImportError:  # pragma: no cover
    import Queue as queue
import time


class DelayQueue(queue.PriorityQueue, object):
    """A queue of (when, item) that doesn't return items until their target time has passed."""

    def _init(self, maxsize):
        super(DelayQueue, self)._init(maxsize)
        self.__subqueue = []

    def puthourly(self, offset, item):
        """Schedule item to be returned at the next offset past the hour."""

        now = time.time()
        when = now // 3600 * 3600 + offset
        if when <= now:
            when += 3600
        return self.putwhen(when, item)

    def putwhen(self, when, item):
        """Schedule item to be returned when time.time() >= when."""

        return super(DelayQueue, self).put((when, time.time(), item))

    def put(self, item):  # pylint: disable=arguments-differ
        return self.putwhen(0, item)

    def get(self):  # pylint: disable=arguments-differ
        while True:
            delay = 10000
            if self.__subqueue:
                when, _, item = self.__subqueue[0]
                now = time.time()
                if when <= now:
                    heapq.heappop(self.__subqueue)
                    return item
                delay = when - now

            try:
                record = super(DelayQueue, self).get(True, delay)
            except queue.Empty:
                pass
            else:
                heapq.heappush(self.__subqueue, record)