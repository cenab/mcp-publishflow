import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile
import yaml # Import yaml for frontmatter testing
from pathlib import Path # Import Path for file path manipulation
import jwt # Import jwt for token testing
from datetime import datetime, timedelta # Import datetime and timedelta for token testing
from fastapi import HTTPException # Import HTTPException for security tests
import redis # Import redis for rate limiting tests

from src.content_manager import ContentManager # Import ContentManager
from src.security import SecurityManager # Import SecurityManager
from src.exceptions import PublishingError, ContentValidationError, APIError # Import specific exceptions
from mcp_publish_server import make_api_request # Keep make_api_request for now, will move later

class TestContentManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory and markdown file
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_file_path = Path(self.temp_dir.name) / "test_article.md"
        self.empty_file_path = Path(self.temp_dir.name) / "empty_file.md"
        self.non_md_file_path = Path(self.temp_dir.name) / "test.txt"

        self.valid_content = """---
title: Test Title
subtitle: Test Subtitle
tags: [test, markdown]
language: en
---

# This is a test article

Some content here.
"""
        with open(self.temp_file_path, "w", encoding="utf-8") as f:
            f.write(self.valid_content)

        with open(self.empty_file_path, "w", encoding="utf-8") as f:
            f.write("")
            
        with open(self.non_md_file_path, "w", encoding="utf-8") as f:
            f.write("Just plain text.")

        self.content_manager = ContentManager() # Initialize ContentManager

    def tearDown(self):
        # Clean up the temporary directory
        self.temp_dir.cleanup()

    def test_validate_file_path(self):
        # Test valid file path
        self.content_manager.validate_file_path(self.temp_file_path)

        # Test non-existent file
        with self.assertRaises(ValueError): # Expect ValueError from ContentManager
            self.content_manager.validate_file_path("nonexistent.md")

        # Test non-markdown file
        with self.assertRaises(ValueError): # Expect ValueError from ContentManager
            self.content_manager.validate_file_path(self.non_md_file_path)

    def test_validate_title(self):
        # Test valid title
        self.content_manager.validate_title("Valid Title")

        # Test empty title
        with self.assertRaises(ValueError): # Expect ValueError from ContentManager
            self.content_manager.validate_title("")

        # Test too long title (using default max_title_length from ContentManager)
        with self.assertRaises(ValueError): # Expect ValueError from ContentManager
            self.content_manager.validate_title("a" * (self.content_manager.max_title_length + 1))

    def test_validate_subtitle(self):
        # Test valid subtitle
        self.content_manager.validate_subtitle("Valid Subtitle")

        # Test empty subtitle (should pass)
        self.content_manager.validate_subtitle("")

        # Test too long subtitle (using default max_subtitle_length from ContentManager)
        with self.assertRaises(ValueError): # Expect ValueError from ContentManager
            self.content_manager.validate_subtitle("a" * (self.content_manager.max_subtitle_length + 1))

    def test_validate_tags(self):
        # Test valid tags
        self.content_manager.validate_tags(["python", "tech", "coding"])

        # Test too many tags (using default max_tags from ContentManager)
        with self.assertRaises(ValueError): # Expect ValueError from ContentManager
            self.content_manager.validate_tags(["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"])

        # Test invalid tag format
        with self.assertRaises(ValueError): # Expect ValueError from ContentManager
            self.content_manager.validate_tags(["invalid tag!"])

    def test_read_markdown_file(self):
        # Test valid file
        content = self.content_manager.read_markdown_file(self.temp_file_path)
        # Compare content after frontmatter
        expected_content_after_frontmatter = "\n# This is a test article\n\nSome content here.\n"
        self.assertEqual(content, self.valid_content) # read_markdown_file reads the whole file

        # Test empty file
        with self.assertRaises(ValueError): # Expect ValueError from ContentManager
            self.content_manager.read_markdown_file(self.empty_file_path)

    def test_parse_frontmatter(self):
        frontmatter, content = self.content_manager.parse_frontmatter(self.valid_content)
        self.assertEqual(frontmatter['title'], 'Test Title')
        self.assertEqual(frontmatter['tags'], ['test', 'markdown'])
        self.assertEqual(content.strip(), "# This is a test article\n\nSome content here.")

        # Test content without frontmatter
        no_frontmatter_content = "# Just a title\nSome content."
        frontmatter, content = self.content_manager.parse_frontmatter(no_frontmatter_content)
        self.assertEqual(frontmatter, {})
        self.assertEqual(content, no_frontmatter_content)

    def test_validate_language(self):
        self.assertEqual(self.content_manager.validate_language("en-US"), "en")
        self.assertEqual(self.content_manager.validate_language("fr"), "fr")
        self.assertEqual(self.content_manager.validate_language("unsupported"), self.content_manager.default_language)
        self.assertEqual(self.content_manager.validate_language(None), self.content_manager.default_language)

    def test_validate_frontmatter(self):
        valid_fm = {'title': 'Valid', 'tags': ['a'], 'language': 'en'}
        self.assertEqual(self.content_manager.validate_frontmatter(valid_fm), valid_fm)

        invalid_fm_title = {'title': 'a' * (self.content_manager.max_title_length + 1)}
        with self.assertRaises(ValueError):
            self.content_manager.validate_frontmatter(invalid_fm_title)

        invalid_fm_tags = {'tags': ['a', 'b', 'c', 'd', 'e', 'f']}
        with self.assertRaises(ValueError):
            self.content_manager.validate_frontmatter(invalid_fm_tags)

        invalid_fm_tag_format = {'tags': ['invalid tag!']}
        with self.assertRaises(ValueError):
            self.content_manager.validate_frontmatter(invalid_fm_tag_format)

    @patch('requests.post')
    @patch('requests.get')
    @patch('PIL.Image.open')
    def test_process_images(self, mock_image_open, mock_requests_get, mock_requests_post):
        # Mock image data
        mock_image = MagicMock()
        mock_image_open.return_value = mock_image

        # Mock successful upload response
        mock_upload_response = MagicMock()
        mock_upload_response.status_code = 200
        mock_upload_response.json.return_value = {'url': 'http://uploaded.com/image.png'}
        mock_requests_post.return_value = mock_upload_response

        # Mock successful download response for remote image
        mock_download_response = MagicMock()
        mock_download_response.content = b'fakeimagedata'
        mock_requests_get.return_value = mock_download_response

        # Test with local image
        content_with_local_image = "![alt text](local_image.png)"
        processed_content = self.content_manager.process_images(content_with_local_image, upload_images=True)
        self.assertIn("http://uploaded.com/image.png", processed_content)
        mock_requests_post.assert_called_once()
        mock_requests_post.reset_mock()

        # Test with remote image
        content_with_remote_image = "![alt text](http://example.com/remote_image.jpg)"
        processed_content = self.content_manager.process_images(content_with_remote_image, upload_images=True)
        self.assertIn("http://uploaded.com/image.png", processed_content)
        mock_requests_get.assert_called_once_with("http://example.com/remote_image.jpg")
        mock_requests_post.assert_called_once()
        mock_requests_post.reset_mock()
        mock_requests_get.reset_mock()

        # Test without upload
        content_with_image = "![alt text](image.png)"
        processed_content = self.content_manager.process_images(content_with_image, upload_images=False)
        self.assertEqual(processed_content, content_with_image)
        mock_requests_post.assert_not_called()
        mock_requests_get.assert_not_called()

    def test_validate_content(self):
        # Test valid content
        valid_content = "# Title\nSome content that is long enough."
        self.assertTrue(self.content_manager.validate_content(valid_content))

        # Test content too short
        short_content = "# Title\nShort."
        self.assertFalse(self.content_manager.validate_content(short_content))

        # Test content missing main heading
        no_heading_content = "Some content."
        self.assertFalse(self.content_manager.validate_content(no_heading_content))

    def test_sanitize_content(self):
        html_content = "<h1>Title</h1><script>alert('xss')</script><iframe src='evil.com'></iframe><p>Content</p>"
        sanitized_content = self.content_manager.sanitize_content(html_content)
        self.assertNotIn("<script", sanitized_content)
        self.assertNotIn("<iframe", sanitized_content)
        self.assertIn("<h1>Title</h1><p>Content</p>", sanitized_content)

        whitespace_content = "Line1\n\n\nLine2\n\n\n\nLine3"
        sanitized_content = self.content_manager.sanitize_content(whitespace_content)
        self.assertEqual(sanitized_content, "Line1\n\nLine2\n\nLine3")

    @patch('content_manager.ContentManager.read_markdown_file')
    @patch('content_manager.ContentManager.parse_frontmatter')
    @patch('content_manager.ContentManager.validate_frontmatter')
    @patch('content_manager.ContentManager.sanitize_content')
    @patch('content_manager.ContentManager.process_images')
    @patch('content_manager.ContentManager.validate_content')
    def test_process_markdown(self, mock_validate_content, mock_process_images, mock_sanitize_content, mock_validate_frontmatter, mock_parse_frontmatter, mock_read_markdown_file):
        mock_read_markdown_file.return_value = self.valid_content
        mock_parse_frontmatter.return_value = ({'title': 'Test'}, "content")
        mock_validate_frontmatter.return_value = {'title': 'Test'}
        mock_sanitize_content.return_value = "sanitized content"
        mock_process_images.return_value = "processed content"
        mock_validate_content.return_value = True

        frontmatter, content = self.content_manager.process_markdown(self.temp_file_path)

        mock_read_markdown_file.assert_called_once_with(self.temp_file_path)
        mock_parse_frontmatter.assert_called_once_with(self.valid_content)
        mock_validate_frontmatter.assert_called_once_with({'title': 'Test'})
        mock_sanitize_content.assert_called_once_with("content")
        mock_process_images.assert_called_once_with("sanitized content", upload_images=True)
        mock_validate_content.assert_called_once_with("processed content")

        self.assertEqual(frontmatter, {'title': 'Test'})
        self.assertEqual(content, "processed content")

        # Test with upload_images=False
        mock_process_images.reset_mock()
        self.content_manager.process_markdown(self.temp_file_path, upload_images=False)
        mock_process_images.assert_called_once_with("sanitized content", upload_images=False)


