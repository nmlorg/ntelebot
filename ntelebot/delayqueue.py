"""A queue of (when, item) that doesn't return items until their target time has passed."""

import heapq
import queue
import time


class DelayQueue(queue.PriorityQueue, object):
    """A queue of (when, item) that doesn't return items until their target time has passed."""

    def _init(self, maxsize):
        super(DelayQueue, self)._init(maxsize)
        self.__subqueue = []

    def puthourly(self, offset, item, jitter=0):
        """Schedule item to be returned at the next offset past the hour.

        jitter is intended to allow randomness without affecting scheduling, while offset sets a
        fixed pivot point for determining whether to use the current or the next hour. If it is
        currently 1:00:05, item will be returned at:
                     offset=0  offset=10
          jitter=0   2:00:00   1:00:10
          jitter=10  2:00:10   1:00:20
        """

        now = time.time()
        when = now // 3600 * 3600 + offset
        if when <= now:
            when += 3600
        return self.putwhen(when + jitter, item)

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
