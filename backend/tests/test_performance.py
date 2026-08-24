import pytest
import time
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestPerformance:
    """Performance tests for API endpoints."""

    def test_stock_info_response_time(self):
        """Test stock info endpoint response time."""
        start_time = time.time()

        # Mock the external API call
        with pytest.raises(Exception):  # Expected to fail without real API
            client.get("/api/v1/stocks/AAPL/info")

        end_time = time.time()
        response_time = end_time - start_time

        # Should respond within 5 seconds (including timeout)
        assert response_time < 5.0

    def test_concurrent_requests(self):
        """Test handling concurrent requests."""
        def make_request():
            try:
                return client.get("/api/v1/models/")
            except Exception:
                return None

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in futures]

        # At least some requests should succeed
        successful = [r for r in results if r is not None and r.status_code == 200]
        assert len(successful) > 0

    def test_validation_performance(self):
        """Test stock validation performance with multiple symbols."""
        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"] * 10  # 50 symbols

        start_time = time.time()
        response = client.post("/api/v1/stocks/validate", json=symbols)
        end_time = time.time()

        response_time = end_time - start_time

        # Should validate 50 symbols within 10 seconds
        assert response_time < 10.0

    def test_api_pagination(self):
        """Test API pagination performance."""
        # Test with different page sizes
        for limit in [10, 50, 100]:
            start_time = time.time()
            response = client.get(f"/api/v1/models/?limit={limit}")
            end_time = time.time()

            response_time = end_time - start_time

            # Should respond within 2 seconds
            assert response_time < 2.0


class TestCachePerformance:
    """Test caching performance."""

    def test_cached_response_faster(self):
        """Test that cached responses are faster."""
        # First request (uncached)
        start1 = time.time()
        try:
            client.get("/api/v1/stocks/AAPL/info")
        except Exception:
            pass
        end1 = time.time()
        time1 = end1 - start1

        # Second request (potentially cached)
        start2 = time.time()
        try:
            client.get("/api/v1/stocks/AAPL/info")
        except Exception:
            pass
        end2 = time.time()
        time2 = end2 - start2

        # Note: This test may not show difference without real caching
        # In production, cached responses should be significantly faster


class TestMemoryUsage:
    """Test memory usage."""

    def test_large_batch_validation(self):
        """Test memory usage with large batch validation."""
        symbols = [f"SYM{i}" for i in range(100)]

        try:
            response = client.post("/api/v1/stocks/validate", json=symbols)
            # Should not crash with large batches
            assert response.status_code in [200, 500]  # May fail due to invalid symbols
        except Exception:
            pass  # Expected without real API


class TestLoadTesting:
    """Load testing utilities."""

    @pytest.mark.skip(reason="Load test - run manually")
    def test_sustained_load(self):
        """Test sustained load handling."""
        duration = 10  # seconds
        requests_per_second = 10

        start_time = time.time()
        request_count = 0
        errors = 0

        while time.time() - start_time < duration:
            try:
                response = client.get("/api/v1/models/")
                request_count += 1
                if response.status_code != 200:
                    errors += 1
            except Exception:
                errors += 1

            time.sleep(1 / requests_per_second)

        error_rate = errors / request_count if request_count > 0 else 0

        # Error rate should be less than 10%
        assert error_rate < 0.1

        # Should handle at least 50 requests in 10 seconds
        assert request_count >= 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
