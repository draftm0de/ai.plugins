"""Constants and the Conflict error of the setup state helper."""
import re


MANIFEST_KEYS = {'schema_version', 'product', 'requires_marketplace', 'derived'}


SYNC_KEYS = {'schema_version', 'files', 'removed'}


HASH_HINT = ' (run make build-skeleton-hashes in the Plugin Manager repository)'


# A folder without configuration evidence and without plugin.json/marketplace.json is a valid target when it holds
# nothing but these top-level entries plus the common skeleton paths of the planning kind (names only; .git and
# .idea are never opened).
BASE_ENTRIES = ('.git', '.idea', '.gitignore', '.project')


PROJECT_ENTRIES = ('operator.json', 'plugins')


IGNORE_RULE = '/.project/operator.json'


OLD_LOCK_PATH = '.project/plugin.skeleton.lock.json'  # former location: unsupported, never read or migrated


EVIDENCE_PATH = '.project/plugins/{plugin}/config.json'


SKELETON_PATH = '.project/plugins/{plugin}/skeleton.json'


EVIDENCE_KEYS = {'schema_version', 'plugin', 'kind', 'artifact', 'configured_at', 'marketplace'}


EVIDENCE_VERSION = 2


LOCAL_PATH = '.project/plugins/{plugin}/local.json'  # ignored, machine-specific: path of the one marketplace checkout


LOCAL_KEYS = {'schema_version', 'marketplace_path'}


TIMESTAMP = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z')


LANGUAGE_PATH = '.project/operator.json'


NAME = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')


SHA256 = re.compile(r'[0-9a-f]{64}')


class Conflict(Exception):
    def __init__(self, path, reason, code=None, entries=None):
        super().__init__(reason)
        self.path, self.reason, self.code, self.entries = path, reason, code, entries


LOCK_VERSION = 2
