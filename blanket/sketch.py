
class Scenario:
    @BoundInnerClass
    class Lock:
        def __init__(self, scenario):
            self._lock = threading.Lock()

        def __repr__(self):
            return repr(self._lock)

def acquire(self, blocking=True, timeout=None):
    blocker = self.scenario.blockers[current_thread]
    blocker.acquire()

    result = self._lock.acquire(blocking=blocking, timeout=timeout)

    pauser = self.scenario.pausers[current_thread]
    pauser.acquire()

    return result

        def release(self):
            blocker = self.scenario.blockers[current_thread]
            blocker.acquire()

            result = self._lock.release()

            pauser = self.scenario.pausers[current_thread]
            pauser.acquire()

            return result

        def locked(self):
            blocker = self.scenario.blockers[current_thread]
            blocker.acquire()

            result = self._lock.locked()

            pauser = self.scenario.pausers[current_thread]
            pauser.acquire()

            return result

