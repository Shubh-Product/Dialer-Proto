import requests
import sys
from datetime import datetime

class DemoAPITester:
    def __init__(self, base_url="https://lead-dialer-2.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.demo_ids = []

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"Response: {response.text}")
                except:
                    pass
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_seed_demos(self):
        """Test seeding demo data"""
        success, response = self.run_test(
            "Seed Demos",
            "POST",
            "seed-demos",
            200
        )
        return success

    def test_get_demos(self):
        """Test getting all demos"""
        success, response = self.run_test(
            "Get All Demos",
            "GET",
            "demos",
            200
        )
        if success and isinstance(response, list):
            print(f"   Found {len(response)} demos")
            if len(response) > 0:
                self.demo_ids = [demo['id'] for demo in response if 'id' in demo]
                print(f"   Demo IDs: {self.demo_ids[:3]}...")
        return success

    def test_create_demo(self):
        """Test creating a new demo"""
        demo_data = {
            "time_slot": "16:00 - 16:30",
            "demo_time": "4:15 PM",
            "client_name": "Test Client",
            "company_name": "Test Company",
            "mobile": "9999999999",
            "status": "Pending",
            "date_type": "Today"
        }
        success, response = self.run_test(
            "Create Demo",
            "POST",
            "demos",
            200,
            data=demo_data
        )
        if success and 'id' in response:
            self.demo_ids.append(response['id'])
            print(f"   Created demo with ID: {response['id']}")
        return success

    def test_update_demo(self):
        """Test updating a demo"""
        if not self.demo_ids:
            print("⚠️  Skipping update test - no demo IDs available")
            return True
        
        demo_id = self.demo_ids[0]
        update_data = {
            "status": "Completed"
        }
        success, response = self.run_test(
            "Update Demo Status",
            "PUT",
            f"demos/{demo_id}",
            200,
            data=update_data
        )
        if success:
            print(f"   Updated demo {demo_id} status to Completed")
        return success

    def test_delete_demo(self):
        """Test deleting a demo"""
        if len(self.demo_ids) < 2:
            print("⚠️  Skipping delete test - not enough demo IDs")
            return True
        
        demo_id = self.demo_ids[-1]
        success, response = self.run_test(
            "Delete Demo",
            "DELETE",
            f"demos/{demo_id}",
            200
        )
        if success:
            print(f"   Deleted demo {demo_id}")
        return success

    def test_leads_api(self):
        """Test leads API (for dialing integration)"""
        # Seed leads
        success1, _ = self.run_test(
            "Seed Leads",
            "POST",
            "seed",
            200
        )
        
        # Get leads
        success2, response = self.run_test(
            "Get All Leads",
            "GET",
            "leads",
            200
        )
        if success2 and isinstance(response, list):
            print(f"   Found {len(response)} leads")
        
        return success1 and success2

def main():
    print("=" * 60)
    print("DEMO API TESTING")
    print("=" * 60)
    
    tester = DemoAPITester()
    
    # Run tests in sequence
    print("\n📋 Testing Demo APIs...")
    tester.test_seed_demos()
    tester.test_get_demos()
    tester.test_create_demo()
    tester.test_update_demo()
    tester.test_delete_demo()
    
    print("\n📋 Testing Leads API (for integration)...")
    tester.test_leads_api()
    
    # Print results
    print("\n" + "=" * 60)
    print(f"📊 RESULTS: {tester.tests_passed}/{tester.tests_run} tests passed")
    print("=" * 60)
    
    if tester.tests_passed == tester.tests_run:
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {tester.tests_run - tester.tests_passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
