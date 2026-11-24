import tempfile
import unittest
import zipfile
from pathlib import Path
from tools.analyze_play_stats import analyze_stats
from tools.verify_play_package import verify_package, REQUIRED

class PlayValidationTests(unittest.TestCase):
    def test_no_omission_of_zero_after_warmup(self):
        r=analyze_stats("0\t0\n60\t5\n60\t5\n60\t5\n0\t0\n30\t2\n60\t5\n")
        self.assertEqual(r["mean_frames_per_interval"],37.5)
        self.assertEqual(r["zero_intervals"],1)
        self.assertEqual(r["below_90_percent_target"],2)

    def test_invalid_stats(self):
        for s in ("", "a\t2", "-1\t2", "60", "60\t4\t1"):
            with self.subTest(s=s), self.assertRaises(ValueError):
                analyze_stats(s,0)

    def test_zip_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"package.zip"
            entries={name:b"content" for name in REQUIRED}
            def write():
                with zipfile.ZipFile(p,"w") as z:
                    for name,data in entries.items():
                        z.writestr(name,data)
            write()
            self.assertEqual(verify_package(p)["status"],"structural_checks_passed")
            for bad in ("engine/play/opengl32.dll","engine/pcsx2.exe","game.iso","../bad.dll"):
                with self.subTest(bad=bad):
                    entries[bad]=b"bad"
                    write()
                    with self.assertRaises(ValueError):
                        verify_package(p)
                    del entries[bad]
            entries["engine/play-mesa/play.exe"]=b"different"
            write()
            with self.assertRaisesRegex(ValueError,"differ"):
                verify_package(p)

if __name__=="__main__":
    unittest.main()
