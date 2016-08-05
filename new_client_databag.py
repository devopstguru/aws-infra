import random
import string
import sys
import click
from collections import OrderedDict
import hvac

def get_vault_client():
    vault_token = os.environ.get('GITHUB_TOKEN', "NO TOKEN FOUND") if 'GITHUB_TOKEN' in os.environ else os.environ.get('VAULT_TOKEN', "NO TOKEN FOUND")
    if vault_token == "NO TOKEN FOUND":
        print "Could not find GITHUB_TOKEN or VAULT_TOKEN in your environment. Have you run `drud secret auth`?"
        sys.exit(1)
    vault_client = hvac.Client(url='https://sanctuary.drud.io:8200', token=vault_token, verify=False)
    
    if vault_client.is_initialized() and vault_client.is_sealed():
        try:
            vault_client.unseal(os.getenv('VAULT_KEY_1', ''))
            vault_client.unseal(os.getenv('VAULT_KEY_2', ''))
            vault_client.unseal(os.getenv('VAULT_KEY_3', ''))
        except:
            pass
    if vault_client.is_initialized() and not vault_client.is_sealed():
        if not vault_client.is_authenticated():
            vault_client.auth_github(vault_token)
        if vault_client.is_authenticated():
            return vault_client

def to_boolean(x):
    return x == 'true' or x == "True"

def rand_string(num_digits=16, string_type=string.hexdigits):
    if string_type == "base64":
        string_type = string.ascii_letters + string.digits + "+" + "/"
    return ''.join([random.choice(string_type) for _ in range(num_digits)])

# sitename = sys.argv[4]
# site_type = sys.argv[5]
# db_server_local = sys.argv[6]
# db_server_staging = sys.argv[7]
# db_server_production = sys.argv[8]
# admin_username = sys.argv[9]
# #production_domain = sys.argv[10]
# new_site = to_boolean(sys.argv[10])
# web_server_staging = sys.argv[11]
# web_server_prod = sys.argv[12]
# wp_active_theme = sys.argv[14]
# wp_multisite = to_boolean(sys.argv[13])

