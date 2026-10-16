"""One background thread, one queue: the GPU handles one model job at a time. Extraction and narrative jobs share the queue.

Each job runs in a helper thread with a deadline (JOB_TIMEOUT_SECONDS). A Python thread cannot be killed, so on timeout the document is marked
failed/timeout, the job is told to stop writing (cancel event) and the worker moves on; the model call itself is bounded by the HTTP timeout."""
import logging
import queue
import threading

log = logging.getLogger("carebridge")


class Worker:
    def __init__(self, pipeline, timeout_s: float, queue_max: int):
        self.pipeline, self.timeout_s, self.queue_max = pipeline, timeout_s, queue_max
        self.q: queue.Queue = queue.Queue()
        self._extractions = 0  # queued + running extraction jobs (the limit applies to these)
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        pipeline.worker = self

    def start(self) -> None:
        if self._thread is None:
            self._thread = threading.Thread(target=self._loop, name="carebridge-worker", daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self.q.put(None)
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

    def has_room(self) -> bool:
        with self._lock:
            return self._extractions < self.queue_max

    def submit_extraction(self, doc_id: str) -> bool:
        with self._lock:
            if self._extractions >= self.queue_max:
                return False
            self._extractions += 1
        self.q.put(("extract", doc_id, None))
        return True

    def submit_narrative(self, doc_id: str, lang: str) -> None:
        self.q.put(("narrative", doc_id, lang))

    def join(self) -> None:
        self.q.join()

    def _loop(self) -> None:
        while True:
            job = self.q.get()
            try:
                if job is None:
                    return
                self._run(*job)
            except Exception as e:  # a job must never kill the worker
                log.error("worker job crashed type=%s", type(e).__name__)
            finally:
                if job is not None and job[0] == "extract":
                    with self._lock:
                        self._extractions -= 1
                self.q.task_done()

    def _run(self, kind: str, doc_id: str, lang: str | None) -> None:
        cancel = threading.Event()
        target = (lambda: self.pipeline.run_extraction(doc_id, cancel)) if kind == "extract" else (lambda: self.pipeline.run_narrative(doc_id, lang, cancel))
        def guarded():
            try:
                target()
            except Exception as e:  # type only: the message may contain user content
                log.error("doc=%s job=%s crashed type=%s", doc_id, kind, type(e).__name__)
                if kind == "extract":
                    self.pipeline.fail(doc_id, "interrupted")

        t = threading.Thread(target=guarded, daemon=True)
        t.start()
        t.join(self.timeout_s)
        if t.is_alive():
            cancel.set()
            log.error("doc=%s job=%s timed out after %ss", doc_id, kind, self.timeout_s)
            if kind == "extract":
                self.pipeline.fail(doc_id, "timeout")
            else:
                with self.pipeline.db.session() as c:
                    self.pipeline._set_narrative(c, doc_id, lang, "failed")
