# Describe this module's purpose.
"""HTTP client for NASA's Astronomy Picture of the Day (APOD) feed."""  

# Import HTTPX, the library used to send asynchronous web requests.
import httpx

# Import the model that validates one APOD record.
from app.models.apod import ApodRecord

# Keep the official APOD Basic endpoint URL in one reusable constant.
APOD_ENDPOINT = "https://science.nasa.gov/wp-json/wp/v2/apod-basic"


# Define a class to keep NASA APOD request logic together.
class NasaApodClient:
    """Fetch and validate records from NASA's APOD Basic endpoint."""  # Document this class.

    # Accept an HTTP client created and managed by the application.
    def __init__(self, http_client: httpx.AsyncClient) -> None:
        # Remember the shared client so methods in this class can use it.
        self._http_client = http_client  # Store the supplied HTTP client.

    # Define an async method because a network request must wait for NASA.
    async def get_latest(self) -> ApodRecord:
        """Fetch the newest APOD record and validate its fields."""  # Document this method.

        # Send a GET request and wait for NASA's HTTP response.
        response = await self._http_client.get(  # Await the asynchronous request.
            APOD_ENDPOINT,  # Use the NASA APOD Basic endpoint.
            params={"page": 1, "per_page": 1},  # Request one item from the first page.
        )  # Finish the request and assign its response above.

        # Convert non-success HTTP status codes into exceptions.
        response.raise_for_status()  # Stop here if NASA returned an HTTP error.

        # Decode the response body from JSON into Python data.
        payload = response.json()  # The endpoint returns a list of APOD records.

        # Check that the response is a non-empty list before indexing into it.
        if not isinstance(payload, list) or not payload:  # Reject the wrong shape or no records.
            # Explain why the response cannot be used as an APOD record.
            # Report invalid data.
            raise ValueError("NASA APOD returned an empty or unexpected response.")  
            
            
        # Select the first list item and validate its fields with Pydantic.
        return ApodRecord.model_validate(payload[0])  # Return one validated APOD record.
