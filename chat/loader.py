# chat/loader.py
import pathlib
import yaml
from .models import Product, Taxonomy

_DEFAULT_PRODUCTS_DIR = pathlib.Path(__file__).parent.parent / "products"
_DEFAULT_JOBS_DIR = pathlib.Path(__file__).parent.parent / "jobs"


def load_product(slug: str, products_dir: pathlib.Path = _DEFAULT_PRODUCTS_DIR) -> Product:
    path = products_dir / f"{slug}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"No product file found for slug '{slug}' at {path}")
    with open(path) as f:
        data = yaml.safe_load(f)
    return Product(**data)


def load_all_products(products_dir: pathlib.Path = _DEFAULT_PRODUCTS_DIR) -> list[Product]:
    return [
        load_product(p.stem, products_dir)
        for p in sorted(products_dir.glob("*.yaml"))
    ]


def load_taxonomy(jobs_dir: pathlib.Path = _DEFAULT_JOBS_DIR) -> Taxonomy:
    path = jobs_dir / "taxonomy.yaml"
    with open(path) as f:
        data = yaml.safe_load(f)
    return Taxonomy(**data)
