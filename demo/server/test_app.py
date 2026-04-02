import unittest
import json
from fastapi.testclient import TestClient
from app import app
from models import Namespace, ObjectType, ObjectInstanceMinimal
import threading
import time
import asyncio


class TestI3XEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)

    def test_namespaces_endpoint(self):
        """Test RFC 4.1.1 - Namespaces"""
        response = self.client.get("/namespaces")
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])
        self.assertIsInstance(data["result"], list)

    def test_object_types_endpoint(self):
        """Test RFC 4.1.3 - Object Types"""
        response = self.client.get("/objecttypes")
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])
        self.assertIsInstance(data["result"], list)

    def test_object_type_definition_endpoint(self):
        """Test RFC 4.1.2 - Object Type Definition (POST /objecttypes/query)"""
        # Test single elementId (via array)
        response = self.client.post("/objecttypes/query", json={"elementIds": ["work-center-type"]})
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])
        succeeded = [r for r in data["results"] if r["success"]]
        self.assertEqual(len(succeeded), 1)
        self.assertEqual(succeeded[0]["elementId"], "work-center-type")

        # Test non-existent type (appears as failed)
        response = self.client.post("/objecttypes/query", json={"elementIds": ["non-existent"]})
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(data["success"])
        self.assertEqual(len([r for r in data["results"] if not r["success"]]), 1)

    def test_object_type_definition_batch(self):
        """Test RFC 4.1.2 - Object Type Definition batch query"""
        response = self.client.post("/objecttypes/query", json={
            "elementIds": ["work-center-type", "non-existent"]
        })
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertFalse(data["success"])  # one item failed
        self.assertEqual(len([r for r in data["results"] if r["success"]]), 1)
        self.assertEqual(len([r for r in data["results"] if not r["success"]]), 1)

    def test_instances_endpoint(self):
        """Test RFC 4.1.6 - Instances of an Object Type"""
        response = self.client.get("/objects")
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])
        self.assertIsInstance(data["result"], list)

    def test_object_definition_endpoint(self):
        """Test RFC 4.1.8 - Object Definition (POST /objects/list)"""
        # Test single elementId (via array)
        response = self.client.post("/objects/list", json={"elementIds": ["pump-101"]})
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])
        succeeded = [r for r in data["results"] if r["success"]]
        self.assertEqual(len(succeeded), 1)
        self.assertEqual(succeeded[0]["elementId"], "pump-101")

        # Test non-existent object (appears as failed)
        response = self.client.post("/objects/list", json={"elementIds": ["non-existent"]})
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(data["success"])
        self.assertEqual(len([r for r in data["results"] if not r["success"]]), 1)

    def test_object_definition_batch(self):
        """Test RFC 4.1.8 - Object Definition batch query"""
        response = self.client.post("/objects/list", json={
            "elementIds": ["pump-101", "pump-101-state", "non-existent"]
        })
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertFalse(data["success"])  # one item failed
        self.assertEqual(len([r for r in data["results"] if r["success"]]), 2)
        self.assertEqual(len([r for r in data["results"] if not r["success"]]), 1)

    def test_last_known_value_endpoint(self):
        """Test RFC 4.2.1.1 - Object Element LastKnownValue (POST /objects/value)"""
        # Test single elementId (via array)
        response = self.client.post("/objects/value", json={"elementIds": ["pump-101-state"]})
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])
        succeeded = [r for r in data["results"] if r["success"]]
        self.assertEqual(len(succeeded), 1)
        item = succeeded[0]
        self.assertEqual(item["elementId"], "pump-101-state")
        self.assertIn("value", item["result"])

        # Test with maxDepth (0=infinite, 2=recurse to depth 2)
        response = self.client.post("/objects/value", json={"elementIds": ["pump-101"], "maxDepth": 2})
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(data, dict)

    def test_last_known_value_batch(self):
        """Test RFC 4.2.1.1 - LastKnownValue batch query"""
        response = self.client.post("/objects/value", json={
            "elementIds": ["pump-101-state", "pump-101-measurements"],
            "maxDepth": 1
        })
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(data, dict)
        succeeded_ids = [item["elementId"] for item in data["results"] if item["success"]]
        self.assertIn("pump-101-state", succeeded_ids)
        self.assertIn("pump-101-measurements", succeeded_ids)

    def test_related_objects_endpoint(self):
        """Test RFC 4.1.6 - Related Objects (POST /objects/related)"""
        response = self.client.post("/objects/related", json={"elementIds": ["pump-101"]})
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])
        self.assertIn("results", data)

    def test_historical_values_endpoint(self):
        """Test RFC 4.2.1.2 - Historical Values (POST /objects/history)"""
        response = self.client.post("/objects/history", json={"elementIds": ["pump-101-state"]})
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(data, dict)
        succeeded = [r for r in data["results"] if r["success"]]
        self.assertEqual(len(succeeded), 1)
        item = succeeded[0]
        self.assertEqual(item["elementId"], "pump-101-state")
        self.assertIsInstance(item["result"], dict)
        self.assertIn("values", item["result"])
        self.assertIsInstance(item["result"]["values"], list)

    def test_relationship_type_query_endpoint(self):
        """Test RFC 4.1.4 - Relationship Type query (POST /relationshiptypes/query)"""
        response = self.client.post("/relationshiptypes/query", json={"elementIds": ["HasComponent"]})
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(data, dict)
        self.assertIn("results", data)

    def test_include_metadata(self):
        """Test RFC 3.1.2 - Optional Object Metadata returned when includeMetadata=true"""
        # Without metadata: base fields only, no metadata block
        response = self.client.post("/objects/list", json={"elementIds": ["pump-101"], "includeMetadata": False})
        data = response.json()
        self.assertTrue(data["success"])
        result = data["results"][0]["result"]
        self.assertNotIn("metadata", result)

        # With metadata: all metadata fields present
        response = self.client.post("/objects/list", json={"elementIds": ["pump-101"], "includeMetadata": True})
        data = response.json()
        self.assertTrue(data["success"])
        result = data["results"][0]["result"]
        self.assertIn("metadata", result)
        metadata = result["metadata"]

        # description
        self.assertIn("description", metadata)
        self.assertIsInstance(metadata["description"], str)
        self.assertEqual(metadata["description"], "Primary centrifugal pump supplying coolant to Tank 201 on the west production line")

        # type provenance fields
        self.assertIn("typeNamespaceUri", metadata)
        self.assertEqual(metadata["typeNamespaceUri"], "https://isa.org/isa95")
        self.assertIn("sourceTypeId", metadata)
        self.assertEqual(metadata["sourceTypeId"], "WorkUnitType")

        # relationships
        self.assertIn("relationships", metadata)

        # vendor/system fields go into metadata.system
        self.assertIn("system", metadata)
        self.assertIn("operationStartDate", metadata["system"])
        self.assertIn("lastMaintainedDate", metadata["system"])

        # Objects without description should omit metadata.description
        response = self.client.post("/objects/list", json={"elementIds": ["pump-101-state"], "includeMetadata": True})
        data = response.json()
        self.assertTrue(data["success"])
        result = data["results"][0]["result"]
        self.assertIn("metadata", result)
        self.assertNotIn("description", result["metadata"])

    def test_request_validation_errors(self):
        """Test request validation - must provide elementIds array"""
        # elementIds not provided
        response = self.client.post("/objects/list", json={})
        self.assertEqual(response.status_code, 422)

        # Empty array provided
        response = self.client.post("/objects/list", json={"elementIds": []})
        self.assertEqual(response.status_code, 422)

    def test_hierarchical_relationships_endpoint(self):
        """Test RFC 4.1.4 - Relationship Types"""
        response = self.client.get("/relationshiptypes")
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])
        self.assertIsInstance(data["result"], list)

    # TODO this probably belongs on the client side and is more than a unit test, placing here so I have a place to test subscriptions
    def test_streaming_subscription(self):
        # Step 1: Create a subscription
        response = self.client.post("/subscriptions", json={})
        self.assertEqual(response.status_code, 200)
        subscription_id = response.json()["result"]["subscriptionId"]
        self.assertIsNotNone(subscription_id)

        # Step 2: Register monitored items
        payload = {"subscriptionId": subscription_id, "elementIds": ["sensor-001"]}
        response = self.client.post("/subscriptions/register", json=payload)
        self.assertEqual(response.status_code, 200)

        # Step 3: Start streaming
        # We will run the streaming request in a separate thread to allow timeout
        results = []

        def stream_reader():
            with self.client.stream("POST", "/subscriptions/stream", json={"subscriptionId": subscription_id}) as stream_resp:
                self.assertEqual(stream_resp.status_code, 200)
                count = 0
                for line in stream_resp.iter_lines():
                    if line:
                        decoded = line.decode("utf-8")
                        print("Received chunk:", decoded)
                        results.append(decoded)
                        count += 1
                        if count >= 3:  # read 3 update batches then stop
                            break

        thread = threading.Thread(target=stream_reader)
        thread.start()
        thread.join(timeout=10)

        # Check that we got streaming data and parseable JSON
        self.assertGreaterEqual(
            len(results), 1, "Did not receive any streaming updates"
        )

        for chunk in results:
            data = json.loads(chunk)
            self.assertIsInstance(data, list)
            self.assertTrue(all("elementId" in update for update in data))


if __name__ == "__main__":
    unittest.main()
