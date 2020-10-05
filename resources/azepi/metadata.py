import sys


METADATA_CONTENT = '''
labels:
  version: {M_VERSION}
  name: Classic Epiphany on AKS
  short: {M_MODULE_SHORT}
  kind: infrastructure
  provider: azure
'''


def main(variables={}):
    """Handle metadata method."""
    print(METADATA_CONTENT.format(**variables).strip(), file=sys.stdout)
