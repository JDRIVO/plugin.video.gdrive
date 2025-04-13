from .parse import PTN

__author__ = "Giorgio Momigliano"
__email__ = "gmomigliano@protonmail.com"
__version__ = "2.8.1"
__license__ = "MIT"


def parse(name, standardise=True, coherent_types=False):
	return PTN().parse(name, standardise, coherent_types)
