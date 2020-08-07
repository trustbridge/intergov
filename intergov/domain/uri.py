"""
Messages contain references to things.
We call the value of these references "URIs",
Universal Resource Indicators.

There are different types of URI:

* Name; A kind of "indirect handles"
  to a thing, which may be resolved
  using some kind of resource discovery protocol
* Address; i.e. a URL (web address).
  Better than a name because
  you don't need to resolve it,
  but worse than a name because
  links to URLs break
  when the resource moves.
* Content Address (or multihash).
  Pointer to a resource in a
  Content addressable memory system.
  Has benefits of both name and address,
  but only if the content never changes.

This module is where we define the behavior
of our URI parser/validator.
It's anticipated that this will change
as we collaborate with various stakeholders
about the kinds of URIs that make sense.
"""
try:
    # python2
    from urlparse import urlparse
except ImportError:
    # python3
    from urllib.parse import urlparse

import multihash
from cid import is_cid


class URI:
    def __init__(self, value):
        """
        The URI is initiated with value
        that may or may not be a valid URI.
        """
        self.value = value

    def is_valid(self):
        """
        The public interface of the URI class
        is basically a validation method.

        If the value is valid for any one
        of the allowable URI types,
        then it's considered a valid URI.

        If value starts with /ipfs/ it MUST be multihash or ipfs address
        """
        if not self.value:
            return False
        if self.is_valid_ipfs():
            return True
        if isinstance(self.value, str) and not self.value.startswith('/ipfs/'):
            if self.is_valid_url():
                return True
        if self.is_valid_multihash():
            return True
        if isinstance(self.value, str) and not self.value.startswith('/ipfs/'):
            if self.is_valid_fqn():
                return True
        return False

    def is_valid_url(self):
        """
        Returns true if the URI is a URL.
        """
        try:
            result = urlparse(self.value)
            return all([result.scheme, result.netloc, result.path])
        except Exception:
            return False

    def is_valid_ipfs(self):
        """
        Returns true if the URI is a valid IPFS address.

        i.e. '/ipfs/{some valid multihash}'
        https://docs.ipfs.io/guides/concepts/cid/
        only string (ASCII/UTF-8) CIDs are supported
        https://github.com/ipld/py-cid is required library
        """
        # CIDv0 - multihash
        if not isinstance(self.value, str):
            return False
        if self.value.startswith('/ipfs/'):
            normalized_value = self.value[len('/ipfs/'):]
        else:
            normalized_value = self.value
        try:
            return is_cid(normalized_value)
        except Exception:
            return False

    def is_valid_multihash(self):
        """
        Returns true if the URI is a valid multihash.

        Note: in some scenarios, this could be
        a very interesting URI type.
        If jurisdictions have a way to resolve document repositories,
        and if the resources are unchanging,
        then multihash identifiers have
        the interesting proof characteristics.

        Multihash URIs are complimentary
        of Name URIs
        in distributed asynchronous systems,
        due to the way they support
        "append only" data structures.
        """
        if not isinstance(self.value, str):
            return False
        if self.value.startswith('/ipfs/'):
            normalized_value = self.value[len('/ipfs/'):]
        else:
            normalized_value = self.value
        try:
            return multihash.is_valid(
                multihash.from_b58_string(
                    normalized_value
                )
            )
        except ValueError:
            return False

    def is_valid_fqn(self):
        """
        Returns true if the URI is a Fully Qualified Name.
        i.e. if it is a name can be resolved.

        Current naming scheme requires that a Fully Qualified Name be
        a string containing three or more values separated by a '.'

        Note the relation to the proposed
        UN/CEFACT cross border digital identifier project,
        and UN/CEFACT resource discovery protocol project.
        """
        if not isinstance(self.value, str):
            return False
        return len(self.value.split('.')) > 2

    def __str__(self):
        return str(self.value)
