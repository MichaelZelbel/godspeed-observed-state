import datetime as dt
import unittest

import refresh_if_stale as refresh


class RefreshTests(unittest.TestCase):
    def test_dispatch_only_when_shared_copy_is_old(self):
        now = dt.datetime(2026, 11, 9, 11, 0, tzinfo=dt.timezone.utc)
        self.assertFalse(refresh.needs_refresh({'checked_utc': '2026-11-09T10:00:00Z'}, now))
        self.assertTrue(refresh.needs_refresh({'checked_utc': '2026-11-09T09:00:00Z'}, now))
        self.assertTrue(refresh.needs_refresh({}, now))

    def test_active_run_prevents_duplicate_dispatch(self):
        now = dt.datetime(2026, 11, 9, 11, 0, tzinfo=dt.timezone.utc)
        rows = [{'status': 'in_progress', 'createdAt': '2026-11-09T10:45:00Z'}]
        self.assertTrue(refresh.active_refresh(rows, now))
        self.assertFalse(refresh.active_refresh([{'status': 'completed', 'createdAt': '2026-11-09T10:45:00Z'}], now))


if __name__ == '__main__':
    unittest.main()
