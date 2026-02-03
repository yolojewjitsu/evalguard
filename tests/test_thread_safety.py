"""Thread safety tests for evalguard."""

import threading
from concurrent.futures import ThreadPoolExecutor

from evalguard import check, expect


class TestThreadSafety:
    def test_expect_concurrent_access(self):
        """Test expect() is safe from multiple threads."""
        errors = []

        def worker(thread_id):
            try:
                for i in range(100):
                    value = f"test_{thread_id}_{i}"
                    expect(value).contains("test").not_contains("invalid")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Errors occurred: {errors}"

    def test_decorator_concurrent_calls(self):
        """Test decorated function called from multiple threads."""
        call_count = [0]
        lock = threading.Lock()

        @check(contains=["result"], not_contains=["error"])
        def safe_func(thread_id, call_id):
            with lock:
                call_count[0] += 1
            return f"result_{thread_id}_{call_id}"

        errors = []

        def worker(thread_id):
            try:
                for i in range(50):
                    safe_func(thread_id, i)
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker, i) for i in range(10)]
            for f in futures:
                f.result()

        assert not errors, f"Errors occurred: {errors}"
        assert call_count[0] == 500
