import io, os, sys, unittest

base = os.path.dirname(os.path.abspath(__file__))
os.chdir(base)
sys.path.insert(0, os.path.join(base, "src"))
sys.path.insert(0, os.path.join(base, "test"))

loader = unittest.TestLoader()
suite = loader.discover(os.path.join(base, "test"), top_level_dir=base)
buf = io.StringIO()
result = unittest.TextTestRunner(stream=buf, verbosity=1).run(suite)
resumen = (
    f"tests={result.testsRun} "
    f"failures={len(result.failures)} "
    f"errors={len(result.errors)} "
    f"ok={result.wasSuccessful()}\n"
)
with open(os.path.join(base, ".cache", "_resultado.txt"), "w", encoding="utf-8") as fh:
    fh.write(resumen)
    fh.write(buf.getvalue()[-2000:])
