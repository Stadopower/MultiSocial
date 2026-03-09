"""
MultiSocial Test Suite
Run with: pytest test_multisocial.py -v
"""
import pytest
import os
import sys
from unittest.mock import MagicMock, patch, mock_open
from PIL import Image
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def small_jpg(tmp_path):
    """Creates a small 1920x1080 (16:9) test JPEG under 1MB."""
    path = tmp_path / "test.jpg"
    img = Image.new("RGB", (1920, 1080), color=(100, 149, 237))
    img.save(path, "JPEG")
    return str(path)

@pytest.fixture
def small_png(tmp_path):
    """Creates a small PNG test image."""
    path = tmp_path / "test.png"
    img = Image.new("RGB", (1920, 1080), color=(255, 100, 50))
    img.save(path, "PNG")
    return str(path)

@pytest.fixture
def large_image(tmp_path):
    """Creates a large image that exceeds size limits."""
    path = tmp_path / "large.jpg"
    # 4000x3000 uncompressed-ish to push file size up
    img = Image.new("RGB", (4000, 3000), color=(200, 200, 200))
    # Save with minimal compression to make it large
    img.save(path, "JPEG", quality=100, subsampling=0)
    return str(path)

@pytest.fixture
def bluesky_creds():
    return {"handle": "test.bsky.social", "app_password": "test-app-password"}

@pytest.fixture
def twitter_creds():
    return {
        "api_key": "test_api_key",
        "api_secret": "test_api_secret",
        "access_token": "test_access_token",
        "access_token_secret": "test_access_token_secret",
    }

@pytest.fixture
def instagram_creds():
    return {"username": "testuser", "password": "testpassword"}

@pytest.fixture
def pinterest_creds():
    return {"access_token": "test_token", "board_id": "123456789"}


# ─────────────────────────────────────────────────────────────────────────────
# utils.py Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestCheckImageSize:
    def test_small_image_under_limit(self, small_jpg):
        from platforms.utils import check_image_size
        assert check_image_size(small_jpg, 5) == False

    def test_image_over_limit(self, small_jpg):
        from platforms.utils import check_image_size
        # Set limit to 0 so any file exceeds it
        assert check_image_size(small_jpg, 0) == True

    def test_exact_limit_boundary(self, small_jpg):
        from platforms.utils import check_image_size
        size_mb = os.path.getsize(small_jpg) / (1024 * 1024)
        # Just below limit should return False
        assert check_image_size(small_jpg, size_mb + 0.01) == False
        # Just above limit should return True
        assert check_image_size(small_jpg, size_mb - 0.01) == True


class TestCropToVertical:
    def test_instagram_crop_produces_file(self, small_jpg, tmp_path):
        from platforms.utils import crop_to_vertical
        result = crop_to_vertical(small_jpg, 'instagram')
        assert os.path.exists(result)

    def test_instagram_crop_correct_ratio(self, small_jpg):
        from platforms.utils import crop_to_vertical
        result = crop_to_vertical(small_jpg, 'instagram')
        img = Image.open(result)
        w, h = img.size
        ratio = w / h
        assert abs(ratio - 0.8) < 0.01  # 4:5 = 0.8

    def test_pinterest_crop_produces_file(self, small_jpg):
        from platforms.utils import crop_to_vertical
        result = crop_to_vertical(small_jpg, 'pinterest')
        assert os.path.exists(result)

    def test_pinterest_crop_correct_ratio(self, small_jpg):
        from platforms.utils import crop_to_vertical
        result = crop_to_vertical(small_jpg, 'pinterest')
        img = Image.open(result)
        w, h = img.size
        ratio = w / h
        assert abs(ratio - (2/3)) < 0.01  # 2:3

    def test_instagram_suffix_in_filename(self, small_jpg):
        from platforms.utils import crop_to_vertical
        result = crop_to_vertical(small_jpg, 'instagram')
        assert '_insta' in os.path.basename(result)

    def test_pinterest_suffix_in_filename(self, small_jpg):
        from platforms.utils import crop_to_vertical
        result = crop_to_vertical(small_jpg, 'pinterest')
        assert '_pint' in os.path.basename(result)

    def test_instagram_no_double_crop(self, small_jpg):
        """Already cropped image should not be cropped again."""
        from platforms.utils import crop_to_vertical
        first = crop_to_vertical(small_jpg, 'instagram')
        second = crop_to_vertical(first, 'instagram')
        assert '_insta_insta' not in os.path.basename(second)

    def test_pinterest_no_double_crop(self, small_jpg):
        from platforms.utils import crop_to_vertical
        first = crop_to_vertical(small_jpg, 'pinterest')
        second = crop_to_vertical(first, 'pinterest')
        assert '_pint_pint' not in os.path.basename(second)

    def test_png_converted_to_jpg(self, small_png):
        from platforms.utils import crop_to_vertical
        result = crop_to_vertical(small_png, 'instagram')
        assert result.endswith('.jpg')

    def test_output_is_valid_image(self, small_jpg):
        from platforms.utils import crop_to_vertical
        result = crop_to_vertical(small_jpg, 'instagram')
        img = Image.open(result)
        assert img is not None


