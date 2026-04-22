import logging
import re


class MaskedDataFilter(logging.Filter):
    def filter(self, record):
        # TODO: add more data masking rules
        rules = [
            (r'password":"\S*"', 'password":"[redacted]"'),
            # mask passwords in connection strings
            (r'([a-zA-Z0-9+.-]+://[^/\s:@]+:)([^@\s]+)(@[^?\s#]+)', r'\1[redacted]\3')
        ]

        if hasattr(record, "msg") and isinstance(record.msg, str):
            for old, new in rules:
                record.msg = re.sub(old, new, record.msg)

        return True
