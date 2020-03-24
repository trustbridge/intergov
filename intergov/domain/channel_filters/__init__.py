"""
Chanel Filters are used to block messages.

By default, they block all messages.
The .allow_any("attr") method overrides this default behavior,
so if every message attribute is added to the allow_any(),
then the filter will block no messages.

The .whitelist(attr, value) method will allow only those messages
with that exact value for that partiular attribute.
The .blacklist(attr, value) method specifically blocks all messages
with that particular value for that attribute.

Blacklist has higher precedence to order_any.
Adding items to blacklist removes them from whitelist
(and vica versa), so there is no sense in defining precedence between them.
"""
