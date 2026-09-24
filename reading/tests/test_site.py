import os
import subprocess
import sys
import tempfile
from pathlib import Path

from django.conf import settings
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

    def test_unknown_page_gets_our_404_page(self):
        with self.settings(DEBUG=False):
            response = self.client.get("/no-such-page/")
            self.assertEqual(response.status_code, 404)
            self.assertTemplateUsed(response, "404.html")

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

        with Image.open(self.media_dir / "demo" / "phantom-v3.png") as image:
            self.assertEqual(image.mode, "L")  # 8-bit greyscale: pixels only, no DICOM
            self.assertEqual(image.size, (1024, 1280))

    def test_image_response_carries_no_file_name(self):
        response = self.client.get(reverse("demo_image"))
        self.assertNotIn("Content-Disposition", response.headers)

    def test_case_images_are_not_public_static_files(self):
        self.client.get(reverse("demo_image"))
        self.assertIsNone(finders.find("demo/phantom-v3.png"))
        self.assertEqual(self.client.get("/static/demo/phantom-v3.png").status_code, 404)


class VenueAdminGuardTests(TestCase):
    """At the venue, admin pages answer only the laptop itself (the Wi-Fi is plain HTTP)."""

    guarded = override_settings(
        MIDDLEWARE=[*settings.MIDDLEWARE, "reading.middleware.admin_only_from_this_computer"]
    )

    @guarded
    def test_admin_is_hidden_from_phones(self):
        response = self.client.get("/admin/", REMOTE_ADDR="192.168.8.20")
        self.assertEqual(response.status_code, 404)

    @guarded
    def test_admin_answers_the_laptop(self):
        response = self.client.get("/admin/", REMOTE_ADDR="127.0.0.1")
        self.assertEqual(response.status_code, 302)  # redirect to the admin sign-in page

    @guarded
    def test_other_pages_still_answer_phones(self):
        response = self.client.get(reverse("home"), REMOTE_ADDR="192.168.8.20")
        self.assertEqual(response.status_code, 200)


class ModeSettingsTests(TestCase):
    """Each mode must fail safe. Settings are read once per process, so check in a new one."""

    def load_settings(self, **env):
        code = "import config.settings as s; print(s.ALLOWED_HOSTS, s.DEBUG)"
        with tempfile.TemporaryDirectory() as data_dir:
            return subprocess.run(
                [sys.executable, "-c", code],
                cwd=settings.BASE_DIR,
                env={**os.environ, "NESHAT_DATA_DIR": data_dir, **env},
                capture_output=True,
                text=True,
            )

    def test_dev_mode_answers_only_this_computer(self):
        result = self.load_settings(NESHAT_MODE="dev")
        self.assertEqual(result.stdout.strip(), "[] True")

    def test_online_mode_refuses_to_start_without_host_names(self):
        result = self.load_settings(NESHAT_MODE="online", NESHAT_HOSTS=" ")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("NESHAT_HOSTS", result.stderr)

    def test_online_mode_strips_spaces_from_host_names(self):
        result = self.load_settings(NESHAT_MODE="online", NESHAT_HOSTS="a.ir, www.a.ir")
        self.assertEqual(result.stdout.strip(), "['a.ir', 'www.a.ir'] False")
