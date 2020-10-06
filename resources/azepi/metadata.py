"""Implementation of the "metadata" method."""

import sys


METADATA_CONTENT = '''
labels:
  version: {M_VERSION}
  name: Generic Epiphany on AKS
  short: {M_MODULE_SHORT}
  kind: provisioner
  provider: azure
'''


def main(variables={}):
    """Handle metadata method."""
    print(METADATA_CONTENT.format(**variables).strip(), file=sys.stdout)