# ─────────────────────────────────────────────────────────────────────────────
# bluesky.py Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestBluesky:
    def test_missing_handle(self, bluesky_creds):
        from platforms.bluesky import post
        creds = {**bluesky_creds, "handle": None}
        result = post("Hello", creds)
        assert "Missing Handle" in result

    def test_missing_password(self, bluesky_creds):
        from platforms.bluesky import post
        creds = {**bluesky_creds, "app_password": None}
        result = post("Hello", creds)
        assert "Missing Password" in result

    def test_empty_handle(self, bluesky_creds):
        from platforms.bluesky import post
        creds = {**bluesky_creds, "handle": ""}
        result = post("Hello", creds)
        assert "Missing" in result

    def test_image_over_size_limit(self, bluesky_creds, small_jpg):
        from platforms.bluesky import post
        with patch('platforms.utils.check_image_size', return_value=True):
            result = post("Hello", bluesky_creds, [small_jpg])
        assert "ERROR" in result or "exceeds" in result

    @patch('platforms.bluesky.Client')
    def test_text_only_post(self, mock_client_class, bluesky_creds):
        from platforms.bluesky import post
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        result = post("Hello Bluesky!", bluesky_creds, None)
        mock_client.login.assert_called_once_with(bluesky_creds["handle"], bluesky_creds["app_password"])
        mock_client.send_post.assert_called_once_with(text="Hello Bluesky!")
        assert "Posted" in result

    @patch('platforms.bluesky.Client')
    def test_single_image_post(self, mock_client_class, bluesky_creds, small_jpg):
        from platforms.bluesky import post
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        result = post("Hello!", bluesky_creds, [small_jpg])
        mock_client.send_image.assert_called_once()
        assert "Posted" in result

    @patch('platforms.bluesky.Client')
    def test_multiple_images_post(self, mock_client_class, bluesky_creds, small_jpg):
        from platforms.bluesky import post
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        result = post("Hello!", bluesky_creds, [small_jpg, small_jpg])
        mock_client.send_images.assert_called_once()
        assert "Posted" in result

    @patch('platforms.bluesky.Client')
    def test_max_4_images_enforced(self, mock_client_class, bluesky_creds, small_jpg):
        from platforms.bluesky import post
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        # Pass 6 images, only 4 should be uploaded
        images = [small_jpg] * 6
        post("Hello!", bluesky_creds, images)
        call_kwargs = mock_client.send_images.call_args
        assert len(call_kwargs[1]['images']) <= 4

    @patch('platforms.bluesky.Client')
    def test_login_error_returns_error_string(self, mock_client_class, bluesky_creds):
        from platforms.bluesky import post
        mock_client = MagicMock()
        mock_client.login.side_effect = Exception("Invalid credentials")
        mock_client_class.return_value = mock_client
        result = post("Hello!", bluesky_creds, None)
        assert "ERROR" in result


