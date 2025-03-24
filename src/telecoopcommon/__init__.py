from os.path import dirname, basename, isfile, join
import glob

names = glob.glob(join(dirname(__file__), "*.py"))
modules = [
    basename(f)[:-3] for f in names if isfile(f) and not f.endswith("__init__.py")
]
#__all__ = modules
