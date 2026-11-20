"""Tests for ntelebot.delayqueue."""

import time

import ntelebot


def test_simple():
    """Test simple queue ordering."""

    queue = ntelebot.delayqueue.DelayQueue()
    queue.put(2)
    queue.put(3)
    queue.put(4)
    assert queue.get() == 2
    assert queue.get() == 3
    assert queue.get() == 4

    now = time.time()
    queue.putwhen(now + 1, 5)
    queue.putwhen(now + .5, 4)
    queue.putwhen(now + .25, 3)
    assert queue.get() == 3
    assert queue.get() == 4
    assert queue.get() == 5


def test_puthourly(monkeypatch):
    """Test DelayQueue.puthourly."""

    queue = ntelebot.delayqueue.DelayQueue()
    monkeypatch.setattr('time.time', lambda: 0)
    queue.puthourly(100, 2)
    assert queue.queue == [(100, 0, 2)]

    queue = ntelebot.delayqueue.DelayQueue()
    monkeypatch.setattr('time.time', lambda: 0)
    queue.puthourly(100, 2, jitter=300)
    assert queue.queue == [(100 + 300, 0, 2)]

    queue = ntelebot.delayqueue.DelayQueue()
    monkeypatch.setattr('time.time', lambda: 200)
    queue.puthourly(100, 2)
    assert queue.queue == [(3600 + 100, 200, 2)]

    queue = ntelebot.delayqueue.DelayQueue()
    monkeypatch.setattr('time.time', lambda: 200)
    queue.puthourly(100, 2, jitter=300)
    assert queue.queue == [(3600 + 100 + 300, 200, 2)]
