from zerver.actions.realm_playgrounds import do_add_realm_playground
from zerver.lib.test_classes import ZulipTestCase
from zerver.models import RealmPlayground, get_realm


class RealmPlaygroundTests(ZulipTestCase):
    def test_create_one_playground_entry(self) -> None:
        iago = self.example_user("iago")

        payload = {
            "name": "Python playground",
            "pygments_language": "Python",
            "url_prefix": "https://python.example.com",
        }
        # Now send a POST request to the API endpoint.
        resp = self.api_post(iago, "/api/v1/realm/playgrounds", payload)
        self.assert_json_success(resp)

        # Check if the actual object exists
        realm = get_realm("zulip")
        self.assertTrue(
            RealmPlayground.objects.filter(realm=realm, name="Python playground").exists()
        )

    def test_create_multiple_playgrounds_for_same_language(self) -> None:
        iago = self.example_user("iago")

        data = [
            {
                "name": "Python playground 1",
                "pygments_language": "Python",
                "url_prefix": "https://python.example.com",
            },
            {
                "name": "Python playground 2",
                "pygments_language": "Python",
                "url_prefix": "https://python2.example.com",
            },
        ]
        for payload in data:
            resp = self.api_post(iago, "/api/v1/realm/playgrounds", payload)
            self.assert_json_success(resp)

        realm = get_realm("zulip")
        self.assertTrue(
            RealmPlayground.objects.filter(realm=realm, name="Python playground 1").exists()
        )
        self.assertTrue(
            RealmPlayground.objects.filter(realm=realm, name="Python playground 2").exists()
        )

    def test_invalid_params(self) -> None:
        iago = self.example_user("iago")

        payload = {
            "name": "Invalid URL",
            "pygments_language": "Python",
            "url_prefix": "https://invalid-url",
        }
        resp = self.api_post(iago, "/api/v1/realm/playgrounds", payload)
        self.assert_json_error(resp, "url_prefix is not a URL")

        payload["url_prefix"] = "https://python.example.com"
        payload["pygments_language"] = "a$b$c"
        resp = self.api_post(iago, "/api/v1/realm/playgrounds", payload)
        self.assert_json_error(resp, "Invalid characters in pygments language")

        payload = {
            "name": "Template with an unexpected variable",
            "pygments_language": "Python",
            "url_prefix": "https://template.com?test={test}",
        }
        resp = self.api_post(iago, "/api/v1/realm/playgrounds", payload)
        self.assert_json_error(
            resp, '"code" should be the only variable present in the URL template'
        )

        payload = {
            "name": "Invalid URL template",
            "pygments_language": "Python",
            "url_prefix": "https://template.com?test={test",
        }
        resp = self.api_post(iago, "/api/v1/realm/playgrounds", payload)
        self.assert_json_error(resp, "Invalid URL template.")

    def test_create_already_existing_playground(self) -> None:
        iago = self.example_user("iago")

        payload = {
            "name": "Python playground",
            "pygments_language": "Python",
            "url_prefix": "https://python.example.com",
        }
        resp = self.api_post(iago, "/api/v1/realm/playgrounds", payload)
        self.assert_json_success(resp)

        resp = self.api_post(iago, "/api/v1/realm/playgrounds", payload)
        self.assert_json_error(
            resp, "Realm playground with this Realm, Pygments language and Name already exists."
        )

    def test_not_realm_admin(self) -> None:
        hamlet = self.example_user("hamlet")

        resp = self.api_post(hamlet, "/api/v1/realm/playgrounds")
        self.assert_json_error(resp, "Must be an organization administrator")

        resp = self.api_delete(hamlet, "/api/v1/realm/playgrounds/1")
        self.assert_json_error(resp, "Must be an organization administrator")

    def test_delete_realm_playground(self) -> None:
        iago = self.example_user("iago")
        realm = get_realm("zulip")

        playground_id = do_add_realm_playground(
            realm,
            acting_user=iago,
            name="Python playground",
            pygments_language="Python",
            url_prefix="https://python.example.com",
        )
        self.assertTrue(RealmPlayground.objects.filter(name="Python playground").exists())

        result = self.api_delete(iago, f"/api/v1/realm/playgrounds/{playground_id + 1}")
        self.assert_json_error(result, "Invalid playground")

        result = self.api_delete(iago, f"/api/v1/realm/playgrounds/{playground_id}")
        self.assert_json_success(result)
        self.assertFalse(RealmPlayground.objects.filter(name="Python").exists())
