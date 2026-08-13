import os, sys, unittest

base = os.path.dirname(os.path.abspath(__file__))
os.chdir(base)
sys.path.insert(0, os.path.join(base, "src"))
sys.path.insert(0, os.path.join(base, "test"))

loader = unittest.TestLoader()
suite = loader.discover(os.path.join(base, "test"), top_level_dir=base)
result = unittest.TextTestRunner(verbosity=1).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
