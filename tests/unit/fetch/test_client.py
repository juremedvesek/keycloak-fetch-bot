from pytest import mark
from pytest_unordered import unordered
import json
import os
from kcfetcher.fetch import ClientFetch
from kcfetcher.store import Store
from kcfetcher.utils import remove_folder, make_folder, login, find_in_list


@mark.vcr()
class TestClientFetch_vcr:
    def test_fetch(self):
        datadir = "output/ci/outd"
        remove_folder(datadir)
        make_folder(datadir)
        store_api = Store(datadir)
        server = os.environ["SSO_API_URL"]
        user = os.environ["SSO_API_USERNAME"]
        password = os.environ["SSO_API_PASSWORD"]
        kc = login(server, user, password)
        realm_name = "ci0-realm"
        resource_name = "clients"
        resource_identifier = "clientId"

        obj = ClientFetch(kc, resource_name, resource_identifier, realm_name)

        obj.fetch(store_api)

        # check generated content
        assert os.listdir(datadir) == unordered(["client-0", "client-1"])
        assert os.listdir(os.path.join(datadir, "client-0")) == unordered(['ci0-client-0.json', 'scope-mappings.json', 'roles'])
        assert os.listdir(os.path.join(datadir, "client-0/roles")) == ['roles.json']
        assert os.listdir(os.path.join(datadir, "client-1")) == unordered(['ci0-client-1.json', 'scope-mappings.json', 'roles'])
        assert os.listdir(os.path.join(datadir, "client-1/roles")) == ['roles.json']
        #
        data = json.load(open(os.path.join(datadir, "client-0/ci0-client-0.json")))
        assert list(data.keys()) == [
            'access',
            'alwaysDisplayInConsole',
            'attributes',
            'authenticationFlowBindingOverrides',
            'bearerOnly',
            'clientAuthenticatorType',
            'clientId',
            'consentRequired',
            'defaultClientScopes',
            'description',
            'directAccessGrantsEnabled',
            'enabled',
            'frontchannelLogout',
            'fullScopeAllowed',
            'implicitFlowEnabled',
            'name',
            'nodeReRegistrationTimeout',
            'notBefore',
            'optionalClientScopes',
            'protocol',
            'publicClient',
            'redirectUris',
            'serviceAccountsEnabled',
            'standardFlowEnabled',
            'surrogateAuthRequired',
            'webOrigins',
        ]
        assert data["clientId"] == "ci0-client-0"
        assert data["name"] == "ci0-client-0-name"
        assert os.listdir(os.path.join(datadir, "client-0/roles")) == ['roles.json']

        # authenticationFlowBindingOverrides must contain names, not UUIDs
        assert isinstance(data["authenticationFlowBindingOverrides"], dict)
        assert list(data["authenticationFlowBindingOverrides"].keys()) == ["browser"]
        assert data["authenticationFlowBindingOverrides"]["browser"] == "browser"

        # =======================================================================================
        # Check client scope mappings
        data_unsorted = json.load(open(os.path.join(datadir, "client-0/scope-mappings.json")))
        data = sorted(data_unsorted, key=lambda obj: obj["name"])
        assert isinstance(data, list)
        assert len(data) == 3

        assert list(data[0].keys()) == [
            'clientRole',
            'containerName',
            'name',
        ]

        assert data[0]["name"] == "ci0-client1-role0"
        assert data[0]["clientRole"] is True
        assert data[0]["containerName"] == "ci0-client-1"

        assert data[1]["name"] == "ci0-role-0"
        assert data[1]["clientRole"] is False
        assert data[1]["containerName"] == "ci0-realm"

        assert data[2]["name"] == "ci0-role-1b"
        assert data[2]["clientRole"] is False
        assert data[2]["containerName"] == "ci0-realm"

        # =======================================================================================
        # Check client role
        data = json.load(open(os.path.join(datadir, "client-0/roles/roles.json")))
        assert isinstance(data, list)
        assert len(data) == 4

        role = find_in_list(data, name="ci0-client0-role0")
        assert list(role.keys()) == [
            'attributes',
            'clientRole',
            'composite',
            # containerId UUID - clientId, it MUST be removed.
            # The parent client clientId will be derived from roles.json filepath.
            # 'containerId',
            'description',
            'name',
        ]
        assert role["name"] == "ci0-client0-role0"
        assert role["description"] == "ci0-client0-role0-desc"
        assert role["clientRole"] is True
        assert role["composite"] is False
        assert role["attributes"] == {"ci0-client0-role0-key0": ["ci0-client0-role0-value0"]}

        role = find_in_list(data, name="ci0-client0-role1")
        assert list(role.keys()) == [
            'attributes',
            'clientRole',
            'composite',
            'composites',
            # 'containerId',
            'description',
            'name',
        ]
        assert role["name"] == "ci0-client0-role1"
        assert role["description"] == "ci0-client0-role1-desc"
        assert role["clientRole"] is True
        assert role["composite"] is True
        assert role["attributes"] == {"ci0-client0-role1-key0": ["ci0-client0-role1-value0"]}
        assert len(role["composites"]) == 3
        #
        composites_sorted = sorted(role["composites"], key=lambda obj: obj["name"])
        assert list(composites_sorted[0].keys()) == [
            'clientRole',
            # 'composite',
            'containerName',
            # 'description',
            'name',
        ]
        # check only important attributes.
        assert composites_sorted[0]["clientRole"] is True
        assert composites_sorted[0]["containerName"] == "ci0-client-0"
        assert composites_sorted[0]["name"] == "ci0-client0-role1a"
        #
        assert composites_sorted[1]["clientRole"] is True
        assert composites_sorted[1]["containerName"] == "ci0-client-0"
        assert composites_sorted[1]["name"] == "ci0-client0-role1b"
        #
        assert composites_sorted[2]["clientRole"] is False
        assert composites_sorted[2]["containerName"] == "ci0-realm"
        assert composites_sorted[2]["name"] == "ci0-role-1a"
