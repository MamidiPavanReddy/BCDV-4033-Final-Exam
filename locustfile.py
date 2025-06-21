from locust import HttpUser, task, between
import json


class PetstoreUser(HttpUser):
    """
    Locust user class for testing Petstore API endpoints
    """
    
    # Wait time between requests (1-3 seconds)
    wait_time = between(1, 3)
    
    # Base host for the API
    host = "https://petstore.swagger.io/v2"
    
    def on_start(self):
        """
        Called when a user starts - can be used for setup
        """
        print(f"Starting user: {self}")
    
    @task(2)
    def get_pet_by_id(self):
        """
        Test GET /pet/{petId} endpoint
        Weight: 2 (will be called twice as often as other tasks)
        """
        pet_id = 1
        endpoint = f"/pet/{pet_id}"
        
        with self.client.get(
            endpoint,
            catch_response=True,
            name="GET /pet/{id}"
        ) as response:
            if response.status_code == 200:
                try:
                    pet_data = response.json()
                    # Validate response structure
                    if 'id' in pet_data and 'name' in pet_data:
                        response.success()
                        print(f"✓ Successfully retrieved pet: {pet_data.get('name', 'Unknown')}")
                    else:
                        response.failure("Invalid response structure")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 404:
                response.failure("Pet not found")
            else:
                response.failure(f"Unexpected status code: {response.status_code}")
    
    @task(2)
    def find_pets_by_status(self):
        """
        Test GET /pet/findByStatus endpoint
        Weight: 2 (will be called twice as often as other tasks)
        """
        status = "available"
        endpoint = f"/pet/findByStatus"
        params = {"status": status}
        
        with self.client.get(
            endpoint,
            params=params,
            catch_response=True,
            name="GET /pet/findByStatus"
        ) as response:
            if response.status_code == 200:
                try:
                    pets_data = response.json()
                    # Validate response is a list
                    if isinstance(pets_data, list):
                        response.success()
                        print(f"✓ Found {len(pets_data)} pets with status '{status}'")
                        
                        # Additional validation - check if pets have required fields
                        if pets_data:  # If list is not empty
                            first_pet = pets_data[0]
                            if not all(key in first_pet for key in ['id', 'status']):
                                response.failure("Pet objects missing required fields")
                    else:
                        response.failure("Expected list response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 400:
                response.failure("Invalid status value")
            else:
                response.failure(f"Unexpected status code: {response.status_code}")
    
    @task(1)
    def health_check(self):
        """
        Optional health check task - tests basic connectivity
        Weight: 1 (lower frequency)
        """
        # This endpoint might not exist in Petstore, but good for monitoring
        with self.client.get("/", catch_response=True, name="Health Check") as response:
            # Accept any response as this is just a connectivity check
            if response.status_code in [200, 404, 405]:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")


# Custom event handlers for additional monitoring
from locust import events

@events.request.add_listener
def my_request_handler(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    """
    Custom request handler for logging request details
    """
    if exception:
        print(f"❌ Request failed: {name} - {exception}")
    elif response.status_code >= 400:
        print(f"⚠️  Request error: {name} - Status: {response.status_code}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    Called when test starts
    """
    print("🚀 Starting Petstore API Load Test")
    print(f"Target: {environment.host}")
    print("Endpoints to test:")
    print("  - GET /pet/1")
    print("  - GET /pet/findByStatus?status=available")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    Called when test stops
    """
    print("🏁 Petstore API Load Test Completed")


# Configuration for running the test
if __name__ == "__main__":
    print("To run this test, use the following command:")
    print("locust -f petstore_load_test.py --host=https://petstore.swagger.io/v2 -u 5 -r 1 --run-time 60s --headless")
    print("\nParameters explanation:")
    print("  -f: Locust file")
    print("  --host: Target host")
    print("  -u 5: 5 concurrent users")
    print("  -r 1: Ramp up 1 user per second")
    print("  --run-time 60s: Run for 60 seconds")
    print("  --headless: Run without web UI")