# ─────────────────────────────────────────────────────────────────────────────
# X.py (Twitter) Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestTwitter:
    def test_missing_api_key(self, twitter_creds):
        from platforms.X import post
        creds = {**twitter_creds, "api_key": ""}
        result = post("Hello", creds)
        assert "missing" in result.lower()

    def test_missing_api_secret(self, twitter_creds):
        from platforms.X import post
        creds = {**twitter_creds, "api_secret": ""}
        result = post("Hello", creds)
        assert "missing" in result.lower()

    def test_missing_access_token(self, twitter_creds):
        from platforms.X import post
        creds = {**twitter_creds, "access_token": ""}
        result = post("Hello", creds)
        assert "Missing" in result

    def test_missing_access_token_secret(self, twitter_creds):
        from platforms.X import post
        creds = {**twitter_creds, "access_token_secret": ""}
        result = post("Hello", creds)
        assert "Missing" in result

    @patch('platforms.X.Client')
    def test_text_only_post(self, mock_client_class, twitter_creds):
        from platforms.X import post
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        result = post("Hello Twitter!", twitter_creds, None)
        mock_client.create_tweet.assert_called_once_with(text="Hello Twitter!")
        assert "✅" in result

    @patch('platforms.X.API')
    @patch('platforms.X.OAuth1UserHandler')
    @patch('platforms.X.Client')
    def test_single_image_post(self, mock_client_class, mock_auth, mock_api_class, twitter_creds, small_jpg):
        from platforms.X import post
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_v1 = MagicMock()
        mock_api_class.return_value = mock_v1
        mock_v1.media_upload.return_value = MagicMock(media_id=12345)
        result = post("Hello!", twitter_creds, [small_jpg])
        mock_client.create_tweet.assert_called_once_with(text="Hello!", media_ids=[12345])
        assert "✅" in result

    @patch('platforms.X.API')
    @patch('platforms.X.OAuth1UserHandler')
    @patch('platforms.X.Client')
    def test_max_4_images_enforced(self, mock_client_class, mock_auth, mock_api_class, twitter_creds, small_jpg):
        from platforms.X import post
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_v1 = MagicMock()
        mock_api_class.return_value = mock_v1
        mock_v1.media_upload.return_value = MagicMock(media_id=1)
        images = [small_jpg] * 6
        post("Hello!", twitter_creds, images)
        # Should only upload 4
        assert mock_v1.media_upload.call_count <= 4

    def test_image_over_size_limit(self, twitter_creds, small_jpg):
        from platforms.X import post
        with patch('platforms.X.check_image_size', return_value=True):
            result = post("Hello!", twitter_creds, [small_jpg])
        assert "ERROR" in result or "exceeds" in result

    @patch('platforms.X.Client')
    def test_api_error_returns_error_string(self, mock_client_class, twitter_creds):
        from platforms.X import post
        mock_client = MagicMock()
        mock_client.create_tweet.side_effect = Exception("API Error")
        mock_client_class.return_value = mock_client
        result = post("Hello!", twitter_creds, None)
        assert "ERROR" in result


# ─────────────────────────────────────────────────────────────────────────────
# instagram.py Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestInstagram:
    def test_missing_username(self, instagram_creds):
        from platforms.instagram import post
        creds = {**instagram_creds, "username": ""}
        result = post("Hello", creds, ["img.jpg"])
        assert "Missing" in result

    def test_missing_password(self, instagram_creds):
        from platforms.instagram import post
        creds = {**instagram_creds, "password": ""}
        result = post("Hello", creds, ["img.jpg"])
        assert "Missing" in result

    def test_no_image_returns_error(self, instagram_creds):
        from platforms.instagram import post
        result = post("Hello", instagram_creds, [])
        assert "required" in result.lower() or "Image" in result

    def test_none_image_returns_error(self, instagram_creds):
        from platforms.instagram import post
        result = post("Hello", instagram_creds, None)
        assert "required" in result.lower() or "Image" in result

    def test_image_over_size_limit(self, instagram_creds, small_jpg):
        from platforms.instagram import post
        with patch('platforms.instagram.check_image_size', return_value=True):
            result = post("Hello", instagram_creds, [small_jpg])
        assert "ERROR" in result or "exceeds" in result

    @patch('platforms.instagram.instagrapi.Client')
    @patch('platforms.instagram.crop_to_vertical')
    def test_single_image_uses_photo_upload(self, mock_crop, mock_client_class, instagram_creds, small_jpg):
        from platforms.instagram import post
        mock_crop.return_value = small_jpg
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        result = post("Hello!", instagram_creds, [small_jpg])
        mock_client.photo_upload.assert_called_once()
        assert "Posted" in result

    @patch('platforms.instagram.instagrapi.Client')
    @patch('platforms.instagram.crop_to_vertical')
    def test_multiple_images_uses_album_upload(self, mock_crop, mock_client_class, instagram_creds, small_jpg):
        from platforms.instagram import post
        mock_crop.return_value = small_jpg
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        result = post("Hello!", instagram_creds, [small_jpg, small_jpg])
        mock_client.album_upload.assert_called_once()
        assert "Posted" in result

    @patch('platforms.instagram.instagrapi.Client')
    @patch('platforms.instagram.crop_to_vertical')
    def test_max_10_images_enforced(self, mock_crop, mock_client_class, instagram_creds, small_jpg):
        from platforms.instagram import post
        mock_crop.return_value = small_jpg
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        images = [small_jpg] * 15
        post("Hello!", instagram_creds, images)
        call_args = mock_client.album_upload.call_args
        assert len(call_args[1]['paths']) <= 10

    @patch('platforms.instagram.instagrapi.Client')
    @patch('platforms.instagram.crop_to_vertical')
    def test_login_error_returns_error_string(self, mock_crop, mock_client_class, instagram_creds, small_jpg):
        from platforms.instagram import post
        mock_crop.return_value = small_jpg
        mock_client = MagicMock()
        mock_client.login.side_effect = Exception("Login failed")
        mock_client_class.return_value = mock_client
        result = post("Hello!", instagram_creds, [small_jpg])
        assert "ERROR" in result


