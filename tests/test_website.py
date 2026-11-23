"""Checks for the static site: navigation, SEO and no pre-approval advertising."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree as ET
import unittest

ROOT = Path(__file__).resolve().parents[1] / "site"
ORIGIN = "https://ps2-studio-windows.kiikoo1995.workers.dev"

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.lang = False
        self.title = False
        self.description = False
        self.h1 = 0
        self.hrefs = []
        self.scripts = []
        self.canonical = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html": self.lang = a.get("lang") == "es"
        if tag == "title": self.title = True
        if tag == "h1": self.h1 += 1
        if tag == "meta" and a.get("name") == "description" and a.get("content"): self.description = True
        if tag in ("a", "link") and a.get("href"): self.hrefs.append(a["href"])
        if tag == "link" and a.get("rel") == "canonical": self.canonical.append(a.get("href"))
        if tag == "script": self.scripts.append(a.get("src", "inline"))

class WebsiteTests(unittest.TestCase):
    def test_html_metadata_links_and_no_tracking(self):
        pages = list(ROOT.rglob("*.html"))
        self.assertGreaterEqual(len(pages), 11)
        for file in pages:
            with self.subTest(page=file.as_posix()):
                data = file.read_text(encoding="utf8")
                p = Parser(); p.feed(data)
                self.assertTrue(p.lang)
                self.assertTrue(p.title)
                self.assertTrue(p.description)
                self.assertEqual(p.h1, 1)
                self.assertFalse(p.scripts, "No ads/analytics until approval and consent")
                self.assertNotIn("adsbygoogle.js", data)
                for url in p.hrefs:
                    if not url.startswith("/") or url.startswith("//"): continue
                    dest = urlparse(url).path.lstrip("/")
                    path = ROOT / dest
                    if not path.suffix: path = path / "index.html"
                    self.assertTrue(path.is_file(), f"Broken link: {file} => {url}")
                if file.name == "index.html":
                    expected = ORIGIN + ("/" if file == ROOT/"index.html" else "/" + file.parent.relative_to(ROOT).as_posix() + "/")
                    self.assertEqual(p.canonical, [expected])

    def test_sitemap_matches_indexable_pages(self):
        sitemap = ET.parse(ROOT / "sitemap.xml").getroot()
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locs = [loc.text for loc in sitemap.findall(".//s:loc", ns)]
        expected = {ORIGIN + ("/" if f == ROOT/"index.html" else "/" + f.parent.relative_to(ROOT).as_posix() + "/") for f in ROOT.rglob("index.html")}
        self.assertEqual(set(locs), expected)
        self.assertEqual(len(locs), len(expected))
        self.assertIn("Sitemap: " + ORIGIN + "/sitemap.xml", (ROOT / "robots.txt").read_text(encoding="utf8"))

    def test_program_manual(self):
        manual = (ROOT / "guias/uso/index.html").read_text(encoding="utf8")
        for label in ("Seleccionar PCSX2", "Añadir carpeta", "Quitar carpeta", "Actualizar", "Pantalla completa", "Subcarpetas", "Iniciar juego"):
            self.assertIn(label, manual)
        self.assertIn('href="/guias/uso/"', (ROOT / "index.html").read_text(encoding="utf8"))

    def test_external_blog_navigation(self):
        blog_url = "https://ps2studio-guias.blogspot.com/"
        for file in ROOT.rglob("index.html"):
            self.assertIn(blog_url, file.read_text(encoding="utf8"), file)

    def test_download_and_legal_text(self):
        download = (ROOT/"descargar/index.html").read_text(encoding="utf8")
        self.assertIn("/releases/download/preview/PS2Studio-Windows.zip", download)
        self.assertIn("PS2Studio-Windows.zip.sha256", download)
        self.assertIn("Solo favoritos", (ROOT / "guias/uso/index.html").read_text(encoding="utf8"))
        self.assertIn("preliminar", download.lower())
        self.assertIn("consentimiento", (ROOT/"legal/privacidad/index.html").read_text(encoding="utf8"))
        self.assertTrue((ROOT/"_headers").exists())

if __name__ == "__main__": unittest.main()
