# Small threading demo
import threading
from time import sleep

# Every second, we want to allow 25 more requests to be sent.
# If we get a throttle request, we should also pause for some amount of time

N_REQUESTS_PER_SECOND = 25


class SharedData:
    def __init__(self):
        self.cv = threading.Condition()
        self.n_requests_available = N_REQUESTS_PER_SECOND
        self.n_requests_sent = 0


def rate_limiter(requests_per_second, *, sync):
    while True:
        sleep(1)

        # Acquire lock and update requests allowed
        with sync.cv:
            print(f"Requests sent: {sync.n_requests_sent}")
            sync.n_requests_available = requests_per_second
            sync.cv.notify_all()


def worker(i, *, sync):
    # Acquire lock and clear for sending a request
    with sync.cv:
        while not sync.n_requests_available:
            sync.cv.wait()
        sync.n_requests_available -= 1
        sync.n_requests_sent += 1

    # print(f"Sending request {i}!")


def orchestrate():
    shared = SharedData()

    # Daemons are killed when the program exits.
    threading.Thread(
        target=rate_limiter,
        args=(N_REQUESTS_PER_SECOND,),
        kwargs={"sync": shared},
        daemon=True,
    ).start()

    # Should launch 25 threads per second
    threads = []
    for i in range(100):
        t = threading.Thread(target=worker, args=(i,), kwargs={"sync": shared})
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print(f"Requests sent: {shared.n_requests_sent}")
    print("All done!")


if __name__ == "__main__":
    orchestrate()
