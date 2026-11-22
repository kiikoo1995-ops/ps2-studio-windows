"""Validación del sitio estático, enlaces y ausencia de anuncios sin consentimiento."""
import unittest
from pathlib import Path
from urllib.parse import urlparse
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1] / "site"
class Parser(HTMLParser):
    def __init__(self):
        super().__init__(); self.lang=False; self.title=False; self.desc=False; self.h1=0; self.links=[]; self.scripts=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="html": self.lang=a.get("lang")=="es"
        if tag=="title": self.title=True
        if tag=="h1": self.h1+=1
        if tag=="meta" and a.get("name")=="description" and a.get("content"): self.desc=True
        if tag in ("a","link") and a.get("href"): self.links.append(a["href"])
        if tag=="script": self.scripts.append(a.get("src","inline"))
class WebsiteTests(unittest.TestCase):
    def test_html_metadata_and_links(self):
        pages=list(ROOT.rglob("*.html"))
        self.assertGreaterEqual(len(pages),7)
        for file in pages:
            with self.subTest(page=str(file)):
                data=file.read_text(encoding="utf8"); p=Parser(); p.feed(data)
                self.assertTrue(p.lang);self.assertTrue(p.title);self.assertTrue(p.desc)
                self.assertEqual(p.h1,1)
                self.assertFalse(p.scripts)
                self.assertNotIn("adsbygoogle.js",data)
                for url in p.links:
                    if not url.startswith("/") or url.startswith("//"):continue
                    dest=urlparse(url).path.lstrip("/")
                    path=ROOT/dest
                    if not path.suffix:path=path/"index.html"
                    self.assertTrue(path.is_file(),f"Enlace roto {file} => {url}")
    def test_download_and_privacy(self):
        download=(ROOT/"descargar/index.html").read_text(encoding="utf8")
        self.assertIn("/releases/download/preview/PS2Studio-Windows.zip",download)
        self.assertIn("preliminar",download.lower())
        privacy=(ROOT/"legal/privacidad/index.html").read_text(encoding="utf8")
        self.assertIn("consentimiento",privacy)
        self.assertTrue((ROOT/"_headers").exists())
if __name__=="__main__":unittest.main()
