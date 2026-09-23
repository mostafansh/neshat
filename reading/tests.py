import tempfile
from pathlib import Path

from django.contrib.staticfiles import finders
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image


class HomePageTests(TestCase):
    def test_home_page_uses_the_reading_room_style(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "css/reading-room.css")
        self.assertContains(response, 'class="site-header"')

    def test_unknown_page_says_so(self):
        with self.settings(DEBUG=False):
            response = self.client.get("/no-such-page/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "That page does not exist.", status_code=404)

    def test_style_and_brand_files_exist(self):
        self.assertIsNotNone(finders.find("css/reading-room.css"))
        self.assertIsNotNone(finders.find("img/brand.svg"))


class SecurityHeaderTests(TestCase):
    def test_pages_load_nothing_from_other_servers(self):
        response = self.client.get(reverse("home"))
        policy = response.headers["Content-Security-Policy"]
        self.assertIn("default-src 'self'", policy)
        self.assertIn("frame-ancestors 'none'", policy)
        self.assertIn("object-src 'none'", policy)

    def test_pages_cannot_be_framed_or_sniffed(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["Referrer-Policy"], "same-origin")


class DemoImageTests(TestCase):
    def setUp(self):
        self.media_dir = Path(tempfile.mkdtemp())
        self.override = override_settings(CASE_MEDIA_ROOT=self.media_dir)
        self.override.enable()

    def tearDown(self):
        self.override.disable()

    def test_demo_image_is_drawn_on_first_use_and_served_privately(self):
        response = self.client.get(reverse("demo_image"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "image/png")
        self.assertIn("private", response.headers["Cache-Control"])
        response.close()

        with Image.open(self.media_dir / "demo" / "phantom.png") as image:
            self.assertEqual(image.mode, "L")  # 8-bit greyscale: pixels only, no DICOM
            self.assertEqual(image.size, (1024, 1280))

    def test_case_images_are_not_public_static_files(self):
        self.client.get(reverse("demo_image")).close()
        self.assertIsNone(finders.find("demo/phantom.png"))
        self.assertEqual(self.client.get("/static/demo/phantom.png").status_code, 404)
