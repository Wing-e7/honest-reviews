import click
from typing import Optional


@click.command()
@click.option("--product", required=True, help="Product slug (e.g. warmly)")
@click.option(
    "--source", required=True,
    type=click.Choice(["vendor", "g2", "changelog", "community"]),
    help="Source type to scrape",
)
@click.option("--url", default=None, help="Override URL (uses product.yaml url by default)")
@click.option("--check-stale", is_flag=True, default=False,
              help="List stale claims instead of scraping")
def scrape(product: str, source: str, url: Optional[str], check_stale: bool) -> None:
    """Scrape a product source and generate a draft YAML patch."""
    if check_stale:
        from tagger.staleness import check_stale as _check
        ctx = click.get_current_context()
        ctx.invoke(_check)
        return

    from chat.loader import load_product
    from chat.store import ChromaStore
    p = load_product(product)
    target_url = url or p.url
    store = ChromaStore()

    if source == "vendor":
        from scrapers.vendor_docs import scrape_vendor_docs
        scrape_vendor_docs(product, target_url, store=store)
    else:
        click.echo(
            f"Scraper '{source}' not yet implemented. "
            f"Contribute at github.com/your-org/honest-reviews"
        )