@click.command()
@click.option('--sitename', type=click.STRING)
@click.option('--site-type', type=click.Choice(['wp', 'd7', 'd8', 'none']))
@click.option('--db-server-local', type=click.STRING)
@click.option('--db-server-staging', type=click.STRING)
@click.option('--db-server-production', type=click.STRING)
@click.option('--admin-username', type=click.STRING)
@click.option('--new-site', type=click.BOOL)
@click.option('--web-server-staging', type=click.STRING)
@click.option('--web-server-prod', type=click.STRING)
@click.option('--wp-active-theme', type=click.STRING)
@click.option('--wp-multisite', type=click.BOOL)
def create_bag(sitename, site_type, db_server_local, db_server_staging, db_server_production, admin_username, new_site, web_server_staging, web_server_prod, wp_active_theme, wp_multisite):
    if site_type == 'd7' or site_type == 'd8':
        site_type = 'drupal'

    # values that are consistent across environment and platform
    common = {
        'sitename': sitename,
        'site_type': site_type,
        'apache_owner': 'nginx',
        'apache_group': 'nginx',
        'admin_mail': 'accounts@newmediadenver.com',
        'db_name': sitename,
        'db_username': sitename + '_db',
        'php': {
          'version': "5.6"
        },
        'docroot': '/var/www/' + sitename + '/current/docroot'
    }

    # values that are different per environment
    default = {
        'admin_username': admin_username,
        'admin_password': rand_string(),
        'repository': 'git@github.com:newmediadenver/' + sitename + '.git',
        'revision': 'staging',
        'db_host': db_server_local,
        'db_user_password': rand_string(),
        'server_aliases': [
          "localhost"
        ],
        'hosts': [
            "localhost"
        ]
    }
    staging = {
        'admin_username': admin_username,
        'admin_password': rand_string(),
        'repository': 'git@github.com:newmediadenver/' + sitename + '.git',
        'revision': 'staging',
        'db_host': db_server_staging,
        'db_user_password': rand_string(),
        'server_aliases': [
          sitename + '.nmdev.us'
        ],
        'hosts': [
            web_server_staging
        ]
    }
    production = {
        'admin_username': admin_username,
        'admin_password': rand_string(),
        'repository': 'git@github.com:newmediadenver/' + sitename + '.git',
        'revision': 'master',
        'db_host': db_server_production,
        'db_user_password': rand_string(),
        'server_aliases': [
          sitename + 'prod.nmdev.us'
        ],
        'hosts': [
            web_server_prod
        ]
    }
    client_metadata = {
        'company_legal_name': '',
        'company_city': '',
        'company_state': '',
        'primary_contact': {
            'name': '',
            'phone_number': '',
            'email_address': ''
        },
        'production_url': '',
        'we_are_hosting': True,
        'transactional_email': {
            'provider': '',
            'username': '',
            'password': ''
        },
        'dns': {
            'provider': '',
            'username': '',
            'password': ''
        },
        'ssl': {
            'provider': '',
            'username': '',
            'password': ''
        }
    }
    # Override the production hosts directive if we need to expand a group
    if web_server_prod == 'webcluster01':
        production['hosts'] = [
            'web02.newmediadenver.com',
            'web03.newmediadenver.com',
            'web04.newmediadenver.com'
        ]

    # Override the staging hosts directive if we need to expand a group
    if web_server_staging == 'webstagingcluster01':
        staging['hosts'] = [
            'web01.nmdev.us',
            'web02.nmdev.us'
        ]

    # xtradb specifics
    if db_server_production == 'mysql.newmediadenver.com':
        xtradb = {
            'db_port': '3307',
            'custom_port': 'enabled'
        }
    else:
        xtradb = {}


    # new site
    if new_site == True:
        new_site = {
            'new_site': True,
            'install_profile': sitename
        }
    else:
        new_site = {}


    # Need to set new_site in all envs - add to common
    common = dict(common.items() + new_site.items())

    # values that are different per platform
    if site_type == 'wp':
        type_keys_default = {
            'auth_key': rand_string(48, 'base64'),
            'secure_auth_key': rand_string(48, 'base64'),
            'logged_in_key': rand_string(48, 'base64'),
            'nonce_key': rand_string(48, 'base64'),
            'auth_salt': rand_string(48, 'base64'),
            'secure_auth_salt': rand_string(48, 'base64'),
            'logged_in_salt': rand_string(48, 'base64'),
            'nonce_salt': rand_string(48, 'base64'),
            'url': 'http://localhost:1025',
            'active_theme': wp_active_theme,
            'multisite': wp_multisite
        }
        type_keys_staging = {
            'auth_key': rand_string(48, 'base64'),
            'secure_auth_key': rand_string(48, 'base64'),
            'logged_in_key': rand_string(48, 'base64'),
            'nonce_key': rand_string(48, 'base64'),
            'auth_salt': rand_string(48, 'base64'),
            'secure_auth_salt': rand_string(48, 'base64'),
            'logged_in_salt': rand_string(48, 'base64'),
            'nonce_salt': rand_string(48, 'base64'),
            'url': 'https://' + sitename + '.nmdev.us',
            'active_theme': wp_active_theme,
            'multisite': wp_multisite
        }
        type_keys_production = {
            'auth_key': rand_string(48, 'base64'),
            'secure_auth_key': rand_string(48, 'base64'),
            'logged_in_key': rand_string(48, 'base64'),
            'nonce_key': rand_string(48, 'base64'),
            'auth_salt': rand_string(48, 'base64'),
            'secure_auth_salt': rand_string(48, 'base64'),
            'logged_in_salt': rand_string(48, 'base64'),
            'nonce_salt': rand_string(48, 'base64'),
            'url': 'https://' + sitename + 'prod.nmdev.us',
            'active_theme': wp_active_theme,
            'multisite': wp_multisite
        }
    elif site_type == 'drupal':
        type_keys_default = {
            'hash_salt': rand_string(48, 'base64'),
            'cmi_sync': '/var/www/' + sitename + '/current/sync',
        }
        type_keys_staging = {
            'hash_salt': rand_string(48, 'base64'),
            'cmi_sync': '/var/www/' + sitename + '/current/sync',
        }
        type_keys_production = {
            'hash_salt': rand_string(48, 'base64'),
            'cmi_sync': '/var/www/' + sitename + '/current/sync',
        }
    else:
        type_keys_default = {}
        type_keys_staging = {}
        type_keys_production = {}
        

    # # Construct a new data bag
    # bag_item = Chef::DataBagItem.new
    bag_item = OrderedDict()
    # bag_item.data_bag('nmdhosting')
    bag_item['id'] = sitename
    bag_item['_default'] = dict(common.items() + default.items() + type_keys_default.items())
    bag_item['staging'] = dict(common.items() + staging.items() + type_keys_staging.items())
    bag_item['production'] = dict(common.items() + production.items() + xtradb.items() + type_keys_production.items())
    bag_item['client_metadata'] = client_metadata

    client = get_vault_client()
    client.write('secret/nmdhosting/' + sitename, **bag_item)
    # # Encrypt and save new data bag
    # enc_hash = Chef::EncryptedDataBagItem.encrypt_data_bag_item(bag_item, secret)
    # ebag_item = Chef::DataBagItem.from_hash(enc_hash)
    # ebag_item.data_bag('nmdhosting')
    # ebag_item.save
if __name__ == '__main__':
    create_bag()


    
