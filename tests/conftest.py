"""Keep automated tests isolated from local dotenv files and credentials."""

import os

os.environ["COSMOS_TEST_MODE"] = "true"