# ─────────────────────────────────────────────────────────────────────────────
# pinterest.py Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestPinterest:
    def test_missing_access_token(self, pinterest_creds):
        from platforms.pinterest import post
        creds = {**pinterest_creds, "access_token": ""}
        result = post("Hello", creds, image_path="img.jpg")
        assert "Token" in result or "token" in result

    def test_missing_board_id(self, pinterest_creds):
        from platforms.pinterest import post
        creds = {**pinterest_creds, "board_id": ""}
        result = post("Hello", creds, image_path="img.jpg")
        assert "board" in result.lower()

    def test_no_image_returns_error(self, pinterest_creds):
        from platforms.pinterest import post
        result = post("Hello", pinterest_creds, image_path=None)
        assert "required" in result.lower() or "Image" in result

    def test_title_defaults_to_text(self, pinterest_creds, small_jpg):
        from platforms.pinterest import post
        with patch('platforms.pinterest.requests.post') as mock_post, \
             patch('platforms.pinterest.crop_to_vertical', return_value=small_jpg):
            mock_post.return_value = MagicMock(status_code=201)
            post("My text", pinterest_creds, title=None, image_path=small_jpg)
            call_json = mock_post.call_args[1]['json']
            assert call_json['title'] == "My text"

    def test_custom_title_used(self, pinterest_creds, small_jpg):
        from platforms.pinterest import post
        with patch('platforms.pinterest.requests.post') as mock_post, \
             patch('platforms.pinterest.crop_to_vertical', return_value=small_jpg):
            mock_post.return_value = MagicMock(status_code=201)
            post("My text", pinterest_creds, title="Custom Title", image_path=small_jpg)
            call_json = mock_post.call_args[1]['json']
            assert call_json['title'] == "Custom Title"

    def test_successful_post_returns_success(self, pinterest_creds, small_jpg):
        from platforms.pinterest import post
        with patch('platforms.pinterest.requests.post') as mock_post, \
             patch('platforms.pinterest.crop_to_vertical', return_value=small_jpg):
            mock_post.return_value = MagicMock(status_code=201)
            result = post("Hello!", pinterest_creds, image_path=small_jpg)
            assert "✅" in result

    def test_api_failure_returns_error(self, pinterest_creds, small_jpg):
        from platforms.pinterest import post
        with patch('platforms.pinterest.requests.post') as mock_post, \
             patch('platforms.pinterest.crop_to_vertical', return_value=small_jpg):
            mock_post.return_value = MagicMock(status_code=403, json=lambda: {"message": "Forbidden"})
            result = post("Hello!", pinterest_creds, image_path=small_jpg)
            assert "403" in result or "❌" in result

    def test_bearer_token_in_header(self, pinterest_creds, small_jpg):
        from platforms.pinterest import post
        with patch('platforms.pinterest.requests.post') as mock_post, \
             patch('platforms.pinterest.crop_to_vertical', return_value=small_jpg):
            mock_post.return_value = MagicMock(status_code=201)
            post("Hello!", pinterest_creds, image_path=small_jpg)
            headers = mock_post.call_args[1]['headers']
            assert headers['Authorization'] == f"Bearer {pinterest_creds['access_token']}"

    def test_image_is_cropped_before_upload(self, pinterest_creds, small_jpg):
        from platforms.pinterest import post
        with patch('platforms.pinterest.requests.post') as mock_post, \
             patch('platforms.pinterest.crop_to_vertical') as mock_crop:
            mock_crop.return_value = small_jpg
            mock_post.return_value = MagicMock(status_code=201)
            post("Hello!", pinterest_creds, image_path=small_jpg)
            mock_crop.assert_called_once_with(small_jpg, 'pinterest')
