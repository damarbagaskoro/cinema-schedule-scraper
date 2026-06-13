# ====================================
# SCRAPER CONFIGURATION
# ====================================

# Paste the city of interest's URL here. Default city is Bandung.
BASE_URL = "https://jadwalnonton.com/bioskop/di-bandung/"

# Paste your browser HEADERS here.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0"
}

# List theater URLs you want to skip during scraping.
# Set EXCLUDED_THEATERS = [] if no exclusions are needed.
EXCLUDED_THEATERS = [
    "https://jadwalnonton.com/bioskop/di-bandung/dakota-cinema-rancaekek-bandung.html",
    "https://jadwalnonton.com/bioskop/di-bandung/jatos-bandung.html",
    "https://jadwalnonton.com/bioskop/di-bandung/thee-matic-mall-xxi-bandung.html",
    "https://jadwalnonton.com/bioskop/di-bandung/transmart-buah-batu-xxi-bandung.html",
]

# Data quality parameters.
MIN_ACTIVE_RECORDS = 5  # minimum expected active screening records per run, try 20% of the typical records
MAX_NULL_RATE = 0.20  # max allowed null rate for critical fields in active records
MAX_FAILURE_RATE = (
    0.50  # failure rate threshold that triggers a high-failure-rate warning
)

# HTTP and crawl configurations.
REQUEST_TIMEOUT = 10  # seconds before a request gives up
MAX_RETRIES = 3  # how many times to retry a failed request
RETRY_DELAY = 5  # base seconds to wait between retries
CRAWL_DELAY_MIN = 1  # minimum seconds to wait between requests
CRAWL_DELAY_MAX = 3  # maximum seconds to wait between requests
