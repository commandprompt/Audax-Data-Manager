import unittest

from app.bgjob.process_executor import parse_pigz_tail


class ParsePigzTailTests(unittest.TestCase):
    def test_genuine_backup_pipe_tail_is_parsed(self):
        tokens = parse_pigz_tail("| pigz -p4 -6 > /tmp/backup.dump.gz")
        self.assertEqual(tokens, ["|", "pigz", "-p4", "-6", ">", "/tmp/backup.dump.gz"])

    def test_genuine_backup_tail_with_quoted_spacey_filename_is_parsed(self):
        tokens = parse_pigz_tail("| pigz -p4 -6 > '/tmp/test backup.dump.gz'")
        self.assertEqual(tokens, ["|", "pigz", "-p4", "-6", ">", "/tmp/test backup.dump.gz"])

    def test_genuine_restore_decompress_tail_is_parsed(self):
        tokens = parse_pigz_tail("pigz -dc -p2 /tmp/backup.dump.gz")
        self.assertEqual(tokens, ["pigz", "-dc", "-p2", "/tmp/backup.dump.gz"])

    def test_plain_filename_without_spaces_is_not_a_pigz_tail(self):
        self.assertIsNone(parse_pigz_tail("/tmp/backup.dump.gz"))

    def test_filename_with_apostrophe_does_not_raise(self):
        # a literal, unbalanced quote character in a real filename must not
        # blow up shlex.split for ordinary, non-pigz jobs
        self.assertIsNone(parse_pigz_tail("/tmp/O'Brien.dump"))

    def test_plain_filename_with_multiple_spaces_is_not_misdetected_as_pigz(self):
        # three whitespace-separated words alone isn't enough evidence -
        # it must also carry the "|" or "-dc" marker we generate ourselves
        self.assertIsNone(parse_pigz_tail("/tmp/a b c.dump"))

    def test_two_word_string_is_not_a_pigz_tail(self):
        self.assertIsNone(parse_pigz_tail("pigz -dc"))

    def test_filename_containing_dash_dc_word_is_not_misdetected_as_pigz(self):
        # "-dc" alone isn't proof of a pigz tail - the leading token must
        # actually be a pigz executable
        self.assertIsNone(parse_pigz_tail("/tmp/report -dc final.dump"))

    def test_pigz_with_custom_absolute_path_is_still_recognized(self):
        tokens = parse_pigz_tail("| /usr/local/bin/pigz -6 > /tmp/backup.dump.gz")
        self.assertEqual(
            tokens, ["|", "/usr/local/bin/pigz", "-6", ">", "/tmp/backup.dump.gz"]
        )

    def test_backup_tail_missing_redirect_operator_is_rejected(self):
        # leading "|" and a pigz executable alone aren't enough without ">"
        self.assertIsNone(parse_pigz_tail("| pigz -6 -p4 /tmp/backup.dump.gz"))


if __name__ == "__main__":
    unittest.main()