class TestMonitoringManager(unittest.TestCase):
    @patch('monitoring.start_http_server')
    @patch('monitoring.threading.Thread')
    def test_init(self, mock_thread, mock_start_http_server):
        manager = MonitoringManager(metrics_port=9091)
        self.assertEqual(manager.metrics_port, 9091)
        mock_start_http_server.assert_called_once_with(9091)
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()

    @patch('monitoring.start_http_server')
    def test_start_metrics_server_success(self, mock_start_http_server):
        manager = MonitoringManager(metrics_port=9092)
        mock_start_http_server.assert_called_once_with(9092)

    @patch('monitoring.start_http_server')
    def test_start_metrics_server_failure(self, mock_start_http_server):
        mock_start_http_server.side_effect = Exception("Server error")
        with patch('monitoring.logger.error') as mock_logger_error:
            manager = MonitoringManager(metrics_port=9093)
            mock_logger_error.assert_called_once_with("Failed to start metrics server: Server error")

    @patch('monitoring.psutil.Process')
    def test_update_system_metrics(self, mock_process):
        mock_process_instance = MagicMock()
        mock_process.return_value = mock_process_instance
        mock_process_instance.memory_info.return_value.rss = 1000
        with patch('monitoring.psutil.cpu_percent') as mock_cpu_percent:
            mock_cpu_percent.return_value = 50.0
            manager = MonitoringManager()
            manager.update_system_metrics()
            self.assertEqual(manager.memory_usage._value.get(), 1000)
            self.assertEqual(manager.cpu_usage._value.get(), 50.0)
            mock_process.assert_called_once()
            mock_cpu_percent.assert_called_once()

    def test_record_request(self):
        manager = MonitoringManager()
        manager.record_request("test_endpoint")
        self.assertEqual(manager.request_count.collect()[0].samples[0].value, 1.0)
        manager.record_request("another_endpoint")
        self.assertEqual(manager.request_count.collect()[0].samples[0].value, 2.0) # Counter is global

    def test_record_error(self):
        manager = MonitoringManager()
        manager.record_error("test_endpoint", "TestError")
        self.assertEqual(manager.error_count.collect()[0].samples[0].value, 1.0)
        manager.record_error("test_endpoint", "AnotherError")
        self.assertEqual(manager.error_count.collect()[0].samples[0].value, 2.0) # Counter is global

    def test_record_publish_latency(self):
        manager = MonitoringManager()
        manager.record_publish_latency("medium", 0.5)
        self.assertEqual(manager.publish_latency.collect()[0].samples[0].labelvalues, ('medium',))
        self.assertEqual(manager.publish_latency.collect()[0].samples[-2].value, 1.0) # Check sum

    @patch('monitoring.psutil.Process')
    @patch('monitoring.psutil.cpu_percent')
    @patch('monitoring.time.time')
    @patch('monitoring.datetime')
    def test_get_health_status_healthy(self, mock_datetime, mock_time, mock_cpu_percent, mock_process):
        mock_time.return_value = 100.0
        mock_cpu_percent.return_value = 25.0
        mock_process_instance = MagicMock()
        mock_process.return_value = mock_process_instance
        mock_process_instance.memory_info.return_value.rss = 2000
        mock_datetime.utcnow.return_value.isoformat.return_value = "timestamp"

        manager = MonitoringManager()
        manager.start_time = 50.0 # Set a start time for uptime calculation

        status = manager.get_health_status()

        self.assertEqual(status['status'], 'healthy')
        self.assertEqual(status['uptime'], 50.0)
        self.assertEqual(status['memory_usage'], 2000)
        self.assertEqual(status['cpu_usage'], 25.0)
        self.assertEqual(status['timestamp'], "timestamp")

    @patch('monitoring.psutil.Process')
    def test_get_health_status_unhealthy(self, mock_process):
        mock_process.side_effect = Exception("Health check error")
        with patch('monitoring.logger.error') as mock_logger_error:
            manager = MonitoringManager()
            status = manager.get_health_status()
            self.assertEqual(status['status'], 'unhealthy')
            self.assertIn('error', status)
            mock_logger_error.assert_called_once_with("Error getting health status: Health check error")

    @patch('builtins.open', new_callable=MagicMock)
    @patch('monitoring.json.dump')
    def test_save_metrics(self, mock_json_dump, mock_open):
        manager = MonitoringManager()
        manager.request_count.inc()
        manager.error_count.inc()
        manager.memory_usage.set(1000)
        manager.cpu_usage.set(50.0)

        with patch('monitoring.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value.isoformat.return_value = "timestamp"
            manager.save_metrics("metrics.json")

            mock_open.assert_called_once_with("metrics.json", 'w')
            mock_json_dump.assert_called_once()
            # Check if dump was called with expected data (approximately)
            args, kwargs = mock_json_dump.call_args
            metrics_data = args[0]
            self.assertIn('request_count', metrics_data)
            self.assertIn('error_count', metrics_data)
            self.assertIn('memory_usage', metrics_data)
            self.assertIn('cpu_usage', metrics_data)
            self.assertEqual(metrics_data['timestamp'], "timestamp")

    @patch('monitoring.threading.Thread')
    def test_start_metrics_collection(self, mock_thread):
        manager = MonitoringManager()
        manager.start_metrics_collection(interval=10)
        mock_thread.assert_called_once_with(target=manager.update_system_metrics, daemon=True) # Target should be update_system_metrics
        mock_thread.return_value.start.assert_called_once()


class TestSecurityManager(unittest.TestCase):
    def setUp(self):
        self.secret_key = "test_secret_key"
        self.security_manager = SecurityManager(secret_key=self.secret_key, redis_url=None) # Initialize without Redis for most tests

    def test_generate_token(self):
        user_id = "test_user"
        token = self.security_manager.generate_token(user_id, expires_in=1) # Short expiry for testing
        self.assertIsInstance(token, str)

        # Verify the token
        decoded_payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
        self.assertEqual(decoded_payload['user_id'], user_id)
        self.assertIn('exp', decoded_payload)

    def test_verify_token_valid(self):
        user_id = "test_user"
        token = self.security_manager.generate_token(user_id)
        payload = self.security_manager.verify_token(token)
        self.assertEqual(payload['user_id'], user_id)

    def test_verify_token_expired(self):
        user_id = "test_user"
        token = self.security_manager.generate_token(user_id, expires_in=-1) # Expired token
        with self.assertRaises(HTTPException) as cm:
            self.security_manager.verify_token(token)
        self.assertEqual(cm.exception.status_code, 401)
        self.assertEqual(cm.exception.detail, "Token has expired")

    def test_verify_token_invalid(self):
        invalid_token = "invalid.token.string"
        with self.assertRaises(HTTPException) as cm:
            self.security_manager.verify_token(invalid_token)
        self.assertEqual(cm.exception.status_code, 401)
        self.assertEqual(cm.exception.detail, "Invalid token")

    def test_verify_token_blacklisted(self):
        user_id = "test_user"
        token = self.security_manager.generate_token(user_id)
        self.security_manager.revoke_token(token)
        with self.assertRaises(HTTPException) as cm:
            self.security_manager.verify_token(token)
        self.assertEqual(cm.exception.status_code, 401)
        self.assertEqual(cm.exception.detail, "Token has been revoked")

    def test_revoke_token(self):
        user_id = "test_user"
        token = self.security_manager.generate_token(user_id)
        self.assertNotIn(token, self.security_manager.token_blacklist)
        self.security_manager.revoke_token(token)
        self.assertIn(token, self.security_manager.token_blacklist)

    @patch('security.redis.from_url')
    def test_rate_limit_no_redis(self, mock_redis_from_url):
        mock_redis_from_url.return_value = None
        security_manager_no_redis = SecurityManager(secret_key="test", redis_url="redis://localhost")
        self.assertFalse(security_manager_no_redis.rate_limit("key", 5, 60))
        mock_redis_from_url.assert_called_once()

    @patch('security.redis.from_url')
    def test_rate_limit_within_limit(self, mock_redis_from_url):
        mock_redis_client = MagicMock()
        mock_redis_from_url.return_value = mock_redis_client
        mock_redis_client.zcard.return_value = 3 # Current count is 3
        
        security_manager_with_redis = SecurityManager(secret_key="test", redis_url="redis://localhost")
        self.assertFalse(security_manager_with_redis.rate_limit("key", 5, 60)) # Limit is 5

        mock_redis_client.zremrangebyscore.assert_called_once()
        mock_redis_client.zcard.assert_called_once()
        mock_redis_client.zadd.assert_called_once()
        mock_redis_client.expire.assert_called_once()

    @patch('security.redis.from_url')
    def test_rate_limit_exceeds_limit(self, mock_redis_from_url):
        mock_redis_client = MagicMock()
        mock_redis_from_url.return_value = mock_redis_client
        mock_redis_client.zcard.return_value = 5 # Current count is 5
        
        security_manager_with_redis = SecurityManager(secret_key="test", redis_url="redis://localhost")
        self.assertTrue(security_manager_with_redis.rate_limit("key", 5, 60)) # Limit is 5

        mock_redis_client.zremrangebyscore.assert_called_once()
        mock_redis_client.zcard.assert_called_once()
        mock_redis_client.zadd.assert_not_called() # Should not add if limit is exceeded
        mock_redis_client.expire.assert_not_called() # Should not expire if limit is exceeded


class TestMCPPublishServer(unittest.TestCase):
    # Keep existing tests for make_api_request for now
    @patch('requests.post')
    def test_make_api_request(self, mock_post):
        # Test successful request
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        response = make_api_request("http://test.com", {}, {})
        self.assertEqual(response.status_code, 200)

        # Test rate limit handling
        mock_response.status_code = 429
        mock_post.return_value = mock_response
        with self.assertRaises(PublishingError):
            make_api_request("http://test.com", {}, {})

        # Test request failure
        mock_post.side_effect = requests.exceptions.RequestException("Test error")
        with self.assertRaises(PublishingError):
            make_api_request("http://test.com", {}, {})


if __name__ == '__main__':
    unittest.main()